class NzbHydraException(Exception):
    def __init__(self, message=""):
        super(NzbHydraException, self).__init__()
        self.message = message

    def __str__(self):
        return str(self.__class__.__name__) + ": " + self.message


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


class IndexerApiLimitReachedException(IndexerException):
    """The API limit of the indexer was rechead.
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


class IndexerResultParsingRowException(NzbHydraException):
    """An entry in the returned search results could not be parsed
    """
    pass


class DownloaderException(NzbHydraException):
    pass


class DownloaderNotFoundException(NzbHydraException):
    """An downloader of the given type could not be found
    """
    pass


class IndexerNotFoundException(NzbHydraException):
    """An indexer by the given name could not be found
    """
    pass


class NzbDownloadException(NzbHydraException):
    """A search result download failed
    """
    pass