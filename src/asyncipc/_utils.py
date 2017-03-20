def _runtime_dir():
    from os import getenv, getuid
    rundir = getenv('XDG_RUNTIME_DIR')
    if rundir:
        return rundir
    return '/run/user/{:d}'.format(getuid())


RUNTIME_DIR = _runtime_dir()

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
