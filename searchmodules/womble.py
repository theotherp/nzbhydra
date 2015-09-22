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

    def __init__(self, config_section):
        super(Womble, self).__init__(config_section)
        self.module_name = "womble"
        self.name = config_section.get("name", "Womble's NZB Index")
        self.query_url = config_section.get("query_url", "http://www.newshost.co.za/rss/")
        self.base_url = config_section.get("base_url", "http://www.newshost.co.za/")
        self.search_types = ["tv"]  # will need to check this but I think is mainly/only used for tv shows
        self.supports_queries = config_section.get("supports_queries", False)  # Only as support for general tv search
        self.search_ids = config_section.get("search_ids", [])

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
                if c in (5000, 5020):  # SD
                    urls.append(self.build_base_url().tostr())
                if c == 5030:  # SD
                    urls.append(self.build_base_url().add({"sec": "tv-dvd"}).tostr())
                if c == 5040:  # HD
                    urls.append(self.build_base_url().add({"sec": "tv-x264"}).tostr())
        else:
            urls.append(self.build_base_url().tostr())
        return urls

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
            pubDate = elem.find("pubDate")
            if title is None or url is None or pubDate is None:
                continue
            
            entry = NzbSearchResult()
            entry.title = title.text
            entry.url = url.attrib["url"]
            
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
            
            pubDate = arrow.get(pubDate.text, 'M/DD/YYYY h:mm:ss A')
            entry.epoch = pubDate.timestamp
            entry.pubdate_utc = str(pubDate)
            entry.age_days = (arrow.utcnow() - pubDate).days
             
            entries.append(entry)
            
        return entries


def get_instance(config_section):
    return Womble(config_section)
