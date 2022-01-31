
# RedisBridge

RedisBridge is a package that handles sending and receiving messages via a Redis server.

## Installation

The RedisBridge package can be installed via `pip`.  This can be done with the following commands:
```
git clone https://gitlab.com/cmu_asist/RedisBridge
cd RedisBridge
pip install --user -e .
```

## Server

This package does **NOT** actually require running a Redis server. As long as you are only running one RedisBridge instance on a single process, the bridge is able to simulate a server by storing state internally ([see docs](./docs/bridge.md)).

However, for high-performance applications, one may want to spin up an actual Redis server. See [Redis's quickstart](https://redis.io/topics/quickstart) for installation instructions.

For those running on the CMU RI "ripley" host, there should already be a Redis server running on port 6379.

## Basic Usage

1) Create a bridge
```
>>> from RedisBridge import RedisBridge
>>> bridge = RedisBridge()
```

2) Register callbacks through a `CallbackDecorator` interface
```
>>> from RedisBridge.interfaces import CallbackDecorator
>>> callback = lambda msg: print('Received message:', msg)
>>> bridge_interface = CallbackDecorator(bridge)
>>> bridge_interface.register_callback(callback, channel='my_channel')
```

3) Start the bridge to begin receiving messages
```
>>> bridge.start()
```

4. Send messages via the bridge (or via an interface)
```
>>> bridge.send('Hello World!', channel='my_channel')
```

The `CallbackDecorator` calls all callbacks registered with it on the given channel
```
Received message: <Message: id='t2yedxi3', channel='my_channel', data='Hello World!'>
```

5. Stop the bridge to stop receiving messages

```
>>> bridge.stop()
```

## Docs

For much more detail about RedisBridge classes, messages, and usage patterns, [check out the documentation](./docs/). Seriously, go take a look.

## Demos

For some toy examples and demos, [check out the demos folder](./demos/).

