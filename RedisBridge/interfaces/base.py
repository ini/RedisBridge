from abc import ABC, abstractmethod
from ..utils import Loggable



class RedisInterface(ABC, Loggable):
	"""
	Abstract base class for a wrapper around a RedisBridge that
	provides and specifies its own interface via which clients
	can interact with the bridge.
	"""

	@abstractmethod
	def	__init__(self, bridge):
		pass

