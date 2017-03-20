import pytest
from asyncipc.message import BaseMessage

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
