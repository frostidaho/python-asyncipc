from collections import namedtuple
import pytest
from asyncipc.message import BaseMessage, message_types

class Alpha(BaseMessage):
    _fields = ['a', 'b']
    _kwfields = {'x': 42}

class Beta(Alpha):
    _fields = ['c']
    _kwfields = {'y': 37}


Param = namedtuple('Param', 'input expected')

@pytest.mark.parametrize(
    'msg,d_expected',
    (
        Param(Alpha(1,2, x=3), {'a':1, 'b':2, 'x':3}),
        Param(Alpha(1,2), {'a':1, 'b':2, 'x': Alpha._kwfields['x']}),
        Param(Beta(3,1,2), {'a':1, 'b':2, 'c':3, 'x': Alpha._kwfields['x'], 'y': Beta._kwfields['y']}),
        Param(Beta('c','a','b', x='x',y='y'), {x:x for x in 'cabxy'}),
    ),
)
def test_basic_msg(msg, d_expected):
    for k,v in d_expected.items():
        assert getattr(msg, k) == v
    assert msg.as_dict == d_expected

def test_sig():
    sig = Alpha.__signature__
    assert list(sig.parameters) == ['a', 'b', 'x']

def test_sig_inheritance():
    sig = Beta.__signature__
    assert list(sig.parameters) == ['c', 'a', 'b', 'y', 'x']

def test_repr():
    a = Alpha(98, 99, x=97)
    assert repr(a) == 'Alpha(a=98, b=99, x=97)'
    
    
