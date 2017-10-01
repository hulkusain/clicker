"""Lottery"""


class Lottery(object):
    def __init__(self, random, limit, prize, streak=0):
        self._limit = limit
        self._prize = prize
        self._current = 0
        self._streak = 0
        self._random = random

    def generate(self):
        """Generate random number"""
        self._current = self._random.randint(0, self._limit)

    def win(self, input):
        """Check if guess is correct"""
        self.generate()
        if (self._current == input):
            self._streak += 1
        else:
            self._streak = 0
            return 0
        return self._prize * (2 ** self._streak)

    def get_limit(self):
        return self._limit

    def get_streak(self):
        return self._streak

    def set_streak(self, streak):
        self._streak = streak
