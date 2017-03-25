import pytest

from asyncipc.commands import RUNTIME_DIR


def new_socket(path):
    from socket import socket, AF_UNIX, SOCK_STREAM
    sock = socket(AF_UNIX, SOCK_STREAM)
    sock.connect(path)
    return sock


@pytest.fixture
def sockpath():
    from os import path
    return path.join(RUNTIME_DIR, 'adfasfz38')

