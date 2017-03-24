from collections import namedtuple
from inspect import _empty as empty
from asyncipc.structure import Structure
import struct as _struct
from weakref import WeakValueDictionary as _WeakValueDictionary

_StructFmt = namedtuple('_StructFmt', 'format length')

def header_hook(metacls, clsname, bases, clsdict, kw):
    fields = clsdict.get('_fields', [])
    fmt = []
    # NOTE: this depends on the _headers dictionary being ordered
    for k,v in clsdict.get('_headers', {}).items():
        fmt.append(v)
        fields.append(k)
    # clsdict['_struct_format'] = fmt

    def apply_defaults(fields):
        defaults = clsdict.get('_defaults', {})
        for field in fields:
            try:
                yield (field, defaults[field])
            except KeyError:
                yield field
    fields = list(apply_defaults(fields))
    clsdict['_fields'] = fields
    

def header_init_hook(cls, clsname, bases, clsdict, kw):
    params = list(cls.__signature__.parameters)
    def inner():
        for p in params:
            for klass in cls.__mro__:
                try:
                    yield (p, klass._headers[p])
                    break
                except KeyError:
                    continue
    
    d = dict(inner())
    fmt = [d[x] for x in params]
    fmt = ''.join(fmt)
    cls._struct_format = _StructFmt(fmt, _struct.calcsize(fmt))
    cls._pack_format = cls._struct_format_prefix[0] + fmt

_n_headers = 0


class BaseHeader(Structure, hooks=[header_hook], init_hooks=[header_init_hook]):
    # _struct_id_format = 'H'
    _id_to_headers = _WeakValueDictionary()
    _struct_format_prefix = _StructFmt('H', _struct.calcsize('H'))

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        for name in self._parameters:
            val = getattr(self, name)
            if isinstance(val, bytes):
                setattr(self, name, val.replace(b'\x00', b''))

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        global _n_headers
        _n_headers += 1
        cls._id = _n_headers
        cls._parameters = tuple(cls.__signature__.parameters)
        cls._id_to_headers[_n_headers] = cls

    def __bytes__(self):
        from struct import pack
        fmt = self._pack_format
        params = self._parameters
        ga = getattr
        topack = self._id, *(ga(self, x) for x in params)
        print(topack)
        return pack(fmt, *topack)

    @classmethod
    def unpack(cls, b_str):
        from struct import unpack
        pre_fmt, pre_len = cls._struct_format_prefix
        header_id = unpack(pre_fmt, b_str[:pre_len])[0]
        header_cls = cls._id_to_headers[header_id]
        return header_cls(*unpack(header_cls._pack_format, b_str)[1:])
        # from struct import unpack
        # return unpack('H'+self._struct_format, b_str)

class ClientHeader(BaseHeader):
    _headers = {
        'tag': '10s',
        'data_length': 'I',
        'message_id': 'I',
    }
    _defaults = {
        'tag': b'json',
    }
    

class Swag(ClientHeader):
    _headers = {'tag': '15s', 'woops': '10s'}
    _defaults = {'tag': b'pickle'}

s = Swag(b'yup', 32, 1)
x = bytes(s)
from struct import pack
asdf = s.unpack(x)
