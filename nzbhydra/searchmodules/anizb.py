from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import super
from builtins import str
from builtins import int
from future import standard_library
#standard_library.install_aliases()
from builtins import *
import logging
import re
import arrow
from furl import furl
import xml.etree.ElementTree as ET

from nzbhydra.categories import getUnknownCategory, getCategoryByName
from nzbhydra.exceptions import IndexerResultParsingException
from nzbhydra.nzb_search_result import NzbSearchResult

from nzbhydra.search_module import SearchModule, IndexerProcessingResult

logger = logging.getLogger('root')


class Anizb(SearchModule):

    def __init__(self, indexer):
        super(Anizb, self).__init__(indexer)
        self.module = "anizb"
        
        self.settings.generate_queries = True
        self.needs_queries = False
        self.category_search = True
        self.supports_queries = True  # Only as support for general tv search
        
        

    def build_base_url(self):
        f = furl(self.host)
        f.path.add("api")
        return f

    def get_search_urls(self, search_request):
        f = self.build_base_url()
        f = f.add({"q": search_request.query})
        return [f.tostr()]

    def get_showsearch_urls(self, search_request):
        self.error("This indexer does not support tv search")
        return []

    def get_moviesearch_urls(self, search_request):
        self.error("This indexer does not support movie search")
        return []

    def get_ebook_urls(self, search_request):
        self.error("This indexer does not support ebook search")
        return []

    def get_audiobook_urls(self, search_request):
        self.error("This indexer does not support audiobook search")
        return []

    def get_comic_urls(self, search_request):
        self.error("This indexer does not support comic search")
        return []

    def get_anime_urls(self, search_request):
        return self.get_search_urls(search_request)
    
    

    def process_query_result(self, xml, searchRequest, maxResults=None):
        entries = []
        countRejected = self.getRejectedCountDict()
        try:
            tree = ET.fromstring(xml)
        except Exception:
            self.exception("Error parsing XML: %s..." % xml[:500])
            logger.debug(xml)
            raise IndexerResultParsingException("Error parsing XML", self)
        for elem in tree.iter('item'):
            title = elem.find("title")
            url = elem.find("enclosure")
            pubdate = elem.find("pubDate")
            if title is None or url is None or pubdate is None:
                continue
            
            entry = self.create_nzb_search_result()
            entry.title = title.text
            entry.link = url.attrib["url"]
            entry.size = int(url.attrib["length"])
            entry.has_nfo = NzbSearchResult.HAS_NFO_NO
            entry.category = getCategoryByName("anime")
            entry.indexerguid = elem.find("guid").text 
            entry.details_link = entry.link.replace("dl", "info")
            pubdate = arrow.get(pubdate.text, 'ddd, DD MMM YYYY HH:mm:ss Z')
            self.getDates(entry, pubdate)

            accepted, reason, ri = self.accept_result(entry, searchRequest, self.supportedFilters)
            if accepted:
                entries.append(entry)
            else:
                countRejected[ri] += 1
                self.debug("Rejected search result. Reason: %s" % reason)
        
        return IndexerProcessingResult(entries=entries, queries=[], total_known=True, has_more=False, total=len(entries), rejected=countRejected)
    
    def get_nzb_link(self, guid, title):
        f = furl(self.settings.host)
        f.path.add("dl")
        f.path.add(guid)
        return f.tostr()


def get_instance(indexer):
    return Anizb(indexer)
