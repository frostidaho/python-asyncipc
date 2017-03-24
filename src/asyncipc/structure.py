import inspect as _inspect
from itertools import chain as _chain

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
    for param in _get_parameters(fields):
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

def _fields_from_dict(d_cls, name_filter):
    for name in name_filter(d_cls.keys()):
        try:
            yield d_cls[name]
        except KeyError:
            continue

def name_filter(keys):
    for key in keys:
        if key in {'_fields', '_kwfields'}:
            yield key


class StructureMeta(type):
    def __new__(cls, clsname, bases, clsdict):
        fields = StructureMeta._get_all_fields(clsdict, bases)
        fields = (x for x in fields if x)
        fields2 = []
        for x in fields:
            try:
                fields2.append(tuple(x.items()))
            except AttributeError:
                fields2.append(x)
        fields = _chain(*fields2)

        def keyfn(x):
            if isinstance(x, str):
                return x
            else:
                name, default = x
                return name

        fields = dedupe(fields, key=keyfn)
        sig = _make_signature(fields)
        clsdict['__signature__'] = sig
        clsdict['__slots__'] = tuple(sig.parameters)
        return super().__new__(cls, clsname, bases, clsdict)

    @staticmethod
    def _get_all_fields(clsdict, bases):
        all_classes = _unique_classes(bases, instance_of=StructureMeta)
        yield from _fields_from_dict(clsdict, name_filter)
        for cls in all_classes:
            print(cls, cls.__name__)
            yield from _fields_from_dict(vars(cls), name_filter)

class Structure(metaclass=StructureMeta):
    _fields = []
    _kwfields = {}
    def __init__(self, *args, **kwargs):
        bound_values = self.__signature__.bind(*args, **kwargs)
        # print(bound_values)
        bound_values.apply_defaults()
        # print(bound_values)
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


class Alpha(Structure):
    _fields = ['a']
    pass

class Beta(Structure):
    _fields = ['b']
    pass


# class Gamma(Alpha, Beta):
#     _fields = ['c']
#     pass
class Gamma(Beta):
    pass

class Delta(Gamma):
    _fields = ['d']
    _kwfields = {'wee': 37}


class Swag(Delta):
    _fields = ['baller']
    _kwfields = {'wee': 389}

