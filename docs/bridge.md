[`Back to Docs`](./README.md)
***
<br>

# `RedisBridge.RedisBridge`

**Source Code:** [bridge.py](../RedisBridge/bridge.py)

`RedisBridge.RedisBridge` is a bridge class for handling sending / receiving messages via a Redis connection.


## Example Usage

1. Create a RedisBridge

```
>>> import RedisBridge
>>> bridge = RedisBridge.RedisBridge(host='localhost', port=6379)
```

If we wanted to run locally and were unable to run a Redis server on the machine, we could set the optional `mock_redis_server` argument to `True`:

```
>>> bridge = RedisBridge.RedisBridge(mock_redis_server=True)
```

2. Create clients, which need to implement `_receive_redis(message)`

```
>>> class MyClient:
...     def _receive_redis(self, message):
...         print(message)
...
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


## class `RedisBridge.RedisBridge`

**Source Code:** [bridge.py](../RedisBridge/bridge.py)

**Description:** Bridge class for handling sending / receiving messages via a Redis server.

**Initialization:** `RedisBridge.RedisBridge(name=None, mock_redis_server=False, host='localhost', port=6379, db=0, **redis_kwargs)`

[Check here](https://redis-py.readthedocs.io/en/stable/connections.html#redis.Redis) for a full list of optional Redis keyword arguments.

### Attributes

- `name` - the name of this RedisBridge

### Methods

- `subscribe(channel)` - Subscribe to messages from a specific channel.

- `register(observer, channel)` - Register an observer object to receive messages of a specific channel. When messages of the given channel are received, the bridge calls `observer._receive_redis(message)`.

- `deregister(observer, channel=None)` - Remove an observer from receiving messages of a given channel. If no channel is provided, then the observer is deregistered from all channels.

- `start(sleep_time=0)` - Start receiving messages in a non-blocking background thread.

- `stop(timeout=None)` - Stop receiving messages.

- `send(data, channel)` - Send a message with the provided data on the given channel.

- `request(data, channel, blocking=True, timeout=None)` - Send a request with the provided data on the given channel.

- `respond(data, channel, request_id)` - Send a response to the given request, on the given channel with the provided data.


<br><br>
***
[`Back to Docs`](./README.md)
