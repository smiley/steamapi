__author__ = 'SmileyBarry'


class Enum(object):
    def __init__(self):
        raise TypeError("Enums cannot be instantiated, use their attributes instead")


class CommunityVisibilityState(Enum):
    PRIVATE = 1
    FRIENDS_ONLY = 2
    FRIENDS_OF_FRIENDS = 3
    USERS_ONLY = 4
    PUBLIC = 5


class OnlineState(Enum):
    OFFLINE = 0
    ONLINE = 1
    BUSY = 2
    AWAY = 3
    SNOOZE = 4
    LOOKING_TO_TRADE = 5
    LOOKING_TO_PLAY = 6