[`Back to Docs`](./README.md)
***
<br>

# `RedisBridge.messages`

**Source Code:** [messages/](../RedisBridge/messages/)

The `RedisBridge.messages` module defines the message classes that get sent to observing clients. This document also provides some detail about usage patterns.


## Basics

The base `Message` class has three important properties:
- `id`: a unique string identifier for the message
- `channel`: the string name of the channel the message was sent on
- `data`: the data for the message

Sending data on a particular channel can be done via the RedisBridge method `bridge.send()`:
```
>>> bridge = RedisBridge()
>>> data = "thunder and lightning"
>>> bridge.send(data, channel='weather')
```
This automatically creates and sends a `Message` object with a unique ID and the given channel and data.

Receiving data is as simple as implementing the `_receive_redis(msg)` on the client side, where `msg` will be a `Message` instance.
```
>>> class MyClient:
...     def _receive_redis(self, msg):
...         print(msg)
...
<Message: id='z6brcq36', channel='weather', data='thunder and lightning'>
```


## Request / Response

RedisBridge also supports a request / response usage pattern.  `Request` and `Response`  are subclasses of `Message` that are defined for this purpose. To see a little toy demo of this pattern in action, check out [demos/sorting.py](../demos/sorting.py).

Note: the examples in this section use the `RedisBridge.interfaces.CallbackInterface` bridge interface. For more information about the `RedisBridge.interfaces` module, [read here](./interfaces.md).
```
>>> from RedisBridge.interfaces import CallbackInterface
>>> bridge = CallbackInterface(bridge)
```

### Requesting

#### Blocking
To send a request, use the RedisBridge (or RedisInterface) method `bridge.request()`:
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
4) Otherwise, if no response is received before the specified timeout, the `request()` call raises a `TimeoutError`.

#### Non-Blocking
A client may also want to send a request as a non-blocking call. To do so, simply set the `blocking` flag to false:

```
>>> my_request_id = bridge.request(data, channel, blocking=False)
```

Rather than returning the first response immediately, the ID of the request message is returned for the client to keep track of and check against any incoming response messages (potentially multiple).

If a requesting client sends a non-blocking request, it can handle responses by registering a callback for responses on the channel:
```
>>> def on_response(msg): # Requester
...     if msg.request_id == my_request_id:
...         print(msg.data)
...
>>> bridge.register_callback(
        on_response, channel='my_channel', message_type='Response')
```

### Responding

To send a response to a message, use the RedisBridge (or RedisInterface) method `bridge.respond()`:
```
>>> bridge.respond(data, channel, request_id=msg.id)
```

This is typically done by a client via registering a callback for request messages on a particular channel:
```
>>> def on_request(msg): # Responder
...     data = "i gotchu"
...     bridge.respond(data, 'my_channel', request_id=msg.id)
...
>>> bridge.register_callback(
        on_request, channel='my_channel', message_type='Request')
```
This will create a `Response` message where `msg.request_id` is the ID of the relevant `Request` message. **All** clients registered to the channel will receive the response, and can choose to process it or to ignore it (typically by checking the request ID).

To see a little demo of the non-blocking request/response pattern in action, check out [demos/sorting_nonblocking.py](../demos/sorting_nonblocking.py).


## class `RedisBridge.messages.Message`

**Source Code:** [base.py](../RedisBridge/messages/base.py)

**Description:** Base class for RedisBridge messages.

### Attributes

- `id` - a unique string identifier for this message

- `channel` - the string name of the channel this message was sent on

- `data` - the data for this message

## class `RedisBridge.messages.Request(Message)`

**Source Code:** [request_response.py](../RedisBridge/messages/request_response.py)

**Description:** A request message that expects some response.

## class `RedisBridge.messages.Response(Message)`

**Source Code:** [request_response.py](../RedisBridge/messages/request_response.py)

**Description:** A response message that stores the ID of its corresponding request.

### Attributes

- `request_id` - The ID of the request message being responded to.


<br><br>
***
[`Back to Docs`](./README.md)
