from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import super
from future import standard_library

#standard_library.install_aliases()
from builtins import *


class NzbHydraException(Exception):
    def __init__(self, message=None, exception=None):
        super(NzbHydraException, self).__init__(message)


class ExternalApiInfoException(NzbHydraException):
    # An error occurred while contacting an external info API (tvdaze, omdbapi, etc) or parsing its returned data
    def __init__(self, message):
        super(NzbHydraException, self).__init__(message)
        self.message = message


class IndexerIllegalSearchException(NzbHydraException):
    # Thrown if an internal sanity check fails, for example if we tried to execute an id based search on a indexer that doesn't support it
    def __init__(self, message, search_module):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        self.search_module = search_module


class IndexerAuthException(NzbHydraException):
    # The indexer indicated that the authentication failed. This indexer should not be user until the problem is solved.
    def __init__(self, message, search_module):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        self.search_module = search_module


class IndexerAccessException(NzbHydraException):
    # The connection to the indexer was successful but we got an error page. We should probably wait some time until we use it again but don't assume it's a permanent problem
    def __init__(self, message, search_module):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        self.search_module = search_module


class IndexerConnectionException(NzbHydraException):
    # The connection to the indexer failed. We should probably wait some time until we use it again but don't assume it's a permanent problem
    def __init__(self, message, search_module):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        self.search_module = search_module


class IndexerResultParsingException(NzbHydraException):
    # The connection to the indexer was successful but we were unable to parse the returned results
    def __init__(self, message, search_module):
        super(NzbHydraException, self).__init__(message)
        self.message = message
        self.search_module = search_module


class DownloaderException(NzbHydraException):
    def __init__(self, message):
        super(NzbHydraException, self).__init__(message)
        self.message = message
