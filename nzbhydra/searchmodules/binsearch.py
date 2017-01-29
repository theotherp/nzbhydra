from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import urlparse
from sets import Set

from builtins import super
from builtins import str
from builtins import int
from builtins import *
from future import standard_library
#standard_library.install_aliases()
import logging
import re

import arrow
from bs4 import BeautifulSoup
from furl import furl

from nzbhydra import config
from nzbhydra.categories import getUnknownCategory
from nzbhydra.exceptions import IndexerResultParsingException, IndexerAccessException, IndexerResultParsingRowException

from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule, IndexerProcessingResult

logger = logging.getLogger('root')


class Binsearch(SearchModule):
    title_pattern = re.compile(r'"(.*)\.(rar|nfo|mkv|par2|001|nzb|url|zip|r[0-9]{2})"')
    size_pattern = re.compile(r"size: (?P<size>[0-9]+(\.[0-9]+)?).(?P<unit>(GB|MB|KB|B))")
    poster_pattern = re.compile(r"&p=(.*)&")
    goup_pattern = re.compile(r"&g=([\w\.]*)&")
    nfo_pattern = re.compile(r"\d nfo file")
    
    def __init__(self, settings):
        super(Binsearch, self).__init__(settings)
        self.module = "Binsearch"
        self.supports_queries = True  # We can only search using queries
        self.needs_queries = True
        self.category_search = False
        self.last_results_count = 0
        self.supportedFilters = ["minsize", "maxsize", "maxage"]
        self.supportsNot = False

    def build_base_url(self, offset=0):
        f = furl(self.host)
        f.path.add("index.php")
        url = f.add({"max": self.limit,
                     "adv_col": "on",  # collections only 
                     "postdate": "date",  # show pubDate, not age
                     # "adv_nfo": "off", #if enabled only show results with nfo file #todo make configurable. setting it to off doesnt work, its still done
                     "adv_sort": "date",  # prefer the newest
                     "min": offset
                     })
        return url

    def get_search_urls(self, search_request):
        f = self.build_base_url(offset=search_request.offset).add({"q": search_request.query})
        if search_request.minsize:
            f = f.add({"xminsize": search_request.minsize})
        if search_request.maxsize:
            f = f.add({"xmaxsize": search_request.maxsize})
        if search_request.maxage:
            f = f.add({"adv_age": search_request.maxage})

        return [f.tostr()]

    def get_showsearch_urls(self, search_request):
        urls = []
        query = search_request.query
        if search_request.query:
            urls = self.get_search_urls(search_request)
        if search_request.season is not None:
            # Restrict query if  season and/or episode is given. Use s01e01 and 1x01 and s01 and "season 1" formats
            # binsearch doesn't seem to support "or" in searches, so create separate queries
            urls = []
            if search_request.episode is not None:
                if self.isNumber(search_request.episode):
                    search_request.query = "%s s%02de%02d" % (query, search_request.season, search_request.episode)
                    urls.extend(self.get_search_urls(search_request))
                    search_request.query = "%s %dx%02d" % (query, search_request.season, search_request.episode)
                    urls.extend(self.get_search_urls(search_request))
                else:
                    search_request.query = '%s "%s %s"' % (search_request.query, search_request.season, search_request.episode.replace("/", " "))
                    self.debug("Assuming we're searching for a daily show. Using query: " + search_request.query)
                    urls = self.get_search_urls(search_request)
            elif self.isNumber(search_request.season):
                search_request.query = "%s s%02d" % (query, search_request.season)
                urls.extend(self.get_search_urls(search_request))
                search_request.query = '%s "season %d"' % (query, search_request.season)
                urls.extend(self.get_search_urls(search_request))
        return urls

    def get_moviesearch_urls(self, search_request):
        return self.get_search_urls(search_request)
    
    def get_ebook_urls(self, search_request):
        if not search_request.query and (search_request.author or search_request.title):
            search_request.query = "%s %s" % (search_request.author if search_request.author else "", search_request.title if search_request.title else "")
        urls = []
        query = search_request.query
        search_request.query = query + " ebook"
        urls.extend(self.get_search_urls(search_request))
        search_request.query = query + " mobi"
        urls.extend(self.get_search_urls(search_request))
        search_request.query = query + " pdf"
        urls.extend(self.get_search_urls(search_request))
        search_request.query = query + " epub"
        urls.extend(self.get_search_urls(search_request))
        return urls

    def get_audiobook_urls(self, search_request):
        return self.get_search_urls(search_request)

    def get_comic_urls(self, search_request):
        return self.get_search_urls(search_request)

    def get_anime_urls(self, search_request):
        return self.get_search_urls(search_request)
    
    def get_details_link(self, guid):
        logger.info("Details for binsearch not yet implemented")
        #Unfortunately binsearch uses different GUIDs for downloading and detail links. We store the one for NZBs
        return None

    def process_query_result(self, html, searchRequest, maxResults=None):
        self.debug("Started processing results")
        logger.info("Last results count %d" % self.last_results_count)
                
        entries = Set([])
        countRejected = self.getRejectedCountDict()
        self.debug("Using HTML parser %s" % config.settings.searching.htmlParser)
        soup = BeautifulSoup(html, config.settings.searching.htmlParser)

        if "No results in most popular groups" in soup.text:
            logger.info("No results found for query")
            return IndexerProcessingResult(entries=[], queries=[], total_known=0, has_more=False, total=0, rejected=self.getRejectedCountDict())
        main_table = soup.find('table', attrs={'id': 'r2'})

        if not main_table:
            self.debug(html[:500])
            raise IndexerResultParsingException("Unable to find main table in binsearch page. This happens sometimes... :-)", self)

        items = main_table.find_all('tr')
        
        for row in items:
            try:
                entry = self.parseRow(row)
            except IndexerResultParsingRowException:
                continue
            accepted, reason, ri = self.accept_result(entry, searchRequest, self.supportedFilters)
            if accepted:
                entries.add(entry)
            else:
                countRejected[ri] += 1
                self.debug("Rejected search result. Reason: %s" % reason)
            
        self.debug("Finished processing %d results" % len(entries))
        
        page_links = soup.find_all('table', attrs={'class': 'xMenuT'})[1].find_all("a")
        has_more = len(page_links) > 0 and page_links[-1].text == ">"
        total_known = False
        total = 100
        if len(page_links) == 0:
            m = re.compile(r".* (\d+)\+? records.*").search(soup.find_all('table', attrs={'class': 'xMenuT'})[1].text)
            if m:
                total = int(m.group(1))
                total_known = True
        
        return IndexerProcessingResult(entries=entries, queries=[], total_known=total_known, has_more=has_more, total=total, rejected=countRejected)
    
    def parseRow(self, row):
        entry = self.create_nzb_search_result()
        title = row.find('span', attrs={'class': 's'})

        if title is None:
            self.debug("Ignored entry because it has no title")
            raise IndexerResultParsingRowException("No title found")
        title = title.text

        if "password protect" in title.lower() or "passworded" in title.lower():
            entry.passworded = True

        m = self.title_pattern.search(title)
        if m:
            entry.title = m.group(1)
        else:
            entry.title = title

        entry.indexerguid = row.find("input", attrs={"type": "checkbox"})["name"]
        entry.link = self.get_nzb_link(entry.indexerguid, None)
        info = row.find("span", attrs={"class": "d"})
        if info is None:
            self.debug("Ignored entry because it has no info")
            raise IndexerResultParsingRowException("No info found")

        collection_link = info.find("a")["href"]  # '/?b=MARVELS.AVENGERS.AGE.OF.ULTRON.3D.TOPBOT.TrueFrench.1080p.X264.A&g=alt.binaries.movies.mkv&p=Ramer%40marmer.com+%28Clown_nez%29&max=250'
        entry.details_link = "%s%s" % (self.host, collection_link)
        m = self.goup_pattern.search(collection_link)
        if m:
            entry.group = m.group(1).strip()

        m = self.poster_pattern.search(collection_link)
        if m:
            poster = m.group(1).strip()
            try:
                entry.poster = urlparse.unquote(poster).replace("+", " ")
            except UnicodeDecodeError:
                logger.debug("Unable to decode poster from %s" % poster)
                entry.poster = None

        # Size
        m = self.size_pattern.search(info.text)
        if not m:
            self.debug("Unable to find size information in %s" % info.text)
        else:
            size = float(m.group("size"))
            unit = m.group("unit")
            if unit == "GB":
                size = size * 1024 * 1024 * 1024
            elif unit == "KB":
                size *= 1024
            elif unit == "MB":
                size = size * 1024 * 1024

            entry.size = int(size)

        entry.category = getUnknownCategory()

        if self.nfo_pattern.search(info.text):  # 1 nfo file is missing if there is no NFO
            entry.has_nfo = NzbSearchResult.HAS_NFO_YES
        else:
            entry.has_nfo = NzbSearchResult.HAS_NFO_NO

        # Age
        try:
            pubdate = re.compile(r"(\d{1,2}\-\w{3}\-\d{4})").search(row.text).group(1)
            pubdate = arrow.get(pubdate, "DD-MMM-YYYY")
            entry.epoch = pubdate.timestamp
            self.getDates(entry, pubdate, False)
        except Exception as e:
            self.error("Unable to find age in %s" % row.find_all("td")[-1:][0].text)
            raise IndexerResultParsingRowException("Unable to parse age")
        return entry

        

    def get_nfo(self, guid):
        f = furl(self.host)
        f.path.add("viewNFO.php")
        f.add({"oid": guid})
        r, papiaccess, _ = self.get_url_with_papi_access(f.tostr(), "nfo")
        if r is not None:
            html = r.text
            p = re.compile(r"<pre>(?P<nfo>.*)<\/pre>", re.DOTALL)
            m = p.search(html)
            if m:
                return True, m.group("nfo"), None
        return False, None, None
    
    def get_nzb_link(self, guid, title):
        f = furl(self.host + "/")
        f.add({"action": "nzb", guid: "1"})
        return f.tostr()
    
    def check_auth(self, body):
        if "The search service is temporarily unavailable" in body:
            raise IndexerAccessException("The search service is temporarily unavailable.", self)


    

def get_instance(settings):
    return Binsearch(settings)
