# RedisBridge

RedisBridge is a bridge to an internal pub/sub Redis bus.

## Requirements

This package requires a running Redis server. See [Redis's quickstart](https://redis.io/topics/quickstart) for local installation instructions (although this should be already taken care of on ripley).

## Installation

The RedisBridge package can be installed via `pip`.  This can be done from the root folder of the package with the following command:

```git clone https://gitlab.com/cmu_asist/RedisBridge```

```cd RedisBridge```

```pip install -e .```

## Demos

Check out the [`demos`](./demos/) directory.

## Example Usage

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
>>> bridge.register(client1, 'belief')
>>> bridge.register(client2, 'disalignment')
```

4. Start the bridge to begin receiving messages

```
>>> bridge.start()
```

5. Messages can be constructed and sent to Redis

```
>>> bridge.send(belief_state, 'belief')
```

6. Stop the bridge to stop receiving messages

```
>>> bridge.stop()
```

## Docs

[`RedisBridge.messages`](./RedisBridge/messages/)
