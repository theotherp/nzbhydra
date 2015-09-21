import calendar
import datetime
import email
import time
from furl import furl
from datestuff import now
from nzb_search_result import NzbSearchResult
from search_module import SearchModule

#Probably only as RSS supply, not for searching. Will need to do a (config) setting defining that. When searches without specifier are done we can include indexers like that
class Womble(SearchModule):
    
    #TODO init of config which is dynmic with its path
    
    def __init__(self, config_section):
        super(Womble, self).__init__(config_section)
        self.module_name = "womble"
        self.name = config_section.get("name", "Womble's NZB Index")
        self.query_url = config_section.get("query_url", "http://www.newshost.co.za/rss/")
        self.base_url = config_section.get("base_url", "http://www.newshost.co.za/")
        self.search_types = ["tv"] #will need to check this but I think is mainly/only used for tv shows
        self.supports_queries = config_section.get("supports_queries", False) #Only as support for general tv search
        
    def build_base_url(self):
        url = furl(self.query_url)
        return url

    def get_search_urls(self, query, categories=None):
        f = self.build_base_url("search").add({"s": query})
        return [f.url]

    def get_showsearch_urls(self, identifier=None, season=None, episode=None, categories=None):
        return []
        

    def get_moviesearch_urls(self, identifier=None, categories=None):
        return []

    def process_query_result(self, json_response):
        return []


def get_instance(config_section):
    return Womble(config_section)
