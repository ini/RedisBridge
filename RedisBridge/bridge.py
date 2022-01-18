import logging
import pickle
import redis
import time

from .messages import Message, Request, Response
from .utils import Loggable



class RedisBridge(Loggable):
    """
    A bridge class for handling connections to Redis as an internal bus.

    Example usage:

    1. Create a RedisBridge

    >>> bridge = RedisBridge(host='localhost', port=6379)

    2. Create clients (that implement `receive_redis(message)`)

    >>> client1 = MyClient()
    >>> client2 = MyOtherClient()

    3. Register clients with various channels

    >>> bridge.register(client1, 'belief')
    >>> bridge.register(client2, 'disalignment')

    4. Start the bridge to begin receiving messages

    >>> bridge.start()

    5. Messages can be constructed and sent to Redis:

    >>> bridge.send(belief_state, 'belief')

    6. Stop the bridge to stop receiving messages

    >>> bridge.stop()
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
        self.observers = {}
        self.responses = {}

        if dummy_redis_server:
            import fakeredis
            self.connection = fakeredis.FakeRedis(host=host, port=port, db=db, health_check_interval=1)
            self.logger.info(f"{self}:  Connected to dummy Redis server.")
        else:
            # Set client pubsub hard / soft output buffer limits
            # 1 GB hard limit, 64 MB per 60 seconds soft limit
            self.connection = redis.Redis(host=host, port=port, db=db, health_check_interval=1)
            self.connection.config_set(
                'client-output-buffer-limit',
                f'normal 0 0 0 slave 268435456 67108864 60 pubsub {2 ** 32} {2 ** 32} 60')
            self.logger.info(f"{self}:  Connected to Redis at host={host}, port={port}, db={db}")

        self.pubsub = self.connection.pubsub(ignore_subscribe_messages=True)
        self.thread = None


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
        self.pubsub.subscribe(**{channel: self.on_message})


    def register(self, observer, channel):
        """
        Register an observer object to receive messages of a specific channel.
        When messages of the given channel are received,
        the bridge calls observer.recieve(message).

        Arguments:
            - observer: client object to receive messages
            - channel: the name of the channel on which the client should receive
        """
        self.logger.debug(f"{self}:  Registering {observer} to receive messages on channel '{channel}'")

        if not channel in self.observers.keys():
            self.subscribe(channel)
            self.observers[channel] = set()

        # Add the observer
        self.observers[channel].add(observer)


    def deregister(self, observer, channel=None):
        """
        Remove an observer from receiving messages of a given channel.
        If no channel is provided, then the observer is deregistered from all channels.
        message classes

        Arguments:
            - observer: client object to receive messages
            - channel: the name of the channel on which the client should receive
        """

        # Deregister observer from all channels
        if channel is None:
            for c in self.observers.keys():
                if observer in self.observers[c]:
                    self.logger.debug(f"{self}:  Deregistering {observer} from channel '{c}'")
                    self.observers[c].remove(observer)

        # Deregister observer from given channel
        else:
            self.logger.debug(f"{self}:  Deregistering {observer} from channel '{channel}'")
            self.observers[channel].remove(observer)

        # Unsuscribe to any channels that no longer have any observers
        for c in self.observers.keys():
            if len(self.observers[c]) == 0:
                self.logger.info(f"{self}:  Unsubscribing from channel '{c}' -- no registered listeners")
                self.pubsub.unsubscribe(c)


    def on_message(self, message):
        """
        Callback when the bridge receives a message from Redis.
        Forwards a message to relevant observers (via `observer.receive_redis(message)`).

        Arguments:
            - message: dictionary representing the recived message.
                The field message['data'] is given as a `bytes` object,
                which may be decoded or unpickled by clients as needed.
        """
        message = Message.from_redis(message)
        self.logger.debug(f"{self}:  Received {message}'")

        # Update responses
        if isinstance(message, Response):
            self.responses[message.request_id] = message

        # Forward message to relevant observers
        if message.channel in self.observers.keys():
            for observer in self.observers[message.channel]:
                try:
                    observer.receive_redis(message)
                except Exception as e:
                    self.logger.exception(
                        f"{self}:  Error in observer {observer} receiving message - {e}")


    def start(self, sleep_time=0):
        """
        Start receiving messages from the Redis connection
        in a non-blocking background thread.

        Arguments:
            sleep_time: number of seconds to time.sleep() per loop iteration
        """
        self.logger.info(f"{self}:  Starting callback loop with internal Redis bus")
        if self.pubsub.connection is None:
            self.logger.warning(
                f"{self}:  Cannot start RedisBridge, as it is not currently subscribed to any channels.")
        else:
            self.connection.flushdb()
            self.thread = self.pubsub.run_in_thread(sleep_time=sleep_time)


    def stop(self, timeout=1.0):
        """
        Stop receiving messages from the Redis connection.

        Arguments:
            - timeout: seconds before background thread timeout
        """
        self.logger.info(f"{self}:  Stopping callback loop for the internal Redis bus")
        self.thread.stop()
        self.thread.join(timeout=timeout)
        self.pubsub.close()
        self.connection.flushdb()


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
        self.connection.publish(channel, pickle.dumps(msg))


    def request(self, data, channel, blocking=True, timeout=1.0):
        """
        Sends a request with the provided data on the given channel
        through the Redis connection.

        Arguments:
            - data: the request data to be published
            - channel: the channel on which to publish the request
            - blocking: boolean for whether or not to block and return the response,
                or to return the request ID immediately
            - timeout: number of seconds to wait for a response before returning None
        """
        self.logger.debug(f"{self}:  Sending request {data} on channel '{channel}'")

        # Create and send the request
        msg = Request(channel, data)
        self.connection.publish(channel, pickle.dumps(msg))

        # If non-blocking, return the request ID
        if not blocking:
            return msg.id

        # If blocking, wait for a response
        timeout_time = time.time() + timeout
        self.responses[msg.id] = None
        while self.responses[msg.id] is None:
            if time.time() >= timeout_time:
                self.logger.warning(
                    f"{self}:  Request {data} on channel '{channel}' timed out after {timeout} seconds")
                break

        # Return the response
        response = self.responses[msg.id]
        del self.responses[msg.id]
        return response


    def respond(self, data, channel, request_id):
        """
        Sends a response to the given request on the given channel,
        with the provided data through the Redis connection.

        Arguments:
            - data: the response data to be published
            - channel: the channel on which to publish the response
            - request_id: the ID of the message being responded to
        """
        self.logger.debug(f"{self}:  Sending response {data} on channel '{channel}'")

        # Create and send the response
        msg = Response(channel, data, request_id=request_id)
        self.connection.publish(channel, pickle.dumps(msg))

