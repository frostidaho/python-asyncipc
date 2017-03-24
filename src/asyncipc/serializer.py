from collections import namedtuple, OrderedDict
from .message import Structure

class BaseHeader(Structure):
    pass

class ClientHeader(BaseHeader):
    header_tag = '10s'
    header_data_length = 'I'
    header_message_id = 'I'

    default_tag = 'json'
    

