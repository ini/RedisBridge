# RedisBridge

RedisBridge is a bridge to an internal pub/sub Redis bus.

## Installation

The RedisBridge package can be installed via `pip`.  This can be done from the root folder of the package with the following command:

```git clone https://gitlab.com/cmu_asist/RedisBridge```

```cd RedisBridge```

```pip install -e .```

## Server

This package does **NOT** require running a Redis server. As long as you are only running one RedisBridge instance on a single process, the bridge is able to simulate a server by storing state internally ([see below](#basic-usage)).

However, for high-performance applications, one may want to spin up an actual Redis server. See [Redis's quickstart](https://redis.io/topics/quickstart) for installation instructions (although this should be already taken care of on ripley).

## Basic Usage

1. Create a RedisBridge

```
>>> from RedisBridge import RedisBridge
>>> bridge = RedisBridge(host='localhost', port=6379)
```

If we wanted to run locally and were unable to run a Redis server on the machine, we could set the optional `dummy_redis_server` argument to `True`:

```
>>> bridge = RedisBridge(dummy_redis_server=True)
```

2. Create clients, which need to implement `client.receive_redis(message)`

```
>>> client1 = MyClient()
>>> client2 = MyOtherClient()
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

5. Messages can be constructed and sent to Redis

```
>>> data = "Hello World!"
>>> bridge.send(data, 'channel1')
```

6. Clients registered to the channel get a callback in `client.receive_redis(message)`
```
>>> class MyClient:
... 	def receive_redis(message):
... 		print(message.channel, message.data)
...
channel1 Hello World!
```
7. Stop the bridge to stop receiving messages

```
>>> bridge.stop()
```
## [Messages](./RedisBridge/messages/)

For much more detail about RedisBridge messages, message types, and usage patterns, check out the documentation that lives in [`RedisBridge.messages`](./RedisBridge/messages/). Seriously, go take a look.

## Demos

For some toy examples and demos, check out the [`demos`](./demos/) directory.

