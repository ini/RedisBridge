
# RedisBridge

RedisBridge is a Python package that handles sending and receiving messages across clients via a Redis server.

## Installation

```
pip install RedisBridge
```

## Requirements

* RedisBridge is intended to connect to a Redis server. To install and run Redis, [see the instructions here](https://redis.io/topics/quickstart).
* RedisBridge supports Python 3.6 or later.

## Getting Started

1) Spin up a Redis server
```
$ redis-server --port 6379 &
```

2) Create a bridge on each client
```
>>> from RedisBridge import RedisBridge
>>> bridge = RedisBridge(host='localhost', port=6379)
```

3) Register callbacks to receive messages
```
>>> def callback(msg):
...     print('Received message:', msg)

>>> bridge.register_callback(callback, 'my_channel')
```

4) Start each bridge to begin sending/receiving messages
```
>>> bridge.start()
```

5. Send messages to other clients via bridge
```
>>> bridge.send('Hello World!', 'my_channel')
```

Each bridge calls all callbacks registered with it on the given channel
```
Received message: <Message: id='t2yedxi3', channel='my_channel', data='Hello World!'>
```

6. Stop a bridge to close its connection to the server
```
>>> bridge.stop()
```

## Docs

For much more detail about RedisBridge classes, messages, and usage patterns, [check out the documentation](./docs/). Seriously, go take a look.

## Demos

For some toy examples and demos, [check out the demos folder](./demos/).
