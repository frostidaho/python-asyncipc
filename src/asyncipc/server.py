# # http://stackoverflow.com/a/27198531
# # https://github.com/joidegn/leo-cli
# # https://pymotw.com/2/socket/uds.html
# import asyncio
# from os import path as _path

# from . import _utils
# from .serializer import Serialize
# from collections import namedtuple


# Observer = namedtuple('Observer', 'func callback')
# class Server:
#     def __init__(self, socket_name, message_types):
#         self.socket_path = _path.join(_utils.RUNTIME_DIR, socket_name)
#         self.logr = _utils.get_logger()
#         self.serial = Serialize(**message_types)
#         self.messages = asyncio.Queue(30)
#         d_observer = {}
#         for key in message_types:
#             d_observer[key] = []
#         self.observers = d_observer

#     def register(self, msgtype, fn, callback=None):
#         d = self.observers
#         fn2 = asyncio.coroutine(fn)
#         obs = Observer(fn2, callback)
#         if isinstance(msgtype, str):
#             d[msgtype].append(obs)
#         else:
#             d[msgtype.__name__].append(obs)

#     def __call__(self, loop):
#         coro = asyncio.start_unix_server(self.listener, path=self.socket_path)
#         loop.run_until_complete(coro)
#         loop.create_task(self.queue_reader())

#     async def queue_reader(self):
#         messages = self.messages
#         logr = self.logr
#         d_observers = self.observers
#         create_task = asyncio.get_event_loop().create_task
#         while True:
#             msg = await messages.get()
#             msg_type = msg.__class__.__name__
#             observers = d_observers[msg_type]
#             if observers:
#                 for obs in observers:
#                     fn, callback = obs
#                     task = create_task(fn(msg))
#                     if callback is not None:
#                         task.add_done_callback(callback)
#             else:
#                 logr.debug(f'{msg_type} has no observers')

#     async def get_header(self, reader):
#         data = await reader.read(self.serial.header_length)
#         return self.serial.load(data)

#     async def listener(self, reader, writer):
#         logr = self.logr
#         logr.debug(f"In listener!")
#         header = await self.get_header(reader)
#         value = await reader.read(header.data_length)
#         msg = header.data_loader(value)
#         logr.debug(f"Received {msg!r}")
#         await self.messages.put(msg)
#         writer.close()
#         # self.msg = msg

#         # writer.close()
#         # writer.write(b'got it')
#         # try:
#         #     await writer.drain()
#         #     logr.debug("Closing the client socket")
#         #     writer.close()
#         # except ConnectionResetError:
#         #     pass
#         return
