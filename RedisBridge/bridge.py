import queue
import redis

from .messages import decode, Message, Request, Response
from .utils import Loggable

from collections import defaultdict



class RedisBridge(Loggable):
    """
    A bridge class that handles sending / receiving messages via a Redis server.

    Attributes:
        - name: the name of this RedisBridge

    Methods:
        - subscribe(channel)
        - register(observer, channel)
        - deregister(observer, channel=None)
        - start(sleep_time=0)
        - stop(timeout=None)
        - send(data, channel)
        - request(data, channel, blocking=True, timeout=None)
        - respond(data, channel, request_id)
    """

    def __init__(self, name=None, dummy_redis_server=False, host='localhost', port=6379, db=0):
        """
        Arguments:
            - name: the name of this RedisBridge
            - dummy_redis_server: boolean indicating whether or not to use a dummy Redis connection
                that simulates talking to a Redis server by storing state internally
            - host: host of the Redis server
            - port: port for the Redis server
            - db: database index to use with the Redis server
        """
        self.name = name
        self._observers = {}
        self._responses = defaultdict(queue.Queue)

        if dummy_redis_server:
            import fakeredis
            self._connection = fakeredis.FakeRedis(host=host, port=port, db=db, health_check_interval=1)
            self.logger.info(f"{self}:  Connected to dummy Redis server.")
        else:
            # Set client pubsub hard / soft output buffer limits
            # 1 GB hard limit, 256 MB per 60 seconds soft limit
            self._connection = redis.Redis(host=host, port=port, db=db, health_check_interval=1)
            self._connection.config_set(
                'client-output-buffer-limit',
                f'normal 0 0 0 slave 268435456 67108864 60 pubsub {2 ** 30} {2 ** 28} 60')
            self.logger.info(f"{self}:  Connected to Redis at host={host}, port={port}, db={db}")

        self._pubsub = self._connection.pubsub(ignore_subscribe_messages=True)
        self._thread = None


    def __str__(self):
        """
        Return a string representation of the object.
        """
        if self.name:
            return f"[{self.__class__.__name__} - {self.name}]"
        else:
            return f"[{self.__class__.__name__}]"


    def subscribe(self, channel):
        """
        Subscribe to messages from a specific channel through the Redis connection.

        Arguments:
            - channel: the name of the channel
        """
        self.logger.info(f"{self}:  Subscribing to channel '{channel}'")
        self._pubsub.subscribe(**{channel: self._on_message})


    def register(self, observer, channel):
        """
        Register an observer object to receive messages of a specific channel.
        When messages of the given channel are received,
        the bridge calls observer._receive_redis(message).

        Arguments:
            - observer: client object to receive messages
            - channel: the name of the channel on which the client should receive
        """
        self.logger.debug(f"{self}:  Registering {observer} to receive messages on channel '{channel}'")

        if not channel in self._observers.keys():
            self.subscribe(channel)
            self._observers[channel] = set()

        # Add the observer
        self._observers[channel].add(observer)


    def deregister(self, observer, channel=None):
        """
        Remove an observer from receiving messages of a given channel.
        If no channel is provided, then the observer is deregistered from all channels.

        Arguments:
            - observer: client object to receive messages
            - channel: the name of the channel on which the client should receive
        """

        # Deregister observer from all channels
        if channel is None:
            for c in self._observers.keys():
                if observer in self._observers[c]:
                    self.logger.debug(f"{self}:  Deregistering {observer} from channel '{c}'")
                    self._observers[c].remove(observer)

        # Deregister observer from given channel
        else:
            self.logger.debug(f"{self}:  Deregistering {observer} from channel '{channel}'")
            self._observers[channel].remove(observer)

        # Unsuscribe to any channels that no longer have any observers
        for c in self._observers.keys():
            if len(self._observers[c]) == 0:
                self.logger.info(f"{self}:  Unsubscribing from channel '{c}' -- no registered listeners")
                self._pubsub.unsubscribe(c)


    def start(self, sleep_time=0):
        """
        Start receiving messages from the Redis connection
        in a non-blocking background thread.

        Arguments:
            sleep_time: number of seconds to time.sleep() per loop iteration
        """

        # Subscribe to internal RedisBridge channel
        self.subscribe('__RedisBridge__')

        # Start the bridge
        self.logger.info(f"{self}:  Starting callback loop with RedisBridge")
        self._connection.flushdb()
        if self._thread:
            self.logger.warning(f"{self}:  Attempting to start RedisBridge that is already running")
        else:
            self._thread = self._pubsub.run_in_thread(sleep_time=sleep_time)


    def stop(self, timeout=None):
        """
        Stop receiving messages from the Redis connection.

        Arguments:
            - timeout: seconds before background thread timeout
        """
        self.logger.info(f"{self}:  Stopping callback loop for RedisBridge")

        if self._thread:
            self._thread.stop()
            self._thread.join(timeout=timeout)
            self._thread = None

        self._pubsub.close()
        self._connection.flushdb()


    def send(self, data, channel):
        """
        Send a message with the provided data on the given channel
        through the Redis connection.

        Arguments:
            - data: the message data to be published
            - channel: the channel on which to publish the message
        """
        self.logger.debug(f"{self}:  Publishing {data} on channel '{channel}'")

        # Create and send the message
        msg = Message(channel, data)
        self._connection.publish(channel, msg._encode())


    def request(self, data, channel, blocking=True, timeout=None):
        """
        Send a request with the provided data on the given channel
        through the Redis connection.

        Arguments:
            - data: the request data to be published
            - channel: the channel on which to publish the request
            - blocking: boolean for whether or not to block and return the response,
                or to return the request ID immediately
            - timeout: number of seconds to wait for a response
        """
        self.logger.debug(f"{self}:  Sending request {data} on channel '{channel}'")

        # Create and send the request
        msg = Request(channel, data)
        self._connection.publish(channel, msg._encode())

        # If non-blocking, return the request ID
        if not blocking:
            return msg.id

        # If blocking, wait for a response
        try:
            response = self._responses[msg.id].get(timeout=timeout)
            return response

        # Raise a TimeoutError if no response received
        except queue.Empty:
            e = TimeoutError(f"Request {data} on channel '{channel}' timed out after {timeout} seconds")
            self.logger.error(f"{self}:  {e}")
            raise e


    def respond(self, data, channel, request_id):
        """
        Send a response to the given request on the given channel,
        with the provided data through the Redis connection.

        Arguments:
            - data: the response data to be published
            - channel: the channel on which to publish the response
            - request_id: the ID of the message being responded to
        """
        self.logger.debug(f"{self}:  Sending response {data} on channel '{channel}'")

        # Create and send the response
        msg = Response(channel, data, request_id=request_id)
        self._connection.publish(channel, msg._encode())


    def _on_message(self, message):
        """
        Callback when the bridge receives a message from Redis.
        Forwards a message to relevant observers (via `observer._receive_redis(message)`).

        Arguments:
            - message: dictionary representing the recived message.
                The field message['data'] is given as a `bytes` object,
                which may be decoded by clients as needed.
        """

        # Decode `Message` instance from raw Redis message 
        try:
            message = decode(message)
            self.logger.debug(f"{self}:  Received {message}'")
        except Exception as e:
            self.logger.error(f"{self}:  Could not decode message - {message}")
            self.logger.exception(f"{self}:  {e}")
            return

        # Update responses
        if isinstance(message, Response):
            self._responses[message.request_id].put(message)

        # Forward message to relevant observers
        if message.channel in self._observers.keys():
            for observer in self._observers[message.channel]:
                try:
                    observer._receive_redis(message)
                except Exception as e:
                    self.logger.exception(
                        f"{self}:  Error in observer {observer} receiving message - {e}")


    @property
    def _unwrapped(self):
        """
        Internal property that returns the underlying bridge.
        """
        return self
