import json
from database import Provider


class SearchModule(object):
    # regarding quality:
    # possibly use newznab qualities as base, map for other providers (nzbclub etc)


    def __init__(self, provider):
        self.provider = provider  # Database object of this module
        self.name = self.provider.name
        self.module = "Abstract search module"
        
        self.generate_queries = provider.generate_queries  # If true and a search by movieid or tvdbid or rid is done then we attempt to find the title and generate queries for providers which don't support id-based searches
        
        self.supports_queries = True
        self.needs_queries = False
        self.category_search = True  # If true the provider supports searching in a given category (possibly without any query or id)
    
    @property
    def query_url(self):
        return self.provider.query_url
        
    @property
    def base_url(self):
        return self.provider.base_url
    
    @property
    def settings(self):
        return self.provider.settings
        
    @property
    def search_types(self):
        return self.provider.search_types
    
    @property
    def search_ids(self):
        return self.provider.search_ids
    


    # Access to most basic functions
    def get_search_urls(self, query):
        # return url(s) to search. Url is then retrieved and result is returned if OK
        # we can return multiple urls in case a module needs to make multiple requests (e.g. when searching for a show
        # using general queries
        pass

    def get_showsearch_urls(self, query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
        # to extend
        # if module supports it, search specifically for show, otherwise make sure we create a query that searches
        # for for s01e01, 1x1 etc
        pass

    def get_moviesearch_urls(self, query=None, identifier_key=None, identifier_value=None, categories=None):
        # to extend
        # if module doesnt support it possibly use (configurable) size restrictions when searching
        pass

    def process_query_result(self, result):
        return []

    def check_auth(self, body=""):
        # check the response body to see if request was authenticated. If yes, do nothing, if no, raise exception 
        pass

    def get_nfo(self, guid):
        pass

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
