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

    # Properties to include in string representation (i.e. __repr__())
    REPR_PROPERTIES = ['id', 'channel', 'data']


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


    def dict(self):
        """
        Returns a dictionary of message properties.
        """
        class_attributes = {k: getattr(self.__class__, k) for k in dir(self.__class__)}
        class_properties = {k for k, v in class_attributes.items() if isinstance(v, property)}
        return {k: getattr(self, k) for k in class_properties}


    def __getitem__(self, key):
        """
        Backwards compatibility for clients who treat messages as dictionaries.
        """
        return self.dict()[key]


    def __repr__(self):
        """
        Returns a string representation of this message.
        """
        properties = {k: getattr(self, k) for k in self.__class__.REPR_PROPERTIES}
        for k, v in properties.items():
            properties[k] = min(v.__repr__(), object.__repr__(v), key=len)

        properties_repr = ', '.join([f'{k}={v}' for k, v in properties.items()])
        return f'<{self.__class__.__name__}: {properties_repr}>'


    @staticmethod
    def from_redis(message):
        """
        Constructs a Message object from a raw Redis message.
        """
        try:
            msg = pickle.loads(message['data'])
            assert isinstance(msg, Message)
            assert msg.channel == message['channel'].decode()
            return msg

        except Exception as e:
            raise e

