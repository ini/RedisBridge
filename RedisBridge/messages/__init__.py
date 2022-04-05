import json

from .base import Message
from .request_response import Request, Response



MESSAGE_CLASSES = {
    'Message': Message,
    'Request': Request,
    'Response': Response,
}


def decode(message):
    """
    Decode a Message instance from a raw Redis message.

    Arguments:
        - message: dictionary representing the recived message.
            The field message['data'] is given as a `bytes` object,
            which may be decoded by clients as needed.
    """
    json_data = json.loads(message['data'].decode())
    if json_data['type'] in MESSAGE_CLASSES:
        cls = MESSAGE_CLASSES[json_data['type']]
        return cls._decode(json_data)
    else:
        raise KeyError(f"Invalid message type '{json_data['type']}'")
