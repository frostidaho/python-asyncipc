import pytest
import asyncipc.serializer as serial

class Header0(serial.BaseHeader):
    _headers = {
        'data_length': 'I',
        'message_id': 'I',
        'tag': '10s',
    }
    _defaults = {
        'tag': b'json',
    }


class Header1(serial.BaseHeader):
    _headers = {
        'tag': '10s',
        'data_length': 'I',
        'response_id': 'I',
    }
    _defaults = {
        'tag': b'pickle',
    }
    

class Header2(Header0):
    _headers = {
        'response_id': 'I',
    }


# h = Header0(4096, 1, b'asdfasldfsdfjsdlkfjasdl')



def test_repr():
    h2 = Header2(1,2,3)
    assert repr(h2) == "Header2(response_id=1, data_length=2, message_id=3, tag=b'json')"
    assert h2 == eval(repr(h2))


