import inspect as _inspect
from itertools import chain as _chain
from collections import namedtuple

def dedupe(items, key=None):
    """Remove duplicates from items.

    Specify key function if items are unhashable.
    Taken from Python Cookbook 3rd edition, Chapter 1.
    """
    seen = set()
    for item in items:
        val = item if key is None else key(item)
        if val not in seen:
            yield item
            seen.add(val)

def _get_parameters(fields):
    """Yield an inspect.Parameter() obj for each element in fields.

    Elements in fields can be a string which corresponds to the name
    of the parameter.

    Alternatively, each element can be an iterable of length two
    which contains the name and the default value in that order.
    """
    Parameter = _inspect.Parameter
    pos_or_kw = Parameter.POSITIONAL_OR_KEYWORD
    for field in fields:
        if isinstance(field, str):
            yield Parameter(field, pos_or_kw)
        else:
            name, default = field
            yield Parameter(name, pos_or_kw, default=default)

def _make_signature(fields):
    """Create a signature from fields.

    The signature's order may be different from the order of fields,
    if fields which specify default values come before those that do not.
    For example:
        In [17]: _make_signature(['a', ('x', 99), 'b', ('y', 98)])
        Out[18]: <Signature (a, b, x=99, y=98)>

    Elements in fields can be a string which corresponds to the name
    of the parameter.

    Alternatively, each element can be an iterable of length two
    which contains the name and the default value in that order.
    """
    Signature, empty = _inspect.Signature, _inspect._empty
    pos_parms, default_parms = [], []
    def keyfn(x):
        if isinstance(x, str):
            return x
        else:
            name, default = x
            return name

    for param in _get_parameters(dedupe(fields, key=keyfn)):
        if param.default == empty:
            pos_parms.append(param)
        else:
            default_parms.append(param)
    return Signature(_chain(pos_parms, default_parms))

def _unique_classes(klasses, instance_of=type):
    "Yield the unique classes which are derived from instance_of"
    total_mro = _chain(*(x.__mro__ for x in klasses))
    for cls in dedupe(total_mro):
        if isinstance(cls, instance_of):
            yield cls

class HookMeta(type):
    def __new__(metacls, clsname, bases, clsdict, **kw):
        hooks = []
        hooks.append(clsdict.get('_hooks', []))
        hooks.append(kw.pop('hooks', []))
        for klass in _unique_classes(bases, instance_of=HookMeta):
            try:
                hooks.append(klass.__getattribute__(klass, '_hooks'))
            except AttributeError:
                pass
        hooks = list(dedupe(_chain(*hooks)))
        clsdict['_hooks'] = hooks

        init_hooks = []
        init_hooks.append(clsdict.get('_init_hooks', []))
        init_hooks.append(kw.pop('init_hooks', []))
        for klass in _unique_classes(bases, instance_of=HookMeta):
            try:
                init_hooks.append(klass.__getattribute__(klass, '_init_hooks'))
            except AttributeError:
                pass
        init_hooks = list(dedupe(_chain(*init_hooks)))
        clsdict['_init_hooks'] = init_hooks


        kw['bases_mro'] = tuple(_unique_classes(bases, instance_of=HookMeta))
        for hook in hooks:
            hook(metacls, clsname, bases, clsdict, kw)
        return super().__new__(metacls, clsname, bases, clsdict)

    def __init__(cls, clsname, bases, clsdict, **kw):
        # print('clsdict issss ', clsdict)
        kw['bases_mro'] = tuple(_unique_classes(bases, instance_of=HookMeta))
        for hook in clsdict['_init_hooks']:
            hook(cls, clsname, bases, clsdict, kw)
        super().__init__(clsname, bases, clsdict)


def hook_add_fields(cls, clsname, bases, clsdict, kw):
    fields = []
    bases_mro = kw['bases_mro']
    fields.append(clsdict.get('_fields', []))
    for klass in bases_mro:
        fields.append(klass.__getattribute__(klass, '_fields'))
    sig = _make_signature(_chain(*fields))
    clsdict['__signature__'] = sig
    clsdict['__slots__'] = list(sig.parameters.keys())

class Structure(metaclass=HookMeta, hooks=[hook_add_fields]):
    _fields = []
    def __init__(self, *args, **kwargs):
        bound_values = self.__signature__.bind(*args, **kwargs)
        bound_values.apply_defaults()
        for name, value in bound_values.arguments.items():
            setattr(self, name, value)

    @property
    def as_dict(self):
        return {x:getattr(self, x) for x in self.__slots__}

    def __repr__(self):
        sig = self.__signature__
        bound = sig.bind(**self.as_dict)
        kwargs = (f'{key}={val!r}' for key,val in bound.arguments.items())
        inner = ', '.join(kwargs)
        cname = self.__class__.__name__
        return f'{cname}({inner})'

