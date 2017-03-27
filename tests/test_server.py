import pytest
import asyncio
from asyncipc.commands import HasCommands, cmd
from threading import Thread
from fixtures import sockpath

@pytest.fixture
def CmdPower():
    class CmdPower(HasCommands):
        _class_power = 3
        def __init__(self, instance_power=2, *args, **kwargs):
            self._instance_power = instance_power
            super().__init__(*args, **kwargs)

        @staticmethod
        @cmd
        def pow(x, y):
            return x**y

        @classmethod
        @cmd
        def pow_class(cls, x):
            return x**cls._class_power

        @cmd
        def pow_instance(self, x, power=None):
            power = power if power is not None else self._instance_power
            return x**power

    return CmdPower

@pytest.fixture
def cmdpower(CmdPower, sockpath):
    c = CmdPower()
    c.socket_path = sockpath
    return c

def thread_server(command_obj):
    def fn(loop):
        asyncio.set_event_loop(loop)
        loop = command_obj.get_server_loop()
        loop.run_forever()
    loop = asyncio.get_event_loop()
    t = Thread(target=fn, args=(loop,))
    t.start()
    return t

def test_cmd_power(cmdpower):
    assert cmdpower.pow(1, 3) == 1
    assert cmdpower.pow(2, 3) == 8
    assert cmdpower.pow_instance(2) == 4
    assert cmdpower.pow_class(2) == 8

def test_server(cmdpower):
    t = thread_server(cmdpower)
    client = cmdpower.get_client()
    client.server_stop()
    t.join()

def test_server_fn(cmdpower):
    t = thread_server(cmdpower)
    client = cmdpower.get_client()
    cmds = {'pow', 'pow_instance', 'pow_class'}
    assert (cmds & set(dir(client))) == cmds
    assert client.pow(2,5).data == 32
    assert client.pow(2, 3).data == 8
    assert client.pow_instance(2).data == 4
    assert client.pow_class(2).data == 8
    client.server_stop()
    t.join()

    

