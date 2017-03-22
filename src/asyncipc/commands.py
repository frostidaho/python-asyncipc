import inspect
import os
from collections import namedtuple as _namedtuple
from enum import Enum as _Enum
from functools import partial as _partial


def _runtime_dir():
    rundir = os.getenv('XDG_RUNTIME_DIR')
    if rundir:
        return rundir
    return '/run/user/{:d}'.format(os.getuid())
RUNTIME_DIR = _runtime_dir()

CmdContext = _Enum('CmdContext', 'BASIC PASS_SERVER')
def cmd(*func, context=CmdContext.BASIC):
    "Mark a method as a command"
    try:
        fn = func[0]
        fn._context = context
    except IndexError:
        return _partial(cmd, context=context)
    return fn

def close_other_server(path):
    from socket import socket, AF_UNIX, SOCK_STREAM
    sock = socket(AF_UNIX, SOCK_STREAM)
    print(path)
    try:
        sock.bind(path)
        sock.close()
        return
    except OSError:
        print('server wasnt closed')
    from .client import Client
    client = Client(path)
    try:
        client.stop_server()
    except ConnectionRefusedError:
        os.remove(path)
    

    
_FuncCtx = _namedtuple('_FuncCtx', 'func context signature method_type')
class HasCommands:
    def __init__(self, *args, socket_path='', **kwargs):
        super().__init__(*args, **kwargs)
        if socket_path:
            self.socket_path = socket_path
        else:
            cname = self.__class__.__name__
            self.socket_path = os.path.join(RUNTIME_DIR, f'py_asyncipc_{cname}')

    @staticmethod
    def _get_method_type(klass, name):
        return type(klass.__getattribute__(klass, name))

    @classmethod
    def _find_commands(cls):
        ga = getattr
        signature = inspect.signature
        get_method_type = cls._get_method_type
        commands = {}
        for name in (x for x in dir(cls) if not x.startswith('__')):
            attr = ga(cls, name)
            try:
                ctx = attr._context
            except AttributeError:
                continue
            if isinstance(ctx, CmdContext):
                sig = signature(attr)
                mtype = get_method_type(cls, name)
                commands[name] = _FuncCtx(attr, ctx, sig, mtype)
        cls._commands = commands

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._find_commands()

    @staticmethod
    def get_server_class():
        from .server2 import Server
        return Server

    def get_server_loop(self):
        from asyncio import get_event_loop
        Server = self.get_server_class()
        loop = get_event_loop()
        close_other_server(self.socket_path)
        serv = Server(self.socket_path, self)
        serv(loop)
        return loop # then loop.run_forever()

    @classmethod
    def get_client_class(cls):
        cname = cls.__name__
        from .client import Client
        client_cls = type(cname + 'Client', (Client,), {'_commands': cls._commands})
        return client_cls

    def get_client(self):
        CustomClient = self.get_client_class()
        return CustomClient(self.socket_path)
