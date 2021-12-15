import redis



class RedisBridge:
    """
    A bridge class for handling connections to Redis as an internal bus.

    Example usage:
    
    1. Create a RedisBridge

    >>> bridge = RedisBridge(host='localhost', port=6379)

    2. Create clients (that implement `receive(message)`)

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

    def __init__(self, name='RedisBridge', host='localhost', port=6379, db=0):
        self.connection = redis.Redis(host='localhost', port=6379, db=0)
        self.pubsub = self.connection.pubsub(ignore_subscribe_messages=True)
        self.thread = None

        self.name = name
        self.observers = {}

        # Set client pubsub hard / soft output buffer limits
        # 1 GB hard limit, 64 MB per 60 seconds soft limit
        self.connection.config_set(
            'client-output-buffer-limit', 
            f'normal 0 0 0 slave 268435456 67108864 60 pubsub {2 ** 30} {2 ** 26} 60')


    def subscribe(self, channel):
        """
        Subscribe to messages from a specific channel through the Redis connection.

        Arguments:
            - channel: the name of the channel
        """
        self.pubsub.subscribe(**{channel: self.receive})


    def register(self, observer, channel):
        """
        Register an observer object to receive messages of a specific channel.
        When messages of the given channel are received, 
        the bridge calls observer.recieve(message).

        Arguments:
            - observer: client object to receive messages
            - channel: the name of the channel on which the client should receive
        """
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
                    self.observers[c].remove(observer)

        # Deregister observer from given channel
        else:
            self.observers[channel].remove(observer)

        # Unsuscribe to any channels that no longer have any observers
        for c in self.observers.keys():
            if len(self.observers[c]) == 0:
                self.pubsub.unsubscribe(c)


    def receive(self, message):
        """
        Forward a message to relevant observers (via `observer.receive(message)`).

        Arguments:
            - message: dictionary representing the recived message.
                The field message['data'] is given as a `bytes` object, 
                which may be decoded or unpickled by clients as needed.
        """
        message['channel'] = message['channel'].decode() # convert channel to string
        if message['channel'] in self.observers.keys():
            for observer in self.observers[message['channel']]:
                observer.receive(message)


    def start(self, sleep_time=0):
        """
        Start receiving messages from the Redis connection 
        in a non-blocking background thread.

        Arguments:
            sleep_time: number of seconds to time.sleep() per loop iteration
        """
        if self.pubsub.connection is None:
            print("Can't start RedisBridge, as it is not currently subscribed to any channels.")
        else:
            self.thread = self.pubsub.run_in_thread(sleep_time=sleep_time)


    def stop(self, timeout=1.0):
        """
        Stop receiving messages from the Redis connection.

        Arguments:
            - timeout: seconds before background thread timeout 
        """
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
        if should_pickle:
            import pickle
            self.connection.publish(channel, pickle.dumps(data))
        else:
            self.connection.publish(channel, data)

