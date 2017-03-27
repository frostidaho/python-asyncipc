import struct as _struct
from collections import namedtuple
from inspect import _empty as empty
from weakref import WeakValueDictionary as _WeakValueDictionary
from itertools import chain

from .structure import Structure
# from asyncipc.structure import Structure

_StructFmt = namedtuple('_StructFmt', 'format length')

def header_hook(metacls, clsname, bases, clsdict, kw):
    fields = clsdict.get('_fields', [])
    # NOTE: this depends on the _headers dictionary being ordered
    for k,v in clsdict.get('_headers', {}).items():
        fields.append(k)
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
    cls._d_struct_format = d
    cls._struct_format = _StructFmt(fmt, _struct.calcsize(fmt))
    pf = cls._struct_format_prefix[0] + fmt
    cls._pack_format = _StructFmt(pf, _struct.calcsize(pf))


def header_doc_hook(cls, clsname, bases, clsdict, kw):
    header_doc = f"""\
    {clsname} is a data structure for passing messages.

    To serialize a message: bytes({clsname}(...))
    To deserialize a message: {clsname}.from_bytes(...)

    {cls.__signature__!r}
    """
    cls.__doc__ = header_doc

_n_headers = 0


class _BaseHeader(Structure, hooks=[header_hook], init_hooks=[header_init_hook, header_doc_hook]):
    # _struct_id_format = 'H'
    _id_to_headers = _WeakValueDictionary()
    _struct_format_prefix = _StructFmt('IH', _struct.calcsize('IH'))

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        pack = _struct.pack
        dfmt = self._d_struct_format
        error = _struct.error
        for name in self._parameters:
            val = getattr(self, name)
            try:
                pack(dfmt[name], val)
            except error as e:
                raise TypeError(f"Can't set {name!r} to {val!r}") from e
            if isinstance(val, bytes):
                setattr(self, name, val.replace(b'\x00', b''))

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        global _n_headers
        _n_headers += 1
        cls._id = _n_headers
        params = tuple(cls.__signature__.parameters)
        cls._parameters = params
        pack_params = chain(('_total_data_length', '_id'), params)
        cls._pack_params = tuple(pack_params)
        cls._id_to_headers[_n_headers] = cls

    def __iter__(self):
        ga = getattr
        for name in self._parameters:
            yield ga(self, name)

    def __bytes__(self):
        ga = getattr
        vals = (ga(self, x) for x in self._pack_params)
        return _struct.pack(self._pack_format[0], *vals)

    def __hash__(self):
        return hash(bytes(self))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return bytes(self) == bytes(other)
        return False

    @property
    def _total_data_length(self):
        try:
            dl = self.data_length
        except AttributeError:
            dl = 0
        return dl + self._pack_format.length

    @classmethod
    def from_bytes(cls, b_str):
        unpack = _struct.unpack
        pre_fmt, pre_len = cls._struct_format_prefix
        total_len, header_id = unpack(pre_fmt, b_str[:pre_len])
        header_cls = cls._id_to_headers[header_id]
        pack_fmt = header_cls._pack_format

        len_b_str = len(b_str)
        len_pack_fmt = pack_fmt.length

        if len_b_str == len_pack_fmt:
            data = unpack(pack_fmt.format, b_str)
        elif len_b_str > len_pack_fmt:
            data = unpack(pack_fmt.format, b_str[:len_pack_fmt])
        else:
            raise ValueError(f"{b_str} is not long enough to unpack!")
        return header_cls(*data[2:])

    # @classmethod
    # def from_bytes(cls, b_str, read_fn=None):
    #     from struct import unpack
    #     pre_fmt, pre_len = cls._struct_format_prefix
    #     total_len, header_id = unpack(pre_fmt, b_str[:pre_len])
    #     header_cls = cls._id_to_headers[header_id]
    #     pack_fmt = header_cls._pack_format

    #     remaining = pack_fmt.length - len(b_str)
    #     if remaining > 0:
    #         b_str += read_fn(remaining)
    #     return header_cls(*unpack(pack_fmt.format, b_str)[2:])

class ClientHeader(_BaseHeader):
    _headers = {
        'data_length': 'I',
        'want_result': '?',
        'tag': '10s',
    }
    _defaults = {
        'want_result': True,
        'tag': b'json',
    }


class ServerHeader(_BaseHeader):
    _headers = {
        'message_id': 'I',
        'data_length': 'I',
        'tag': '10s',
    }
    _defaults = {
        'tag': b'json',
    }


LoadFailed = namedtuple('LoadFailed', 'header data_loader objstr_partial remaining')
LoadSuccess = namedtuple('LoadSuccess', 'header data')

class Serialize:
    def __init__(self, header_cls, **header_defaults):
        self.header_cls = header_cls
        self.header_defaults = header_defaults

    def dump(self, message, formatter='pickle', **kwargs):
        dumper_name = f'_dump_{formatter}'
        try:
            dumper = getattr(self, dumper_name)
        except AttributeError as e:
            txt = f"data dumper {dumper_name!r} doesn't exist!"
            raise NotImplementedError(txt) from e

        hd = self.header_defaults.copy()
        hd.update(kwargs)

        objstr = dumper(message)
        header = self.header_cls(
            data_length=len(objstr),
            tag=formatter.encode(),
            **hd
        )
        return b''.join((bytes(header), objstr))

    @staticmethod
    def _dump_json(message_tupl):
        from json import dumps
        objstr = dumps(message_tupl, ensure_ascii=True)
        return objstr.encode('ascii')

    @staticmethod
    def _dump_pickle(message_tupl):
        from pickle import dumps
        return dumps(message_tupl)

    def load(self, b_header):
        header = _BaseHeader.from_bytes(b_header)
        tag = header.tag.decode()

        loader_name = f'_load_{tag}'
        try:
            data_loader = getattr(self, loader_name)
        except AttributeError as e:
            txt = f"data_loader {loader_name!r} doesn't exist!"
            raise NotImplementedError(txt) from e

        len_b_header = len(b_header)
        data_len = header.data_length
        header_len = header._pack_format.length
        total_len = header_len + data_len
        if len_b_header >= total_len:
            return LoadSuccess(header, data_loader(b_header[header_len:total_len]))
        elif header_len < len_b_header < total_len:
            objstr_partial = b_header[header_len:]
            remaining = data_len - len(objstr_partial)
        else:
            objstr_partial = b''
            remaining = data_len
        return LoadFailed(header, data_loader, objstr_partial, remaining)

    @staticmethod
    def _load_json(b_obj, *args, **kwargs):
        from json import loads
        return loads(b_obj.decode('ascii'), *args, **kwargs)

    @staticmethod
    def _load_pickle(b_obj, *args, **kwargs):
        from pickle import loads
        return loads(b_obj, *args, **kwargs)



