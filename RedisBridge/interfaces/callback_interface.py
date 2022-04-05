from collections import defaultdict
from .base import RedisInterface
from .. import messages



class CallbackInterface(RedisInterface):
    """
    A wrapper around a Redis bridge that extends with functionality to
    register and deregister individual callback methods for specific
    channels and message types, as opposed to registering objects
    to handle message reception.

    Internally maintains a lookup table of callbacks
    for each message class / type.

    Methods:
        - register_callback(callback, channel, message_type=None)
        - deregister_callback(callback, channel=None, message_type=None)
        - send(data, channel)
        - request(data, channel, blocking=True, timeout=None)
        - respond(data, channel, request_id)
    """

    def __init__(self, bridge):
        """
        Arguments:
            - bridge: a RedisBridge or RedisInterface instance
        """
        super().__init__(bridge)
        self._bridge = bridge
        self._message_processors = defaultdict(list)


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
            self.logger.error(f"Expected string instance for channel, not {type(channel)}")

        if not callable(callback):
            self.logger.error(f"Callback {callback} is not callable")

        if isinstance(message_type, str):
            if not hasattr(messages, message_type):
                self.logger.error(f"Invalid message type: {message_type}")
            else:
                message_type = getattr(messages, message_type)

        if message_type is not None:
            if not isinstance(message_type, type) or messages.Message not in message_type.mro():
                self.logger.error(f"Invalid message type: {message_type}")

        if callback in self._get_processors(channel, message_type):
            # Issue a warning that the callback has already been registered
            self.logger.warning(
                f"{self}:  Attempting to register existing callback for channel {channel}")

        else:
            # Add the callback
            self._message_processors[channel, message_type].append(callback)

            # Register with the bridge to receive this message
            self._bridge.register(self, channel)


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
        removed = set()
        for c, mt in self._message_processors.keys():
            if channel in {c, None} and message_type in {mt, None}:
                if callback in self._message_processors[c, mt]:
                    self._message_processors[c, mt].remove(callback)
                    removed.add((c, mt))

        # Deregister with the bridge from any unneeded channels
        for c, mt in removed:
            del self._message_processors[c, mt]
            if len(self._get_processors(c)) == 0:
                self.logger.info(f"{self}:  Deregistering from channel '{c}' -- no registered callbacks")
                self._bridge.deregister(self, channel=c)


    def send(self, data, channel):
        """
        Send a message with the provided data on the given channel through Redis.

        Arguments:
            - data: the message data to be published
            - channel: the channel on which to publish the message
        """
        return self._bridge.send(data, channel)


    def request(self, data, channel, blocking=True, timeout=None):
        """
        Send a request with the provided data on the given channel through Redis.

        Arguments:
            - data: the request data to be published
            - channel: the channel on which to publish the request
            - blocking: boolean for whether or not to block and return the response,
                or to return the request ID immediately
            - timeout: number of seconds to wait for a response
        """
        return self._bridge.request(
            data, channel, blocking=blocking, timeout=timeout)


    def respond(self, data, channel, request_id):
        """
        Send a response to the given request on the given channel,
        with the provided data through Redis.

        Arguments:
            - data: the response data to be published
            - channel: the channel on which to publish the response
            - request_id: the ID of the message being responded to
        """
        return self._bridge.respond(data, channel, request_id)


    def _receive_redis(self, message):
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
        processors = self._get_processors(message.channel, type(message))
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
