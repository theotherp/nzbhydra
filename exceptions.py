class NzbHydraException(Exception):
    def __init__(self, message=None):
        super(NzbHydraException, self).__init__(message)


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
