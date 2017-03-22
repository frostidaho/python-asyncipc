# http://stackoverflow.com/a/27198531
# https://github.com/joidegn/leo-cli
# https://pymotw.com/2/socket/uds.html
import asyncio
from os import path as _path

from . import _utils
from .serializer2 import Serialize
from collections import namedtuple


class Server:
    _serial = Serialize()
    def __init__(self, socket_path, obj):
        import logging
        logr = _utils.get_logger()
        logr.setLevel(logging.DEBUG)
        logr.addHandler(logging.StreamHandler())
        self.logr = logr

        self.socket_path = socket_path
        logr.debug(f'server has socket path {socket_path!r}')
        self.obj = obj
        self.messages = []

    def __call__(self, loop):
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
        self.messages.append(msg)
        writer.close()

