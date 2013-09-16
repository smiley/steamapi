__author__ = 'SmileyBarry'

from .core import APIConnection, SteamObject

from .app import SteamApp
from .consts import OnlineState, CommunityVisibilityState
from .decorators import cached_property, INFINITE, MINUTE, HOUR

import datetime


class SteamUserBadge(SteamObject):
    def __init__(self, badge_id, level, completion_time, xp, scarcity, appid=None):
        self._id = badge_id
        self._level = level
        self._completion_time = completion_time
        self._xp = xp
        self._scarcity = scarcity
        self._appid = appid

    @property
    def badge_id(self):
        return self._id

    @property
    def level(self):
        return self._level

    @property
    def xp(self):
        return self._xp

    @property
    def scarcity(self):
        return self._scarcity

    @property
    def appid(self):
        return self._appid

    @property
    def completion_time(self):
        return datetime.datetime.fromtimestamp(self._completion_time)


class SteamGroup(SteamObject):
    def __init__(self, guid):
        self._id = guid

    @property
    def guid(self):
        return self._id


class SteamUser(SteamObject):
    # OVERRIDES
    def __init__(self, userid=None, userurl=None):
        """
        Create a new instance of a Steam user. Use this object to retrieve details about
        that user.

        :param userid: The user's 64-bit SteamID. (Optional, unless steam_userurl isn't specified)
        :param userurl: The user's vanity URL-ending name. (Required if "steam_userid" isn't specified,
        unused otherwise)
        :raise: ValueError on improper usage.
        """
        if userid is None and userurl is None:
            raise ValueError("One of the arguments must be supplied.")

        if userurl is not None:
            response = APIConnection().call("ISteamUser", "ResolveVanityURL", "v0001", vanityurl=userurl)
            userid = response.steamid

        if userid is not None:
            self._id = userid

    def __eq__(self, other):
        if type(other) is SteamUser:
            if self.steamid == other.steamid:
                return True
            else:
                return False
        else:
            return super(SteamUser, self).__eq__(other)

    def __str__(self):
        return self.name

    # PRIVATE UTILITIES
    @cached_property(ttl=2 * HOUR)
    def _summary(self):
        return APIConnection().call("ISteamUser", "GetPlayerSummaries", "v0002", steamids=self.steamid).players[0]

    @cached_property(ttl=INFINITE)
    def _bans(self):
        return APIConnection().call("ISteamUser", "GetPlayerBans", "v1", steamids=self.steamid).players[0]

    @cached_property(ttl=30 * MINUTE)
    def _badges(self):
        return APIConnection().call("IPlayerService", "GetBadges", "v1", steamid=self.steamid)

    # PUBLIC ATTRIBUTES
    @property
    def steamid(self):
        return self._id

    @cached_property(ttl=INFINITE)
    def name(self):
        return self._summary.personaname

    @cached_property(ttl=INFINITE)
    def real_name(self):
        return self._summary.realname

    @cached_property(ttl=INFINITE)
    def country_code(self):
        return self._summary.loccountrycode

    @cached_property(ttl=10 * MINUTE)
    def currently_playing(self):
        if "gameid" in self._summary:
            return SteamApp(self._summary.gameid, self._summary.gameextrainfo)
        else:
            return None

    @property  # Already cached by "_summary".
    def privacy(self):
        # The Web API is a public-facing interface, so it's very unlikely that it will
        # ever change drastically. (More values could be added, but existing ones wouldn't
        # be changed.)
        return self._summary.communityvisibilitystate

    @property  # Already cached by "_summary".
    def last_logoff(self):
        return datetime.datetime.fromtimestamp(self._summary.lastlogoff)

    @cached_property(ttl=INFINITE)  # Already cached, but never changes.
    def time_created(self):
        return datetime.datetime.fromtimestamp(self._summary.timecreated)

    @cached_property(ttl=INFINITE)  # Already cached, but unlikely to change.
    def profile_url(self):
        return self._summary.profileurl

    @property  # Already cached by "_summary".
    def avatar(self):
        return self._summary.avatar

    @property  # Already cached by "_summary".
    def avatar_medium(self):
        return self._summary.avatarmedium

    @property  # Already cached by "_summary".
    def avatar_full(self):
        return self._summary.avatarfull

    @property  # Already cached by "_summary".
    def state(self):
        return self._summary.personastate

    @cached_property(ttl=1 * HOUR)
    def groups(self):
        response = APIConnection().call("ISteamUser", "GetUserGroupList", "v1", steamid=self.steamid)
        group_list = []
        for group in response.groups:
            group_obj = SteamGroup(group.gid)
            group_list += [group_obj]
        return group_list

    @cached_property(ttl=1 * HOUR)
    def group(self):
        return SteamGroup(self._summary.primaryclanid)

    @cached_property(ttl=1 * HOUR)
    def friends(self):
        response = APIConnection().call("ISteamUser", "GetFriendList", "v0001", steamid=self.steamid,
                                        relationship="friend")
        friends_list = []
        for friend in response.friendslist.friends:
            friend_obj = SteamUser(friend.steamid)
            friend_obj.friend_since = friend.friend_since
            friend_obj._cache = {}
            friends_list += [friend_obj]

        # Fetching some details, like name, could take some time.
        # So, do a few combined queries for all users.
        if APIConnection().precache is True:
            id_player_map = {friend.steamid: friend for friend in friends_list}
            ids = id_player_map.keys()
            CHUNK_SIZE = 35

            chunks = [ids[start:start+CHUNK_SIZE] for start in range(len(ids))[::CHUNK_SIZE]]
            # We have to encode "steamids" into one, comma-delimited list because requests
            # just transforms it into a thousand parameters.
            for chunk in chunks:
                player_details = APIConnection().call("ISteamUser",
                                                      "GetPlayerSummaries",
                                                      "v0002",
                                                      steamids=chunk).players

                import time
                now = time.time()
                for player_summary in player_details:
                    # Fill in the cache with this info.
                    id_player_map[player_summary.steamid]._cache["_summary"] = (player_summary, now)
        return friends_list

    @property  # Already cached by "_badges".
    def level(self):
        return self._badges.player_level

    @property  # Already cached by "_badges".
    def badges(self):
        badge_list = []
        for badge in self._badges.badges:
            badge_list += [SteamUserBadge(badge.badgeid,
                                          badge.level,
                                          badge.completion_time,
                                          badge.xp,
                                          badge.scarcity,
                                          badge.appid)]
        return badge_list

    @property  # Already cached by "_badges".
    def xp(self):
        return self._badges.player_xp

    @cached_property(ttl=INFINITE)
    def recently_played(self):
        response = APIConnection().call("IPlayerService", "GetRecentlyPlayedGames", "v1", steamid=self.steamid)
        games_list = []
        for game in response.games:
            game_obj = SteamApp(game.appid, game.name)
            game_obj.playtime_2weeks = game.playtime_2weeks
            game_obj.playtime_forever = game.playtime_forever
            games_list += [game_obj]
        return games_list

    @cached_property(ttl=INFINITE)
    def games(self):
        response = APIConnection().call("IPlayerService",
                                        "GetOwnedGames",
                                        "v1",
                                        steamid=self.steamid,
                                        include_appinfo=1)
        games_list = []
        for game in response.games:
            game_obj = SteamApp(game.appid, game.name)
            if 'playtime_2weeks' in game:
                game_obj.playtime_2weeks = game.playtime_2weeks
            game_obj.playtime_forever = game.playtime_forever
            games_list += [game_obj]
        return games_list

    @cached_property(ttl=INFINITE)
    def is_vac_banned(self):
        return self._bans.VACBanned

    @cached_property(ttl=INFINITE)
    def is_community_banned(self):
        return self._bans.CommunityBanned