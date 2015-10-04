import logging
import re
import xml.etree.ElementTree as ET

import arrow

from furl import furl
import requests

from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule

logger = logging.getLogger('root')


class NzbClub(SearchModule):
    # TODO init of config which is dynmic with its path

    def __init__(self, provider):
        super(NzbClub, self).__init__(provider)
        self.module = "nzbclub"
        self.name = "NZBClub"

        self.supports_queries = True  # We can only search using queries
        self.needs_queries = True
        self.category_search = False

    @property
    def max_results(self):
        return self.getsettings.get("max_results", 250)

    def build_base_url(self):
        url = furl(self.query_url).add({"ig": "2", "rpp": self.max_results, "st": 5, "ns": 1, "sn": 1})  # I need to find out wtf these values are
        return url

    def get_search_urls(self, args):
        f = self.build_base_url().add({"q": args["query"]})
        return [f.tostr()]

    def get_showsearch_urls(self, args):
        if args["season"] is not None:
            # Restrict query if season and/or episode is given. Use s01e01 and 1x01 and s01 and "season 1" formats
            if args["episode"] is not None:
                args["query"] = "%s s%02de%02d or %s %dx%02d" % (args["query"], args["season"], args["episode"], args["query"], args["season"], args["episode"])
            else:
                args["query"] = '%s s%02d or %s "season %d"' % (args["query"], args["season"], args["query"], args["season"])
        return self.get_search_urls(args)

    def get_moviesearch_urls(self, args):
        return self.get_search_urls(args)

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
            entry.category = "N/A"

            entry.guid = elem.find("guid").text[-8:] #GUID looks like "http://www.nzbclub.com/nzb_view58556415" of which we only want the last part
            
            description = elem.find("description").text
            if re.compile(r"\d NFO Files").search(description): # [x NFO Files] is missing if there is no NFO
                entry.has_nfo = True
            else:
                entry.has_nfo = False

            entry.pubDate = pubdate.text
            pubdate = arrow.get(pubdate.text, '"ddd, DD MMM YYYY HH:mm:ss Z')
            entry.epoch = pubdate.timestamp
            entry.pubdate_utc = str(pubdate)
            entry.age_days = (arrow.utcnow() - pubdate).days

            entries.append(entry)

        return {"entries": entries, "queries": []}
    
    def get_nfo(self, guid):
        f = furl(self.base_url)
        f.path.add("api/NFO")
        f.path.segments.append(guid)
        r, papiaccess = self.get_url_with_papi_access(f.tostr(), "nfo")
        if r is not None:
            r.raise_for_status()
            if r.json()["Count"] == 0:
                return None
            return r.json()["Data"][0]["NFOContentData"]
        
    def get_nzb_link(self, guid, title):
        f = furl(self.base_url)
        f.path.add("nzb_get")
        f.path.add("guid")
        f.path.add("title" + ".nzb")
        return f.tostr()
        

def get_instance(provider):
    return NzbClub(provider)
