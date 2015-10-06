import json
import logging
import re
import arrow
from bs4 import BeautifulSoup
from furl import furl
import xml.etree.ElementTree as ET
import requests
from nzbhydra.exceptions import ProviderIllegalSearchException, ProviderResultParsingException, ProviderAccessException
from nzbhydra.nzb_search_result import NzbSearchResult

from nzbhydra.search_module import SearchModule, EntriesAndQueries

logger = logging.getLogger('root')


# Probably only as RSS supply, not for searching. Will need to do a (config) setting defining that. When searches without specifier are done we can include indexers like that
class NzbIndex(SearchModule):

    def __init__(self, provider):
        super(NzbIndex, self).__init__(provider)
        self.module = "nzbindex"
        
        self.supports_queries = True #We can only search using queries
        self.needs_queries = True
        self.category_search = False
        self.max_results = 250
        
        
    
    def build_base_url(self):
        f = furl(self.host)
        f.path.add("search")
        f = f.add({"more": "1", "max": self.max_results, "hidecross": 1}) 
        return f

    def get_search_urls(self, args):
        f = self.build_base_url().add({"q": args["query"]})
        if args["minsize"]:
            f = f.add({"minsize": args["minsize"]})
        if args["maxsize"]:
            f = f.add({"maxsize": args["maxsize"]})
        if args["minage"]:
            f = f.add({"minage": args["minage"]})
        if args["maxage"]:
            f = f.add({"age": args["maxage"]})
        return [f.tostr()]

    def get_showsearch_urls(self, args):
        if args["season"] is not None:
            #Restrict query if generated and season and/or episode is given. Use s01e01 and 1x01 and s01 and "season 1" formats
            if args["episode"] is not None:
                args["query"] = "%s s%02de%02d | %dx%02d" % (args["query"], args["season"], args["episode"], args["season"], args["episode"])
            else:
                args["query"] = '%s s%02d | "season %d"' % (args["query"], args["season"], args["season"])
        return self.get_search_urls(args)


    def get_moviesearch_urls(self, args):
        return self.get_search_urls(args)
    
    def get(self, query, timeout=None, cookies=None):
        #overwrite for special handling, e.g. cookies
        return requests.get(query, timeout=timeout, verify=False, cookies={"agreed": "true", "lang": "2"})

    def process_query_result(self, html, query) -> EntriesAndQueries:
        
        entries = []
        soup = BeautifulSoup(html, 'html.parser')
        main_table = soup.find(id="results").find('table')

        

        if not main_table or not  main_table.find("tbody"):
            logger.error("Unable to find main table in NZBIndex page: %s..." % html[:500])
            logger.debug(html)
            raise ProviderResultParsingException("Unable to find main table in NZBIndex page", self)

        items = main_table.find("tbody").find_all('tr')

        for row in items:
            tds = list(row.find_all("td"))
            if len(tds) != 5:
                #advertisement
                continue
            entry = NzbSearchResult()
            entry.provider = self.name
            
            entry.guid = row.find("input")["value"]
            
            infotd = tds[1]
            
            title = infotd.find("label").text
            p = re.compile(r'"(.*)\.(rar|nfo|mkv|par2|001|nzb|url|zip|r[0-9]{2})"') 
            m = p.search(title)
            if m:
                entry.title = m.group(1)
            else:
                entry.title = title
                
            info = infotd.find("div", class_="fileinfo")
            if info is not None and re.compile(r"\d NFO").search(info.text): # 1 nfo file is missing if there is no NFO
                entry.has_nfo = True
            else:
                entry.has_nfo = False
            poster = infotd.find("span", class_="poster").find("a")
            if poster is not None:
                entry.poster = poster.text
            
            link = infotd.findAll('a', text=re.compile('Download'))
            if link is not None and len(link) == 1:
                entry.link = link[0]["href"]
            else:
                logger.debug("Did not find link in row")
                
            entry.category = "N/A"
                
            
            sizetd = tds[2]
            p = re.compile(r"(?P<size>[0-9]+(\.[0-9]+)?).(?P<unit>(GB|MB|KB))")
            m = p.search(sizetd.text)
            if not m:
                logger.debug("Unable to find size information in %s" % sizetd.text)
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
                        
            agetd = tds[4]
            p = re.compile(r"(?P<days1>\d+)\.(?P<days2>\d)")
            m = p.search(agetd.text)
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
                pubdate = arrow.utcnow().replace(days=-days, hours=-1) #hours because of timezone change below
                if hours > 0:
                    pubdate = pubdate.replace(hours=-hours) 
                pubdate = pubdate.to("+01:00") #nzbindex server time, I guess?
                entry.epoch = pubdate.timestamp
                entry.pubdate_utc = str(pubdate)
                entry.age_days = (arrow.utcnow() - pubdate).days
                entry.age_precise = True #Precise to 2.4 hours, should be enough for duplicate detection
            else:
                logger.debug("Found no age info in %s" % str(agetd))
            entries.append(entry)
            
        return EntriesAndQueries(entries=entries, queries=[])
    
        
    def get_nfo(self, guid):
        f = furl(self.host)
        f.path.add("nfo")
        f.path.add(guid)
        r, papiaccess = self.get_url_with_papi_access(f.tostr(), "nfo", cookies={"agreed": "true"})
        if r is not None:
            html = r.text
            p = re.compile(r'<pre id="nfo0">(?P<nfo>.*)<\/pre>', re.DOTALL)
            m = p.search(html)
            if m:
                return m.group("nfo")
        return None
    
    
    def get_nzb_link(self, guid, title):
        #https://nzbindex.com/download/126435066/ATG-Avengers-02-Lre-dUltron-2015-TF-720p.zip.nzb
        f = furl(self.host)
        f.path.add("download")
        f.path.add("guid")
        f.path.add(title + ".nzb")
        return f.tostr()
    
    def check_auth(self, body: str):
        if "503 Service Temporarily Unavailable" in body or "The search service is temporarily unavailable" in body:
            raise ProviderAccessException("The search service is temporarily unavailable.", self) #The server should return code 503 instead of 200...


def get_instance(provider):
    return NzbIndex(provider)
