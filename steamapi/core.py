__author__ = 'SmileyBarry'

import requests

from .decorators import Singleton
from . import errors

GET = "GET"
POST = "POST"

@Singleton
class APIConnection(object):
    QUERY_TEMPLATE = "http://api.steampowered.com/{interface}/{command}/{version}/"

    def __init__(self, api_key=None, settings={}):
        """
        Initialise the main APIConnection. Since APIConnection is a singleton object, any further "initialisations"
        will not re-initialise the instance but just retrieve the existing instance. To reassign an API key,
        retrieve the Singleton instance and call "reset" with the key.

        :param api_key: A Steam Web API key. (Optional, but recommended)
        :param settings: A dictionary of advanced tweaks. Beware! (Optional)
            precache -- True/False. (Default: True) Decides whether attributes that retrieve
                        a group of users, such as "friends", should precache player summaries,
                        like nicknames. Recommended if you plan to use nicknames right away, since
                        caching is done in groups and retrieving one-by-one takes a while.

        """
        self.reset(api_key)

        self.precache = True

        if 'precache' in settings and type(settings['precache']) is bool:
            self.precache = settings['precache']

    def reset(self, api_key):
        self._api_key = api_key

    def call(self, interface, command, version, method=GET, **kwargs):
        """
        Call an API command. All keyword commands past method will be made into GET/POST-based commands,
        automatically.

        :param interface: Interface name that contains the requested command. (E.g.: "ISteamUser")
        :param command: A matching command. (E.g.: "GetPlayerSummaries")
        :param version: The version of this API you're using. (Usually v000X or vX, with "X" standing in for a number)
        :param method: Which HTTP method this call should use. GET by default, but can be overriden to use POST for
                       POST-exclusive APIs or long parameter lists.
        :param kwargs: A bunch of keyword arguments for the call itself. "key" and "format" should NOT be specified.
                       If APIConnection has an assoociated key, "key" will be overwritten by it, and overriding "format"
                       cancels out automatic parsing. (The resulting object WILL NOT be an APIResponse but a string.)

        :rtype : APIResponse or str
        """
        for argument in kwargs:
            if type(kwargs[argument]) is list:
                # The API takes multiple values in a "a,b,c" structure, so we
                # have to encode it in that way.
                kwargs[argument] = ','.join(kwargs[argument])
            elif type(kwargs[argument]) is bool:
                # The API treats True/False as 1/0. Convert it.
                if kwargs[argument] is True:
                    kwargs[argument] = 1
                else:
                    kwargs[argument] = 0

        automatic_parsing = True
        if "format" in kwargs:
            automatic_parsing = False
        else:
            kwargs["format"] = "json"

        if self._api_key is not None:
            kwargs["key"] = self._api_key

        query = self.QUERY_TEMPLATE.format(interface=interface, command=command, version=version)

        if method == POST:
            response = requests.request(method, query, data=kwargs)
        else:
            response = requests.request(method, query, params=kwargs)

        if response.status_code != 200:
            errors.raiseAppropriateException(response.status_code)

        if automatic_parsing is True:
            response_obj = response.json()
            if len(response_obj.keys()) == 1 and 'response' in response_obj:
                return APIResponse(response_obj['response'])
            else:
                return APIResponse(response_obj)


class APIResponse(object):
    """
    A dict-proxying object which objectifies API responses for prettier code,
    easier prototyping and less meaningless debugging ("Oh, I forgot square brackets.").

    Recursively wraps every response given to it, by replacing each 'dict' object with an
    APIResponse instance. Other types are safe.
    """
    def __init__(self, father_dict):
        # Initialize an empty dictionary.
        self._real_dictionary = {}
        # Recursively wrap the response in APIResponse instances.
        for item in father_dict:
            if type(father_dict[item]) is dict:
                self._real_dictionary[item] = APIResponse(father_dict[item])
            elif type(father_dict[item]) is list:
                self._real_dictionary[item] = [APIResponse(entry) for entry in father_dict[item]]
            else:
                self._real_dictionary[item] = father_dict[item]

    def __repr__(self):
        return dict.__repr__(self._real_dictionary)

    @property
    def __dict__(self):
        return self._real_dictionary

    def __getattribute__(self, item):
        if item.startswith("_"):
            return super(APIResponse, self).__getattribute__(item)
        else:
            if item in self._real_dictionary:
                return self._real_dictionary[item]
            else:
                return None

    def __getitem__(self, item):
        return self._real_dictionary[item]

    def __iter__(self):
        return self._real_dictionary.__iter__()


class SteamObject(object):
    @property
    def id(self):
        return self._id

    def __repr__(self):
        try:
            return '<{clsname} "{name}" ({id})>'.format(clsname=self.__class__.__name__,
                                                        name=self.name.encode(errors="ignore"),
                                                        id=self._id)
        except AttributeError:
            return '<{clsname} ({id})>'.format(clsname=self.__class__.__name__, id=self._id)