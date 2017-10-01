"""Redis DB connection"""

import redis


class RedisDB(object):
    def __init__(self):
        self.rdb = redis.StrictRedis(host='localhost', port=6379, db=0)

    def user_exists(self, user):
        return self.rdb.exists('user:' + user)

    def user_password(self, user):
        if not self.user_exists(user):
            return None
        return self.rdb.get('user:' + user)

    def user_add(self, user, hash):
        self.rdb.set('user:' + user, hash)

    def score_sync(self, user, score):
        self.rdb.set('score:' + user, score)

    def score_load(self, user):
        if self.rdb.exists('score:' + user):
            return int(float(self.rdb.get('score:' + user).decode()))
        return 0

    def _clicker_sync(self, user, name, clicker):
        base_query = 'clicker:' + user + ':' + name + ':'
        self.rdb.set(base_query + 'v_quantity', clicker.get_value_quantity())
        self.rdb.set(base_query + 'm_quantity', clicker.get_mult_quantity())

    def _clicker_load(self, user, name):
        clicker = {}
        base_query = 'clicker:' + user + ':' + name + ':'
        clicker['v_quantity'] = int(float(self.rdb.get(
            base_query + 'v_quantity')))
        clicker['m_quantity'] = int(float(self.rdb.get(
            base_query + 'm_quantity')))
        return clicker

    def clickers_sync(self, user, clickers):
        names = ''
        for name, click in clickers.items():
            names += name + ':'
            self._clicker_sync(user, name, click)
        names = names[:-1]
        self.rdb.set('clicker:' + user, names)

    def clickers_load(self, user):
        clickers = {}
        result = self.rdb.get('clicker:' + user)
        if (not result):
            return None
        result = result.decode()
        names = result.split(':')
        for name in names:
            clickers[name] = self._clicker_load(user, name)
        return clickers

    def lottery_sync(self, user, streak):
        base_query = 'lottery:' + user + ':'
        self.rdb.set(base_query + 'streak', streak)

    def lottery_load(self, user):
        base_query = 'lottery:' + user + ':'
        if self.rdb.exists(base_query + 'streak'):
            return int(float(self.rdb.get(base_query + 'streak')))
        return None

    def achievements_sync(self, user, achievements):
        base_query = 'achievements:' + user + ':'
        self.rdb.set(base_query + 'click', achievements.get_click())
        self.rdb.set(base_query + 'lottery', achievements.get_lottery())
        self.rdb.set(base_query + 'total', achievements.get_total())

    def achievements_load(self, user):
        achievements = {}
        base_query = 'achievements:' + user + ':'
        if not self.rdb.exists(base_query + 'click'):
            return achievements
        achievements['click'] = int(float(self.rdb.get(
            base_query + 'click')))
        achievements['lottery'] = int(float(self.rdb.get(
            base_query + 'lottery')))
        achievements['total'] = int(float(self.rdb.get(
            base_query + 'total')))
        return achievements

    def frenzy_sync(self, user, available, cd_time):
        base_query = 'frenzy:' + user + ':'
        if available:
            self.rdb.set(base_query + 'available', 1)
        else:
            self.rdb.set(base_query + 'available', 0)
        self.rdb.set(base_query + 'cd_time', cd_time)

    def frenzy_load(self, user):
        frenzy = {}
        base_query = 'frenzy:' + user + ':'
        if not self.rdb.exists(base_query + 'available'):
            return frenzy
        available = int(float(self.rdb.get(base_query + 'available')))
        if available == 1:
            frenzy['avail'] = True
        else:
            frenzy['avail'] = False
        frenzy['cd_time'] = int(float(self.rdb.get(base_query + 'cd_time')))
        return frenzy
