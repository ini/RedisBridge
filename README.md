
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

1) Create a bridge and an observer
```
>>> import RedisBridge
>>> bridge = RedisBridge.RedisBridge()
>>> observer = RedisBridge.Observer(bridge)
```

2) Register callbacks with the observer
```
>>> callback = lambda msg: print('Received message:', msg)
>>> observer.register_callback(callback, channel='my_channel')
```

3) Start the bridge to begin receiving messages
```
>>> bridge.start()
```

4. Send messages via the bridge
```
>>> bridge.send('Hello World!', channel='my_channel')
```

The observer calls all callbacks registered with it on the given channel
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

For some toy examples and demos, check out the [`demos`](./demos/) directory.

