__author__ = 'SmileyBarry'

from .core import APIConnection, SteamObject

from .app import SteamApp
from .decorators import cached_property, INFINITE, MINUTE, HOUR
from .errors import *

import datetime


class SteamUserBadge(SteamObject):
    def __init__(self, badge_id, level, completion_time, xp, scarcity, appid=None):
        """
        Create a new instance of a Steam user badge. You usually shouldn't initialise this object,
        but instead receive it from properties like "SteamUser.badges".

        :param badge_id: The badge's ID. Not a unique instance ID, but one that helps to identify it
        out of a list of user badges. Appears as `badgeid` in the API specification.
        :type badge_id: int
        :param level: The badge's current level.
        :type level: int
        :param completion_time: The exact moment when this badge was unlocked. Can either be a
        datetime.datetime object or a Unix timestamp.
        :type completion_time: int or datetime.datetime
        :param xp: This badge's current experience value.
        :type xp: int
        :param scarcity: How rare this badge is. Expressed as a count of how many people have it.
        :type scarcity: int
        :param appid: This badge's associated app ID.
        :type appid: int
        """
        self._badge_id = badge_id
        self._level = level
        if type(completion_time) is datetime.datetime:
            self._completion_time = completion_time
        else:
            self._completion_time = datetime.datetime.fromtimestamp(completion_time)
        self._xp = xp
        self._scarcity = scarcity
        self._appid = appid
        if self._appid is not None:
            self._id = self._appid
        else:
            self._id = self._badge_id

    @property
    def badge_id(self):
        return self._badge_id

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
        return self._completion_time

    def __repr__(self):
        return '<{clsname} {id} ({xp} XP)>'.format(clsname=self.__class__.__name__,
                                                   id=self._id,
                                                   xp=self._xp)

    def __hash__(self):
        # Don't just use the ID so ID collision between different types of objects wouldn't cause a match.
        return hash((self._appid, self.id))


