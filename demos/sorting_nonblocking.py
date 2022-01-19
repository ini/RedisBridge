"""
A simple example demonstrating non-blocking request / response
through a Redis server via RedisBridge.

A request client sends over an unsorted list,
and a response client sends back a sorted list.
"""
import socket
import time
from RedisBridge import RedisBridge



class RequestClient:
	"""
	A client that sends unsorted data on the 'sort' channel,
	and waits for a response.
	"""

	def __init__(self, bridge):
		self.bridge = bridge
		self.bridge.register(self, 'sort')
		self.requests = set()

	def send(self, data, is_request=True):
		msg_id = self.bridge.request(data, channel='sort', blocking=False)
		self.requests.add(msg_id)

	def receive_redis(self, msg):
		if msg.type == 'Response':
			if msg.request_id in self.requests:
				print(self.__class__.__name__, 'receiving a response ...')
				print(msg)
				print('Sorted Data:', msg.data, '\n')


class ResponseClient:
	"""
	A client that listens for requests on the 'sort' channel,
	and responds with a message containing the sorted data.
	"""

	def __init__(self, bridge):
		self.bridge = bridge
		self.bridge.register(self, 'sort')

	def receive_redis(self, msg):
		if msg.type == 'Request':
			print(self.__class__.__name__, 'receiving a request ...')
			print(msg)
			print('Unsorted Data:', msg.data, '\n')

			# Send back the same message data, but sorted
			data = sorted(msg.data)
			self.bridge.respond(data, channel='sort', request_id=msg.id)



if __name__ == '__main__':
	is_ripley = (socket.gethostname() == 'ripley')

	# Set up bridge and clients
	bridge = RedisBridge(dummy_redis_server=(not is_ripley))
	request_client = RequestClient(bridge)
	response_client = ResponseClient(bridge)
	bridge.start()

	# Make a request
	print('\n', '-' * 32, '\n')
	request_client.send([3, 2, 1])
	time.sleep(2)

	# Make another request
	print('\n', '-' * 32, '\n')
	request_client.send(['orange', 'apple', 'banana'])
	time.sleep(2)

	# Send a request, but NOT from our RequestClient
	# Our ResponseClient should still receive the request and respond
	# Our RequestClient should NOT receive any response
	print('\n', '-' * 32, '\n')
	bridge.request(['uno', 'dos', 'tres'], channel='sort')
	time.sleep(2)

	# Send a normal message on the 'sort' channel (i.e. neither request nor response)
	# Both our clients should do nothing
	print('\n', '-' * 32, '\n')
	bridge.send(['c', 'b', 'a'], channel='sort')
	time.sleep(2)

	# Exit
	bridge.stop()

