__author__ = 'SmileyBarry'

from .decorators import debug


class APIException(Exception):
    """
    Base class for all API exceptions.
    """
    pass


class AccessException(APIException):
    """
    You are attempting to query an object that you have no permission to query. (E.g.: private user,
    hidden screenshot, etc.)
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


class APIKeyRequired(APIFailure):
    """
    This API requires an API key to call and does not support anonymous requests.
    """
    pass


class APIPrivate(APIFailure):
    """
    The API you're trying to call requires a privileged API key. Your existing key is not allowed to call this.
    """


class APIConfigurationError(APIFailure):
    """
    There's either no APIConnection defined, or the parameters given to "APIConnection" or "APIInterface" are
    invalid.
    """
    pass


def check(response):
    """
    :type response: requests.Response
    """
    if response.status_code // 100 == 4:
        if response.status_code == 404:
            raise APINotFound(
                "The function or service you tried to call does not exist.")
        elif response.status_code == 401:
            raise APIUnauthorized("This API is not accessible to you.")
        elif response.status_code == 403:
            if '?key=' in response.request.url or '&key=' in response.request.url:
                raise APIPrivate(
                    "You have no permission to use this API, or your key may be invalid.")
            else:
                raise APIKeyRequired("This API requires a key to call.")
        elif response.status_code == 400:
            raise APIBadCall(
                "The parameters you sent didn't match this API's requirements.")
        else:
            raise APIFailure(
                "Something is wrong with your configuration, parameters or environment.")
    elif response.status_code // 100 == 5:
        raise APIError("The API server has encountered an unknown error.")
    else:
        return
