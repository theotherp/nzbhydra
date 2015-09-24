import calendar
import datetime
import email
import logging
import time
import arrow
import xml.etree.ElementTree as ET
import requests
import re
from furl import furl

from datestuff import now
from exceptions import ProviderAuthException, ProviderAccessException
from nzb_search_result import NzbSearchResult
from search_module import SearchModule

logger = logging.getLogger('root')


def get_age_from_pubdate(pubdate):
    timepub = datetime.datetime.fromtimestamp(email.utils.mktime_tz(email.utils.parsedate_tz(pubdate)))
    timenow = now()
    dt = timenow - timepub
    epoch = calendar.timegm(time.gmtime(email.utils.mktime_tz(email.utils.parsedate_tz(pubdate))))
    pubdate_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(email.utils.mktime_tz(email.utils.parsedate_tz(pubdate))))
    age_days = int(dt.days)
    return epoch, pubdate_utc, int(age_days)


class NewzNab(SearchModule):
    # TODO init of config which is dynmic with its path

    #todo feature: read caps from server on first run and store them in the config/database
    def __init__(self, config_section):
        super(NewzNab, self).__init__(config_section)
        self.module_name = "NewzNab"
        self.name = config_section.get("name")
        self.query_url = config_section.get("query_url")
        self.base_url = config_section.get("base_url")
        self.apikey = config_section.get("apikey")
        self.username = config_section.get("username")
        self.password = config_section.get("password")
        self.search_types = config_section.get("search_types", ["general", "tv", "movie"])
        self.supports_queries = True
        self.search_ids = config_section.get("search_ids", ["tvdbid", "rid", "imdbid"])
        self.needs_queries = False
        self.generate_queries = config_section.get("generate_queries", False) #Could be set true, but not needed if searching using ids
        self.category_search = True
        
        
    def __repr__(self):
        return "Provider: %s" % self.name

    def build_base_url(self, action, o="json", extended=1):
        url = furl(self.query_url).add({"apikey": self.apikey, "o": o, "extended": extended, "t": action})
        return url

    def get_search_urls(self, query, categories=None):
        f = self.build_base_url("search").add({"q": query})
        if categories is not None:
            f.add({"cat": ",".join(str(x) for x in categories)})
        return [f.url]

    def get_showsearch_urls(self, query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
        if query is None:
            url = self.build_base_url("tvsearch")
            if identifier_key is not None:
                url.add({identifier_key: identifier_value})
            if episode is not None:
                url.add({"ep": episode})
            if season is not None:
                url.add({"season": season})
        else:
            url = self.build_base_url("search").add({"q": query})
        
        if categories is None:
            categories = [5000]
        
        url.add({"cat": ",".join(str(x) for x in categories)})
            
        
        return [url.url]

    def get_moviesearch_urls(self, query=None, identifier_key=None, identifier_value=None, categories=None):
        if query is None:
            url = self.build_base_url("movie")
            if identifier_key is not None:
                url.add({identifier_key: identifier_value})
        else:
            url = self.build_base_url("search").add({"q": query})
        
        if categories is None:
            categories = [2000]
        
        url.add({"cat": ",".join(str(x) for x in categories)})
        
        return [url.url]

    def process_query_result(self, json_response):
        import json
        # from Helpers import getAgeFromPubdate
        # from Helpers import sizeof_readable

        entries = []
        json_result = json.loads(json_response)
        if "0" == json_result["channel"]["response"]["@attributes"]["total"]:
            return entries

        result_items = json_result["channel"]["item"]
        if "title" in result_items:
            # Only one item, put it in a list so the for-loop works
            result_items = [result_items]
        for item in result_items:
            entry = NzbSearchResult()
            entry.title = item["title"]
            entry.link = item["link"]
            entry.pubDate = item["pubDate"]
            pubdate = arrow.get(entry.pubDate, '"ddd, DD MMM YYYY HH:mm:ss Z')
            entry.epoch = pubdate.timestamp
            entry.pubdate_utc = str(pubdate)
            entry.age_days = (arrow.utcnow() - pubdate).days
            entry.precise_date = True
            entry.provider = self.name
            entry.attributes = []

            entry.categories = []
            for i in item["attr"]:
                if i["@attributes"]["name"] == "size":
                    entry.size = int(i["@attributes"]["value"])
                    # entry.sizeReadable = sizeof_readable(entry.size)
                elif i["@attributes"]["name"] == "guid":
                    entry.guid = i["@attributes"]["value"]
                elif i["@attributes"]["name"] == "category":
                    entry.categories.append(int(i["@attributes"]["value"]))
                # Store all the extra attributes, we will return them later for external apis
                entry.attributes.append({"name": i["@attributes"]["name"], "value": i["@attributes"]["value"]})
            entry.categories = sorted(entry.categories) #Sort to make the general category appear first
            entries.append(entry)
        return entries
    
    def check_auth(self, body):
        #TODO: unfortunately in case of an auth problem newznab doesn't return json even if requested. So this would be easier/better if we used XML responses instead of json
        if '<error code="100"' in body:
            raise ProviderAuthException("The API key seems to be incorrect.", self)
        if '<error code="101"' in body:
            raise ProviderAuthException("The account seems to be suspended.", self)
        if '<error code="102"' in body:
            raise ProviderAuthException("You're not allowed to use the API.", self)
        if '<error code="910"' in body:
            raise ProviderAccessException("The API seems to be disabled for the moment.", self)
        if '<error code=' in body:
            raise ProviderAccessException("Unknown error while trying to access the provider.", self)
        
    def get_nfo(self, guid):
        #try to get raw nfo. if it is xml the provider doesn't actually return raw nfos (I'm looking at you, DOGNzb)
        url = self.build_base_url("getnfo", o="xml", extended=0).add({"id": guid})
        response = requests.get(url)
        nfo = response.text #todo error handling
        if "<?xml" in nfo:
            #parse
            try:
                tree = ET.fromstring(nfo)
            except Exception as e:
                logger.exception("Error parsing NFO response", e)
                return []
            for elem in tree.iter('item'):
                nfo = elem.find("description").text
                #And replace line breaks by html brs
                #nfo = re.sub("\\\\n", "<br>", nfo)
                return nfo
        else:
            #Return it and hope that it's the NFO...
            return nfo
        
        
        
            


def get_instance(config_section):
    return NewzNab(config_section)
