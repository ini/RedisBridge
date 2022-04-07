import random, time
from RedisBridge import RedisBridge
from RedisBridge.interfaces import CallbackInterface



GAME_RANGE = (1, 100)
GAME_OVER = False


class Oracle:
	
	def __init__(self, bridge):
		self.secret_number = random.randint(*GAME_RANGE)
		self.bridge = CallbackInterface(bridge)
		self.bridge.register_callback(
			self.judge_guess, channel='game', message_type='Request')


	def judge_guess(self, msg):
		guess = msg.data

		if self.secret_number > guess:
			answer = 'higher'
		elif self.secret_number < guess:
			answer = 'lower'
		else:
			answer = 'perfect'
		
		print(self.__class__.__name__, 'Answer:', answer)

		# Send feedback over bridge
		time.sleep(1)
		self.bridge.respond(
			data=answer, channel='game', request_id=msg.id)


class Guesser:

	def __init__(self, bridge):
		self.bridge = CallbackInterface(bridge)
		self.bridge.register_callback(
			self.get_feedback, channel='game', message_type='Response')

		self.min, self.max = GAME_RANGE
		self.guess, self.guess_id = None, None


	def make_guess(self):
		self.guess = random.randint(self.min, self.max) # (self.min + self.max) // 2
		print(self.__class__.__name__, 'Guess:', self.guess)

		# Send guess over bridge
		time.sleep(1)
		self.guess_id = self.bridge.request(
			data=self.guess, channel='game', blocking=False)


	def get_feedback(self, msg):
		if msg.request_id == self.guess_id:
			answer = msg.data

			if answer == 'higher':
				self.min = self.guess + 1
				self.make_guess()

			if answer == 'lower':
				self.max = self.guess - 1
				self.make_guess()

			if answer == 'perfect':
				global GAME_OVER
				GAME_OVER = True



if __name__ == '__main__':
	# Initialize the bridge and the players
	bridge = RedisBridge()
	p1 = Oracle(bridge)
	p2 = Guesser(bridge)

	# Start the bridge and make a 1st guess
	bridge.start()
	p2.make_guess()

	# Wait until game over, then stop the bridge
	while not GAME_OVER: pass
	bridge.stop()

