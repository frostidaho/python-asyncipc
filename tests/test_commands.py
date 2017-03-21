import pytest
from asyncipc.commands import HasCommands, CmdContext, cmd


@pytest.fixture
def Commander():
    class Commander(HasCommands):
        @staticmethod
        @cmd(context=CmdContext.PASS_SERVER)
        def xyz(*args, _server=None, **kw):
            return 'xyz', _server

        @cmd
        def abc(self, a, b, c, *args, swag=37, **kw):
            return a, b, c, swag, args, kw

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
    return commander.get_client()

@pytest.fixture
def client(Client):
    return Client('asdfasdf')

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

