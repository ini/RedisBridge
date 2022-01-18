from .utils import Loggable
from collections import defaultdict



class Observer(Loggable):
    """
    Minimal base implementation for objects that observe a Redis bridge.
    Internally maintains a lookup table of callbacks for each message class.


    Attributes:
        - redis_bridge: RedisBridge.RedisBridge instance being observed
        - logger: logging.Logger instance that log messages are sent to


    Methods:
        - register_callback(channel, callback)
    """

    def __init__(self, redis_bridge):
        """
        Arguments:
            - redis_bridge: a RedisBridge.RedisBridge instance
        """
        self.__message_processors = defaultdict(list)
        self.redis_bridge = redis_bridge


    def __str__(self):
        """
        Provide a string representation of the object.
        """
        return self.__class__.__name__


    def register_callback(self, channel, callback):
        """
        Register a callback, indicating the function that should be called when
        a message is received on the given channel. Note that multiple callbacks
        may be registered, however, for a given channel,
        each callback will only be registered once.

        Arguments:
            - channel: string indicating the name of a channel
            - callback: function to call when a message on the channel is received
        """

        # Validate arguments
        if not isinstance(str, type):
            raise TypeError(f"Expected string instance for channel, not {type(channel)}")
        if not callable(callback):
            raise ValueError(f"Callback {callback} is not callable")

        # Issue a warning if a client is trying to register the same callback
        # for the same channel
        if callback in self.__message_processors[channel]:
            self.logger.warning(
                f'{self}:  Attempting to register existing callback for channel {channel}')
            return

        # Add the callback
        self.__message_processors[channel].append(callback)

        # Register with the bridge to receive this message
        self.redis_bridge.register(self, channel)


    def receive_redis(self, message):
        """
        Receive a message from the RedisBridge. Delegate the message to a
        callback registered in the message processors dictionary based on the
        message channel. Return a list of return values from the channel processors.

        Arguments:
            - message: RedisBridge.messages.Message instance
        """
        self.logger.debug(f'{self}:  Received {message} message')

        # Get the processors for the message, and send to each callback
        if message.channel in self.__message_processors:
            processors = self.__message_processors[message.channel]
            return [processor(message) for processor in processors]
        else:
            self.logger.warning(
                f'{self}:  No message processors found for {message} message.  Ignoring message.')
            return []

