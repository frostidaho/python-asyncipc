from fixtures import *
from asyncipc.serializer import Serialize, HeaderFormat
from asyncipc.message import BaseMessage, message_types
import pytest

@pytest.fixture
def serialize():
    return Serialize(**message_types)

def test_dump_iter(msg_obj, serialize):
    assert len(list(serialize.dump_iter(msg_obj))) == 2
    for obj in serialize.dump_iter(msg_obj):
        assert isinstance(obj, bytes)

def test_dump_and_load(msg_obj, serialize):
    b_header, b_data = serialize.dump_iter(msg_obj, formatter='json')
    header = serialize.load(b_header)
    assert header.tag == b'json'
    assert header.data_length == len(b_data)
    msg = header.data_loader(b_data)
    assert msg.as_dict == msg_obj.as_dict

def test_formatter_implemented(alpha, serialize):
    with pytest.raises(NotImplementedError):
        list(serialize.dump_iter(alpha, formatter='asdfasdf'))

def test_loader_implemented(alpha, serialize):
    b_header = HeaderFormat.pack(b'blaas', 9000)
    with pytest.raises(NotImplementedError):
        serialize.load(b_header)

    
