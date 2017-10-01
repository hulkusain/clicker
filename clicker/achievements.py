"""Achievements"""

import os

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class Achievements(object):
    def __init__(self, config, click=None, lottery=None, total=None):
        self._config = config

        if click is None:
            self._click = config['click'][0]
        else:
            self._click = click
        if lottery is None:
            self._lottery = config['lottery'][0]
        else:
            self._lottery = lottery
        if total is None:
            self._total = config['total'][0]
        else:
            self._total = total

    def get_all(self):
        if self._click != 0:
            click_val = 'Earn ' + str(self._click) + ' in a single click'
        else:
            click_val = self._click_flag()
        if self._lottery != 0:
            lottery_val = ('Win the lottery ' + str(self._lottery) +
                           ' times in a row')
        else:
            lottery_val = self._lottery_flag()
        if self._total != 0:
            total_val = 'Earn ' + str(self._total) + ' passive points in 1 second'
        else:
            total_val = self._total_flag()
        return {'click': click_val,
                'lottery': lottery_val,
                'total': total_val}

    def get_click(self):
        return self._click

    def get_lottery(self):
        return self._lottery

    def get_total(self):
        return self._total

    def check_click(self, value):
        if self._click != 0 and value >= self._click:
            self._upgrade_click()

    def check_lottery(self, value):
        if self._lottery != 0 and value >= self._lottery:
            self._upgrade_lottery()

    def check_total(self, value):
        if self._total != 0 and value >= self._total:
            self._upgrade_total()

    def _upgrade_click(self):
        for click in self._config['click']:
            if click > self._click:
                self._click = click
                return
        self._click = 0

    def _upgrade_lottery(self):
        for lottery in self._config['lottery']:
            if lottery > self._lottery:
                self._lottery = lottery
                return
        self._lottery = 0

    def _upgrade_total(self):
        for total in self._config['total']:
            if total > self._total:
                self._total = total
                return
        self._total = 0

    def _read_flag(self, index):
        flag_file = 'flag{}.txt'.format(index)
        file_path = os.path.join(__location__, '..', flag_file)
        with open(file_path) as f:
            return f.read()

    def _click_flag(self):
        return self._read_flag(0)

    def _lottery_flag(self):
        return self._read_flag(1)

    def _total_flag(self):
        return self._read_flag(2)
