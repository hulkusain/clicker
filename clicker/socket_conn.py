"""User game state"""

from collections import OrderedDict
import json
import os
from random import Random
import time

import eventlet

from clicker import clicker
from clicker import redis
from clicker import lottery
from clicker import achievements

MAX_CYCLE_CLICKS = 20
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class BaseSock(type):
    _sids = {}
    _user_sids = {}
    _timeouts = {}
    _timed_out = []

    def __call__(cls, *args, **kwargs):
        """Generate SockConn if necessary"""
        sid = args[0]
        user = args[1]
        if not user:
            return None

        if sid not in cls._sids:
            cls._sids[sid] = super(BaseSock, cls).__call__(*args, **kwargs)
            cls._user_sids[user] = sid

        if user in cls._user_sids:
            if sid != cls._user_sids[user] or sid in cls._timed_out:
                return None

        for conn, timeout in cls._timeouts.copy().items():
            if int(time.time()) - timeout > 100:
                del cls._sids[conn]
                del cls._timeouts[conn]
                cls._timed_out.append(conn)

        if sid not in cls._sids:
            return None

        cls._timeouts[sid] = int(time.time())
        return cls._sids[sid]


class SockConn(object, metaclass=BaseSock):
    def __init__(self, sid, user):
        self._random = Random(time.time())
        self._user = user
        self._update_cycle = 0
        self._rdb = redis.RedisDB()
        self._clickers = {}
        self._config = self._load_config()
        self._cycle_clicks = 0
        self._lottery = self._load_lottery()
        self._achievements = None
        self._last_update = int(time.time())
        self._frenzy = False
        self._frenzy_start = int(time.time())
        self._frenzy_duration = 5
        self._frenzy_avail = True
        self._frenzy_cd_time = int(time.time())
        self._frenzy_cooldown = 60
        self._load()
        self._prev_score = 0

    def _get_score(self):
        return self._rdb.score_load(self._user)

    def _sync_score(self, score):
        """Sync score, but limit to 20 digits"""
        if len(str(score)) < 20:
            self._rdb.score_sync(self._user, score)
        else:
            self._rdb.score_sync(self._user, 9999999999999999999)

    def _load(self):
        """Load once on creation"""
        clickers = self._rdb.clickers_load(self._user)
        if not clickers:
            clickers = {'BaseClick': {'v_quantity': 1, 'm_quantity': 1}}
        for name, data in clickers.items():
            click = self._create_clicker(name, data['v_quantity'],
                                         data['m_quantity'])
            self._clickers[name] = click
        achieve_data = self._rdb.achievements_load(self._user)
        self._achievements = achievements.Achievements(
            self._config['achievements'], achieve_data.get('click'),
            achieve_data.get('lottery'),
            achieve_data.get('total'))
        lottery_streak = self._rdb.lottery_load(self._user)
        if lottery_streak:
            self._lottery.set_streak(lottery_streak)
        frenzy = self._rdb.frenzy_load(self._user)
        if 'avail' in frenzy:
            self._frenzy_avail = frenzy['avail']
        if 'cd_time' in frenzy:
            self._frenzy_cd_time = frenzy['cd_time']
        self._prev_score = self._get_score()

    def _load_config(self):
        with open(os.path.join(__location__, 'config/clickers.json')) as f:
            base_vals = json.load(f, object_pairs_hook=OrderedDict)
            return base_vals

    def _load_lottery(self):
        prize = self._config['lottery']['prize']
        limit = self._config['lottery']['limit']
        return lottery.Lottery(self._random, limit, prize)

    def click(self, clicker):
        """Process click. Check frenzy and check achievement"""
        if clicker not in self._clickers:
            return
        score = self._get_score()
        self._cycle_clicks += 1
        if self._cycle_clicks < MAX_CYCLE_CLICKS:
            click_val = self._clickers[clicker].click()
            self._frenzy_check()
            if self._frenzy:
                click_val *= 2
            self.achieve_click(click_val)
            score += click_val
        self._sync_score(score)

    def _update(self, cycles):
        """Update to redis db"""
        self._cycle_clicks = 0
        self._rdb.clickers_sync(self._user, self._clickers)
        self._rdb.achievements_sync(self._user, self._achievements)
        self._rdb.lottery_sync(self._user, self._lottery.get_streak())
        self._rdb.frenzy_sync(self._user, self._frenzy_avail,
                              self._frenzy_cd_time)

        score = self._get_score()
        total = 0
        for name, click in self._clickers.items():
            if name == 'BaseClick':
                continue
            for _ in range(cycles):
                total += click.passive_click()
        score += total
        self._sync_score(score)

    def get_update(self):
        """Format update for socket"""
        cycles = int(time.time()) - self._last_update
        self._last_update = int(time.time())
        self._frenzy_check()
        self._update(cycles)

        result = {}
        result['upgrades'] = self._get_upgrades()
        result['unlockables'] = self._get_unlockables()
        result['clickers'] = self._update_clickers()
        result['score'] = self._get_score()
        result['limit'] = self._lottery.get_limit()
        result['frenzy'] = self._frenzy
        result['frenzy_avail'] = self._frenzy_avail

        new_score = self._get_score()
        if cycles > 0:
            self.achieve_total((new_score - self._prev_score) // cycles)
        self._prev_score = new_score
        return result

    def _update_clickers(self):
        """Format clickers for socket"""
        clickers = {}
        for name, click in self._clickers.items():
            clickers[name] = {'value': click.get_value(),
                              'mult': click.get_mult()}
        return clickers

    def _create_clicker(self, name, v_quantity=1, m_quantity=1):
        """Create clicker based on name"""
        if hasattr(clicker, name):
            class_ = getattr(clicker, name)
            if name == 'RandomClick':
                click = class_(self._config['clickers'][name], v_quantity,
                               m_quantity, self._random)
            else:
                click = class_(self._config['clickers'][name], v_quantity,
                               m_quantity)
            return click

    def _unlock_clicker(self, name):
        """Unlock a clicker if price is suitable"""
        click = self._create_clicker(name)
        price = click.get_price()
        score = self._get_score()
        if score >= price:
            score -= price
            self._clickers[name] = click
        self._sync_score(score)

    def _get_upgrades(self):
        """Get available upgrades"""
        upgrades = OrderedDict({})
        for name, click in self._clickers.items():
            upgrades[name] = click.get_upgrades()
        return upgrades

    def upgrade(self, data):
        """Upgrade based on clicker name and upgrade type"""
        if 'name' not in data or 'type' not in data:
            return
        if data['name'] in self._clickers:
            click = self._clickers[data['name']]
        else:
            self._unlock_clicker(data['name'])
            return

        upgrade_cost = click.get_upgrade_cost(data['name'], data['type'])
        score = self._get_score()
        if upgrade_cost and score >= upgrade_cost:
            score -= upgrade_cost
            click.upgrade(data['type'])
            self._sync_score(score)

    def _get_unlockables(self):
        """Get all available unlockables"""
        unlockables = OrderedDict({})
        for name, config in self._config['clickers'].items():
            if name in self._clickers:
                continue
            value = config['value']
            price = config['price']
            unlockables[name] = {'value': value,
                                 'price': price}
        return unlockables

    def lottery(self, guess):
        """Process lottery guess"""
        try:
            guess = int(guess)
        except ValueError:
            return None
        prize = self._lottery.win(guess)
        self.achieve_lottery(self._lottery.get_streak())
        score = self._get_score()
        score += prize
        self._sync_score(score)
        self._prev_score = self._get_score()
        return prize

    def frenzy(self):
        """Activate frenzy"""
        if self._frenzy_avail:
            self._frenzy = True
            self._frenzy_start = int(time.time())
            self._frenzy_avail = False

    def _frenzy_check(self):
        """Check if frenzy is over and if frenzy is available"""
        if self._frenzy:
            cycles = int(time.time()) - self._frenzy_start
            if cycles > self._frenzy_duration:
                self._frenzy = False
                self._frenzy_cd_time = int(time.time())
        if not self._frenzy_avail:
            cycles = int(time.time()) - self._frenzy_cd_time
            if cycles > self._frenzy_cooldown:
                self._frenzy_avail = True

    def achievements(self):
        """Return achievements"""
        return self._achievements.get_all()

    def achieve_click(self, value):
        """Check if click achievement has been achieved"""
        self._achievements.check_click(value)

    def achieve_lottery(self, value):
        """Check if lottery achievement has been achieved"""
        self._achievements.check_lottery(value)

    def achieve_total(self, value):
        """Check if total achievement has been achieved"""
        self._achievements.check_total(value)
