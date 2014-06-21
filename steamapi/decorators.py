__author__ = 'SmileyBarry'

import threading
import time


class debug(object):
    @staticmethod
    def no_return(originalFunction, *args, **kwargs):
        def callNoReturn(*args, **kwargs):
            originalFunction(*args, **kwargs)
            # This code should never return!
            raise AssertionError("No-return function returned.")
        return callNoReturn

MINUTE = 60
HOUR = 60 * MINUTE
INFINITE = 0


class cached_property(object):
    """(C) 2011 Christopher Arndt, MIT License

    Decorator for read-only properties evaluated only once within TTL period.

    It can be used to created a cached property like this::

        import random

        # the class containing the property must be a new-style class
        class MyClass(object):
            # create property whose value is cached for ten minutes
            @cached_property(ttl=600)
            def randint(self):
                # will only be evaluated every 10 min. at maximum.
                return random.randint(0, 100)

    The value is cached  in the '_cache' attribute of the object instance that
    has the property getter method wrapped by this decorator. The '_cache'
    attribute value is a dictionary which has a key for every property of the
    object which is wrapped by this decorator. Each entry in the cache is
    created only when the property is accessed for the first time and is a
    two-element tuple with the last computed property value and the last time
    it was updated in seconds since the epoch.

    The default time-to-live (TTL) is 300 seconds (5 minutes). Set the TTL to
    zero for the cached value to never expire.

    To expire a cached property value manually just do::

        del instance._cache[<property name>]

    """
    def __init__(self, ttl=300):
        self.ttl = ttl

    def __call__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        return self

    def __get__(self, inst, owner):
        now = time.time()
        try:
            value, last_update = inst._cache[self.__name__]
            if now - last_update > self.ttl > 0:
                raise AttributeError
        except (KeyError, AttributeError):
            value = self.fget(inst)
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = (value, now)
        return value


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    Limitations: The decorated class cannot be inherited from.

    :author: Paul Manta, Stack Overflow.
             http://stackoverflow.com/a/7346105/2081507
             (with slight modification)

    """

    def __init__(self, decorated):
        self._lock = threading.Lock()
        self._decorated = decorated

    def __call__(self, *args, **kwargs):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        with self._lock:
            try:
                return self._instance
            except AttributeError:
                self._instance = self._decorated(*args, **kwargs)
                return self._instance

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)