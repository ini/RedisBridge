import logging
import random
import socket
import string



def check_server(host, port):
    """
    Try to connect to the given host at the given port and return TCP error code.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return s.connect_ex((host, port))


def uid(length=8):
    """
    Returns a unique string identifier.
    """
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(random.choices(alphabet, k=length))



class Loggable:
    """
    Base class for objects that need to grab a logger.
    """
    @property
    def logger(self):
        """
        Grab a handle to logger for the class, if it exists,
        otherwise use the default logger.
        """
        if self.__class__.__name__ in logging.Logger.manager.loggerDict:
            return logging.getLogger(self.__class__.__name__)
        else:
            return logging.getLogger(__name__)
