import inspect
from collections import namedtuple
from functools import wraps
from itertools import chain

from .serializer2 import Serialize
from ._utils import CmdInfo, Msg, CmdContext

def _receive(sock, nbytes):
    n_received = 0
    received = []
    while n_received < nbytes:
        bobj = sock.recv(nbytes - n_received)
        received.append(bobj)
        n_received += len(bobj)
    return b''.join(received)

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
    def _make_fn(cls, name, cmd_info):
        mtype = cmd_info.method_type
        if  mtype not in {classmethod, staticmethod}:
            return cls._make_method(name, cmd_info)
        Param = inspect.Parameter
        self_param = Param('self', Param.POSITIONAL_OR_KEYWORD)
        new_sig = inspect.Signature(chain([self_param], cmd_info.signature.parameters.values()))
        d = cmd_info._asdict()
        d['signature'] = new_sig
        return cls._make_method(name, CmdInfo(**d))


class Client(CmdProxy):
    connect_timeout = 2.0
    receive_timeout = 10.0

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
    def _make_method(name, cmd_info):
        original_func = cmd_info.func
        signature = cmd_info.signature
        ctx_name = cmd_info.context.name
        @wraps(original_func)
        def fn(self, *args, **kwargs):
            bound_values = signature.bind(self, *args, **kwargs)
            bound_values.apply_defaults()
            msg = Msg(ctx_name, name, bound_values.args[1:], bound_values.kwargs)
            return self._send_and_receive(msg)
        fn.__signature__ = signature
        return fn

    def _send_message(self, msg):
        header, objstr = self._serial.dump_iter(msg)
        sock = self._new_socket()
        sock.sendall(header)
        sock.sendall(objstr)
        return sock

    def _send_and_receive(self, msg):
        sock = self._send_message(msg)
        serial = self._serial
        b_header = _receive(sock, serial.header_length)
        info = serial.load(b_header)
        b_obj = _receive(sock, info.data_length)
        result = info.data_loader(b_obj)
        sock.close()
        return result

    def _send_server_message(self, name, *args, **kwargs):
        msg = Msg(CmdContext.SERVER.name, name, args, kwargs)
        self._send_message(msg)

    def server_stop(self):
        self._send_server_message('stop')

