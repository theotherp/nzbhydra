import calendar
import datetime
import email
import logging
import time
import xml.etree.ElementTree as ET

import arrow
from requests import RequestException
import requests

from furl import furl

from nzbhydra.database import ProviderApiAccess
from nzbhydra.datestuff import now
from nzbhydra.exceptions import ProviderAuthException, ProviderAccessException, ProviderConnectionException
from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule

logger = logging.getLogger('root')

categories_to_newznab = {
    'All': [],
    'Movies': [2000],
    'Movies HD': [2040, 2050, 2060],
    'Movies SD': [2030],
    'TV': [5000],
    'TV SD': [5030],
    'TV HD': [5040],
    'Audio': [3000],
    'Audio FLAC': [3040],
    'Audio MP3': [3010],
    'Console': [1000],
    'PC': [4000],
    'XXX': [6000],
    'Other': [7000]
}


def get_age_from_pubdate(pubdate):
    timepub = datetime.datetime.fromtimestamp(email.utils.mktime_tz(email.utils.parsedate_tz(pubdate)))
    timenow = now()
    dt = timenow - timepub
    epoch = calendar.timegm(time.gmtime(email.utils.mktime_tz(email.utils.parsedate_tz(pubdate))))
    pubdate_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(email.utils.mktime_tz(email.utils.parsedate_tz(pubdate))))
    age_days = int(dt.days)
    return epoch, pubdate_utc, int(age_days)


def map_category(category):
    #If we know this category we return a list of newznab categories
    if category in categories_to_newznab.keys():
        return categories_to_newznab[category]
    #If not we return an empty list so that we search in all categories
    return []


class NewzNab(SearchModule):
    # todo feature: read caps from server on first run and store them in the config/database
    def __init__(self, provider):
        """

        :type provider: NewznabProvider
        """
        super(NewzNab, self).__init__(provider)
        self.module = "newznab"
        self.category_search = True
        self.limit = 100

    def __repr__(self):
        return "Provider: %s" % self.name

    def build_base_url(self, action, category, o="json", extended=1):
        url = furl(self.provider.settings.get("query_url")).add({"apikey": self.provider.settings.get("apikey"), "o": o, "extended": extended, "t": action, "limit": self.limit, "offset": 0})
        
        categories = map_category(category)
        if len(categories) > 0:
            url.add({"cat": ",".join(str(x) for x in categories)})
        return url

    def get_search_urls(self, query=None, category=None):
        f = self.build_base_url("search", "All")
        if query is not None:
            f = f.add({"q": query})
        return [f.url]

    def get_showsearch_urls(self, query=None, identifier_key=None, identifier_value=None, season=None, episode=None, category=None):
        if category is None:
            category = "TV"
        
        if query is None:
            url = self.build_base_url("tvsearch", category)
            if identifier_key is not None:
                url.add({identifier_key: identifier_value})
            if episode is not None:
                url.add({"ep": episode})
            if season is not None:
                url.add({"season": season})
        else:
            url = self.build_base_url("search", category).add({"q": query})

        return [url.url]

    def get_moviesearch_urls(self, query=None, identifier_key=None, identifier_value=None, category=None):
        if category is None:
            category = "Movies"
        if query is None:
            url = self.build_base_url("movie", category)
            if identifier_key is not None:
                url.add({identifier_key: identifier_value})
        else:
            url = self.build_base_url("search", category).add({"q": query})

        return [url.url]

    test = 0

    def process_query_result(self, json_response, query):
        import json

        entries = []
        queries = []
        json_result = json.loads(json_response)
        total = int(json_result["channel"]["response"]["@attributes"]["total"])
        offset = int(json_result["channel"]["response"]["@attributes"]["offset"])
        if "0" == total:
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
            pubdate = arrow.get(entry.pubDate, 'ddd, DD MMM YYYY HH:mm:ss Z')
            entry.epoch = pubdate.timestamp
            entry.pubdate_utc = str(pubdate)
            entry.age_days = (arrow.utcnow() - pubdate).days
            entry.precise_date = True
            entry.provider = self.name
            entry.attributes = []

            categories = []
            for i in item["attr"]:
                if i["@attributes"]["name"] == "size":
                    entry.size = int(i["@attributes"]["value"])
                    # entry.sizeReadable = sizeof_readable(entry.size)
                elif i["@attributes"]["name"] == "guid":
                    entry.guid = i["@attributes"]["value"]
                elif i["@attributes"]["name"] == "category":
                    categories.append(int(i["@attributes"]["value"]))
                elif i["@attributes"]["name"] == "poster":
                    entry.poster = (i["@attributes"]["value"])
                # Store all the extra attributes, we will return them later for external apis
                entry.attributes.append({"name": i["@attributes"]["name"], "value": i["@attributes"]["value"]})
            #Map category. Try to find the most specific category (like 2040), then the more general one (like 2000)
            categories = sorted(categories, reverse=True)  # Sort to make the most specific category appear first
            if len(categories) > 0:
                for k, v in categories_to_newznab.items():
                    for c in categories:
                        if c in v:
                            entry.category = k
                            break
                
            entries.append(entry)

        offset += self.limit
        if offset < total and offset < 400:
            f = furl(query)
            query = f.remove("offset").add({"offset": offset})
            queries.append(query.url)

            return {"entries": entries, "queries": queries}

        return {"entries": entries, "queries": []}

    def check_auth(self, response):
        body = response.text
        # TODO: unfortunately in case of an auth problem newznab doesn't return json even if requested. So this would be easier/better if we used XML responses instead of json
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
        # try to get raw nfo. if it is xml the provider doesn't actually return raw nfos (I'm looking at you, DOGNzb)
        url = self.build_base_url("getnfo", "All", o="xml", extended=0).add({"id": guid})
        papiaccess = ProviderApiAccess(provider=self.provider, type="nfo")
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise ProviderConnectionException("Error while retrieving NFO for ID %s. Returned status code:" % (guid, response.status_code), self)
            papiaccess.response_time = response.elapsed.microseconds / 1000

            nfo = response.text
            if "<?xml" in nfo:
                tree = ET.fromstring(nfo)
                for elem in tree.iter('item'):
                    nfo = elem.find("description").text
                    # otherwise we just hope it's the nfo...
        except RequestException:
            raise ProviderConnectionException("Error while connecting.", self)
        except ProviderConnectionException as e:
            logger.exception("Error while connecting to %s" % self, e)
            papiaccess.error = "Error while retrieving NFO for ID %s." % guid
            papiaccess.save()
            raise

        papiaccess.save()
        return nfo


def get_instance(provider):
    return NewzNab(provider)
