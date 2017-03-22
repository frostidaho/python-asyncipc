import inspect
import types
from collections import namedtuple as _namedtuple
from enum import Enum as _Enum
from functools import partial as _partial
from functools import wraps as _wraps
from itertools import chain as _chain

from .serializer2 import Serialize

CmdContext = _Enum('CmdContext', 'BASIC PASS_SERVER')

def cmd(*func, context=CmdContext.BASIC):
    "Mark a method as a command"
    try:
        fn = func[0]
        fn._context = context
    except IndexError:
        return _partial(cmd, context=context)
    return fn

def run_till_success(func, *args, swallow=(), timeout=10.0,
                     sleep_min=0.01, sleep_max=0.05, **kwargs):
    """Run function func(*args, **kwargs) and return its value

    If it raises an exception in swallow, retry until it no longer
    raises one of those exceptions or the timeout is reached.

    Once the timeout is reached the func(*args, **kwargs) is called one more time
    and no exceptions are trapped.

    timeout, sleep_min, and sleep_max are all given in seconds.
    """
    try:
        return func(*args, **kwargs)
    except swallow:
        pass

    from time import time, sleep
    tsleep = sleep_min
    dt = sleep_min * 0.5
    sleep_max_dt = sleep_max - dt
    tmax = timeout + time()
    while time() < tmax:
        try:
            return func(*args, **kwargs)
        except swallow:
            pass
        sleep(tsleep)
        if tsleep < sleep_max_dt:
            tsleep += dt
        else:
            tsleep = sleep_max
        continue
    return func(*args, **kwargs)
    
class CmdProxy:
    def __init__(self, socket_path):
        self.socket_path = socket_path

    _serial = Serialize()
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        try:
            cmds = cls._commands
        except AttributeError:
            return
        for name,value in cmds.items():
            fn = cls._make_fn(name, value)
            setattr(cls, name, fn)

    @classmethod
    def _make_fn(cls, name, funcctx):
        mtype = funcctx.method_type
        if  mtype not in {classmethod, staticmethod}:
            return cls._make_method(name, funcctx.signature, funcctx.func)
        Param = inspect.Parameter
        self_param = Param('self', Param.POSITIONAL_OR_KEYWORD)
        new_sig = inspect.Signature(_chain([self_param], funcctx.signature.parameters.values()))
        # print('new_sig is', new_sig)
        return cls._make_method(name, new_sig, funcctx.func)
    
_Msg = _namedtuple('_Msg', ('name', 'args', 'kwargs'))


class Client(CmdProxy):
    connect_timeout = 2.0

    def _new_socket(self):
        from socket import socket, AF_UNIX, SOCK_STREAM
        sock = socket(AF_UNIX, SOCK_STREAM)
        swallow = (FileNotFoundError, ConnectionRefusedError)
        try:
            sock.connect(self.socket_path)
        except swallow:
            run_till_success(
                sock.connect,
                self.socket_path,
                timeout=self.connect_timeout,
                swallow=swallow,
            )
        return sock
    
    @staticmethod
    def _make_method(name, signature, original_func):
        @_wraps(original_func)
        def fn(self, *args, **kwargs):
            bound_values = signature.bind(self, *args, **kwargs)
            bound_values.apply_defaults()
            self._send_message(_Msg(name, bound_values.args[1:], bound_values.kwargs))
        fn.__signature__ = signature
        return fn

    def _send_message(self, msg):
        header, objstr = self._serial.dump_iter(msg)
        sock = self._new_socket()
        sock.send(header)
        sock.send(objstr)

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
        client_cls = type(cname + 'Client', (Client,), {'_commands': cls._commands})
        print(client_cls)
        return client_cls
