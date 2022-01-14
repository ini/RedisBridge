import pickle
import uuid



class Message:
    """
    Base class for internal bus messages.

    Attributes:
        - id: a unique string identifier for this message
        - type: a string indicating the type of this message
        - channel: the string name of the channel this message was sent on
        - data: the data for this message
    """

    def __init__(self, channel, data, type='message'):
        self._id = str(uuid.uuid4())
        self._type = type
        self._channel = channel
        self._data = data


    @property
    def id(self):
        """
        Returns the unique string identifier for this message.
        """
        return self._id


    @property
    def type(self):
        """
        Returns a string indicating the type of this message.
        """
        return self._type


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


    def __str__(self):
        """
        Returns a string representation of this message.
        """
        return f'{self.__class__.__name__}: {self.dict()}'


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

