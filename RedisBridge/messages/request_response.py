from .base import Message



class Request(Message):
    """
    A request message that expects some response.
    """

    def __init__(self, channel, data):
        super().__init__(channel, data, type='request')



class Response(Message):
    """
    A response message that stores the ID of its corresponding request.
    """

    def __init__(self, channel, data, request_id):
        super().__init__(channel, data, type='response')
        self._request_id = request_id


    @property
    def request_id(self):
        """
        Returns the ID of the message being responded to.
        """
        return self._request_id

