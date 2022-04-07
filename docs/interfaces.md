[`Back to Docs`](./README.md)
***
<br>

# `RedisBridge.interfaces`

**Source Code:** [interfaces/](../RedisBridge/interfaces/)

`RedisBridge.interfaces` provides a family of wrappers around a RedisBridge that provide specific interfaces for interacting with the bridge.

## Basics: CallbackInterface

When implementing RedisBridge clients, it can become cumbersome keep track of various channels and messages types for every received message in `_receive_redis(msg)`. `RedisBridge.interfaces.CallbackInterface` takes care of all this under the hood. All a client needs do is wrap a RedisBridge and register callbacks:
```
>>> bridge = RedisBridge()
>>> interface = CallbackInterface(bridge)
>>> interface.register_callback(callback, channel)
```

We can also register callbacks on a channel that are only triggered for a specific message type:
```
>>> interface.register_callback(callback, channel, message_type='Request')
```


## Example: Guess the Number

In this example we'll implement a two-player random number guessing game, where each player will be a client with a bridge wrapped in a `CallbackInterface`.

First, let's get our imports:
```
import random
from RedisBridge import RedisBridge
from RedisBridge.interfaces import CallbackInterface
```

Second, we'll define a class called `Oracle`, which does the following:
1) Generates a random number from 1 to 100
2) Registers a `judge_guess(msg)` callback for requests on the "game" channel
```
class Oracle:
    def __init__(self, bridge):
        self.secret_number = random.randint(1, 100)
        self.interface = CallbackInterface(bridge)
        self.interface.register_callback(
            self.judge_guess, channel='game', message_type='Request')

    def judge_guess(self, msg):
        guess = msg.data
        if self.secret_number > guess:
            answer = 'higher'
        elif self.secret_number < guess:
            answer = 'lower'
        else:
            answer = 'perfect'
        self.interface.respond(
            data=answer, channel='game', request_id=msg.id)
```

Now we define a `Guesser` class that:
1) Keeps track of the possible range, given it's guesses so far
2) Makes a guess and sends a request for feedback over the bridge
3) Registers a `get_feedback(msg)` callback for responses on the "game" channel
```
class Guesser:
    def __init__(self, bridge):
        self.interface = CallbackInterface(bridge)
        self.interface.register_callback(
            self.get_feedback, channel='game', message_type='Response')
        self.min, self.max = 1, 100
        self.guess, self.guess_id = None, None

    def make_guess(self):
        self.guess = random.randint(self.min, self.max)
        self.guess_id = self.interface.request(
            data=self.guess, channel='game', blocking=False)

    def get_feedback(self, msg):
        if msg.request_id == self.guess_id:
            answer = msg.data
            if answer == 'higher':
                self.min = self.guess + 1
                self.make_guess()
            elif answer == 'lower':
                self.max = self.guess - 1
                self.make_guess()
```

Now let's initialize the bridge and the players:
```
>>> bridge = RedisBridge()
>>> p1 = Oracle(bridge)
>>> p2 = Guesser(bridge)
```
Finally, we start the bridge and make an initial guess:
```
>>> bridge.start()
>>> p2.make_guess()
``` 

To see this example in action, check out [demos/guess.py](../demos/guess.py).


## class `RedisBridge.interfaces.CallbackInterface`

**Source Code:** [callback_interface.py](../RedisBridge/interfaces/callback_interface.py)

**Description:** A wrapper around a Redis bridge that extends with functionality to register and deregister individual callback methods for specific channels and message types, as opposed to handling all messages in a single `_receive_redis()` method.

**Initialization:** `RedisBridge.interfaces.CallbackInterface(bridge)`

### Methods

- `register_callback(callback, channel, message_type=None)` - Register a callback, indicating the function that should be called when a message is received on the given channel.

- `deregister_callback(callback, channel=None, message_type=None)` - Deregister the callback as a message processor for the given channel and message type.

- `send(*args, **kwargs)` - Send a message through the bridge. See `RedisBridge.RedisBridge.send()`.

- `request(*args, **kwargs)` - Send a request through the bridge. See `RedisBridge.RedisBridge.request()`.

- `respond(*args, **kwargs)` - Send a response through the bridge. See `RedisBridge.RedisBridge.respond()`.


<br><br>
***
[`Back to Docs`](./README.md)
