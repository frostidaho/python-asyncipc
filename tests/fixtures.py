import pytest

from asyncipc._utils import RUNTIME_DIR
from asyncipc.message import BaseMessage, message_types
from asyncipc.serializer import Serialize


class Alpha(BaseMessage):
    _fields = ['a', 'b']
    _kwfields = {'x': 42}

class Beta(Alpha):
    _fields = ['c']
    _kwfields = {'y': 37}


@pytest.fixture(params=(Alpha(1,2),
                        Beta(3,1,2,x=4,y=5),))
def msg_obj(request):
    yield request.param

@pytest.fixture
def alpha():
    return Alpha(99,98)


def new_socket(path):
    from socket import socket, AF_UNIX, SOCK_STREAM
    sock = socket(AF_UNIX, SOCK_STREAM)
    sock.connect(path)
    return sock


@pytest.fixture
def sockpath():
    from os import path
    return path.join(RUNTIME_DIR, 'adfasfz38')

@pytest.fixture
def send_msg(sockpath):
    def inner(msg):
        def wrapper():
            sock = new_socket(sockpath)
            serial = Serialize(**message_types)
            for bstr in serial.dump_iter(msg):
                sock.send(bstr)
            sock.close()
        return wrapper
    return inner
