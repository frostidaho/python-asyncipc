import asyncio
import logging

from fixtures import *

from asyncipc.message import message_types
from asyncipc.server import Server

logr = logging.getLogger()
logr.addHandler(logging.StreamHandler())
logr.setLevel(logging.DEBUG)

class Recorder:
    def __init__(self):
        self.msg = None

    def __call__(self, msg):
        logr.debug(f'Got message {msg!r}')
        self.msg = msg

def test_send_msg(send_msg, sockpath, alpha):
    serv = Server(sockpath, message_types)
    fn = Recorder()
    serv.register(alpha.__class__, fn)
    loop = asyncio.get_event_loop()
    serv(loop)
    loop.call_later(2.0, send_msg(alpha))
    loop.call_later(4.0, loop.stop)
    loop.run_forever()
    assert fn.msg.as_dict == alpha.as_dict
