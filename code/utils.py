import json
from collections import namedtuple

# структура сообщения
msg_structure = {
    "user": "",
    "data": "",
    "is_end": "",
    "type": ""
}
MsgInfo = namedtuple('MsgInfo', msg_structure)


def from_bytes_to_message(data: bytes) -> MsgInfo:
    """
    bytes -> json -> dict -> MsgInfo
    message.data(hex) -> bytearray -> bytes
    """
    string_data = data.decode()
    json_data = json.loads(string_data)
    json_data['data'] = bytes(bytearray.fromhex(json_data['data']))
    json_data['is_end'] = bool(int(json_data['is_end']))
    msg_info = MsgInfo(**json_data)
    return msg_info


def from_dict_to_bytes(data: dict) -> bytes:
    """
    dict -> json -> bytes
    message.data(bytes or str) -> bytes -> hex
    """
    if type(data['data']) is str:
        data['data'] = data['data'].encode()
    data['data'] = data['data'].hex()
    string_data = json.dumps(data)
    byte_data = string_data.encode()
    return byte_data
