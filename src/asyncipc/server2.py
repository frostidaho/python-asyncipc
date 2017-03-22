# http://stackoverflow.com/a/27198531
# https://github.com/joidegn/leo-cli
# https://pymotw.com/2/socket/uds.html
import asyncio
from collections import namedtuple

from .serializer2 import Serialize
from ._utils import get_logger as _get_logger, KILL_SERVER as _KILL_SERVER

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
        client.stop_server()
        debug(f"Sent kill server message")
        return True
    except ConnectionRefusedError:
        debug(f"Couldn't message other server; deleting socket {path!r}")
        from os import remove
        remove(path)
        return True


class Server:
    _serial = Serialize()
    def __init__(self, socket_path, obj, loop=None):
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.logr = _get_logger()
        self.socket_path = socket_path
        self.logr.debug(f'server given socket path {socket_path!r}')
        self.obj = obj
        self.messages = []

    def __call__(self):
        close_other_server(self.socket_path)
        coro = asyncio.start_unix_server(self.listener, path=self.socket_path)
        loop = self.loop
        loop.run_until_complete(coro)
        return loop

    async def get_header(self, reader):
        serial = self._serial
        data = await reader.read(serial.header_length)
        return serial.load(data)

    async def listener(self, reader, writer):
        logr = self.logr
        logr.debug(f"In listener!")
        header = await self.get_header(reader)
        value = await reader.read(header.data_length)
        msg = header.data_loader(value)
        logr.debug(f"Received {msg!r}")
        res = await self.dispatcher(msg)
        self.messages.append(msg)
        writer.close()

    async def dispatcher(self, msg):
        self.logr.debug(f'received message {msg}')
        name, args, kwargs = msg
        try:
            method = getattr(self.obj, name)
            self.logr.debug('need to implement dispatcher!')
        except TypeError:
            if tuple(name) == _KILL_SERVER:
                self.loop.stop()
                return
        return NotImplemented

