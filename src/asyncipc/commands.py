import inspect
import types
from collections import namedtuple as _namedtuple
from enum import Enum as _Enum
from functools import partial as _partial
from functools import wraps as _wraps
from itertools import chain as _chain

CmdContext = _Enum('CmdContext', 'BASIC PASS_SERVER')

def cmd(*func, context=CmdContext.BASIC):
    "Mark a method as a command"
    try:
        fn = func[0]
        fn._context = context
    except IndexError:
        return _partial(cmd, context=context)
    return fn

    

    
_FuncCtx = _namedtuple('_FuncCtx', 'func context signature method_type')
class HasCommands:
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

    def get_server():
        raise NotImplementedError

    @classmethod
    def get_client(cls):
        cname = cls.__name__
        from .client import Client
        client_cls = type(cname + 'Client', (Client,), {'_commands': cls._commands})
        print(client_cls)
        return client_cls
