__author__ = 'SmileyBarry'

import requests
import time

from .decorators import Singleton, cached_property, INFINITE
from . import errors

GET = "GET"
POST = "POST"


class APICall(object):
    _QUERY_DOMAIN = "http://api.steampowered.com"
    _QUERY_TEMPLATE = "{domain}/".format(domain=_QUERY_DOMAIN)

    def __init__(self, api_id, parent=None):
        self._api_id = api_id
        self._is_registered = False
        self._parent = parent
        # IPython always looks for this, no matter what (hiding it in __dir__ doesn't work), so this is
        # necessary to keep it from constantly making new APICall instances. (a significant slowdown)
        self.trait_names = lambda: None

    def __str__(self):
        """
        Generate the function URL.
        """
        if self._parent is None:
            return self._QUERY_TEMPLATE + self._api_id + '/'
        else:
            return str(self._parent) + self._api_id + '/'

    @cached_property(ttl=INFINITE)
    def _full_name(self):
        if self._parent is None:
            return self._api_id
        else:
            return self._parent._full_name + '.' + self._api_id

    def __repr__(self):
        if self._is_registered is True:
            note = "(verified)"  # This is a registered, therefore working, API.
        else:
            note = "(unconfirmed)"
        return "<{cls} {full_name} {api_note}>".format(cls=self.__class__.__name__,
                                                       full_name=self._full_name,
                                                       api_note=note)

    def __getattribute__(self, item):
        if item.startswith('_'):
            # Underscore items are special.
            return super(APICall, self).__getattribute__(item)
        else:
            try:
                return super(APICall, self).__getattribute__(item)
            except AttributeError:
                # Not an expected item, so generate a new APICall!
                return APICall(item, self)

    def _register(self, apicall_child):
        """
        Register a child APICall object under the "self._resolved_children" dictionary so it can be used
        normally. Used by API function wrappers after they're deemed working.

        :param apicall_child: A working APICall object that should be stored as resolved.
        :type apicall_child: APICall
        """
        if hasattr(self, apicall_child._api_id) and \
           apicall_child is self.__getattribute__(apicall_child._api_id):
            raise KeyError("This API ID is already taken by another API function!")
        else:
            if self._parent is not None:
                self._parent._register(self)
            else:
                self._is_registered = True
            self.__setattr__(apicall_child._api_id, apicall_child)
            apicall_child._is_registered = True

    def __call__(self, method=GET, **kwargs):
        for argument in kwargs:
            if issubclass(type(kwargs[argument]), list):
                # The API takes multiple values in a "a,b,c" structure, so we
                # have to encode it in that way.
                kwargs[argument] = ','.join(kwargs[argument])
            elif issubclass(type(kwargs[argument]), bool):
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

        if APIConnection()._api_key is not None:
            kwargs["key"] = APIConnection()._api_key

        query = str(self)

        if method == POST:
            response = requests.request(method, query, data=kwargs)
        else:
            response = requests.request(method, query, params=kwargs)

        if response.status_code != 200:
            errors.raiseAppropriateException(response.status_code)

        # Store the object for future reference.
        if self._is_registered is False:
            self._parent._register(self)

        if automatic_parsing is True:
            response_obj = response.json()
            if len(response_obj.keys()) == 1 and 'response' in response_obj:
                return APIResponse(response_obj['response'])
            else:
                return APIResponse(response_obj)

@Singleton
class APIConnection(object):
    QUERY_DOMAIN = "http://api.steampowered.com"
    # Use double curly-braces to tell Python that these variables shouldn't be expanded yet.
    QUERY_TEMPLATE = "{domain}/{{interface}}/{{command}}/{{version}}/".format(domain=QUERY_DOMAIN)

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

        if 'precache' in settings and issubclass(type(settings['precache']), bool):
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


def store(obj, property_name, data, received_time=time.time()):
    """
    Store data inside the cache of a cache-enabled object. Mainly used for pre-caching.

    :param obj: The target object.
    :type obj: SteamObject
    :param property_name: The destination property's name.
    :param data: The data that we need to store inside the object's cache.
    :type data: object
    :param received_time: The time this data was retrieved. Used for the property cache.
    :type received_time: float
    """
    # Just making sure caching is supported for this object...
    if issubclass(type(obj), SteamObject) or hasattr(obj, "_cache"):
        obj._cache[property_name] = (data, received_time)
    else:
        raise TypeError("This object type either doesn't visibly support caching, or has yet to initialise its cache.")


def expire(obj, property_name):
    """
    Expire a cached property

    :param obj: The target object.
    :type obj: SteamObject
    :param property_name:
    :type property_name:
    """
    if issubclass(type(obj), SteamObject) or hasattr(obj, "_cache"):
        del obj._cache[property_name]
    else:
        raise TypeError("This object type either doesn't visibly support caching, or has yet to initialise its cache.")
