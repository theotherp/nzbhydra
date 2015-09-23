needs_config = False


class SearchModule(object):
    # regarding quality:
    # possibly use newznab qualities as base, map for other providers (nzbclub etc)


    def __init__(self, config_section):
        self.module_name = "Abstract search module"
        self.config = config_section
        self.search_types = ["tv", "movie", "general"]  # todo: init settings like this that are only used in subsections
        self.supports_queries = True
        self.search_ids = [] #"tvdbid", "rid", "imdbid"
        self.search_types = config_section.get("search_types", ["general", "tv", "movie"])
        self.supports_queries = config_section.get("supports_queries", True)
        self.search_ids = config_section.get("search_ids", ["tvdbid", "rid", "imdbid"])
        self.generate_queries = config_section.get("generate_queries", True)#If true and a search by movieid or tvdbid or rid is done then we attempt to find the title and generate queries for providers which don't support id-based searches
        self.category_search = config_section.get("category_search", False) #If true the provider supports searching in a given category (possibly without any query or id)

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
        #check the response body to see if request was authenticated. If yes, do nothing, if no, raise exception 
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
