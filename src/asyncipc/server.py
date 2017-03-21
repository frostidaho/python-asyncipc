# http://stackoverflow.com/a/27198531
# https://github.com/joidegn/leo-cli
# https://pymotw.com/2/socket/uds.html
import asyncio
from os import path as _path

# from common import RUNTIME_DIR, serializers, HeaderFormat, MsgTuple
from . import _utils
from .serializer import Serialize


class Server:
    def __init__(self, socket_name, message_types):
        self.socket_path = _path.join(_utils.RUNTIME_DIR, socket_name)
        self.logr = _utils.get_logger()
        self.serial = Serialize(**message_types)

    def __call__(self):
        return asyncio.start_unix_server(self.router, path=self.socket_path)

    async def get_header(self, reader):
        data = await reader.read(self.serial.header_length)
        return self.serial.load(data)

    async def router(self, reader, writer):
        logr = self.logr
        logr.debug(f"In router!")
        header = await self.get_header(reader)
        value = await reader.read(header.data_length)
        msg = header.data_loader(value)
        self.msg = msg
        logr.debug(f"Received {msg!r}")
        writer.write(b'got it')
        try:
            await writer.drain()
            logr.debug("Closing the client socket")
            writer.close()
        except ConnectionResetError:
            pass
        return msg
