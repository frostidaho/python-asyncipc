import inspect as _inspect
from itertools import chain as _chain
from weakref import WeakValueDictionary as _WeakValueDictionary
# The StructureMeta and Structure classes are based on
# code from the python cookbook 3rd edition

class StructureMeta(type):
    def __new__(cls, clsname, bases, clsdict):
        # print(clsname, '->', bases)
        # print(clsdict)
        fields = clsdict.get('_fields', [])
        kwfields = clsdict.get('_kwfields', {})
        parameters = _chain(
            fields,
            kwfields.items(),
            *StructureMeta._get_fields(*bases),
        )
        sig = StructureMeta.make_sig(*parameters)
        clsdict['__signature__'] = sig
        clsdict['__slots__'] = tuple(sig.parameters)
        return super().__new__(cls, clsname, bases, clsdict)

    @classmethod
    def _get_fields(cls, *bases):
        structs = list(StructureMeta._get_structures(*bases))
        for cls in structs:
            yield getattr(cls, '_fields', [])

        d = {}
        for cls in reversed(structs):
            try:
                d.update(cls._kwfields)
            except AttributeError:
                pass
        yield d.items()

    @staticmethod
    def _get_structures(*klasses):
        "Yield the unique Structure subclasses from klasses"
        is_sub = issubclass
        seen = set()
        for cls in klasses:
            if not is_sub(cls, Structure):
                continue
            for cls2 in cls.__mro__:
                if is_sub(cls2, Structure) and cls2 not in seen:
                    yield cls2
                    seen.add(cls2)

    @staticmethod
    def make_sig(*fields):
        Parameter, Signature = _inspect.Parameter, _inspect.Signature
        pos_parms = []
        kw_parms = []
        for field in fields:
            if isinstance(field, str):
                pos_parms.append(Parameter(field, Parameter.POSITIONAL_OR_KEYWORD))
            else:
                name, default = field
                kw_parms.append(Parameter(name, Parameter.KEYWORD_ONLY, default=default))
        return Signature(_chain(pos_parms, kw_parms))


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


message_types = _WeakValueDictionary()

class BaseMessage(Structure):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        clsname = cls.__name__
        # if clsname in message_types:
        #     txt = f"Message type {clsname!r} is already registered"
        #     raise ValueError(txt)
        message_types[clsname] = cls


if __name__ == '__main__':
    class Vec(Structure):
        _fields = ['a', 'b', 'c']
        _kwfields = dict.fromkeys('xyz')

    class Command(BaseMessage):
        pass

    print(message_types['Command']())
    del Command
    print(message_types['Command']())
