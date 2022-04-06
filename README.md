
# RedisBridge

RedisBridge is a Python package that handles sending and receiving messages across clients via a Redis server.

## Installation

```
pip install RedisBridge
```

## Server

This package does **NOT** actually require running a Redis server. As long as you are only running one RedisBridge instance on a single process, the bridge is able to simulate a server by storing state internally ([see docs](./docs/bridge.md)).

However, for high-performance applications, one may want to spin up an actual Redis server. See [Redis's quickstart](https://redis.io/topics/quickstart) for installation instructions.

## Docs

For much more detail about RedisBridge classes, messages, and usage patterns, [check out the documentation](./docs/). Seriously, go take a look.

## Basic Usage

1) Spin up a Redis server
```
$ redis-server --port 6379
```

2) Create a bridge on each client
```
>>> from RedisBridge import RedisBridge
>>> bridge = RedisBridge(host='localhost', port=6379)
```

3) Register clients to receive messages on a given channel through a `CallbackInterface`
```
>>> def callback(msg):
...     print('Received message:', msg)

>>> from RedisBridge.interfaces import CallbackInterface
>>> CallbackInterface(bridge).register_callback(callback, channel='my_channel')
```

4) Start each bridge to begin sending/receiving messages
```
>>> bridge.start()
```

5. Send messages to other clients via bridge
```
>>> bridge.send('Hello World!', channel='my_channel')
```

`CallbackInterface` calls all callbacks registered with it on the given channel
```
Received message: <Message: id='t2yedxi3', channel='my_channel', data='Hello World!'>
```

6. Stop a bridge to close its connection to the server
```
>>> bridge.stop()
```

## Demos

For some toy examples and demos, [check out the demos folder](./demos/).
