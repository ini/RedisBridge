[`Back to Docs`](./README.md)
***
<br>

# `RedisBridge.RedisBridge`

**Source Code:** [bridge.py](../RedisBridge/bridge.py)

`RedisBridge.RedisBridge` is a bridge class for handling sending / receiving messages via a Redis connection.


## Basic Usage

1. Create a RedisBridge

```
>>> import RedisBridge
>>> bridge = RedisBridge.RedisBridge(host='localhost', port=6379)
```

If all of our clients are on the same local process and we are unable to run a Redis server on the machine, we could set the optional `use_mock_redis_server` argument to `True`:

```
>>> bridge = RedisBridge.RedisBridge(use_mock_redis_server=True)
```

2. Create observer clients, which need to implement `_receive_redis(message)`

```
>>> class MyClient:
...     def _receive_redis(self, message):
...         print(message)

>>> client1 = MyClient()
>>> client2 = MyClient()
```

3. Register clients to listen to various channels

```
>>> bridge.register(client1, 'channel1')
>>> bridge.register(client2, 'channel2')
```

4. Start the bridge to begin receiving messages

```
>>> bridge.start()
```

5. Messages can be constructed and sent via the bridge

```
>>> data = "Hello World!"
>>> bridge.send(data, 'channel1')
```

6. All clients registered to the channel get a callback in `client._receive_redis(message)`

```
<Message: id='t2yedxi3', channel='channel1', data='Hello World!'>
```

7. Stop the bridge to stop receiving messages

```
>>> bridge.stop()
```

## Callbacks

When implementing RedisBridge clients, it can become cumbersome keep track of various channels and messages types for every received message in `_receive_redis(msg)`. The bridge also integrates a [`CallbackInterface`](./interfaces.md#class-redisbridgeinterfacescallbackinterface) for triggering callbacks on receiving a message of a given type on a given channel.

### Example: Powers

Let's define a couple callbacks:
```
>>> def square(msg):
... 	print(msg.data ** 2)

>>> def cube(msg):
... 	print(msg.data ** 3)
```

Now we'll create a bridge and register our callbacks for specific channels:
```
>>> from RedisBridge import RedisBridge
>>> bridge = RedisBridge()
>>> bridge.register_callback(square, 'square')
>>> bridge.register_callback(cube, 'cube')
```

Test it out:
```
>>> bridge.start()
>>> bridge.send(3, channel='square')
9
>>> bridge.send(2, channel='cube')
8
```

To see the full example in action, check out [demos/pow.py](../demos/pow.py).


## class `RedisBridge.RedisBridge`

**Source Code:** [bridge.py](../RedisBridge/bridge.py)

**Description:** Bridge class for handling sending / receiving messages via a Redis server.

**Initialization:** `RedisBridge.RedisBridge(name=None, connect_on_creation=True, use_mock_redis_server=False, host='localhost', port=6379, db=0, **redis_kwargs)`

[Check here](https://redis-py.readthedocs.io/en/stable/connections.html#redis.Redis) for a full list of optional Redis keyword arguments.

### Attributes

- `name` - the name of this RedisBridge

### Methods

- `connect(**redis_kwargs)` - Connect to the Redis server. [See here](https://redis-py.readthedocs.io/en/stable/connections.html#redis.Redis) for a full list of keyword arguments.

- `subscribe(*channels)` - Subscribe to messages from one or more channels.

- `unsubscribe(*channels)` - Unsubscribe from the specified channels. If none are provided, unsubscribe from all channels.

- `register(observer, channel)` - Register an observer object to receive messages of a specific channel. When messages of the given channel are received, the bridge calls `observer._receive_redis(message)`.

- `deregister(observer, channel=None)` - Remove an observer from receiving messages of a given channel. If no channel is provided, then the observer is deregistered from all channels.

- `register_callback(callback, channel, message_type=None)` - Register a callback to be triggered when message of a given type is received on a given channel.

- `deregister_callback(callback, channel=None, message_type=None)` - Deregister the callback as a message handler for the given channel and message type.

- `start(sleep_time=0)` - Start receiving messages in a non-blocking background thread.

- `stop(timeout=None)` - Stop receiving messages.

- `send(data, channel)` - Send a message with the provided data on the given channel.

- `request(data, channel, blocking=True, timeout=None)` - Send a request with the provided data on the given channel.

- `respond(data, channel, request_id)` - Send a response to the given request, on the given channel with the provided data.


<br><br>
***
[`Back to Docs`](./README.md)
