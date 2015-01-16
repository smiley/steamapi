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

try:
    get_ipython
    # We're inside IPython. Define all of IPython's custom function/method names so we could special-case them.
    IPYTHON_PEEVES = ["trait_names", "getdoc"]
    IPYTHON_MODE = True
except NameError:
    # IPython's not running us. Don't special-case it. (An empty list instantly makes any "if name in IPYTHON_PEEVES"
    # clause False, without doing unnecessary checks.)
    IPYTHON_PEEVES = []
    IPYTHON_MODE = False

# Unindented so that the docstring won't be overly indented.
API_CALL_DOCSTRING_TEMPLATE = \
"""
{name}

Parameters:
{parameter_list}
"""
API_CALL_PARAMETER_TEMPLATE = "{indent}{{requirement}} {{type}} {{name}}:{indent}{{desc}}"