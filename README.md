# RedisBridge

RedisBridge is a bridge to an internal pub/sub Redis bus.

## Requirements

This repository requires the `redis-py` package. This is most easily installed through `pip`:

```pip install [--user] redis```

This package also requires a running Redis server. See [Redis's quickstart](https://redis.io/topics/quickstart) for local installation instructions (although this should be already taken care of on ripley).

## Installation

The RedisBridge package can be installed via `pip`.  This can be done from the root folder of the package with the following command:

```pip install --user -e .```

## Example Usage

1. Create a RedisBridge

```
>>> bridge = RedisBridge(host='localhost', port=6379)
```

2. Create clients, which need to implement `client.receive(message)`

```
>>> client1 = MyClient()
>>> client2 = MyOtherClient()
```

3. Register clients to various channels

```
>>> bridge.register(client1, 'belief')
>>> bridge.register(client2, 'disalignment')
```

4. Start the bridge to begin receiving messages

```
>>> bridge.start()
```

5. Messages can be constructed and sent to Redis:

```
>>> bridge.send(belief_state, 'belief', should_pickle=True)
```

6. Stop the bridge to stop receiving messages

```
>>> bridge.stop()
```
