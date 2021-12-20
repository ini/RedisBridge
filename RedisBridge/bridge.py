import logging
import redis



class RedisBridge:
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

    >>> bridge.send(belief_state, 'belief', should_pickle=True)

    6. Stop the bridge to stop receiving messages

    >>> bridge.stop()
    """

    def __init__(self, name=None, host='localhost', port=6379, db=0):
        self.connection = redis.Redis(host=host, port=port, db=db, health_check_interval=1)
        self.pubsub = self.connection.pubsub(ignore_subscribe_messages=True)
        self.thread = None

        self.name = name
        self.observers = {}

        # Set client pubsub hard / soft output buffer limits
        # 1 GB hard limit, 64 MB per 60 seconds soft limit
        self.connection.config_set(
            'client-output-buffer-limit', 
            f'normal 0 0 0 slave 268435456 67108864 60 pubsub {2 ** 32} {2 ** 32} 60')

        # Grab a handle to logger for the class, if it exists, else the default logger
        if self.__class__.__name__ in logging.Logger.manager.loggerDict:
            self.logger = logging.getLogger(self.__class__.__name__)
        else:
            self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"{self}:  Connected to Redis at host={host}, port={port}, db={db}")


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
        self.logger.debug(f"{self}:  Received {message}'")

        message['channel'] = message['channel'].decode() # convert channel to string
        if message['channel'] in self.observers.keys():
            for observer in self.observers[message['channel']]:
                try:
                    observer.receive_redis(message)
                except Exception as e:
                    self.logger.exception(f"{self}:  Error in observer {observer} receiving message - {e}")


    def start(self, sleep_time=0):
        """
        Start receiving messages from the Redis connection 
        in a non-blocking background thread.

        Arguments:
            sleep_time: number of seconds to time.sleep() per loop iteration
        """
        self.logger.info(f"{self}:  Starting callback loop with internal Redis bus")
        if self.pubsub.connection is None:
            self.logger.warning(f"{self}:  Cannot start RedisBridge, as it is not currently subscribed to any channels.")
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


    def send(self, data, channel, should_pickle=False):
        """
        Send a message with the provided on the given channel 
        through the Redis connection.

        Arguments:
            - data: the message data to be published
                Data type should be one of {bytes, str, int, float}.
                Pickleable object types can be converted to bytes 
                via the optional `should_pickle` argument. 
            - channel: the channel on which to publish the message
            - pickle: boolean indicating whether or not to pickle the data 
                into bytes before sending; default is False
        """
        self.logger.debug(f"{self}:  Publishing {data} on channel {channel}")
        if should_pickle:
            import pickle
            self.connection.publish(channel, pickle.dumps(data))
        else:
            self.connection.publish(channel, data)

