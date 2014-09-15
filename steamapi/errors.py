__author__ = 'SmileyBarry'

from .decorators import debug


class APIException(Exception):
    """
    Base class for all API exceptions.
    """
    pass


class APIUserError(APIException):
    """
    An API error caused by a user error, like wrong data or just empty results for a query.
    """
    pass


class UserNotFoundError(APIUserError):
    """
    The specified user was not found on the Steam Community. (Bad vanity URL? Non-existent ID?)
    """
    pass


class APIError(APIException):
    """
    An API error signifies a problem with the server, a temporary issue or some other easily-repairable
    problem.
    """
    pass


class APIFailure(APIException):
    """
    An API failure signifies a problem with your request (e.g.: invalid API), a problem with your data,
    or any error that resulted from improper use.
    """
    pass


class APIBadCall(APIFailure):
    """
    Your API call doesn't match the API's specification. Check your arguments, service name, command &
    version.
    """
    pass


class APINotFound(APIFailure):
    """
    The API you tried to call does not exist. (404)
    """
    pass


class APIUnauthorized(APIFailure):
    """
    The API you've attempted to call either requires a key, or your key has insufficient permissions.
    If you're requesting user details, make sure their privacy level permits you to do so, or that you've
    properly authorised said user. (401)
    """
    pass


class APIConfigurationError(APIFailure):
    """
    There's either no APIConnection defined, or
    """
    pass


@debug.no_return
def raiseAppropriateException(status_code):
    if status_code // 100 == 4:
        if status_code == 404:
            raise APINotFound()
        elif status_code == 401:
            raise APIUnauthorized()
        elif status_code == 400:
            raise APIBadCall()
        else:
            raise APIFailure()
    elif status_code // 100 == 5:
        raise APIError()

