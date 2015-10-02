import logging
import re

import arrow
from bs4 import BeautifulSoup
from furl import furl

from nzbhydra.exceptions import ProviderIllegalSearchException
from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule

logger = logging.getLogger('root')


class Binsearch(SearchModule):

    def __init__(self, provider):
        super(Binsearch, self).__init__(provider)
        self.module = "binsearch"
        self.name = "Binsearch"

        self.supports_queries = True  # We can only search using queries
        self.needs_queries = True
        self.category_search = False
        # https://www.nzbclub.com/nzbrss.aspx


    def build_base_url(self):
        url = furl(self.query_url).add({"max": self.provider.settings.get("max_results", 250), 
                                        "adv_col": "on", # collections only 
                                        "postdate": "date", # show pubDate, not age
                                        "adv_nfo": "off" #if enabled only show results with nfo file #todo make configurable
                                        })
        return url

    def get_search_urls(self, query=None, generated_query=None, categories=None):
        return [self.build_base_url().add({"q": query if query else generated_query}).tostr()]

    def get_showsearch_urls(self, generated_query=None, query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
        if query is None and generated_query is None:
            raise ProviderIllegalSearchException("Attempted to search without a query although this provider only supports query-based searches", self)
        
        urls = []
        if query:
            urls = [self.get_search_urls(query, categories)]
        if generated_query and season is not None:
            #Restrict query if generated and season and/or episode is given. Use s01e01 and 1x01 and s01 and "season 1" formats
            #binsearch doesn't seem to support "or" in searches, so create separate queries
            if episode is not None:
                urls.extend(self.get_search_urls(generated_query="%s s%02de%02d" % (generated_query, season, episode)))
                urls.extend(self.get_search_urls(generated_query="%s %dx%02d" % (generated_query, season, episode)))
            else:
                urls.extend(self.get_search_urls(generated_query="%s s%02d" % (generated_query, season)))
                urls.extend(self.get_search_urls(generated_query='%s "season %d"' % (generated_query, season)))
        return urls

    def get_moviesearch_urls(self, generated_query=None, query=None, identifier_key=None, identifier_value=None, categories=None):
        if query is None and generated_query is None:
            raise ProviderIllegalSearchException("Attempted to search without a query although this provider only supports query-based searches", self)
        return self.get_search_urls(query if query else generated_query, categories)

    def process_query_result(self, html, query):
        entries = []
        soup = BeautifulSoup(html, 'html.parser')

        main_table = soup.find('table', attrs={'id': 'r2'})

        if not main_table:
            return

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
                
            collection_link = info.find("a")["href"] #'/?b=MARVELS.AVENGERS.AGE.OF.ULTRON.3D.TOPBOT.TrueFrench.1080p.X264.A&g=alt.binaries.movies.mkv&p=Ramer%40marmer.com+%28Clown_nez%29&max=250'
            m = re.compile(r"&p=(.*)&").search(collection_link)
            if m:
                poster = m.group(1)
                poster = poster.replace("%40", "@")
                poster = poster.replace("%28", "<")
                poster = poster.replace("%29", ">")
                poster = poster.replace("+", " ")
                entry.poster = poster
            #Size
            p = re.compile(r"size: ([0-9]+\.[0-9]+).(GB|MB|KB)")
            m = p.search(info.text)
            if not m:
                logger.debug("Unable to find size information in %s" % info.text)
                continue
            size = float(m.group(1))
            unit = m.group(2)
            if unit == "KB":
                size *= 1024  
            elif unit == "MB":
                size = size * 1024 * 1024
            elif unit == "GB":
                size = size * 1024 * 1024 * 1024
            entry.size = int(size)

            #Age
            p = re.compile(r"(\d{2}\-\w{3}\-\d{4})")
            m = p.search(row.find_all("td")[-1:][0].text)
            if m:
                pubdate = arrow.get(m.group(1), "DD-MMM-YYYY")
                entry.epoch = pubdate.timestamp
                entry.pubdate_utc = str(pubdate)
                entry.age_days = (arrow.utcnow() - pubdate).days
                entry.age_precise = False
            else:
                logger.error("Unable to find age in %s" % row.find_all("td")[-1:][0].text)

            entries.append(entry)

        return {"entries": entries, "queries": []}

def get_instance(provider):
    return Binsearch(provider)
