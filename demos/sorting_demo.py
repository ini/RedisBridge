"""
A simple example demonstrating request / response
through the internal bus via a RedisBridge.

A request client sends over an unsorted list,
and a response client sends back a sorted list.
"""
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
		msg_id = self.bridge.send(data, 'sort', is_request=True)
		self.requests.add(msg_id)

	def receive_redis(self, msg):
		if msg.type == 'response':
			if msg.request_id in self.requests:
				print(self.__class__, 'receiving a response ...', '\n', msg)
				print('Sorted Data:', msg.data, '\n')

				# Remove the request ID from our set of requests
				self.requests.remove(msg.request_id)


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
			self.bridge.send(data, 'sort', response_to=msg.id)



if __name__ == '__main__':
	# Set up bridge and clients
	bridge = RedisBridge()
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
	bridge.send(['uno', 'dos', 'tres'], 'sort', is_request=True)
	time.sleep(2)

	# Send a normal message on the 'sort' channel (i.e. neither request nor response)
	# Both our clients should do nothing
	print('\n', '-' * 32, '\n')
	bridge.send(['c', 'b', 'a'], 'sort', is_request=False)
	time.sleep(2)

	# Exit
	bridge.stop()

