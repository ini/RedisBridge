from .utils import Loggable
from collections import defaultdict



class Observer(Loggable):
    """
    An object that observes a Redis bridge.
    Internally maintains a lookup table of callbacks
    for each message class / type.

    RedisBridge clients can interact with the bridge 
    through an observer by registering callbacks.

    Attributes:
        - bridge: RedisBridge.RedisBridge instance being observed
        - logger: logging.Logger instance that log messages are sent to

    Methods:
        - register_callback()
        - deregister_callback()

    Aliases:
        - redis_bridge:
            alias for `bridge`
        - register_redis_callback():
            alias for register_callback()
        - deregister_redis_callback():
            alias for deregister_callback()
    """

    def __init__(self, bridge):
        """
        Arguments:
            - bridge: a RedisBridge.RedisBridge instance
        """
        self._bridge = bridge
        self._message_processors = defaultdict(list)


    def __str__(self):
        """
        Provide a string representation of the object.
        """
        return self.__class__.__name__


    @property
    def bridge(self):
        """
        The object's RedisBridge instance.
        """
        return self._bridge


    @property
    def redis_bridge(self):
        """
        Alias for `self.bridge`.
        """
        return self._bridge


    def register_callback(self, callback, channel, message_type=None):
        """
        Register a callback, indicating the function that should be called when
        a message is received on the given channel. Note that multiple callbacks
        may be registered, however, for a given (channel, message_type) pair,
        each callback will only be registered once.

        Arguments:
            - callback: function to call when a message on the channel is received
            - channel: string indicating the name of a channel
            - message_type: the type of message that should trigger the callback
                If `None`, all messages types are triggers
        """
        if not isinstance(channel, str):
            raise TypeError(f"Expected string instance for channel, not {type(channel)}")

        elif not callable(callback):
            raise ValueError(f"Callback {callback} is not callable")

        elif callback in self._get_processors(channel, message_type):
            # Issue a warning that the callback has already been registered
            self.logger.warning(
                f"{self}:  Attempting to register existing callback for channel {channel}")

        else:
            # Add the callback
            self._message_processors[channel, message_type].append(callback)

            # Register with the bridge to receive this message
            self.redis_bridge.register(self, channel)


    def deregister_callback(self, callback, channel=None, message_type=None):
        """
        Deregister the callback as a message processor for the
        given channel and message type.

        Arguments:
            - callback: function to call when a message on the channel is received
            - channel: string indicating the name of a channel
                If `None`, deregister from all channels
            - message_type: the type of message that should trigger the callback
                If `None`, deregister from all message types
        """
        self.logger.debug(f"{self}:  Deregistering callback {callback}")

        # Remove the callback from self._message_processors
        for c, mt in self._message_processors.keys():
            if channel in {c, None} and message_type in {mt, None}:
                if callback in self._message_processors[c, mt]:
                    self._message_processors[c, mt].remove(callback)

        # Deregister with the bridge from any unneeded channels
        channels = {c for c, mt in self._message_processors.keys()}
        for c in channels:
            if len(self._get_processors(c)) == 0:
                self.logger.info(f"{self}:  Deregistering from channel '{c}' -- no registered callbacks")
                self.redis_bridge.deregister(self, channel=c)


    def register_redis_callback(self, *args, **kwargs):
        """
        Alias for `self.register_callback()`.
        """
        return self.register_callback(*args, **kwargs)


    def deregister_redis_callback(self, *args, **kwargs):
        """
        Alias for `self.deregister_callback()`.
        """
        return self.deregister_callback(*args, **kwargs)


    def receive_redis(self, message):
        """
        Receive a message from the RedisBridge. Delegate the message to
        callbacks registered in the message processors dictionary based on the
        message channel and message type. 

        Returns a list of return values from the relevant message processors.

        Arguments:
            - message: RedisBridge.messages.Message instance
        """
        self.logger.debug(f"{self}:  Received {message} message")

        # Get the processors for the message
        processors = self._get_processors(message.channel, message.type)
        if len(processors) == 0:
            self.logger.debug(f"{self}:  No message processors found for {message} message.")

        # Send message to each processor
        return [processor(message) for processor in processors]


    def _get_processors(self, channel, message_type=None):
        """
        Get a list of all message processors
        for the given channel and message type.
        """
        if message_type is None:
            return self._message_processors[channel, None]
        else:
            return [
                *self._message_processors[channel, message_type],
                *self._message_processors[channel, None],
            ]

