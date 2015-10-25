import logging
import collections

from typing import Dict, List
import arrow
import requests
from requests import RequestException

from nzbhydra.config import ProviderSettings, searchingSettings
from nzbhydra.database import ProviderSearch, ProviderApiAccess, ProviderStatus, Provider
from nzbhydra.exceptions import ProviderResultParsingException, ProviderAuthException, ProviderAccessException
from nzbhydra.nzb_search_result import NzbSearchResult

QueriesExecutionResult = collections.namedtuple("QueriesExecutionResult", "results dbentry total loaded_results total_known has_more")
ProviderProcessingResult = collections.namedtuple("ProviderProcessingResult", "entries queries total total_known has_more")


class SearchModule(object):
    logger = logging.getLogger('root')
    # regarding quality:
    # possibly use newznab qualities as base, map for other providers (nzbclub etc)


    def __init__(self, settings: ProviderSettings):
        self.settings = settings
        self.module = "Abstract search module"
        self.supports_queries = True
        self.needs_queries = False
        self.category_search = True  # If true the provider supports searching in a given category (possibly without any query or id)
        self.limit = 100
        
    def __repr__(self):
        return self.name

    @property
    def provider(self):
        return Provider.get(Provider.name == self.settings.name.get())

    @property
    def host(self):
        return self.settings.host.get()

    @property
    def name(self):
        return self.settings.name.get()
    
    @property
    def score(self):
        return self.settings.score.get()

    @property
    def search_ids(self):
        return self.settings.search_ids.get()

    @property
    def generate_queries(self):
        return True  # TODO pass when used check for internal vs external
        # return self.provider.settings.get("generate_queries", True)  # If true and a search by movieid or tvdbid or rid is done then we attempt to find the title and generate queries for providers which don't support id-based searches


    def search(self, search_request):
        if search_request.type == "tv":
            if search_request.query is None and search_request.identifier_key is None and self.needs_queries:
                self.logger.error("TV search without query or id or title is not possible with this provider")
                return []
            if search_request.query is None and not self.generate_queries:
                self.logger.error("TV search is not possible with this provideer because query generation is disabled")
            if search_request.identifier_key in self.search_ids:
                # Best case, we can search using the ID
                urls = self.get_showsearch_urls(search_request)
            elif search_request.title is not None:
                # If we cannot search using the ID we generate a query using the title provided by the GUI
                search_request.query = search_request.title
                urls = self.get_showsearch_urls(search_request)
            elif search_request.query is not None:
                # Simple case, just a regular raw search but in movie category
                urls = self.get_showsearch_urls(search_request)
            else:
                # Just show all the latest movie releases
                urls = self.get_showsearch_urls(search_request)
        elif search_request.type == "movie":
            if search_request.query is None and search_request.title is None and search_request.identifier_key is None and self.needs_queries:
                self.logger.error("Movie search without query or IMDB id or title is not possible with this provider")
                return []
            if search_request.query is None and not self.generate_queries:
                self.logger.error("Movie search is not possible with this provideer because query generation is disabled")
            if search_request.identifier_key is not None and "imdbid" in self.search_ids:
                # Best case, we can search using IMDB id
                urls = self.get_moviesearch_urls(search_request)
            elif search_request.title is not None:
                # If we cannot search using the ID we generate a query using the title provided by the GUI
                search_request.query = search_request.title
                urls = self.get_moviesearch_urls(search_request)
            elif search_request.query is not None:
                # Simple case, just a regular raw search but in movie category
                urls = self.get_moviesearch_urls(search_request)
            else:
                # Just show all the latest movie releases
                urls = self.get_moviesearch_urls(search_request)
            return self.execute_queries(urls)
        else:
            urls = self.get_search_urls(search_request)
        queries_execution_result = self.execute_queries(urls)
        return queries_execution_result


    # Access to most basic functions
    def get_search_urls(self, search_request) -> List[str]:
        # return url(s) to search. Url is then retrieved and result is returned if OK
        # we can return multiple urls in case a module needs to make multiple requests (e.g. when searching for a show
        # using general queries
        return []

    def get_showsearch_urls(self, args):
        # to extend
        # if module supports it, search specifically for show, otherwise make sure we create a query that searches
        # for for s01e01, 1x1 etc
        return []

    def get_moviesearch_urls(self, args):
        # to extend
        # if module doesnt support it possibly use (configurable) size restrictions when searching
        return []

    def create_nzb_search_result(self):
        return NzbSearchResult(provider=self.name, providerscore=self.score)

    def process_query_result(self, result: str, query: str) -> ProviderProcessingResult:
        return []

    def check_auth(self, body: str):
        # check the response body to see if request was authenticated. If yes, do nothing, if no, raise exception 
        return []

    

    disable_periods = [0, 15, 30, 60, 3 * 60, 6 * 60, 12 * 60, 24 * 60]

    def handle_provider_success(self):
        # Deescalate level by 1 (or stay at 0) and reset reason and disable-time
        try:
            provider_status = self.provider.status.get()
        except ProviderStatus.DoesNotExist:
            provider_status = ProviderStatus(provider=self.provider)
        if provider_status.level > 0:
            provider_status.level -= 1
        provider_status.reason = None
        provider_status.disabled_until = arrow.get(0)  # Because I'm too dumb to set it to None/null
        provider_status.save()

    def handle_provider_failure(self, reason=None, disable_permanently=False):
        # Escalate level by 1. Set disabled-time according to level so that with increased level the time is further in the future
        try:
            provider_status = self.provider.status.get()
        except ProviderStatus.DoesNotExist:
            provider_status = ProviderStatus(provider=self.provider)

        if provider_status.level == 0:
            provider_status.first_failure = arrow.utcnow()

        provider_status.latest_failure = arrow.utcnow()
        provider_status.reason = reason  # Overwrite the last reason if one is set, should've been logged anyway
        if disable_permanently:
            provider_status.disabled_permanently = True
        else:
            provider_status.level = min(len(self.disable_periods) - 1, provider_status.level + 1)
            provider_status.disabled_until = arrow.utcnow().replace(minutes=self.disable_periods[provider_status.level])

        provider_status.save()

    def get(self, url, timeout=None, cookies=None):
        # overwrite for special handling, e.g. cookies
        return requests.get(url, timeout=timeout, verify=False, cookies=cookies)

    def get_url_with_papi_access(self, url, type, cookies=None, timeout=None):
        papiaccess = ProviderApiAccess(provider=self.provider, type=type, url=url, time=arrow.utcnow().datetime)

        try:
            response = self.get(url, cookies=cookies, timeout=timeout)
            response.raise_for_status()
            papiaccess.response_time = response.elapsed.microseconds / 1000
            papiaccess.response_successful = True
            self.handle_provider_success()
        except RequestException as e:
            self.logger.error("Error while connecting to URL %s: %s" % (url, str(e)))
            papiaccess.error = "Connection failed: %s" % str(e)
            response = None
            self.handle_provider_failure("Connection failed: %s" % str(e))
        finally:
            papiaccess.save()
        return response, papiaccess

    def get_nfo(self, guid):
        return None

    def get_nzb_link(self, guid, title):
        return None

    def execute_queries(self, queries) -> QueriesExecutionResult:
        # todo call all queries, check if further should be called, return all results when done or timeout or whatever
        """

        :rtype : ResultsAndProviderSearchDbEntry
        """
        results = []
        executed_queries = set()
        psearch = ProviderSearch(provider=self.provider)
        psearch.save()
        total_results = 0
        offset = 0
        total_known = False
        has_more = False
        while len(queries) > 0:
            query = queries.pop()
            if query in executed_queries:
                # To make sure that in case an offset is reported wrong or we have a bug we don't get stuck in an endless loop 
                continue

            try:
                self.logger.debug("Requesting URL %s with timeout %d" % (query, searchingSettings.timeout.get()))
                request, papiaccess = self.get_url_with_papi_access(query, "search")
                papiaccess.provider_search = psearch

                executed_queries.add(query)
                papiaccess.save()

                if request is not None:
                    self.check_auth(request.text)
                    self.logger.debug("Successfully loaded URL %s" % request.url)
                    try:

                        parsed_results = self.process_query_result(request.text, query)
                        results.extend(parsed_results.entries)  # Retrieve the processed results
                        queries.extend(parsed_results.queries)  # Add queries that were added as a result of the parsing, e.g. when the next result page should also be loaded
                        total_results += parsed_results.total
                        total_known = parsed_results.total_known
                        has_more = parsed_results.has_more

                        papiaccess.response_successful = True
                        self.handle_provider_success()
                    except Exception as e:
                        self.logger.exception("Error while processing search results from provider %s" % self)
                        raise ProviderResultParsingException("Error while parsing the results from provider", self)
            except ProviderAuthException as e:
                self.logger.error("Unable to authorize with %s: %s" % (e.search_module, e.message))
                papiaccess.error = "Authorization error :%s" % e.message
                self.handle_provider_failure(reason="Authentication failed", disable_permanently=True)
                papiaccess.response_successful = False
            except ProviderAccessException as e:
                self.logger.error("Unable to access %s: %s" % (e.search_module, e.message))
                papiaccess.error = "Access error: %s" % e.message
                self.handle_provider_failure(reason="Access failed")
                papiaccess.response_successful = False
            except ProviderResultParsingException as e:
                papiaccess.error = "Access error: %s" % e.message
                self.handle_provider_failure(reason="Parsing results failed")
                papiaccess.response_successful = False
            except Exception as e:
                self.logger.exception("An error error occurred while searching: %s", e)
                papiaccess.error = "Unknown error :%s" % e
                papiaccess.response_successful = False
            finally:
                papiaccess.save()
                psearch.results = total_results
                psearch.successful = papiaccess.response_successful
                psearch.save()
        return QueriesExecutionResult(results=results, dbentry=psearch, total=total_results, loaded_results=len(results), total_known=total_known, has_more=has_more)


def get_instance(provider):
    return SearchModule(provider)
