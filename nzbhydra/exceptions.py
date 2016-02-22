class NzbHydraException(Exception):
    pass


class ExternalApiInfoException(NzbHydraException):
    """An error occurred while contacting an external info API
    (tvdaze, omdbapi, etc) or parsing its returned data.
    """
    pass


class IndexerException(NzbHydraException):
    def __init__(self, message, search_module):
        super(IndexerException, self).__init__(message)
        self.search_module = search_module


class IndexerIllegalSearchException(IndexerException):
    """Thrown if an internal sanity check fails, for example if we tried
    to execute an id based search on a indexer that doesn't support it.
    """
    pass


class IndexerAuthException(IndexerException):
    """The indexer indicated that the authentication failed.
    This indexer should not be used until the problem is solved.
    """
    pass


class IndexerAccessException(IndexerException):
    """The connection to the indexer was successful but we got an error page.
    We should probably wait some time until we use it again
    but don't assume it's a permanent problem.
    """
    pass


class IndexerConnectionException(IndexerException):
    """The connection to the indexer failed. We should probably wait some time
    until we use it again but don't assume it's a permanent problem.
    """
    pass


class IndexerResultParsingException(IndexerException):
    """The connection to the indexer was successful
    but we were unable to parse the returned results.
    """
    pass


class DownloaderException(NzbHydraException):
    pass
