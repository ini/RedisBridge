
# RedisBridge.messages

The `RedisBridge.messages` module defines the message classes that get sent to observer clients.

## Basics

The base `Message` class has four important properties:
- `id`: a unique string identifier for the message
- `type`: a string indicating the type of the message
- `channel`: the string name of the channel the message was sent on
- `data`: the data for the message

Sending data on a particular channel can be done via the RedisBridge method: `bridge.send(data, channel)`. This automatically creates and sends a `Message` object with a unique ID and the given channel and data.

Receiving data is as simple as implementing the `receive_redis(msg)` on the client side, where `msg` will be a `Message` instance.


## Request / Response

RedisBridge also supports a request/response usage pattern.  `Request` and `Response`  are subclasses of `Message` that are defined for this purpose. To see a little toy demo of this pattern in action, check out [`demos/sorting_demo.py`](../../demos/sorting_demo.py).

### Requesting

To send a request, set the `is_request` flag to true:
```
>>> bridge.send(data, channel, is_request=True)
```
This will create a `Request` message where `msg.type` is `'request'`. All clients registered to the channel will receive the request, and can choose whether or not to respond.

A requesting client may also want to keep track of the ID of its request message:
```
>>> self.request_id = bridge.send(data, channel, is_request=True)
```
Finally, the requesting client needs to be able to handle responses in its `receive_redis()`  method:

```
def receive_redis(msg) # Requester
	if msg.channel == 'my_channel' and msg.type == 'response':
		if msg.request_id == self.request_id:
			pass # do something with `msg.data`
```

### Responding

To send a response, set the optional `response_to` argument to the ID of the original `Request` message:
```
>>> bridge.send(data, 'sort', response_to=request.id)
```

Typically this can be done by a client directly in its `receive_redis()` method:
```
def receive_redis(msg): # Responder
	if msg.channel == 'my_channel' and msg.type == 'request':
		data = 'roger that'
		bridge.send(data, 'my_channel', response_to=msg.id)
```
This will create a `Response` message where `msg.type` is `'response'` and `msg.request_id` is `request.id`.

To see a little toy demo of this pattern in action, check out [`demos/sorting_demo.py`](../../demos/sorting_demo.py).
