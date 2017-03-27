import pytest

from asyncipc.commands import RUNTIME_DIR


# def new_socket(path):
#     from socket import socket, AF_UNIX, SOCK_STREAM
#     sock = socket(AF_UNIX, SOCK_STREAM)
#     sock.connect(path)
#     return sock


@pytest.fixture(scope='function')
def sockpath():
    from os import path
    import random
    import string
    name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    return path.join(RUNTIME_DIR, name)



