import logging



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
