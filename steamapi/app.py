__author__ = 'SmileyBarry'

from .core import APIConnection, SteamObject, store
from .decorators import cached_property, INFINITE


class SteamApp(SteamObject):
    def __init__(self, appid, name=None, owner=None):
        self._id = appid
        if name is not None:
            import time
            self._cache = dict()
            self._cache['name'] = (name, time.time())
        # Normally, the associated userid is also the owner.
        # That would not be the case if the game is borrowed, though. In that case, the object creator
        # usually defines attributes accordingly. However, at this time we can't ask the API "is this
        # game borrowed?", unless it's the actively-played game, so this distinction isn't done in the
        # object's context, but in the object creator's context.
        self._owner = owner
        self._userid = self._owner

    @cached_property(ttl=INFINITE)
    def _schema(self):
        return APIConnection().call("ISteamUserStats", "GetSchemaForGame", "v2", appid=self._id)

    @property
    def appid(self):
        return self._id

    @cached_property(ttl=INFINITE)
    def achievements(self):
        global_percentages = APIConnection().call("ISteamUserStats", "GetGlobalAchievementPercentagesForApp", "v0002",
                                                  gameid=self._id)
        if self._userid is not None:
            # Ah-ha, this game is associated to a user!
            userid = self._userid
            unlocks = APIConnection().call("ISteamUserStats",
                                           "GetUserStatsForGame",
                                           "v2",
                                           appid=self._id,
                                           steamid=userid)
            if 'achievements' in unlocks.playerstats:
                unlocks = [associated_achievement.name
                           for associated_achievement in unlocks.playerstats.achievements
                           if associated_achievement.achieved != 0]
        else:
            userid = None
            unlocks = None
        achievements_list = []
        for achievement in self._schema.game.availableGameStats.achievements:
            achievement_obj = SteamAchievement(self._id, achievement.name, achievement.displayName, userid)
            achievement_obj._cache = {}
            if achievement.hidden == 0:
                store(achievement_obj, "is_hidden", False)
            else:
                store(achievement_obj, "is_hidden", True)
            for global_achievement in global_percentages.achievementpercentages.achievements:
                if global_achievement.name == achievement.name:
                    achievement_obj.unlock_percentage = global_achievement.percent
            achievements_list += [achievement_obj]
        if unlocks is not None:
            for achievement in achievements_list:
                if achievement.apiname in unlocks:
                    store(achievement, "is_achieved", True)
                else:
                    store(achievement, "is_achieved", False)
        return achievements_list

    @cached_property(ttl=INFINITE)
    def name(self):
        return self._schema.game.gameName

    @cached_property(ttl=INFINITE)
    def owner(self):
        if self._owner is None:
            return self._userid
        else:
            return self._owner

    def __str__(self):
        return self.name

    def __hash__(self):
        # Don't just use the ID so ID collision between different types of objects wouldn't cause a match.
        return hash(('app', self.id))


class SteamAchievement(SteamObject):
    def __init__(self, linked_appid, apiname, displayname, linked_userid=None):
        """
        Initialise a new instance of SteamAchievement. You shouldn't create one yourself, but from
        "SteamApp.achievements" instead.

        :param linked_appid: The AppID associated with this achievement.
        :type linked_appid: int
        :param apiname: The API-based name of this achievement. Usually a string.
        :type apiname: str or unicode
        :param displayname: The achievement's user-facing name.
        :type displayname: str or unicode
        :param linked_userid: The user ID this achievement is linked to.
        :type linked_userid: int
        :return: A new SteamAchievement instance.
        """
        self._appid = linked_appid
        self._id = apiname
        self._displayname = displayname
        self._userid = linked_userid
        self.unlock_percentage = 0.0

    def __hash__(self):
        # Don't just use the ID so ID collision between different types of objects wouldn't cause a match.
        return hash((self.id, self._appid))

    @property
    def appid(self):
        return self._appid

    @property
    def name(self):
        return self._displayname

    @property
    def apiname(self):
        return self._id

    @cached_property(ttl=INFINITE)
    def is_hidden(self):
        response = APIConnection().call("ISteamUserStats",
                                        "GetSchemaForGame",
                                        "v2",
                                        appid=self._appid)
        for achievement in response.game.availableGameStats.achievements:
            if achievement.name == self._id:
                if achievement.hidden == 0:
                    return False
                else:
                    return True

    @cached_property(ttl=INFINITE)
    def is_unlocked(self):
        if self._userid is None:
            raise ValueError("No Steam ID linked to this achievement!")
        response = APIConnection().call("ISteamUserStats",
                                        "GetPlayerAchievements",
                                        "v1",
                                        steamid=self._userid,
                                        appid=self._appid,
                                        l="English")
        for achievement in response.playerstats.achievements:
            if achievement.apiname == self._id:
                if achievement.achieved == 1:
                    return True
                else:
                    return False
        # Cannot be found.
        return False