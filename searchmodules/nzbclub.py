import logging
import re
import arrow
from furl import furl
import xml.etree.ElementTree as ET
from nzb_search_result import NzbSearchResult

from search_module import SearchModule

logger = logging.getLogger('root')


# Probably only as RSS supply, not for searching. Will need to do a (config) setting defining that. When searches without specifier are done we can include indexers like that
class NzbClub(SearchModule):
    # TODO init of config which is dynmic with its path

    def __init__(self, config_section):
        super(NzbClub, self).__init__(config_section)
        self.module_name = "nzbclub"
        self.name = "NZBClub"
        self.query_url = config_section.get("query_url", "https://member.nzbclub.com/nzbfeeds.aspx")
        self.base_url = config_section.get("base_url", "https://member.nzbclub.com")
        self.search_types = ["general"]  
        self.supports_queries = config_section.get("supports_queries", True)  
        self.search_ids = config_section.get("search_ids", [])
        self.max_results = config_section.get("max_results", 100)
        

    def build_base_url(self):
        url = furl(self.query_url).add({"ig": "2", "rpp": self.max_results, "st": 5, "ns": 1, "sn":1}) #I need to find out wtf these values are
        return url

    def get_search_urls(self, query, categories=None):
        return [self.build_base_url().add({"q": query}).tostr()]

    def get_showsearch_urls(self, query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
        raise NotImplementedError("This provider does not support queries")


    def get_moviesearch_urls(self, identifier=None, title=None, categories=None):
        raise NotImplementedError("This provider does not movie search")

    def process_query_result(self, xml):
        entries = []
        try:
            tree = ET.fromstring(xml)
        except Exception:
            logger.exception("Error parsing XML")
            return []
        for elem in tree.iter('item'):
            title = elem.find("title")
            url = elem.find("enclosure")
            pubdate = elem.find("pubDate")
            if title is None or url is None or pubdate is None:
                continue
            
            entry = NzbSearchResult()
            entry.title = title.text
            entry.link = url.attrib["url"]
            entry.size = int(url.attrib["length"])
            entry.provider = self.name
            #todo category
            entry.category = 0 #undefined
                
            entry.guid = elem.find("guid").text
            
            entry.pubDate = pubdate.text
            pubdate = arrow.get(pubdate.text, '"ddd, DD MMM YYYY HH:mm:ss Z')
            entry.epoch = pubdate.timestamp
            entry.pubdate_utc = str(pubdate)
            entry.age_days = (arrow.utcnow() - pubdate).days
             
            entries.append(entry)
            
        return entries


def get_instance(config_section):
    return NzbClub(config_section)
