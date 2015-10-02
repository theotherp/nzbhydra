import json
import logging
import re
import arrow
from furl import furl
import xml.etree.ElementTree as ET
from nzbhydra.exceptions import ProviderIllegalSearchException
from nzbhydra.nzb_search_result import NzbSearchResult

from nzbhydra.search_module import SearchModule

logger = logging.getLogger('root')


class NzbClub(SearchModule):
    # TODO init of config which is dynmic with its path

    def __init__(self, provider):
        super(NzbClub, self).__init__(provider)
        self.module = "nzbclub"
        self.name = "NZBClub"
        
        self.supports_queries = True #We can only search using queries
        self.needs_queries = True
        self.category_search = False
        #https://www.nzbclub.com/nzbrss.aspx
        
    @property
    def max_results(self):
        return self.getsettings.get("max_results", 250)
        

    def build_base_url(self):
        url = furl(self.query_url).add({"ig": "2", "rpp": self.max_results, "st": 5, "ns": 1, "sn": 1}) #I need to find out wtf these values are
        return url

    def get_search_urls(self, query=None, generated_query=None, category=None):
        return [self.build_base_url().add({"q": query}).tostr()]

    def get_showsearch_urls(self, query=None, generated_query=None, identifier_key=None, identifier_value=None, season=None, episode=None, category=None):
        if query is None and generated_query is None:
            raise ProviderIllegalSearchException("Attempted to search without a query although this provider only supports query-based searches", self)
        if generated_query and season is not None:
            #Restrict query if generated and season and/or episode is given. Use s01e01 and 1x01 and s01 and "season 1" formats
            if episode is not None:
                generated_query = "%s s%02de%02d or %s %dx%02d" % (generated_query, season, episode, generated_query, season, episode)
            else:
                generated_query = '%s s%02d or %s "season %d"' % (generated_query, season, generated_query, season)
        return self.get_search_urls(query if query else generated_query, category)


    def get_moviesearch_urls(self, query=None, generated_query=None, identifier_key=None, identifier_value=None, category=None):
        if query is None and generated_query is None:
            raise ProviderIllegalSearchException("Attempted to search without a query although this provider only supports query-based searches", self)
        return self.get_search_urls(query if query else generated_query, category)

    def process_query_result(self, xml, query):
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
            p = re.compile(r'"(.*)"') 
            m = p.search(title.text)
            if m:
                entry.title = m.group(1)
            else:
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
            
        return {"entries": entries, "queries": []}


def get_instance(provider):
    return NzbClub(provider)
