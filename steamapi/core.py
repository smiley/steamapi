__author__ = 'SmileyBarry'

import logging
import requests
import time

from .consts import IPYTHON_PEEVES, IPYTHON_MODE
from .decorators import Singleton, cached_property, INFINITE
from . import errors

GET = "GET"
POST = "POST"

# A mapping of all types accepted/required by the API to their Python equivalents.
APITypes = {'bool':      bool,
            'int32':     int,
            'uint32':    int,
            'uint64':    int,
            'string':    [str, unicode],
            'rawbinary': [str, buffer]}


class APICall(object):
    _QUERY_DOMAIN = "http://api.steampowered.com"
    _QUERY_TEMPLATE = "{domain}/".format(domain=_QUERY_DOMAIN)

    def __init__(self, api_id, parent=None, method=None):
        """
        Create a new APICall instance.

        :param api_id: The API's string-based ID. Must start with a letter, as per Python's rules for attributes.
        :type api_id: str
        :param parent: The APICall parent of this object. Can be None if this is a Service or Interface.
        :type parent: APICall
        :param method: The HTTP method used for calling the API.
        :type method: str
        :return: A new instance of APICall.
        :rtype: APICall
        """
        self._api_id = api_id
        self._is_registered = False
        self._parent = parent
        self._method = method

        # Set an empty documentation for now.
        self._api_documentation = ""

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
                if IPYTHON_MODE is True:
                    # We're in IPython. Which means "getdoc()" is also automatically used for docstrings!
                    if item == "getdoc":
                        return lambda: self._api_documentation
                    elif item in IPYTHON_PEEVES:
                        # IPython always looks for this, no matter what (hiding it in __dir__ doesn't work), so this is
                        # necessary to keep it from constantly making new APICall instances. (a significant slowdown)
                        raise
                # Not an expected item, so generate a new APICall!
                return APICall(item, self)

    def __iter__(self):
        return self.__dict__.__iter__()

    def _set_documentation(self, docstring):
        """
        Set a docstring specific to this instance of APICall, explaining the bound function.

        :param docstring: The relevant docstring.
        :return: None
        """
        self._api_documentation = docstring

    def _register(self, apicall_child=None):
        """
        Register a child APICall object under the "self._resolved_children" dictionary so it can be used
        normally. Used by API function wrappers after they're deemed working.

        :param apicall_child: A working APICall object that should be stored as resolved.
        :type apicall_child: APICall
        """
        if apicall_child is not None:
            if apicall_child._api_id in self.__dict__ \
               and apicall_child is not self.__dict__[apicall_child._api_id]:
                raise KeyError("This API ID is already taken by another API function!")
        if self._parent is not None:
            self._parent._register(self)
        else:
            self._is_registered = True
        if apicall_child is not None:
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

        if self._method is not None:
            method = self._method

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


