import json
from collections import namedtuple

msg_structure = {
    "user": "",
    "data": "",
    "is_end": "",
    "type": ""
}
MsgInfo = namedtuple('MsgInfo', msg_structure)


def from_bytes_to_message(data: bytes) -> MsgInfo:
    string_data = data.decode()
    json_data = json.loads(string_data)
    json_data['data'] = json_data['data'].encode()
    json_data['is_end'] = bool(int(json_data['is_end']))
    msg_info = MsgInfo(**json_data)
    return msg_info


def from_dict_to_bytes(data: dict) -> bytes:
    if type(data['data']) is bytes:
        data['data'] = data['data'].decode()
    string_data = json.dumps(data)
    byte_data = string_data.encode()
    return byte_data
