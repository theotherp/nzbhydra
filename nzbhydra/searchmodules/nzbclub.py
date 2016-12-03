from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urlparse
from collections import OrderedDict

from builtins import *
# standard_library.install_aliases()
import logging
import re
import xml.etree.ElementTree as ET

import arrow

from furl import furl

from nzbhydra.categories import getUnknownCategory
from nzbhydra.exceptions import IndexerResultParsingException, IndexerResultParsingRowException

from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule, IndexerProcessingResult

logger = logging.getLogger('root')


class NzbClub(SearchModule):
    group_pattern = re.compile(r"Newsgroup: ?([\w@\. \(\)]+) <br />")
    poster_pattern = re.compile(r"Poster: ?([\w@\. \(\)]+) <br />")
    
    def __init__(self, indexer):
        super(NzbClub, self).__init__(indexer)
        self.module = "NZBClub"

        self.supports_queries = True  # We can only search using queries
        self.needs_queries = True
        self.category_search = False
        self.max_results = 250
        self.supportedFilters = []  # Technically we do but we should still check every result because the defined values may lie between the ones supported by NZBClub
        self.supportsNot = True

        self.sizeMap = OrderedDict([
            (1, 8),
            (5, 9),
            (15, 10),
            (25, 11),
            (30, 12),
            (40, 13),
            (50, 14),
            (75, 15),
            (100, 16),
            (200, 17),
            (300, 18),
            (400, 19),
            (500, 20),
            (750, 21),
            (1 * 1024, 22),
            (2 * 1024, 23),
            (4 * 1024, 24),
            (5 * 1024, 25),
            (6 * 1024, 26),
            (7 * 1024, 27),
            (8 * 1024, 28),
            (9 * 1024, 29),
            (10 * 1024, 30),
            (11 * 1024, 31),
            (12 * 1024, 32),
            (13 * 1024, 33),
            (14 * 1024, 34),
            (15 * 1024, 35),
            (16 * 1024, 36),
            (17 * 1024, 37),
            (18 * 1024, 38),
            (19 * 1024, 39),
            (20 * 1024, 40)
        ])

        self.ageMap = OrderedDict([
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
            (5, 5),
            (6, 6),
            (1 * 7, 7),
            (2 * 7, 8),
            (3 * 7, 9),
            (4 * 7, 10),
            (1 * 31, 11),
            (2 * 31, 12),
            (3 * 31, 13),
            (4 * 31, 14),
            (5 * 31, 15),
            (6 * 31, 16),
            (7 * 31, 17),
            (8 * 31, 18),
            (9 * 31, 19),
            (10 * 31, 20),
            (11 * 31, 21),
            (12 * 31, 22),
            (13 * 31, 23),
            (14 * 31, 24),
            (15 * 31, 25),
            (16 * 31, 26),
            (17 * 31, 27)
        ])

    def build_base_url(self):
        f = furl(self.host)
        f.path.add("nzbrss.aspx")
        url = f.add({"ig": "2", "rpp": self.max_results, "st": 5, "ns": 1, "sn": 1})  # I need to find out wtf these values are

        return url

    def get_search_urls(self, search_request):
        query = search_request.query
        if query:
            for word in search_request.forbiddenWords:
                word = word.strip().lower()
                if "-" in word or " " in word:
                    logger.debug('Not using ignored word "%s" in query because it contains a space or dash which is not supported by newznab queries' % word)
                    continue
                query += " -" + word
        f = self.build_base_url().add({"q": query})
        if search_request.minage:
            ageValue = self.getMinValue(search_request.minage, self.ageMap)
            f.query.add({"ds": ageValue})
        if search_request.maxage:
            ageValue = self.getMaxValue(search_request.maxage, self.ageMap)
            if ageValue is not None:
                f.query.add({"de": ageValue})
        if search_request.minsize:
            ageValue = self.getMinValue(search_request.minsize, self.sizeMap)
            f.query.add({"szs": ageValue})
        if search_request.maxsize:
            ageValue = self.getMaxValue(search_request.maxsize, self.sizeMap)
            if ageValue is not None:
                f.query.add({"sze": ageValue})

        return [f.tostr()]

    def getMinValue(self, wanted, map):
        minageValue = None
        for key, value in map.iteritems():
            if key > wanted:
                break
            minageValue = value
        return minageValue

    def getMaxValue(self, wanted, map):
        minageValue = None
        skipped = False
        for key, value in map.iteritems():
            if key > wanted:
                if skipped:
                    break
                else:
                    skipped = True
            minageValue = value
        else:
            return None
        return minageValue

    def get_showsearch_urls(self, search_request):
        if search_request.season is not None:
            # Restrict query if season and/or episode is given. Use s01e01 and 1x01 and s01 and "season 1" formats
            if search_request.episode is not None:
                if self.isNumber(search_request.episode):
                    search_request.query = "%s s%02de%02d or %s %dx%02d" % (search_request.query, search_request.season, search_request.episode, search_request.query, search_request.season, search_request.episode)
                else:
                    search_request.query = '%s "%s %s"' % (search_request.query, search_request.season, search_request.episode.replace("/", " "))
                    self.debug("Assuming we're searching for a daily show. Using query: " + search_request.query)
            elif self.isNumber(search_request.season):
                search_request.query = '%s s%02d or %s "season %d"' % (search_request.query, search_request.season, search_request.query, search_request.season)
        return self.get_search_urls(search_request)

    def get_moviesearch_urls(self, search_request):
        return self.get_search_urls(search_request)

    def get_ebook_urls(self, search_request):
        if not search_request.query and (search_request.author or search_request.title):
            search_request.query = "%s %s" % (search_request.author if search_request.author else "", search_request.title if search_request.title else "")
        query = search_request.query
        search_request.query = "%s ebook or %s mobi or %s pdf or %s epub" % (query, query, query, query)
        return self.get_search_urls(search_request)

    def get_audiobook_urls(self, search_request):
        return self.get_search_urls(search_request)

    def get_comic_urls(self, search_request):
        return self.get_search_urls(search_request)

    def get_anime_urls(self, search_request):
        return self.get_search_urls(search_request)

    def get_details_link(self, guid):
        f = furl(self.host)
        f.path.add("nzb_view")
        f.path.add(guid)
        return f.url

    def process_query_result(self, xml, searchRequest, maxResults=None):
        self.debug("Started processing results")
        entries = []
        countRejected = self.getRejectedCountDict()
        try:
            tree = ET.fromstring(xml)
        except Exception:
            self.exception("Error parsing XML: %s..." % xml[:500])
            self.debug(xml[:500])
            raise IndexerResultParsingException("Error while parsing XML from NZBClub", self)

        
        for item in tree.iter('item'):
            try:
                entry = self.parseItem(item)
            except IndexerResultParsingRowException:
                continue

            accepted, reason, ri = self.accept_result(entry, searchRequest, self.supportedFilters)
            if accepted:
                entries.append(entry)
            else:
                countRejected[ri] += 1
                self.debug("Rejected search result. Reason: %s" % reason)

        self.debug("Finished processing results")
        return IndexerProcessingResult(entries=entries, queries=[], total=len(entries), total_known=True, has_more=False, rejected=countRejected)  # No paging with RSS. Might need/want to change to HTML and BS

    def parseItem(self, elem):
        title = elem.find("title")
        url = elem.find("enclosure")
        pubdate = elem.find("pubDate")
        if title is None or url is None or pubdate is None:
            raise IndexerResultParsingRowException("Unable to find title, url or date")
        entry = self.create_nzb_search_result()
        if "password protect" in title.text.lower() or "passworded" in title.text.lower():
            entry.passworded = True
        p = re.compile(r'"(.*)"')
        m = p.search(title.text)
        if m:
            entry.title = m.group(1)
        else:
            entry.title = title.text
        entry.link = url.attrib["url"]
        entry.size = int(url.attrib["length"])
        entry.indexer = self.name
        entry.category = getUnknownCategory()
        entry.details_link = elem.find("link").text
        entry.indexerguid = elem.find("guid").text[-8:]  # GUID looks like "http://www.nzbclub.com/nzb_view58556415" of which we only want the last part
        description = elem.find("description").text
        description = urlparse.unquote(description).replace("+", " ")
        if re.compile(r"\d NFO Files").search(description):  # [x NFO Files] is missing if there is no NFO
            entry.has_nfo = NzbSearchResult.HAS_NFO_YES
        else:
            entry.has_nfo = NzbSearchResult.HAS_NFO_NO
        m = self.group_pattern.search(description)
        if m:
            entry.group = m.group(1).strip()
        m = self.poster_pattern.search(description)
        if m:
            entry.poster = m.group(1).strip()
        try:

            pubdate = arrow.get(pubdate.text, 'ddd, DD MMM YYYY HH:mm:ss Z')
            self.getDates(entry, pubdate)
        except Exception:
            self.error("Unable to parse pubdate %s" % pubdate.text)
            raise IndexerResultParsingRowException("Unable to parse date")
        return entry

    def get_nfo(self, guid):
        f = furl(self.settings.host)
        f.path.add("api/NFO")
        f.path.segments.append(guid)
        r, papiaccess, _ = self.get_url_with_papi_access(f.tostr(), "nfo")
        if r is not None:
            r.raise_for_status()
            if r.json()["Count"] == 0:
                return False, None, None
            return True, r.json()["Data"][0]["NFOContentData"], None

    def get_nzb_link(self, guid, title):
        f = furl(self.settings.host)
        f.path.add("nzb_get")
        f.path.add(guid)
        f.path.add(title + ".nzb")
        return f.tostr()


def get_instance(indexer):
    return NzbClub(indexer)
