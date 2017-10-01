
"""Authentication"""

import hashlib

from clicker import redis


class Auth(object):
    def __init__(self):
        self.rdb = redis.RedisDB()

    def authenticate(self, username, password):
        if not username or not password:
            return False
        hash_password = self.hash_password(password.encode())
        db_password = self.rdb.user_password(username)
        if db_password and db_password == hash_password:
            return True
        return False

    def hash_password(self, password):
        hasher = hashlib.sha256()
        hasher.update(password)
        return hasher.digest()

    def user_exists(self, username):
        return self.rdb.user_exists(username)

    def register(self, username, password, confirm):
        if not username or not password or not confirm:
            return 'Fields cannot be empty'
        if self.user_exists(username):
            return 'User already exists'

        if len(password) < 6:
            return 'Password must be at least 6 character long'

        hash_password = self.hash_password(password.encode())
        hash_confirm = self.hash_password(confirm.encode())
        if hash_password != hash_confirm:
            return 'Password does not match'

        self.rdb.user_add(username, hash_password)
        return 'Success'
