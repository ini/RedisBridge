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

If we wanted to run locally and were unable to run a Redis server on the machine, we could set the optional `dummy_redis_server` argument to `True`:

```
>>> bridge = RedisBridge.RedisBridge(dummy_redis_server=True)
```

2. Create clients, which need to implement `receive_redis(message)`

```
>>> class MyClient:
... 	def receive_redis(self, message):
... 		print(message.channel, message.data)
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

6. All clients registered to the channel get a callback in `client.receive_redis(message)`
```
channel1 Hello World!
```
7. Stop the bridge to stop receiving messages

```
>>> bridge.stop()
```

<br><br>
***
[`Back to Docs`](./README.md)
