class NzbHydraException(Exception):
    def __init__(self, message=None):
        super(NzbHydraException, self).__init__(message)
        

class ExternalApiInfoException(NzbHydraException):
    # An error occurred while contacting an external info API (tvdaze, omdbapi, etc) or parsing its returned data
    def __init__(self, message):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        


class ProviderIllegalSearchException(NzbHydraException):
    # Thrown if an internal sanity check fails, for example if we tried to execute an id based search on a provider that doesn't support it
    def __init__(self, message, search_module):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        self.search_module = search_module


class ProviderAuthException(NzbHydraException):
    # The provider indicated that the authentication failed. This provider should not be user until the problem is solved.
    def __init__(self, message, search_module):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        self.search_module = search_module


class ProviderAccessException(NzbHydraException):
    # The connection to the provider was successful but we got an error page. We should probably wait some time until we use it again but don't assume it's a permanent problem
    def __init__(self, message, search_module):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        self.search_module = search_module


class ProviderConnectionException(NzbHydraException):
    # The connection to the provider failed. We should probably wait some time until we use it again but don't assume it's a permanent problem
    def __init__(self, message, search_module):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        self.search_module = search_module


class ProviderResultParsingException(NzbHydraException):
    # The connection to the provider was successful but we were unable to parse the returned results
    def __init__(self, message, search_module):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        self.search_module = search_module

