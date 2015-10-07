import logging
import re

import arrow
from bs4 import BeautifulSoup
from furl import furl
from nzbhydra.config import ProviderBinsearchSettings
from nzbhydra.exceptions import ProviderResultParsingException, ProviderAccessException

from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule, EntriesAndQueries

logger = logging.getLogger('root')


class Binsearch(SearchModule):
    def __init__(self, settings: ProviderBinsearchSettings):
        super(Binsearch, self).__init__(settings)
        self.module = "binsearch"

        self.supports_queries = True  # We can only search using queries
        self.needs_queries = True
        self.category_search = False
        self.max_results = 250

    def build_base_url(self):
        f = furl(self.host)
        f.path.add("index.php")
        url = f.add({"max": self.max_results,
                     "adv_col": "on",  # collections only 
                     "postdate": "date",  # show pubDate, not age
                     # "adv_nfo": "off", #if enabled only show results with nfo file #todo make configurable. setting it to off doesnt work, its still done
                     "adv_sort": "date"  # prefer the newest
                     })
        return url

    def get_search_urls(self, args):
        f = self.build_base_url().add({"q": args["query"]})
        if args["minsize"]:
            f = f.add({"minsize": args["minsize"]})
        if args["maxsize"]:
            f = f.add({"maxsize": args["maxsize"]})
        if args["maxage"]:
            f = f.add({"adv_age": args["maxage"]})

        return [f.tostr()]

    def get_showsearch_urls(self, args):
        urls = []
        query = args["query"]
        if args["query"]:
            urls = self.get_search_urls(args)
        if args["season"] is not None:
            # Restrict query if  season and/or episode is given. Use s01e01 and 1x01 and s01 and "season 1" formats
            # binsearch doesn't seem to support "or" in searches, so create separate queries
            urls = []
            if args["episode"] is not None:
                args["query"] = "%s s%02de%02d" % (query, args["season"], args["episode"])
                urls.extend(self.get_search_urls(args))
                args["query"] = "%s %dx%02d" % (query, args["season"], args["episode"])
                urls.extend(self.get_search_urls(args))
            else:
                args["query"] = "%s s%02d" % (query, args["season"])
                urls.extend(self.get_search_urls(args))
                args["query"] = '%s "season %d"' % (query, args["season"])
                urls.extend(self.get_search_urls(args))
        return urls

    def get_moviesearch_urls(self, args):
        return self.get_search_urls(args)

    def process_query_result(self, html, query) -> EntriesAndQueries:

        entries = []
        soup = BeautifulSoup(html, 'html.parser')

        main_table = soup.find('table', attrs={'id': 'r2'})

        if not main_table:
            logger.error("Unable to find main table in binsearch page: %s..." % html)
            logger.debug(html)
            raise ProviderResultParsingException("Unable to find main table in binsearch page", self)

        items = main_table.find_all('tr')

        for row in items:

            entry = NzbSearchResult()
            entry.provider = self.name
            title = row.find('span', attrs={'class': 's'})

            if title is None:
                continue
            title = title.text

            p = re.compile(r'"(.*)\.(rar|nfo|mkv|par2|001|nzb|url|zip|r[0-9]{2})"')
            m = p.search(title)
            if m:
                entry.title = m.group(1)
            else:
                entry.title = title

            entry.guid = row.find("input", attrs={"type": "checkbox"})["name"]
            entry.link = "https://www.binsearch.info/fcgi/nzb.fcgi?q=%s" % entry.guid
            info = row.find("span", attrs={"class": "d"})
            if info is None:
                continue

            collection_link = info.find("a")["href"]  # '/?b=MARVELS.AVENGERS.AGE.OF.ULTRON.3D.TOPBOT.TrueFrench.1080p.X264.A&g=alt.binaries.movies.mkv&p=Ramer%40marmer.com+%28Clown_nez%29&max=250'
            m = re.compile(r"&p=(.*)&").search(collection_link)
            if m:
                poster = m.group(1)
                poster = poster.replace("%40", "@")
                poster = poster.replace("%28", "<")
                poster = poster.replace("%29", ">")
                poster = poster.replace("+", " ")
                entry.poster = poster
            # Size
            p = re.compile(r"size: (?P<size>[0-9]+(\.[0-9]+)?).(?P<unit>(GB|MB|KB|B))")
            m = p.search(info.text)
            if not m:
                logger.debug("Unable to find size information in %s" % info.text)
            else:
                size = float(m.group("size"))
                unit = m.group("unit")
                if unit == "B":
                    pass
                elif unit == "KB":
                    size *= 1024
                elif unit == "MB":
                    size = size * 1024 * 1024
                elif unit == "GB":
                    size = size * 1024 * 1024 * 1024
                
                entry.size = int(size)

            entry.category = "N/A"

            if re.compile(r"\d nfo file").search(info.text):  # 1 nfo file is missing if there is no NFO
                entry.has_nfo = True
            else:
                entry.has_nfo = False

            # Age
            try:
                pubdate = re.compile(r"(\d{1,2}\-\w{3}\-\d{4})").search(row.find("td").text).group(1)
                pubdate = arrow.get(pubdate, "DD-MMM-YYYY")
                entry.epoch = pubdate.timestamp
                entry.pubdate_utc = str(pubdate)
                entry.age_days = (arrow.utcnow() - pubdate).days
                entry.age_precise = False
            except Exception as e:
                entry.epoch = 0

                logger.error("Unable to find age in %s" % row.find_all("td")[-1:][0].text)

            entries.append(entry)

        return EntriesAndQueries(entries=entries, queries=[])

    def get_nfo(self, guid):
        f = furl(self.base_url)
        f.path.add("viewNFO.php")
        f.add({"oid": guid})
        r, papiaccess = self.get_url_with_papi_access(f.tostr(), "nfo")
        if r is not None:
            html = r.text
            p = re.compile(r"<pre>(?P<nfo>.*)<\/pre>", re.DOTALL)
            m = p.search(html)
            if m:
                return m.group("nfo")
        return None
    
    def get_nzb_link(self, guid, title):
        f = furl(self.host)
        f.add({"action": "nzb", guid: "1"})
        return f.tostr()
    
    def check_auth(self, body: str):
        if "The search service is temporarily unavailable" in body:
            raise ProviderAccessException("The search service is temporarily unavailable.", self)


    

def get_instance(settings):
    return Binsearch(settings)