class APIInterface(object):
    def __init__(self, api_key=None, autopopulate=False, strict=False, settings={}):
        """
        Initialize a new APIInterface object. This object defines an API-interacting session, and is used to call
        any API functions from standard code.

        :param api_key: Your Steam Web API key. Can be left blank, but some APIs will not work.
        :type api_key: str
        :param autopopulate: Whether the interfaces, services and methods supported by the Steam Web API should be \
        auto-populated during initialization.
        :type autopopulate: bool
        :param strict: Should the interface enforce access only to defined functions, and only as defined. Only \
        applicable if :var autopopulate: is True.
        :type strict: bool
        :param settings: A dictionary which defined advanced settings.
        :type settings: dict
        :return:
        """
        if autopopulate is False and strict is True:
            raise ValueError("\"strict\" is only applicable if \"autopopulate\" is set to True.")

        if issubclass(type(api_key), str) and len(api_key) == 0:
            # We were given an empty key (== no key), but the API's equivalent of "no key" is None.
            api_key = None

        super_self = super(type(self), self)

        # Initialization routines must use the original __setattr__ function, because they might collide with the
        # overridden "__setattr__", which expects a fully-built instance to exist before being called.
        def set_attribute(name, value):
            return super_self.__setattr__(name, value)

        set_attribute('_api_key', api_key)
        set_attribute('_strict', strict)
        set_attribute('_settings', settings)

        if autopopulate is True:
            # TODO: Autopopulation should be long-term-cached somewhere for future use, since it won't change much.

            # Regardless of "strict mode", it has to be OFF during auto-population.
            original_strict_value = self._strict
            try:
                self.__dict__['_strict'] = False
                self._autopopulate_interfaces()
            finally:
                self.__dict__['_strict'] = original_strict_value

    def _autopopulate_interfaces(self):
        # Call the API which returns a list of API Services and Interfaces.
        # API definitions describe how the Interfaces and Services are built up, including parameter names & types.
        api_definition = self.ISteamWebAPIUtil.GetSupportedAPIList.v0001(key=self._api_key)

        for interface in api_definition.apilist.interfaces:
            if interface.name == "ISteamApps":
                import pdb
                #pdb.set_trace()
            interface_object = APICall(interface.name)
            parameter_description = "{indent}{{requirement}} {{type}} {{name}}:{indent}{{desc}}".format(indent='\t')
            # Unindented so that the docstring won't be overly indented.
            docstring = \
"""
{name}

Parameters:
{parameter_list}
"""
            for method in interface.methods:
                if method.name in interface_object:
                    base_method_object = interface_object.__getattribute__(method.name)
                else:
                    base_method_object = APICall(method.name, interface_object, method.httpmethod)
                # API calls have version-specific definitions, so backwards compatibility could be maintained.
                # However, the Web API returns versions as integers (1, 2, etc.) but accepts them as "v?" (v1, v2, etc.)
                method_object = APICall('v' + str(method.version), base_method_object, method.httpmethod)

                parameters = []
                for parameter in method.parameters:
                    parameter_requirement = "REQUIRED"
                    if parameter.optional is True:
                        parameter_requirement = "OPTIONAL"
                    if 'description' in parameter:
                        desc = parameter.description
                    else:
                        desc = "(no description)"
                    parameters += [parameter_description.format(requirement=parameter_requirement,
                                                                type=parameter.type,
                                                                name=parameter.name,
                                                                desc=desc)]
                # Now build the docstring.
                func_docstring = docstring.format(name=method.name,
                                                  parameter_list='\n'.join(parameters))
                # Set the docstring appropriately
                method_object._api_documentation = func_docstring
                #method_object.__call__.__func__.__doc__ = func_docstring

                # Now call the standard registration method.
                method_object._register()
            # And now, add it to the APIInterface.
            self.__setattr__(interface.name, interface_object)


    def __getattr__(self, name):
        """
        Creates a new APICall() instance if "strict" is disabled.

        :param name: A Service or Interface name.
        :return: A Pythonic object used to access the remote Service or Interface. (APICall)
        :rtype: APICall
        """
        if name.startswith('_'):
            return super(type(self), self).__getattribute__(name)
        elif name in IPYTHON_PEEVES:
            # IPython always looks for this, no matter what (hiding it in __dir__ doesn't work), so this is
            # necessary to keep it from constantly making new APICall instances. (a significant slowdown)
            raise AttributeError()
        else:
            if self._strict is True:
                raise AttributeError("Strict '{cls}' object has no attribute '{attr}'".format(cls=type(self).__name__,
                                                                                              attr=name))
            new_service = APICall(name)
            # Save this service.
            self.__dict__[name] = new_service
            return new_service

    def __setattr__(self, name, value):
        if self._strict is True:
            raise AttributeError("Cannot set attributes to a strict '{cls}' object.".format(cls=type(self).__name__))
        else:
            return super(type(self), self).__setattr__(name, value)




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
                import pdb
                pdb.set_trace()
                raise AttributeError("'{cls}' has no attribute '{attr}'".format(cls=type(self).__name__,
                                                                                attr=item))

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
