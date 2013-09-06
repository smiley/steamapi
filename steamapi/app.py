__author__ = 'SmileyBarry'

from .core import APIConnection
from .decorators import cached_property, INFINITE


class SteamApp(object):
    def __init__(self, appid, name=None):
        self._id = appid
        if name is not None:
            import time
            self._cache = dict()
            self._cache['name'] = (name, time.time())

    @property
    def appid(self):
        return self._id

    @cached_property(ttl=INFINITE)
    def name(self):
        response = APIConnection().call("ISteamUserStats", "GetSchemaForGame", "v2", appid=self._id)
        return response.game.gameName

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<SteamApp '{name}' ({id})>".format(name=self.name.encode(errors="ignore"), id=self.appid)