import inspect
import os
from functools import partial as _partial
from ._utils import CmdContext, CmdInfo

def _runtime_dir():
    rundir = os.getenv('XDG_RUNTIME_DIR')
    if rundir:
        return rundir
    return '/run/user/{:d}'.format(os.getuid())
RUNTIME_DIR = _runtime_dir()
DEFAULT_SOCK_PREFIX = 'py_asyncipc_'


def cmd(*func, context=CmdContext.BLOCKING):
    "Mark a method as a command"
    try:
        fn = func[0]
        fn._context = context
    except IndexError:
        return _partial(cmd, context=context)
    return fn


class HasCommands:
    @property
    def socket_path(self):
        try:
            return self._socket_path
        except AttributeError:
            cname = self.__class__.__name__
            sp = os.path.join(RUNTIME_DIR, DEFAULT_SOCK_PREFIX + cname)
            self._socket_path = sp
            return sp

    @socket_path.setter
    def socket_path(self, value):
        self._socket_path = value

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
                commands[name] = CmdInfo(attr, ctx, sig, mtype)
        cls._commands = commands

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._find_commands()

    @staticmethod
    def get_server_class():
        from .server import Server
        return Server

    def get_server_loop(self, socket_path=None):
        if socket_path is None:
            socket_path = self.socket_path
        Server = self.get_server_class()
        serv = Server(socket_path, self)
        serv()
        return serv.loop

    @classmethod
    def get_client_class(cls):
        cname = cls.__name__
        from .client import Client
        client_cls = type(cname + 'Client', (Client,), {'_commands': cls._commands})
        return client_cls

    def get_client(self, socket_path=None):
        if socket_path is None:
            socket_path = self.socket_path
        CustomClient = self.get_client_class()
        return CustomClient(socket_path)
