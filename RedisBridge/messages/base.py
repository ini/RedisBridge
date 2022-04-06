import codecs
import json
import pickle
import random
import string



def uid(length=8):
    """
    Returns a unique string identifier.
    """
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(random.choices(alphabet, k=length))



class Message:
    """
    Base class for RedisBridge messages.

    Attributes:
        - id: a unique string identifier for this message
        - channel: the string name of the channel this message was sent on
        - data: the data for this message
    """

    # Properties to include in message encoding
    PROPERTIES = ['id', 'channel', 'data']


    def __init__(self, channel, data):
        self._id = uid()
        self._channel = channel
        self._data = data


    @property
    def id(self):
        """
        Returns the unique string identifier for this message.
        """
        return self._id


    @property
    def channel(self):
        """
        Returns the string name of the channel this message was sent on.
        """
        return self._channel


    @property
    def data(self):
        """
        Returns the data for this message.
        """
        return self._data


    def __getitem__(self, key):
        """
        Backwards compatibility for clients who treat messages as dictionaries.
        """
        if key in self.PROPERTIES:
            return getattr(self, key)

        raise KeyError(key)


    def __repr__(self):
        """
        Returns a string representation of this message.
        """
        properties = {key: getattr(self, key) for key in self.PROPERTIES}
        for k, v in properties.items():
            properties[k] = min(v.__repr__(), object.__repr__(v), key=len)

        properties_repr = ', '.join([f'{k}={v}' for k, v in properties.items()])
        return f'<{self.__class__.__name__}: {properties_repr}>'


    def _encode(self):
        """
        Encode message to JSON string.
        """
        json_data = {key: getattr(self, key) for key in self.PROPERTIES}
        json_data['type'] = self.__class__.__name__

        try:
            # Serialize to JSON
            return json.dumps(json_data)

        except TypeError:
            # Convert data to byte string, then serialize to JSON
            data = codecs.encode(pickle.dumps(json_data['data']), 'base64').decode()
            json_data['data'] = data
            return json.dumps(json_data)


    @classmethod
    def _decode(cls, json_data):
        """
        Decode message from JSON dictionary.
        """
        msg = cls.__new__(cls)
        msg._id = json_data['id']
        msg._channel = json_data['channel']

        # Unpickle data to Python object, if possible
        msg._data = json_data['data']
        if isinstance(json_data['data'], str):
            try:
                msg._data = pickle.loads(codecs.decode(json_data['data'].encode(), 'base64'))
            except:
                msg._data = json_data['data']

        return msg
