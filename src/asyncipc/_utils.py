# def _runtime_dir():
#     from os import getenv, getuid
#     rundir = getenv('XDG_RUNTIME_DIR')
#     if rundir:
#         return rundir
#     return '/run/user/{:d}'.format(getuid())
# RUNTIME_DIR = _runtime_dir()
from enum import Enum as _Enum
from collections import namedtuple as _namedtuple


CmdContext = _Enum('CmdContext', 'SERVER BLOCKING THREAD PROCESS')
CmdInfo = _namedtuple('CmdInfo', 'func context signature method_type')
Msg = _namedtuple('Msg', ('context', 'name', 'args', 'kwargs'))

def get_logger():
    from sys import _getframe
    from logging import getLogger, DEBUG, NullHandler
    fname = _getframe(1).f_globals['__name__']
    logr = getLogger(fname)
    logr.addHandler(NullHandler())
    return logr


# def load_module(path):
#     from inspect import getmodulename
#     from importlib import util
#     mod_name = getmodulename(path)
#     spec = util.spec_from_file_location(mod_name, path)
#     mod = util.module_from_spec(spec)
#     spec.loader.exec_module(mod)
#     return mod

# def get_source_file(obj):
#     from inspect import getsourcefile
#     from os import path
#     fpath = getsourcefile(obj)
#     return path.abspath(fpath)
