import time
from RedisBridge import RedisBridge


def square(msg):
	print(msg.data ** 2)


def cube(msg):
	print(msg.data ** 3)


if __name__ == '__main__':
	# Create the bridge and register callbacks
	bridge = RedisBridge()
	bridge.register_callback(square, 'square')
	bridge.register_callback(cube, 'cube')

	# Test out the bridge by sending a few messages
	bridge.start()
	bridge.send(3, channel='square')
	bridge.send(2, channel='cube')

	# Stop the bridge
	time.sleep(.1)
	bridge.stop()
