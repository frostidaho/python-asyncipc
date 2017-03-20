from fixtures import *

from asyncipc.server import Server
from asyncipc.message import message_types
import asyncio

import logging
logr = logging.getLogger()
logr.addHandler(logging.StreamHandler())
logr.setLevel(logging.DEBUG)

def test_send_msg(send_msg, sockpath, alpha):
    serv = Server(sockpath, message_types)
    loop = asyncio.get_event_loop()
    coro = serv()
    # fut = asyncio.ensure_future(coro)
    loop.run_until_complete(coro)
    loop.call_later(2.0, send_msg(alpha))
    # loop.stop()
    loop.call_later(4.0, loop.stop)
    loop.run_forever()
    assert serv.msg.as_dict == alpha.as_dict
    
