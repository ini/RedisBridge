[`Back to Docs`](./README.md)
***
<br>

# `RedisBridge.messages`

**Source Code:** [messages/](../RedisBridge/messages/)

The `RedisBridge.messages` module defines the message classes that get sent to observing clients. This document also provides some detail about usage patterns.

## Basics

The base `Message` class has four important properties:
- `id`: a unique string identifier for the message
- `channel`: the string name of the channel the message was sent on
- `data`: the data for the message
- `type`: a string indicating the type of the message

Sending data on a particular channel can be done via the RedisBridge method `bridge.send()`:
```
>>> bridge = RedisBridge()
>>> data = "thunder and lightning"
>>> bridge.send(data, channel='weather')
```
This automatically creates and sends a `Message` object with a unique ID and the given channel and data.

Receiving data is as simple as implementing the `receive_redis(msg)` on the client side, where `msg` will be a `Message` instance.
```
>>> class MyClient:
... 	def receive_redis(self, msg):
... 		print(msg.channel, msg.type)
... 		print(msg.data)
...
weather message
thunder and lightning
```


## Request / Response

RedisBridge also supports a request / response usage pattern.  `Request` and `Response`  are subclasses of `Message` that are defined for this purpose. To see a little toy demo of this pattern in action, check out [`demos/sorting.py`](../demos/sorting.py).

### Requesting

#### Blocking
To send a request, use the RedisBridge method `bridge.request()`:
```
>>> response = bridge.request(data, channel)
```
We can also specify an optional `timeout` parameter:
```
>>> response = bridge.request(data, channel, timeout=1.0)
```
This results in the following:
1) RedisBridge creates and publishes a `Request` message with a unique ID.
2) All clients registered to the channel will receive the request, and can choose whether or not to respond.
3) Once the first `Response` message for this particular request is received, RedisBridge returns it as the result of the `request()` call.
4) Otherwise, if no response is received before a timeout (default is 1 second), the `request()` call returns `None`.

#### Non-Blocking
A client may also want to send a request as a non-blocking call. To do so, simply set the `blocking` flag to false:

```
>>> my_request_id = bridge.request(data, channel, blocking=False)
```

Rather than returning the first response immediately, the ID of the request message is returned for the client to keep track of and check against any incoming response messages (potentially multiple).

If a requesting client sends a non-blocking request, it can handle any responses in its `receive_redis()`  method:

```
>>> def receive_redis(msg): # Requester
...		if msg.channel == 'my_channel' and msg.type == 'Response':
...			if msg.request_id == my_request_id:
...				print(msg.data)
...
```

### Responding

To send a response to a message, use the RedisBridge method `bridge.respond()`:
```
>>> bridge.respond(data, channel, request_id=msg.id)
```

Typically this can be done by a client directly in its `receive_redis()` method:
```
>>> def receive_redis(msg): # Responder
...		if msg.channel == 'my_channel' and msg.type == 'Request':
...			data = "i gotchu"
...			bridge.respond(data, 'my_channel', request_id=msg.id)
...
```
This will create a `Response` message where `msg.type` is `'response'` and `msg.request_id` is `request.id`. All clients registered to the channel will receive the response in their own `receive_redis()` callback implementations, and can choose to process it or to ignore it.

To see a little demo of the non-blocking request/response pattern in action, check out [`demos/sorting_nonblocking.py`](../demos/sorting_nonblocking.py).

<br><br>
***
[`Back to Docs`](./README.md)
