import datetime
import email

from furl import furl

from datestuff import now
from nzb_search_result import NzbSearchResult

from search_module import SearchModule


def getAgeFromPubdate(pubdate):
    timepub = datetime.datetime.fromtimestamp(email.utils.mktime_tz(email.utils.parsedate_tz(pubdate)))
    timenow = now()
    dt = timenow - timepub
    return int(dt.total_seconds())


class NewzNab(SearchModule):
    def __init__(self, config_section):
        super(NewzNab, self).__init__(config_section)
        self.module_name = "NewzNab"
        self.name = config_section.get("name")
        self.query_url = config_section.get("query_url")
        self.base_url = config_section.get("base_url")
        self.apikey = config_section.get("apikey")
        self.username = config_section.get("username")
        self.password = config_section.get("password")
        
    def build_base_url(self, action, categories=None):
        url = furl(self.query_url).add({"apikey": self.apikey, "o": "json", "extended": 1, "t": action})
        if categories is not None:
            url.add({"cat": categories})
        return url

    def get_search_urls(self, query, categories=None):
        f = self.build_base_url("search").add({"q": query})
        if categories is not None:
            f = f.add("cat", categories)
        return [f.url]

    def get_showsearch_urls(self, identifier=None, season=None, episode=None, categories=None):
        query = self.build_base_url("tvsearch", categories)
        if identifier is not None:
            query.add({"rid": identifier})
        if episode is not None:
            query.add({"ep": episode})
        if season is not None:
            query.add({"season": season})
        #todo quality/categories
        return [query.url]
        

    def get_moviesearch_urls(self, identifier=None, categories=None):
        query = self.build_base_url("movie", categories)
        if identifier is not None:
            query.add({"imdbid": identifier})
        return [query.url]

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
            entry.age = getAgeFromPubdate(item["pubDate"])
            entry.provider = self.name
            entry.attributes = []

            entry.category = None
            for i in item["attr"]:
                if i["@attributes"]["name"] == "size":
                    entry.size = int(i["@attributes"]["value"])
                    # entry.sizeReadable = sizeof_readable(entry.size)
                elif i["@attributes"]["name"] == "guid":
                    entry.guid = i["@attributes"]["value"]
                elif i["@attributes"]["name"] == "category":
                    if entry.category is None:
                        # First category is always the general one, this is what we want
                        # entry.category = self.getCategory(i["@attributes"]["value"])
                        entry.category = "TODO category"  # TODO
                #Store all the extra attributes, we will return them later for external apis
                entry.attributes.append({"name": i["@attributes"]["name"], "value": i["@attributes"]["value"]})

            entries.append(entry)
        return entries


def get_instance(config_section):
    return NewzNab(config_section)
