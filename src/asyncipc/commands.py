from functools import wraps as _wraps, partial as _partial
from enum import Enum as _Enum
from collections import namedtuple as _namedtuple

    
CmdContext = _Enum('CmdContext', 'BASIC PASS_SERVER')

def cmd(*func, context=CmdContext.BASIC):
    "Mark a method as a command"
    try:
        fn = func[0]
        fn._context = context
    except IndexError:
        return _partial(cmd, context=context)
    return fn

_FuncCtx = _namedtuple('_FuncCtx', 'func context')
class HasCommands:
    @classmethod
    def _find_commands(cls):
        ga = getattr
        commands = {}
        for name in (x for x in dir(cls) if not x.startswith('__')):
            attr = ga(cls, name)
            try:
                ctx = attr._context
            except AttributeError:
                continue
            if isinstance(ctx, CmdContext):
                commands[name] = _FuncCtx(attr, ctx)
        cls._commands = commands

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._find_commands()
    
class Alpha(HasCommands):
    @staticmethod
    @cmd(context=CmdContext.PASS_SERVER)
    def xyz(server=None):
        return 'xyz', server

    @cmd
    def abc(self, *args, **kwargs):
        return args, kwargs
