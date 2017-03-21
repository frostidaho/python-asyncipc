# http://stackoverflow.com/a/27198531
# https://github.com/joidegn/leo-cli
# https://pymotw.com/2/socket/uds.html
import asyncio
from os import path as _path

from . import _utils
from .serializer import Serialize

class Server:
    def __init__(self, socket_name, message_types):
        self.socket_path = _path.join(_utils.RUNTIME_DIR, socket_name)
        self.logr = _utils.get_logger()
        self.serial = Serialize(**message_types)
        self.messages = asyncio.Queue(30)
        d_observer = {}
        for key in message_types:
            d_observer[key] = []
        self.observers = d_observer

    def register(self, msgtype, fn):
        d = self.observers
        if isinstance(msgtype, str):
            d[msgtype].append(fn)
        else:
            d[msgtype.__name__].append(fn)

    def __call__(self, loop):
        coro = asyncio.start_unix_server(self.listener, path=self.socket_path)
        loop.run_until_complete(coro)
        loop.create_task(self.queue_reader())

    async def queue_reader(self):
        while True:
            msg = await self.messages.get()
            msg_type = msg.__class__.__name__
            observers = self.observers[msg_type]
            if observers:
                for fn in observers:
                    fn(msg)
            else:
                self.logr.debug(f'{msg_type} has no observers')

    async def get_header(self, reader):
        data = await reader.read(self.serial.header_length)
        return self.serial.load(data)

    async def listener(self, reader, writer):
        logr = self.logr
        logr.debug(f"In listener!")
        header = await self.get_header(reader)
        value = await reader.read(header.data_length)
        msg = header.data_loader(value)
        logr.debug(f"Received {msg!r}")
        await self.messages.put(msg)
        # self.msg = msg

        # writer.close()
        # writer.write(b'got it')
        # try:
        #     await writer.drain()
        #     logr.debug("Closing the client socket")
        #     writer.close()
        # except ConnectionResetError:
        #     pass
        return
