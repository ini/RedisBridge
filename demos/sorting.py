"""
A simple example demonstrating request / response
through the internal bus via a RedisBridge.

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

	def send(self, data, is_request=True):
		response = self.bridge.request(data, channel='sort')
		print(self.__class__, 'received a response ...', '\n', response)
		print('Sorted Data:', response.data, '\n')


class ResponseClient:
	"""
	A client that listens for requests on the 'sort' channel,
	and responds with a message containing the sorted data.
	"""

	def __init__(self, bridge):
		self.bridge = bridge
		self.bridge.register(self, 'sort')

	def receive_redis(self, msg):
		if msg.type == 'request':
			print(self.__class__, 'receiving a request ...', '\n', msg)
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
