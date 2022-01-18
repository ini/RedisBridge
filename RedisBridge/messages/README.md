

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

RedisBridge also supports a request/response usage pattern.  `Request` and `Response`  are subclasses of `Message` that are defined for this purpose. To see a little toy demo of this pattern in action, check out [`demos/sorting.py`](../../demos/sorting.py).

### Requesting

#### Blocking
To send a request, use the RedisBridge method `request()`:
```
>>> response = bridge.request(data, channel)
```
We can also specify an optional `timeout` parameter:
```
>>> response = bridge.request(data, channel, timeout=1.0)
```

This creates and publishes `Request` message where `msg.type` is `'request'`. All clients registered to the channel will receive the request, and can choose whether or not to respond. Once a response is received, the bridge returns it as the result of the `request()` call.

#### Non-Blocking
A requesting client may also want to send a request as a non-blocking call. To do so, simply set the `blocking` flag to false:

```
>>> self.request_id = bridge.request(data, channel, blocking=False)
```

Rather than returning the first response immediately, the ID of the request message is returned for the client to keep track of and check against any incoming response messages.

If the requesting client sends a non-blocking request, it needs to be able to handle any responses in its `receive_redis()`  method:

```
def receive_redis(msg) # Requester
	if msg.channel == 'my_channel' and msg.type == 'response':
		if msg.request_id == self.request_id:
			pass # do something with `msg.data`
```

### Responding

To send a response to a message, use the RedisBridge method `respond()`:
```
>>> bridge.respond(data, channel, request_id=msg.id)
```

Typically this can be done by a client directly in its `receive_redis()` method:
```
def receive_redis(msg): # Responder
	if msg.channel == 'my_channel' and msg.type == 'request':
		data = 'roger that'
		bridge.respond(data, 'my_channel', request_id=msg.id)
```
This will create a `Response` message where `msg.type` is `'response'` and `msg.request_id` is `request.id`. All clients registered to the channel will receive the response, and can choose to ignore it or process it.

To see a little demo of the non-blocking request/response pattern in action, check out [`demos/sorting_nonblocking.py`](../../demos/sorting_nonblocking.py).
