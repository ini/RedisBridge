from ..utils import Loggable



class RedisInterface(Loggable):
    """
    Base class for wrappers around a RedisBridge that
    provide and specify their own interfaces via which clients
    can interact with the bridge.
    """

    def __init__(self, bridge):
        """
        Arguments:
            - bridge: a RedisBridge or RedisInterface instance
        """
        self._bridge = bridge._unwrapped


    def __str__(self):
        """
        Provide a string representation of the object.
        """
        bridge_str = str(self._bridge).strip('[]')
        return f'[{self.__class__.__name__} @ {bridge_str}]'


    @property
    def _unwrapped(self):
        """
        Internal property that returns the underlying bridge.
        """
        return self._bridge
