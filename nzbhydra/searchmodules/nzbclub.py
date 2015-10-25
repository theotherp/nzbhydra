import logging
import re
import xml.etree.ElementTree as ET

import arrow

from furl import furl
import requests
from nzbhydra.exceptions import ProviderResultParsingException

from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule, ProviderProcessingResult

logger = logging.getLogger('root')


class NzbClub(SearchModule):
    

    def __init__(self, provider):
        super(NzbClub, self).__init__(provider)
        self.module = "nzbclub"

        self.supports_queries = True  # We can only search using queries
        self.needs_queries = True
        self.category_search = False
        self.max_results = 250
    
    

    def build_base_url(self):
        f = furl(self.host)
        f.path.add("nzbrss.aspx")
        url = f.add({"ig": "2", "rpp": self.max_results, "st": 5, "ns": 1, "sn": 1})  # I need to find out wtf these values are
        return url

    def get_search_urls(self, search_request):
        f = self.build_base_url().add({"q": search_request.query})
        return [f.tostr()]

    def get_showsearch_urls(self, search_request) -> ProviderProcessingResult:
        if search_request.season is not None:
            # Restrict query if season and/or episode is given. Use s01e01 and 1x01 and s01 and "season 1" formats
            if search_request.episode is not None:
                search_request.query = "%s s%02de%02d or %s %dx%02d" % (search_request.query, search_request.season, search_request.episode, search_request.query, search_request.season, search_request.episode)
            else:
                search_request.query = '%s s%02d or %s "season %d"' % (search_request.query, search_request.season, search_request.query, search_request.season)
        return self.get_search_urls(search_request)

    def get_moviesearch_urls(self, search_request):
        return self.get_search_urls(search_request)

    def process_query_result(self, xml, query):
        logger.debug("%s started processing results" % self.name)
        entries = []
        try:
            tree = ET.fromstring(xml)
        except Exception:
            logger.exception("Error parsing XML: %s..." % xml[:500])
            logger.debug(xml)
            raise ProviderResultParsingException("Error while parsing XML from NZBClub", self)
        
        group_pattern = re.compile(r"Newsgroup: ?([\w@\. \(\)]+) <br />")
        poster_pattern = re.compile(r"Poster: ?([\w@\. \(\)]+) <br />")
        for elem in tree.iter('item'):
            title = elem.find("title")
            url = elem.find("enclosure")
            pubdate = elem.find("pubDate")
            if title is None or url is None or pubdate is None:
                continue

            entry = self.create_nzb_search_result()
            p = re.compile(r'"(.*)"')
            m = p.search(title.text)
            if m:
                entry.title = m.group(1)
            else:
                entry.title = title.text

            entry.link = url.attrib["url"]
            entry.size = int(url.attrib["length"])
            entry.provider = self.name
            entry.category = "N/A"
            entry.details_link = elem.find("link").text

            entry.guid = elem.find("guid").text[-8:] #GUID looks like "http://www.nzbclub.com/nzb_view58556415" of which we only want the last part
            
            description = elem.find("description").text
            import urllib.parse
            description = urllib.parse.unquote(description).replace("+", " ")
            if re.compile(r"\d NFO Files").search(description): # [x NFO Files] is missing if there is no NFO
                entry.has_nfo = True
            else:
                entry.has_nfo = False
            m = group_pattern.search(description)
            if m:
                entry.group = m.group(1)
            m = poster_pattern.search(description)
            if m:
                entry.poster = m.group(1)

            entry.pubDate = pubdate.text
            pubdate = arrow.get(pubdate.text, '"ddd, DD MMM YYYY HH:mm:ss Z')
            entry.epoch = pubdate.timestamp
            entry.pubdate_utc = str(pubdate)
            entry.age_days = (arrow.utcnow() - pubdate).days

            entries.append(entry)
            
        logger.debug("%s finished processing results" % self.name)
        return ProviderProcessingResult(entries=entries, queries=[], total=len(entries), total_known=True, has_more=False) #No paging with RSS. Might need/want to change to HTML and BS
    
    def get_nfo(self, guid):
        f = furl(self.settings.host.get())
        f.path.add("api/NFO")
        f.path.segments.append(guid)
        r, papiaccess = self.get_url_with_papi_access(f.tostr(), "nfo")
        if r is not None:
            r.raise_for_status()
            if r.json()["Count"] == 0:
                return None
            return r.json()["Data"][0]["NFOContentData"]
        
    def get_nzb_link(self, guid, title):
        f = furl(self.settings.host.get())
        f.path.add("nzb_get")
        f.path.add("guid")
        f.path.add("title" + ".nzb")
        return f.tostr()
        

def get_instance(provider):
    return NzbClub(provider)
