from .base import RedisInterface
from .callback import CallbackInterface


class CallbackDecorator(CallbackInterface):

	def __init__(self, *args, **kwargs):
		self.logger.warning(
			DeprecationWarning("'CallbackDecorator' is being deprecated. Use 'CallbackInterface' instead."),
			stack_info=True,
		)
		super().__init__(*args, **kwargs)
