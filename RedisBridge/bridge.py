import atexit
import fakeredis
import queue
import redis
import subprocess
import time

from collections import defaultdict

from .interfaces import CallbackInterface
from .messages import decode, Message, Request, Response
from .utils import Loggable, check_server



class RedisBridge(Loggable):
    """
    A bridge class that handles sending / receiving messages via a Redis server.

    Attributes:
        - name: the name of this RedisBridge

    Methods:
        - subscribe(channel)
        - register(observer, channel)
        - deregister(observer, channel=None)
        - register_callback(callback, channel, message_type=None)
        - deregister_callback(callback, channel=None, message_type=None)
        - start(sleep_time=0)
        - stop(timeout=None)
        - send(data, channel)
        - request(data, channel, blocking=True, timeout=None)
        - respond(data, channel, request_id)
    """

    def __init__(self, name=None, use_mock_redis_server=False, **redis_kwargs):
        """
        Arguments:
            - name: the name of this RedisBridge
            - use_mock_redis_server: boolean indicating whether or not to use a mock Redis
                connection that simulates talking to a Redis server by storing state internally

        Redis Keyword Arguments:
            - host: host of the Redis server
            - port: port for the Redis server
            - db: database number to use with the Redis server

        For more Redis keyword arguments,
        see: https://redis-py.readthedocs.io/en/stable/connections.html#redis.Redis
        """
        self.name = name

        self._observers = {}
        self._responses = defaultdict(queue.Queue)
        self._connection = None
        self._pubsub = None
        self._thread = None
        self._server_process = None
        self._callback_interface = CallbackInterface(self)

        # If indicated, use mock Redis server
        if use_mock_redis_server:
            self._connect_mock()
            atexit.register(self._cleanup)
            return

        # Try to connect to given host & port
        self._connect(**redis_kwargs)

        # Fallback to connecting to localhost
        if not self._connection:
            # Spin up a local Redis server
            port = redis_kwargs.get('port', 6379)
            self.logger.warning(f"{self}:  Attempting to spin up Redis server at localhost:{port}")
            try:
                self._server_process = subprocess.Popen(['redis-server', '--port', str(port)])

                # Wait for local Redis server
                timeout = 1.0
                start = time.time()
                while check_server('localhost', port):
                    if time.time() - start > timeout:
                        self._server_process.terminate()
                        break
            except FileNotFoundError as e:
                self.logger.error(f"{self}:  Could not find executable 'redis-server'.")
            except Exception as e:
                self.logger.error(f"{self}:  Could not spin up Redis server - {e}")


            # Connect to local Redis server
            self._connect(**dict(redis_kwargs, host='localhost'))

        # Fallback to using mock Redis server
        if not self._connection:
            self._connect_mock()

        # Stop bridge on program termination
        atexit.register(self._cleanup)


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


    def register_callback(self, *args, **kwargs):
        """
        Register a callback to be triggered when message of a given type
        is received on a given channel.

        See `RedisBridge.interfaces.CallbackInterface.register_callback()`.
        """
        self._callback_interface.register_callback(*args, **kwargs)


    def deregister_callback(self, *args, **kwargs):
        """
        Deregister the callback as a message handler for the
        given channel and message type.

        See `RedisBridge.interfaces.CallbackInterface.deregister_callback()`.
        """
        self._callback_interface.deregister_callback(*args, **kwargs)


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
        if self._thread and self._thread.is_alive():
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

        if self._pubsub:
            self._pubsub.close()

        if self._connection:
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


    def _cleanup(self):
        """
        Clean up any connection to the Redis server.
        """
        self.stop()
        if self._server_process:
            self._server_process.terminate()


    def _connect(self, **kwargs):
        """
        Create and configure connection to Redis server.
        """
        host = kwargs.get('host', 'localhost')
        port = kwargs.get('port', 6379)
        db = kwargs.get('db', 0)

        try:
            self._connection = redis.Redis(**kwargs)
            self._connection.ping()

            # Set client pubsub hard / soft output buffer limits
            # 1 GB hard limit, 64 MB per 60 seconds soft limit
            self._connection.config_set('client-output-buffer-limit', f'pubsub {2**30} {2**26} 60')

            self.logger.info(f"{self}:  Connected to Redis at {host}:{port}, database {db}")
            self._pubsub = self._connection.pubsub(ignore_subscribe_messages=True)

        except redis.exceptions.ConnectionError as e:
            self._connection = None
            self._pubsub = None
            self.logger.warning(f"{self}:  Could not connect to Redis server at {host}:{port} - {e}")

        except Exception as e:
            self._connection = None
            self._pubsub = None
            self.logger.warning(f"{self}:  Could not connect to Redis server at {host}:{port} - {e}")
            raise e


    def _connect_mock(self):
        """
        Creat connection to mock Redis server.
        """
        self._connection = fakeredis.FakeRedis()
        self._pubsub = self._connection.pubsub(ignore_subscribe_messages=True)
        self.logger.info(f"{self}:  Connected to mock Redis server")


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
