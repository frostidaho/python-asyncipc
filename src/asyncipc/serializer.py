import json as _json
from collections import namedtuple as _namedtuple
from struct import calcsize as _calcsize
from struct import pack as _pack
from struct import unpack as _unpack

_HeaderFmt = _namedtuple('_HeaderFmt', ('tag', 'data_length'))
class HeaderFormat:
    _taglen = 10
    fmt = _HeaderFmt(tag=f'{_taglen:d}s', data_length='I')
    _fmt = ''.join(fmt)
    length = _calcsize(_fmt)

    @classmethod
    def pack(cls, b_tag, length):
        "Return a bytes object given a b_tag (bytes) and length (int)"
        taglen = cls._taglen
        if len(b_tag) > taglen:
            raise ValueError(f"Header tag {b_tag!r} is longer than {taglen}")
        return _pack(cls._fmt, b_tag, length)

    @classmethod
    def unpack(cls, bstr):
        "Unpack a _HeaderFmt object from the bytes string bstr."
        tag, length = _unpack(cls._fmt, bstr)
        tag = tag.replace(b'\x00', b'')
        return _HeaderFmt(tag, length)

    @classmethod
    def __repr__(cls):
        clsname = cls.__name__
        return f'<{clsname}: fmt={cls.fmt}>'

HeaderFormat = HeaderFormat()


_HeaderInfo = _namedtuple(
    '_HeaderInfo',
    _HeaderFmt._fields + ('data_loader',),
)
_Msg = _namedtuple('_Msg', ('name', 'data'))

class Serialize:
    header_length = HeaderFormat.length
    def __init__(self, **message_types):
        self.message_types = message_types

    def dump_iter(self, message, formatter='json'):
        dumper_name = f'_dump_{formatter}'
        try:
            dumper = getattr(self, dumper_name)
        except AttributeError as e:
            txt = f"data dumper {dumper_name!r} doesn't exist!"
            raise NotImplementedError(txt) from e

        mtupl = _Msg(message.__class__.__name__, message.as_dict)
        objstr = dumper(mtupl)
        yield HeaderFormat.pack(b'json', len(objstr))
        yield objstr

    @staticmethod
    def _dump_json(message_tupl):
        objstr = _json.dumps(message_tupl, ensure_ascii=True)
        return objstr.encode('ascii')

    def load(self, b_header):
        header = HeaderFormat.unpack(b_header)
        tag = header.tag.decode()

        d_header = header._asdict()
        loader_name = f'_load_{tag}'
        try:
            data_loader = getattr(self, loader_name)
        except AttributeError as e:
            txt = f"data_loader {loader_name!r} doesn't exist!"
            raise NotImplementedError(txt) from e

        def load_msg(b_obj, *args, **kwargs):
            'Unpack b_obj and return a corresponding message object'
            mtupl = _Msg._make(data_loader(b_obj, *args, **kwargs))
            return self.message_types[mtupl.name](**mtupl.data)

        d_header['data_loader'] = load_msg
        return _HeaderInfo(**d_header)

    @staticmethod
    def _load_json(b_obj, *args, **kwargs):
        return _json.loads(b_obj.decode('ascii'), *args, **kwargs)
