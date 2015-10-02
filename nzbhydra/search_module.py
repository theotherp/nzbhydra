import logging
import arrow
import requests
from nzbhydra import config
from nzbhydra.database import ProviderSearch, ProviderApiAccess, ProviderSearchApiAccess, ProviderStatus
from nzbhydra.exceptions import ProviderConnectionException, ProviderResultParsingException, ProviderAuthException, ProviderAccessException


class SearchModule(object):
    logger = logging.getLogger('root')
    # regarding quality:
    # possibly use newznab qualities as base, map for other providers (nzbclub etc)


    def __init__(self, provider):
        self.provider = provider  # Database object of this module
        self.name = self.provider.name
        self.module = "Abstract search module"
        self.supports_queries = True
        self.needs_queries = False
        self.category_search = True  # If true the provider supports searching in a given category (possibly without any query or id)

    @property
    def query_url(self):
        return self.provider.settings.get("query_url")

    @property
    def base_url(self):
        return self.provider.settings.get("base_url")

    @property
    def getsettings(self):
        return self.provider.settings

    @property
    def search_types(self):
        return self.provider.settings.get("search_types", [])

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

    # Access to most basic functions
    def get_search_urls(self, query=None, generated_query=None):
        # return url(s) to search. Url is then retrieved and result is returned if OK
        # we can return multiple urls in case a module needs to make multiple requests (e.g. when searching for a show
        # using general queries
        pass

    def get_showsearch_urls(self, query=None, generated_query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
        # to extend
        # if module supports it, search specifically for show, otherwise make sure we create a query that searches
        # for for s01e01, 1x1 etc
        pass

    def get_moviesearch_urls(self, query=None, generated_query=None, identifier_key=None, identifier_value=None, categories=None):
        # to extend
        # if module doesnt support it possibly use (configurable) size restrictions when searching
        pass

    def process_query_result(self, result, query):
        return []

    def check_auth(self, body=""):
        # check the response body to see if request was authenticated. If yes, do nothing, if no, raise exception 
        pass

    def get_nfo(self, guid):
        pass
    
    disable_periods = [0, 15, 30, 60, 3 * 60, 6 * 60, 12 * 60, 24 * 60]


    def handle_provider_success(self):
        #Deescalate level by 1 (or stay at 0) and reset reason and disable-time
        try:
            provider_status = self.provider.status.get()
        except ProviderStatus.DoesNotExist:
            provider_status = ProviderStatus(provider=self.provider)
        if provider_status.level > 0:
            provider_status.level -= 1
        provider_status.reason = None
        provider_status.disabled_until = arrow.get(0) #Because I'm too dumb to set it to None/null
        provider_status.save()
    
    
    def handle_provider_failure(self, reason=None, disable_permanently=False):
        #Escalate level by 1. Set disabled-time according to level so that with increased level the time is further in the future
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
        
        
    def execute_queries(self, queries):
        # todo call all queries, check if further should be called, return all results when done or timeout or whatever
        results = []
        executed_queries = set()
        while len(queries) > 0:
            query = queries.pop()
            if query in executed_queries:
                #To make sure that in case an offset is reported wrong or we have a bug we don't get stuck in an endless loop 
                continue
            try:
                psearch = ProviderSearch(provider=self.provider, query=query)
                psearch.save()
                papiaccess = ProviderApiAccess(provider=self.provider, type="search")
                self.logger.debug("Requesting URL %s with timeout %d" % (query, config.cfg["searching.timeout"]))  
                executed_queries.add(query)
                request = requests.get(query, timeout=config.cfg["searching.timeout"], verify=False)          
                papiaccess.save()
                ProviderSearchApiAccess(search=psearch, api_access=papiaccess).save()  # So we can later see which/how many accesses the search caused and how they went
                
                papiaccess.response_time = request.elapsed.microseconds / 1000
                if request.status_code != 200:
                    raise ProviderConnectionException("Unable to connect to provider. Status code: %d" % request.status_code, self)
                else:
                    self.check_auth(request.text)
                    self.logger.debug("Successfully loaded URL %s" % request.url)
                    papiaccess.response_successful = True
    
                    try:
                        parsed_results = self.process_query_result(request.text, query)
                        psearch.results = len(parsed_results["entries"])
                        results.extend(parsed_results["entries"]) #Retrieve the processed results
                        queries.extend(parsed_results["queries"])
                        psearch.successful = True
                        self.handle_provider_success()
                    except Exception as e:
                        self.logger.exception("Error while processing search results from provider %s" % self, e)
                        raise ProviderResultParsingException("Error while parsing the results from provider", self)
    
            except ProviderAuthException as e:
                self.logger.error("Unable to authorize with %s: %s" % (e.search_module, e.message))
                papiaccess.error = "Authorization error :%s" % e.message
                self.handle_provider_failure(reason="Authentication failed", disable_permanently=True)
    
            except ProviderConnectionException as e:
                self.logger.error("Unable to connect with %s: %s" % (e.search_module, e.message))
                papiaccess.error = "Connection error :%s" % e.message
                self.handle_provider_failure(reason="Connection failed")
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
            psearch.save()
            papiaccess.save()
        return results

        # information, perhaps if we provide basic information, get the info link for a uid, get base url, etc

        # define config, what settings we expect in the config
        # config could be:
        #   enable for api
        #   priority score
        #   base url
        #   search url?
        #   enabled for which search types?
        #
        #   to be extended by e.g. newznab, for example apikey


def get_instance(provider):
    return SearchModule(provider)
