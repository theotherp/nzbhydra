from typing import Dict, List
import logging

import arrow
import collections
import requests
from requests import RequestException

from nzbhydra import config
from nzbhydra.config import SearchingSettings, ProviderSettings
from nzbhydra.database import ProviderSearch, ProviderApiAccess, ProviderStatus, Provider
from nzbhydra.exceptions import ProviderConnectionException, ProviderResultParsingException, ProviderAuthException, ProviderAccessException


ResultsAndProviderSearchDbEntry = collections.namedtuple("ResultsAndProviderSearchDbEntry", "results dbentry")
EntriesAndQueries = collections.namedtuple("ResultsAndQueris", "entries queries")


class SearchModule(object):
    logger = logging.getLogger('root')
    # regarding quality:
    # possibly use newznab qualities as base, map for other providers (nzbclub etc)


    def __init__(self, settings: ProviderSettings):
        self.provider = Provider.get(Provider.id == settings.dbid)
        self.name = self.provider.name
        self.module = "Abstract search module"
        self.supports_queries = True
        self.needs_queries = False
        self.category_search = True  # If true the provider supports searching in a given category (possibly without any query or id)
        

    @property
    def host(self):
        return self.provider.settings.get("query_url")

    @property
    def getsettings(self):
        return self.provider.settings

    @property
    def search_ids(self):
        return self.provider.settings.get("search_ids", [])

    @property
    def generate_queries(self):
        return self.provider.settings.get("generate_queries", True)  # If true and a search by movieid or tvdbid or rid is done then we attempt to find the title and generate queries for providers which don't support id-based searches

    @property
    def max_api_hits(self):
        return self.provider.settings.get("max_api_hits")  # todo: when to check this? when picking a provider? Also this is checked by the provider and we check the returned result, so do we really need this?

    @property
    def api_hits_reset(self):
        return self.provider.settings.get("api_hits_reset")

    def search(self, args):
        urls = self.get_search_urls(args)
        return self.execute_queries(urls)

    def search_movie(self, args: Dict[str, str]) -> ResultsAndProviderSearchDbEntry:
        if args["query"] is None and args["title"] is None and args["imdbid"] is None and self.needs_queries:
            self.logger.error("Movie search without query or IMDB id or title is not possible with this provider")
            return []
        if args["query"] is None and not self.generate_queries:
            self.logger.error("Movie search is not possible with this provideer because query generation is disabled")
        if args["imdbid"] is not None and "imdbid" in self.search_ids:
            # Best case, we can search using IMDB id
            urls = self.get_moviesearch_urls(args)
        elif args["title"] is not None:
            # If we cannot search using the ID we generate a query using the title provided by the GUI
            args["query"] = args["title"]
            urls = self.get_moviesearch_urls(args)
        elif args["query"] is not None:
            # Simple case, just a regular raw search but in movie category
            urls = self.get_moviesearch_urls(args)
        else:
            # Just show all the latest movie releases
            urls = self.get_moviesearch_urls(args)
        return self.execute_queries(urls)

    def search_show(self, args: Dict[str, str]) -> ResultsAndProviderSearchDbEntry:
        if args["query"] is None and args["title"] is None and args["rid"] and args["tvdbid"] is None and self.needs_queries:
            self.logger.error("TV search without query or id or title is not possible with this provider")
            return []
        if args["query"] is None and not self.generate_queries:
            self.logger.error("TV search is not possible with this provideer because query generation is disabled")
        if (args["rid"] is not None and "rid" in self.search_ids) or (args["tvdbid"] is not None and "tvdbid" in self.search_ids):
            # Best case, we can search using the ID
            urls = self.get_showsearch_urls(args)
        elif args["title"] is not None:
            # If we cannot search using the ID we generate a query using the title provided by the GUI
            args["query"] = args["title"]
            urls = self.get_showsearch_urls(args)
        elif args["query"] is not None:
            # Simple case, just a regular raw search but in movie category
            urls = self.get_showsearch_urls(args)
        else:
            # Just show all the latest movie releases
            urls = self.get_showsearch_urls(args)

        return self.execute_queries(urls)

    # Access to most basic functions
    def get_search_urls(self, args: Dict[str, str]) -> List[str]:
        # return url(s) to search. Url is then retrieved and result is returned if OK
        # we can return multiple urls in case a module needs to make multiple requests (e.g. when searching for a show
        # using general queries
        return []

    def get_showsearch_urls(self, args: Dict[str, str]):
        # to extend
        # if module supports it, search specifically for show, otherwise make sure we create a query that searches
        # for for s01e01, 1x1 etc
        return []

    def get_moviesearch_urls(self, args: Dict[str, str]):
        # to extend
        # if module doesnt support it possibly use (configurable) size restrictions when searching
        return []

    def process_query_result(self, result: str, query: str) -> EntriesAndQueries:
        return []

    def check_auth(self, body : str):
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
        #overwrite for special handling, e.g. cookies
        return requests.get(url, timeout=timeout, verify=False, cookies=cookies)

    def get_url_with_papi_access(self, url, type, cookies=None, timeout=None):
        papiaccess = ProviderApiAccess(provider=self.provider, type=type, url=url)
        
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
    

    
    def execute_queries(self, queries) -> ResultsAndProviderSearchDbEntry:
        # todo call all queries, check if further should be called, return all results when done or timeout or whatever
        """

        :rtype : ResultsAndProviderSearchDbEntry
        """
        results = []
        executed_queries = set()
        psearch = ProviderSearch(provider=self.provider)
        psearch.save()
        while len(queries) > 0:
            query = queries.pop()
            if query in executed_queries:
                # To make sure that in case an offset is reported wrong or we have a bug we don't get stuck in an endless loop 
                continue

            try:
                self.logger.debug("Requesting URL %s with timeout %d" % (query, config.get(SearchingSettings.timeout)))
                request, papiaccess = self.get_url_with_papi_access(query, "search")
                papiaccess.provider_search = psearch
                
                executed_queries.add(query)
                papiaccess.save()
                
                if request is not None:
                    self.check_auth(request)
                    self.logger.debug("Successfully loaded URL %s" % request.url)
                    papiaccess.response_successful = True
                    try:
                        parsed_results = self.process_query_result(request.text, query)
                        results.extend(parsed_results.entries)  # Retrieve the processed results
                        queries.extend(parsed_results.queries)  # Add queries that were added as a result of the parsing, e.g. when the next result page should also be loaded
                        self.handle_provider_success()
                    except Exception as e:
                        self.logger.exception("Error while processing search results from provider %s" % self, e)
                        raise ProviderResultParsingException("Error while parsing the results from provider", self)
            except ProviderAuthException as e:
                self.logger.error("Unable to authorize with %s: %s" % (e.search_module, e.message))
                papiaccess.error = "Authorization error :%s" % e.message
                self.handle_provider_failure(reason="Authentication failed", disable_permanently=True)
            except ProviderAccessException as e:
                self.logger.error("Unable to access %s: %s" % (e.search_module, e.message))
                papiaccess.error = "Access error :%s" % e.message
                self.handle_provider_failure(reason="Access failed")
            except ProviderResultParsingException as e:
                papiaccess.error = "Access error :%s" % e.message
                self.handle_provider_failure(reason="Parsing results failed")
            except Exception as e:
                self.logger.exception("An error error occurred while searching: %s", e)
                papiaccess.error = "Unknown error :%s" % e
            finally:
                papiaccess.save()
                psearch.results = len(results)
                psearch.successful = True
                psearch.save()
        return ResultsAndProviderSearchDbEntry(results=results, dbentry=psearch)

      


def get_instance(provider):
    return SearchModule(provider)
