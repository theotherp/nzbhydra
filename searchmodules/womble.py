import logging
import re
import arrow
from furl import furl
import xml.etree.ElementTree as ET
from nzb_search_result import NzbSearchResult

from search_module import SearchModule

logger = logging.getLogger('root')


# Probably only as RSS supply, not for searching. Will need to do a (config) setting defining that. When searches without specifier are done we can include indexers like that
class Womble(SearchModule):
    # TODO init of config which is dynmic with its path

    def __init__(self, provider):
        super(Womble, self).__init__(provider)
        self.module = "womble"
        self.name = "Womble's NZB Index"
        
        self.getsettings["generate_queries"] = False #Doesn't matter because supports_queries is False
        self.needs_queries = False
        self.needs_queries = False # Doesn't even allow them
        self.category_search = True #Same
        self.supports_queries = False  # Only as support for general tv search

    def build_base_url(self):
        url = furl(self.query_url).add({"fr": "false"})
        return url

    def get_search_urls(self, query, categories=None):
        raise NotImplementedError("This provider does not support queries")

    def get_showsearch_urls(self, query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
        urls = []
        if identifier_key or season or episode:
            raise NotImplementedError("This provider does not support specific searches")
        if categories:
            for c in categories:
                if c in (5000, 5020):  # all
                    urls.append(self.build_base_url().tostr())
                if c == 5030:  # SD
                    urls.append(self.build_base_url().add({"sec": "tv-dvd"}).tostr())
                    urls.append(self.build_base_url().add({"sec": "tv-sd"}).tostr())
                if c == 5040:  # HD
                    urls.append(self.build_base_url().add({"sec": "tv-x264"}).tostr())
                    urls.append(self.build_base_url().add({"sec": "tv-hd"}).tostr())
        else:
            urls.append(self.build_base_url().tostr())
        return urls

    def get_moviesearch_urls(self, identifier=None, title=None, categories=None):
        raise NotImplementedError("This provider does not movie search")

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
            entry.title = title.text
            entry.link = url.attrib["url"]
            
            p = re.compile("(.*)\(Size:(\d*)")
            m = p.search(elem.find("description").text)
            if m:
                entry.description = m.group(1)
                entry.size = int(m.group(2)) * 1024 * 1024 #megabyte to byte
            if elem.find("category").text == "TV-DVDRIP":
                entry.category = 5030
            elif elem.find("category").text == "TV-x264":
                entry.category = 5040
            else:
                entry.category = 0 #undefined
                
            entry.guid = elem.find("guid").text
            
            pubdate = arrow.get(pubdate.text, 'M/DD/YYYY h:mm:ss A')
            entry.epoch = pubdate.timestamp
            entry.pubdate_utc = str(pubdate)
            entry.age_days = (arrow.utcnow() - pubdate).days
             
            entries.append(entry)
            
        return {"entries": entries, "queries": []}


def get_instance(provider):
    return Womble(provider)
