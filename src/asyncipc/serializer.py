from collections import namedtuple, OrderedDict
from inspect import _empty as empty
from asyncipc.structure import Structure
# from .structure import Structure


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
    cls._struct_format = ''.join(fmt)

class BaseHeader(Structure, hooks=[header_hook], init_hooks=[header_init_hook]):
    pass

class ClientHeader(BaseHeader):
    _headers = {
        'tag': '10s',
        'data_length': 'I',
        'message_id': 'I',
    }
    _defaults = {
        'tag': 'json',
    }
    

class Swag(ClientHeader):
    _headers = {'tag': '15s', 'woops': '10s'}
    _defaults = {'tag': 'pickle'}