class SteamGroup(SteamObject):
    def __init__(self, guid):
        self._id = guid

    def __hash__(self):
        # Don't just use the ID so ID collision between different types of objects wouldn't cause a match.
        return hash(('group', self.id))

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
        :type userid: int
        :param userurl: The user's vanity URL-ending name. (Required if "steam_userid" isn't specified,
        unused otherwise)
        :type userurl: str
        :raise: ValueError on improper usage.
        """
        if userid is None and userurl is None:
            raise ValueError("One of the arguments must be supplied.")

        if userurl is not None:
            if '/' in userurl:
                # This is a full URL. It's not valid.
                raise ValueError("\"userurl\" must be the *ending* of a vanity URL, not the entire URL!")
            response = APIConnection().call("ISteamUser", "ResolveVanityURL", "v0001", vanityurl=userurl)
            if response.success != 1:
                raise UserNotFoundError("User not found.")
            userid = response.steamid

        if userid is not None:
            self._id = int(userid)

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

    def __hash__(self):
        # Don't just use the ID so ID collision between different types of objects wouldn't cause a match.
        return hash(('user', self.id))

    # PRIVATE UTILITIES
    @staticmethod
    def _convert_games_list(raw_list, associated_userid=None):
        """
        Convert a raw, APIResponse-formatted list of games into full SteamApp objects.
        :type raw_list: list of APIResponse
        :rtype: list of SteamApp
        """
        games_list = []
        for game in raw_list:
            game_obj = SteamApp(game.appid, game.name, associated_userid)
            if 'playtime_2weeks' in game:
                game_obj.playtime_2weeks = game.playtime_2weeks
            if 'playtime_forever' in game:
                game_obj.playtime_forever = game.playtime_forever
            games_list += [game_obj]
        return games_list

    @cached_property(ttl=2 * HOUR)
    def _summary(self):
        """
        :rtype: APIResponse
        """
        return APIConnection().call("ISteamUser", "GetPlayerSummaries", "v0002", steamids=self.steamid).players[0]

    @cached_property(ttl=INFINITE)
    def _bans(self):
        """
        :rtype: APIResponse
        """
        return APIConnection().call("ISteamUser", "GetPlayerBans", "v1", steamids=self.steamid).players[0]

    @cached_property(ttl=30 * MINUTE)
    def _badges(self):
        """
        :rtype: APIResponse
        """
        return APIConnection().call("IPlayerService", "GetBadges", "v1", steamid=self.steamid)

    # PUBLIC ATTRIBUTES
    @property
    def steamid(self):
        """
        :rtype: int
        """
        return self._id

    @cached_property(ttl=INFINITE)
    def name(self):
        """
        :rtype: str
        """
        return self._summary.personaname

    @cached_property(ttl=INFINITE)
    def real_name(self):
        """
        :rtype: str
        """
        return self._summary.realname

    @cached_property(ttl=INFINITE)
    def country_code(self):
        """
        :rtype: str
        """
        return self._summary.loccountrycode

    @cached_property(ttl=10 * MINUTE)
    def currently_playing(self):
        """
        :rtype: SteamApp
        """
        if "gameid" in self._summary:
            game = SteamApp(self._summary.gameid, self._summary.gameextrainfo)
            owner = APIConnection().call("IPlayerService", "IsPlayingSharedGame", "v0001",
                                         steamid=self._id,
                                         appid_playing=game.appid)
            if owner.lender_steamid is not 0:
                game._owner = owner.lender_steamid
            return game
        else:
            return None

    @property  # Already cached by "_summary".
    def privacy(self):
        """
        :rtype: int or CommunityVisibilityState
        """
        # The Web API is a public-facing interface, so it's very unlikely that it will
        # ever change drastically. (More values could be added, but existing ones wouldn't
        # be changed.)
        return self._summary.communityvisibilitystate

    @property  # Already cached by "_summary".
    def last_logoff(self):
        """
        :rtype: datetime
        """
        return datetime.datetime.fromtimestamp(self._summary.lastlogoff)

    @cached_property(ttl=INFINITE)  # Already cached, but never changes.
    def time_created(self):
        """
        :rtype: datetime
        """
        return datetime.datetime.fromtimestamp(self._summary.timecreated)

    @cached_property(ttl=INFINITE)  # Already cached, but unlikely to change.
    def profile_url(self):
        """
        :rtype: str
        """
        return self._summary.profileurl

    @property  # Already cached by "_summary".
    def avatar(self):
        """
        :rtype: str
        """
        return self._summary.avatar

    @property  # Already cached by "_summary".
    def avatar_medium(self):
        """
        :rtype: str
        """
        return self._summary.avatarmedium

    @property  # Already cached by "_summary".
    def avatar_full(self):
        """
        :rtype: str
        """
        return self._summary.avatarfull

    @property  # Already cached by "_summary".
    def state(self):
        """
        :rtype: int or OnlineState
        """
        return self._summary.personastate

    @cached_property(ttl=1 * HOUR)
    def groups(self):
        """
        :rtype: list of SteamGroup
        """
        response = APIConnection().call("ISteamUser", "GetUserGroupList", "v1", steamid=self.steamid)
        group_list = []
        for group in response.groups:
            group_obj = SteamGroup(group.gid)
            group_list += [group_obj]
        return group_list

    @cached_property(ttl=1 * HOUR)
    def group(self):
        """
        :rtype: SteamGroup
        """
        return SteamGroup(self._summary.primaryclanid)

    @cached_property(ttl=1 * HOUR)
    def friends(self):
        """
        :rtype: list of SteamUser
        """
        import time
        
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
            # APIConnection() accepts lists of strings as argument values.
            id_player_map = {str(friend.steamid): friend for friend in friends_list}
            ids = list(id_player_map.keys())

            player_details = APIConnection().call("ISteamUser",
                                                  "GetPlayerSummaries",
                                                  "v0002",
                                                  steamids=ids).players

            now = time.time()
            for player_summary in player_details:
                # Fill in the cache with this info.
                id_player_map[player_summary.steamid]._cache["_summary"] = (player_summary, now)
        return friends_list

    @property  # Already cached by "_badges".
    def level(self):
        """
        :rtype: int
        """
        return self._badges.player_level

    @property  # Already cached by "_badges".
    def badges(self):
        """
        :rtype: list of SteamUserBadge
        """
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
        """
        :rtype: int
        """
        return self._badges.player_xp

    @cached_property(ttl=INFINITE)
    def recently_played(self):
        """
        :rtype: list of SteamApp
        """
        response = APIConnection().call("IPlayerService", "GetRecentlyPlayedGames", "v1", steamid=self.steamid)
        if response.total_count == 0:
            return []
        return self._convert_games_list(response.games, self._id)

    @cached_property(ttl=INFINITE)
    def games(self):
        """
        :rtype: list of SteamApp
        """
        response = APIConnection().call("IPlayerService",
                                        "GetOwnedGames",
                                        "v1",
                                        steamid=self.steamid,
                                        include_appinfo=True,
                                        include_played_free_games=True)
        if response.game_count == 0:
            return []
        return self._convert_games_list(response.games, self._id)

    @cached_property(ttl=INFINITE)
    def owned_games(self):
        """
        :rtype: list of SteamApp
        """
        response = APIConnection().call("IPlayerService",
                                        "GetOwnedGames",
                                        "v1",
                                        steamid=self.steamid,
                                        include_appinfo=True,
                                        include_played_free_games=False)
        if response.game_count == 0:
            return []
        return self._convert_games_list(response.games, self._id)

    @cached_property(ttl=INFINITE)
    def is_vac_banned(self):
        """
        :rtype: bool
        """
        return self._bans.VACBanned

    @cached_property(ttl=INFINITE)
    def is_community_banned(self):
        """
        :rtype: bool
        """
        return self._bans.CommunityBanned