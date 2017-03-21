import pytest
from asyncipc.commands import HasCommands, CmdContext, cmd
from fixtures import sockpath


@pytest.fixture
def Commander():
    class Commander(HasCommands):
        @staticmethod
        @cmd(context=CmdContext.PASS_SERVER)
        def xyz(*args, _server=None, **kw):
            return 'xyz', _server

        @cmd
        def abc(self, a, b, c, *args, swoop=37, **kw):
            return a, b, c, swoop, args, kw

        @classmethod
        @cmd
        def yup(cls, *args, test=None):
            return 'yup'

        @cmd
        def alpha(self, *args, _server=37, **kwargs):
            return args, _server, kwargs

    return Commander

@pytest.fixture
def method_names():
    return {'xyz', 'abc', 'yup', 'alpha'}

@pytest.fixture
def commander(Commander):
    return Commander()

@pytest.fixture
def Client(commander):
    C = commander.get_client()
    def fn(self, msg):
        try:
            msges = self.messages
        except AttributeError:
            msges = []
            self.messages = msges
        msges.append(msg)
        super(C, self)._send_message(msg)
    C._send_message = fn
    return C

@pytest.fixture
def client(Client, sockpath):
    return Client(socket_path=sockpath)

def test_init_subclass(Commander, method_names):
    assert method_names == set(Commander._commands)

def test_client_methods_existance(commander, method_names, Client):
    assert Client._commands == commander._commands
    meths = set(dir(Client))
    for name in method_names:
        assert name in meths
    
def test_client_method_signature(commander, client, method_names):
    from inspect import signature
    for name in method_names:
        s0 = signature(getattr(commander, name))
        s1 = signature(getattr(client, name))
        assert s0 == s1

def test_client_method(client):
    with pytest.raises(FileNotFoundError):
        client.abc(1,2,3)
        msg = client.messages.pop()
        assert msg.name == 'abc'
        assert msg.args == (1, 2, 3)
        assert msg.kwargs == {'swoop':37}

        client.abc(1,2,3,4,5,6, swoop=None, maybe=True)
        msg = client.messages.pop()
        assert msg.name == 'abc'
        assert msg.args == (1, 2, 3, 4, 5, 6)
        assert msg.kwargs == {'swoop':None, 'maybe':True}
    

