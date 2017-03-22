# http://stackoverflow.com/a/27198531
# https://github.com/joidegn/leo-cli
# https://pymotw.com/2/socket/uds.html
import asyncio
from collections import namedtuple
from os import path as _path

from . import _utils
from .serializer2 import Serialize


class Server:
    _serial = Serialize()
    def __init__(self, socket_path, obj):
        self.logr = _utils.get_logger()
        self.socket_path = socket_path
        self.logr.debug(f'server given socket path {socket_path!r}')
        self.obj = obj
        self.messages = []

    def __call__(self, loop):
        self.loop = loop
        coro = asyncio.start_unix_server(self.listener, path=self.socket_path)
        loop.run_until_complete(coro)

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
            if tuple(name) == _utils.KILL_SERVER:
                self.loop.stop()
                return
        return NotImplemented
