import calendar
import datetime
import email
import logging
import re
import time
import xml.etree.ElementTree as ET

import arrow
from furl import furl

from nzbhydra.config import ProviderNewznabSettings
from nzbhydra.datestuff import now
from nzbhydra.exceptions import ProviderAuthException, ProviderAccessException, ProviderResultParsingException
from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule, ProviderProcessingResult

logger = logging.getLogger('root')

categories_to_newznab = {
    # Used to map sabnzbd categories to our categories. newznab results always return a general category and optionally a more specific one, for example 2000,2030. In that case we know it's an SD movie. 
    # If it would return 2000,2010 (=foreign) we could still map it to ourt general movies category 
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
    # This is somewhat hack, will need to fix this later (or never)
    # We check if the category string looks like a typical newznab string (e.g. "2030,2040") and if yes just return it. If not we map it because it probably/hopefully came from us

    if category is None:
        return []
    catparts = category.split(",")
    try:
        cats = []
        for cat in catparts:
            intcat = int(cat)
            cats.append(intcat)
        return cats
    except ValueError:
        # Apparently no newznab category string
        # If we know this category we return a list of newznab categories
        if category in categories_to_newznab.keys():
            return categories_to_newznab[category]
        else:
            # If not we return an empty list so that we search in all categories
            return []


class NewzNab(SearchModule):
    # todo feature: read caps from server on first run and store them in the config/database
    def __init__(self, settings: ProviderNewznabSettings):
        super(NewzNab, self).__init__(settings)
        self.settings = settings  # Already done by super.__init__ but this way PyCharm knows the correct type
        self.module = "newznab"
        self.category_search = True

    def __repr__(self):
        return "Provider: %s" % self.name

    def build_base_url(self, action, category, offset=0):
        f = furl(self.settings.host.get())
        f.path.add("api")
        url = f.add({"apikey": self.settings.apikey.get(), "extended": 1, "t": action, "limit": self.limit, "offset": offset})

        categories = map_category(category)
        if len(categories) > 0:
            url.add({"cat": ",".join(str(x) for x in categories)})
        return url

    def get_search_urls(self, search_request):
        f = self.build_base_url("search", search_request.category, offset=search_request.offset)
        if search_request.query:
            f = f.add({"q": search_request.query})
        # if args["minsize"]:
        #     f = f.add({"minsize": args["minsize"]})
        # if args["maxsize"]:
        #     f = f.add({"maxsize": args["maxsize"]})
        # if args["maxage"]:
        #     f = f.add({"age": args["maxage"]})
        return [f.url]

    def get_showsearch_urls(self, search_request):
        if search_request.category is None:
            search_request.category = "TV"

        if search_request.query is None:
            url = self.build_base_url("tvsearch", search_request.category, offset=search_request.offset)
            if search_request.identifier_key is not None:
                url.add({search_request.identifier_key: search_request.identifier_value})
            if search_request.episode is not None:
                url.add({"ep": search_request.episode})
            if search_request.season is not None:
                url.add({"season": search_request.season})
            if search_request.query is not None:
                url.add({"q": search_request.query})
        else:
            url = self.build_base_url("search", search_request.category, offset=search_request.offset).add({"q": search_request.query})

        return [url.url]

    def get_moviesearch_urls(self, search_request):
        if search_request.category is None:
            search_request.category = "Movies"
        if search_request.query is None:
            url = self.build_base_url("movie", search_request.category, offset=search_request.offset)
            if search_request.identifier_key == "imdbid":
                url.add({"imdbid": search_request.identifier_value})
        else:
            url = self.build_base_url("search", search_request.category, offset=search_request.offset).add({"q": search_request.query})

        return [url.url]

    test = 0

    def process_query_result(self, xml_response, query) -> ProviderProcessingResult:
        logger.debug("%s started processing results" % self.name)

        entries = []
        queries = []

        try:
            tree = ET.fromstring(xml_response)
        except Exception:
            logger.exception("Error parsing XML: %s..." % xml_response[:500])
            logger.debug(xml_response)
            raise ProviderResultParsingException("Error parsing XML", self)
        total = int(tree.find("./channel[1]/newznab:response", {"newznab": "http://www.newznab.com/DTD/2010/feeds/attributes/"}).attrib["total"])
        offset = int(tree.find("./channel[1]/newznab:response", {"newznab": "http://www.newznab.com/DTD/2010/feeds/attributes/"}).attrib["offset"])
        if total == 0:
            logger.info("Query at %s returned no results" % self)
            return ProviderProcessingResult(entries=entries, queries=[], total=0, total_known=True, has_more=False)
        for item in tree.find("channel").findall("item"):
            entry = NzbSearchResult()
            entry.title = item.find("title").text
            entry.link = item.find("link").text
            entry.pubDate = item.find("pubDate").text
            pubdate = arrow.get(entry.pubDate, 'ddd, DD MMM YYYY HH:mm:ss Z')
            entry.epoch = pubdate.timestamp
            entry.pubdate_utc = str(pubdate)
            entry.age_days = (arrow.utcnow() - pubdate).days
            entry.precise_date = True
            entry.provider = self.name
            entry.attributes = []
            entry.details_link = item.find("comments").text
            if "#comments" in entry.details_link:
                entry.details_link = entry.details_link[:-9]

            categories = []
            for i in item.findall("./newznab:attr", {"newznab": "http://www.newznab.com/DTD/2010/feeds/attributes/"}):
                attribute_name = i.attrib["name"]
                attribute_value = i.attrib["value"]
                if attribute_name == "size":
                    entry.size = int(attribute_value)
                elif attribute_name == "guid":
                    entry.guid = attribute_value
                elif attribute_name == "category":
                    categories.append(int(attribute_value))
                elif attribute_name == "poster":
                    entry.poster = attribute_value
                elif attribute_name == "info":
                    entry.details_link = attribute_value
                # Store all the extra attributes, we will return them later for external apis
                entry.attributes.append({"name": attribute_name, "value": attribute_value})
            # Map category. Try to find the most specific category (like 2040), then the more general one (like 2000)
            categories = sorted(categories, reverse=True)  # Sort to make the most specific category appear first
            if len(categories) > 0:
                for k, v in categories_to_newznab.items():
                    for c in categories:
                        if c in v:
                            entry.category = k
                            break

            entries.append(entry)
        # offset += self.limit
        # if offset < total and offset < 400:
        #     f = furl(query)
        #     query = f.remove("offset").add({"offset": offset})
        #     queries.append(query.url)
        # 
        #     logger.debug("%s started processing results" % self.name)
        #     return ProviderProcessingResult(entries=entries, queries=queries)
        # logger.debug("%s finished processing results" % self.name)
        return ProviderProcessingResult(entries=entries, queries=[], total=total, total_known=True, has_more=offset + len(entries) < total)

    def check_auth(self, body: str):
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
        url = furl(self.settings.host.get()).add({"apikey": self.settings.apikey.get(), "t": "getnfo", "o": "xml", "id": guid})  # todo: should use build_base_url but that adds search specific stuff

        response, papiaccess = self.get_url_with_papi_access(url, "nfo")
        if response is not None:
            nfo = response.text
            if "<?xml" in nfo and 'total="1"': #Hacky but fast
                tree = ET.fromstring(nfo)
                for elem in tree.iter('item'):
                    nfo = elem.find("description").text
                    nfo = re.sub("\\n", nfo, "\n")  # TODO: Not completely correct, looks still a bit werid
                    return nfo
            # otherwise we just hope it's the nfo...
        return None

    def get_nzb_link(self, guid, title):
        f = furl(self.settings.host.get())
        f.path.add("api")
        f.add({"t": "get", "apikey": self.settings.apikey.get(), "id": guid})
        return f.tostr()


def get_instance(provider):
    return NewzNab(provider)
