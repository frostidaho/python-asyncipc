import pytest

import asyncipc.serializer as serial


class Header0(serial._BaseHeader):
    _headers = {
        'data_length': 'I',
        'message_id': 'I',
        'tag': '10s',
    }
    _defaults = {
        'tag': b'json',
    }


class Header1(serial._BaseHeader):
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


@pytest.fixture(params=[
    (Header0, 99, 1, {}),
    (Header1, {'tag': b'asdf', 'data_length':9000, 'response_id':37}),
    (Header2, 13, 99, 1, {}),
])
def header(request):
    cls, *rest = request.param
    *args, kws = rest
    return cls(*args, **kws)


def test_equality(header):
    assert header == eval(repr(header))
    assert header == header.from_bytes(bytes(header))
    assert header == serial._BaseHeader.from_bytes(bytes(header) + b' ')

def test_hash(header):
    set_header = set([header, header])
    assert len(set_header) == 1

def test_partial_read(header):
    b_header = bytes(header)
    prefix_len = header._struct_format_prefix.length
    print('prefix len is', prefix_len)
    b_prefix = b_header[0:prefix_len]
    with pytest.raises(ValueError):
        x = header.from_bytes(b_prefix)
