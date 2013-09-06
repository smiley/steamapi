from .decorators import cached_property, INFINITE, MINUTE, HOUR
from .app import SteamApp

__author__ = 'SmileyBarry'

from .core import APIConnection


class SteamUser(object):
    # OVERRIDES
    def __init__(self, steam_userid=None, steam_userurl=None):
        """
        Create a new instance of a Steam user. Use this object to retrieve details about
        that user.

        :param steam_userid: The user's 64-bit SteamID. (Optional, unless steam_userurl isn't specified)
        :param steam_userurl: The user's vanity URL-ending name. (Required if "steam_userid" isn't specified,
        unused otherwise)
        :raise: ValueError on improper usage.
        """
        if steam_userid is None and steam_userurl is None:
            raise ValueError("One of the arguments must be supplied.")

        if steam_userurl is not None:
            response = APIConnection().call("ISteamUser", "ResolveVanityURL", "v0001", vanityurl=steam_userurl)
            steam_userid = response.steamid

        if steam_userid is not None:
            self._id = steam_userid

    def __eq__(self, other):
        if type(other) is SteamUser:
            if self.steamid == other.steamid:
                return True
            else:
                return False
        else:
            return super(SteamUser, self).__eq__(other)

    def __repr__(self):
        return '<SteamUser "{name}" ({id})>'.format(name=self.name, id=self.steamid)

    # PRIVATE UTILITIES
    @cached_property(ttl=2 * HOUR)
    def _summary(self):
        return APIConnection().call("ISteamUser", "GetPlayerSummaries", "v0002", steamids=self.steamid).players[0]

    @property
    def steamid(self):
        return self._id

    @cached_property(ttl=INFINITE)
    def name(self):
        return self._summary.personaname

    @cached_property(ttl=30 * MINUTE)
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
                                                      steamids=','.join(chunk)).players

                import time
                now = time.time()
                for player_summary in player_details:
                    # Fill in the cache with this info.
                    id_player_map[player_summary.steamid]._cache["_summary"] = (player_summary, now)
        return friends_list

    @cached_property(ttl=2 * HOUR)
    def level(self):
        response = APIConnection().call("IPlayerService", "GetSteamLevel", "v1", steamid=self.steamid)
        return response.player_level

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