# http://stackoverflow.com/a/27198531
# https://github.com/joidegn/leo-cli
# https://pymotw.com/2/socket/uds.html
import asyncio
from collections import namedtuple
from functools import partial

from .serializer import Serialize, ServerHeader, LoadSuccess, LoadFailed
from ._utils import get_logger as _get_logger
from ._utils import CmdContext, INITIAL_MSG_LEN
from ._utils import RECEIVED_MSG

def close_other_server(path):
    """Closer or kill any server that is bound to the socket at path"""
    from socket import socket, AF_UNIX, SOCK_STREAM
    debug = _get_logger().debug
    sock = socket(AF_UNIX, SOCK_STREAM)
    try:
        sock.bind(path)
        sock.close()
        return True
    except OSError:
        debug(f"Can't bind socket to {path!r}")
    from .client import Client
    client = Client(path)
    client.connect_timeout = 0.5
    debug(f"Attempting to kill server {path!r}")
    try:
        client.server_stop()
        debug(f"Sent kill server message")
        return True
    except ConnectionRefusedError:
        debug(f"Couldn't message other server; deleting socket {path!r}")
        from os import remove
        remove(path)
        return True


class Server:
    _serial = Serialize(ServerHeader)
    def __init__(self, socket_path, obj, loop=None):
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.logr = _get_logger()
        self.socket_path = socket_path
        self.logr.debug(f'server given socket path {socket_path!r}')
        self.obj = obj
        self._init_executors()
        self.message_id = 0

    def _init_executors(self):
        from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
        self.thread_executor = ThreadPoolExecutor()
        self.proc_executor = ProcessPoolExecutor()

    def __call__(self):
        # Not sure if all of close_other_server()
        # is still necessary https://bugs.python.org/issue28399
        close_other_server(self.socket_path)
        coro = asyncio.start_unix_server(self.listener, path=self.socket_path)
        loop = self.loop
        loop.run_until_complete(coro)
        return loop

    async def get_header(self, reader):
        load = self._serial.load
        data = await reader.read(INITIAL_MSG_LEN)
        loaded = load(data)
        if isinstance(loaded, LoadSuccess):
            return loaded
        data = await reader.read(loaded.remaining)
        return loaded.data_loader(data)

    async def listener(self, reader, writer):
        logr = self.logr
        logr.debug(f"In listener!")
        loaded = await self.get_header(reader)
        logr.debug(f"listener() received {loaded!r}")
        want_result = loaded.header.want_result
        dump = self._serial.dump

        if want_result:
            mid = self.message_id
            self.message_id += 1
            bmsg = dump(RECEIVED_MSG, message_id=mid)
            writer.write(bmsg)

        res = await self.dispatcher(loaded.header, loaded.data)
        logr.debug(f"listener() got result {res!r}")

        if want_result:
            bmsg = dump(res, message_id=mid)
            writer.write(bmsg)

        await writer.drain()
        writer.close()

    async def dispatcher(self, header, data):
        debug = self.logr.debug
        debug(f'dispatcher received message {header!r} and {data!r}')
        ctx, name, args, kwargs = data
        ctx = getattr(CmdContext, ctx)
        if ctx == CmdContext.SERVER:
            obj = self
        else:
            obj = self.obj
        method = getattr(obj, name)
        fn = partial(method, *args, **kwargs)

        if ctx in {CmdContext.SERVER, CmdContext.BLOCKING}:
            return fn()
        elif ctx == CmdContext.THREAD:
            fut = await self.loop.run_in_executor(self.thread_executor, fn)
        elif ctx == CmdContext.PROCESS:
            fut = await self.loop.run_in_executor(self.process_executor, fn)
        else:
            raise NotImplementedError(f'CmdContext {ctx} has not been implemented')
        return fut.result()

    def stop(self, *args, **kwargs):
        self.proc_executor.shutdown(wait=False)
        self.thread_executor.shutdown(wait=False)
        self.loop.stop()
