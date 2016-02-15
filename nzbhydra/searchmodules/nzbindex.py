from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
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
from bs4 import BeautifulSoup

from furl import furl
import requests
from nzbhydra import config

from nzbhydra.exceptions import IndexerResultParsingException, IndexerAccessException
from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule, IndexerProcessingResult

logger = logging.getLogger('root')


# Probably only as RSS supply, not for searching. Will need to do a (config) setting defining that. When searches without specifier are done we can include indexers like that
class NzbIndex(SearchModule):
    def __init__(self, indexer):
        super(NzbIndex, self).__init__(indexer)
        self.module = "NZBIndex"

        self.supports_queries = True  # We can only search using queries
        self.needs_queries = True
        self.category_search = False

    def build_base_url(self):
        f = furl(self.host)
        f.path.add("search")
        f = f.add({"more": "1", "max": self.limit, "hidecross": 1})
        return f

    def get_search_urls(self, search_request):
        f = self.build_base_url().add({"q": search_request.query})
        if search_request.minsize:
            f = f.add({"minsize": search_request.minsize})
        elif config.settings.indexers.nzbindex.generalMinSize:
            f = f.add({"minsize": config.settings.indexers.nzbindex.generalMinSize})
        if search_request.maxsize:
            f = f.add({"maxsize": search_request.maxsize})
        if search_request.minage:
            f = f.add({"minage": search_request.minage})
        if search_request.maxage:
            f = f.add({"age": search_request.maxage})
        if search_request.offset > 0:
            f.query.params["p"] = int(search_request.offset / self.limit)
        return [f.tostr()]

    def get_showsearch_urls(self, search_request):
        if search_request.season is not None:
            # Restrict query if generated and season and/or episode is given. Use s01e01 and 1x01 and s01 and "season 1" formats
            if search_request.episode is not None:
                search_request.query = "%s s%02de%02d | %dx%02d" % (search_request.query, search_request.season, search_request.episode, search_request.season, search_request.episode)
            else:
                search_request.query = '%s s%02d | "season %d"' % (search_request.query, search_request.season, search_request.season)
        return self.get_search_urls(search_request)

    def get_moviesearch_urls(self, search_request):
        return self.get_search_urls(search_request)
    
    def get_details_link(self, guid):
        f = furl(self.host)
        f.path.add("release")
        f.path.add(guid)
        return f.url

    def get(self, query, timeout=None, cookies=None):
        # overwrite for special handling, e.g. cookies
        return requests.get(query, timeout=timeout, verify=False, cookies={"agreed": "true", "lang": "2"})


    def get_ebook_urls(self, search_request):
        #NZBIndex's search is a bit weird, apparently we can only use one "or" or something like that, so we use two different queries
        urls = []
        query = search_request.query
        search_request.query = query + " ebook | pdf"
        urls.extend(self.get_search_urls(search_request))
        search_request.query = query + " mobi | epub"
        urls.extend(self.get_search_urls(search_request))
        return urls

    def get_audiobook_urls(self, search_request):
        return self.get_search_urls(search_request)

    def process_query_result(self, html, maxResults=None):
        self.debug("Started processing results")

        entries = []
        logger.debug("Using HTML parser %s" % config.settings.searching.htmlParser)
        soup = BeautifulSoup(html, config.settings.searching.htmlParser)
        main_table = soup.find(id="results").find('table')

        if "No results found" in soup.text:
            return IndexerProcessingResult(entries=[], queries=[], total=0, total_known=True, has_more=False)
        if not main_table or not main_table.find("tbody"):
            self.error("Unable to find main table in NZBIndex page: %s..." % html[:500])
            self.debug(html[:500])
            raise IndexerResultParsingException("Unable to find main table in NZBIndex page", self)

        items = main_table.find("tbody").find_all('tr')
        size_pattern = re.compile(r"(?P<size>[0-9]+(\.[0-9]+)?).(?P<unit>(GB|MB|KB|B))")
        age_pattern = re.compile(r"(?P<days1>\d+)\.(?P<days2>\d)")
        title_pattern = re.compile(r'"(.*)\.(rar|nfo|mkv|par2|001|nzb|url|zip|r[0-9]{2})"')
        for row in items:
            tds = list(row.find_all("td"))
            if len(tds) != 5:
                # advertisement
                continue
            entry = self.create_nzb_search_result()

            entry.indexerguid = row.find("input")["value"]

            infotd = tds[1]

            if "password protected" in infotd.text.lower():
                entry.passworded = True

            title = infotd.find("label").text
            title = title.replace("\n","")
            title = re.sub(" +", "", title)
            
            m = title_pattern.search(title)
            if m:
                entry.title = m.group(1)
            else:
                entry.title = title

            info = infotd.find("div", class_="fileinfo")
            if info is not None and re.compile(r"\d NFO").search(info.text):  # 1 nfo file is missing if there is no NFO
                entry.has_nfo = NzbSearchResult.HAS_NFO_YES
            else:
                entry.has_nfo = NzbSearchResult.HAS_NFO_NO
            poster = infotd.find("span", class_="poster").find("a")
            if poster is not None:
                poster = poster.text.replace("\n", "")
                poster = re.sub(" +", "", poster)
                entry.poster = poster.replace("(", " (").replace("<", " <").strip()

            link = infotd.findAll('a', text=re.compile('Download'))
            if link is not None and len(link) == 1:
                entry.link = link[0]["href"]
            else:
                self.debug("Did not find link in row")

            entry.category = "N/A"

            sizetd = tds[2]
            
            m = size_pattern.search(sizetd.text)
            if not m:
                self.debug("Unable to find size information in %s" % sizetd.text)
            else:
                size = float(m.group("size"))
                unit = m.group("unit")
                if unit == "KB":
                    size *= 1024
                elif unit == "MB":
                    size = size * 1024 * 1024
                elif unit == "GB":
                    size = size * 1024 * 1024 * 1024
                entry.size = int(size)

            grouptd = tds[3]
            group = grouptd.text.replace("\n", "").replace("a.b.", "alt.binaries.").strip()
            entry.group = group
            
            agetd = tds[4]
            
            m = age_pattern.search(agetd.text)
            days = None
            hours = None
            if m:
                days = int(m.group("days1"))
                hours = int(m.group("days2")) * 2.4
            else:
                p = re.compile(r"(?P<hours>\d+) hours?")
                m = p.search(agetd.text)
                if m:
                    days = 0
                    hours = int(m.group("hours"))
            if hours is not None:
                pubdate = arrow.utcnow().replace(days=-days, hours=-1)  # hours because of timezone change below
                if hours > 0:
                    pubdate = pubdate.replace(hours=-hours)
                pubdate = pubdate.to("+01:00")  # nzbindex server time, I guess?
                entry.epoch = pubdate.timestamp
                entry.pubdate_utc = str(pubdate)
                entry.age_days = (arrow.utcnow() - pubdate).days
                entry.age_precise = True  # Precise to 2.4 hours, should be enough for duplicate detection
                entry.pubDate = pubdate.format("ddd, DD MMM YYYY HH:mm:ss Z") 
            else:
                self.debug("Found no age info in %s" % str(agetd))

            collection_links = infotd.findAll("a", href=True, text="View collection")
            if collection_links is not None and len(collection_links) > 0: 
                entry.details_link = collection_links[0].attrs["href"]
            accepted, reason = self.accept_result(entry)
            if accepted:
                entries.append(entry)
            else:
                self.debug("Rejected search result. Reason: %s" % reason)
        try:
            page_links = main_table.find("tfoot").find_all("tr")[1].find_all('a')
            if len(page_links) == 0:
                total = len(entries)
                has_more = False
            else:
                pagecount = int(page_links[-2].text)
                currentpage = int(main_table.find("tfoot").find_all("tr")[1].find("b").text) #Don't count "next"
                has_more = pagecount > currentpage
                total = self.limit * pagecount #Good enough
        except Exception:
            self.exception("Error while trying to find page count")
            total = len(entries)
            has_more = False

            self.debug("Finished processing results")
        return IndexerProcessingResult(entries=entries, queries=[], total=total, total_known=True, has_more=has_more)

    def get_nfo(self, guid):
        f = furl(self.host)
        f.path.add("nfo")
        f.path.add(guid)
        r, papiaccess, _ = self.get_url_with_papi_access(f.tostr(), "nfo", cookies={"agreed": "true"})
        if r is not None:
            html = r.text
            p = re.compile(r'<pre id="nfo0">(?P<nfo>.*)<\/pre>', re.DOTALL)
            m = p.search(html)
            if m:
                return True, m.group("nfo"), None
        return False, None, None

    def get_nzb_link(self, guid, title):
        f = furl(self.host)
        f.path.add("download")
        f.path.add(guid)
        f.path.add(title + ".nzb")
        return f.tostr()

    def check_auth(self, body):
        if "503 Service Temporarily Unavailable" in body or "The search service is temporarily unavailable" in body:
            raise IndexerAccessException("The search service is temporarily unavailable.", self)  # The server should return code 503 instead of 200...


def get_instance(indexer):
    return NzbIndex(indexer)
