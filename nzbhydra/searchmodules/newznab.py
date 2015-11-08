from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import super
from builtins import int
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import *
import calendar
import datetime
import email
import logging
import re
import time
import xml.etree.ElementTree as ET

import arrow
from furl import furl

import requests
from requests.exceptions import RequestException
from nzbhydra.config import IndexerNewznabSettings
from nzbhydra.datestuff import now
from nzbhydra.exceptions import IndexerAuthException, IndexerAccessException, IndexerResultParsingException
from nzbhydra.search_module import SearchModule, IndexerProcessingResult

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


def check_auth(body):
    if '<error code="100"' in body:
        raise IndexerAuthException("The API key seems to be incorrect.", None)
    if '<error code="101"' in body:
        raise IndexerAuthException("The account seems to be suspended.", None)
    if '<error code="102"' in body:
        raise IndexerAuthException("You're not allowed to use the API.", None)
    if '<error code="910"' in body:
        raise IndexerAccessException("The API seems to be disabled for the moment.", None)
    if '<error code=' in body:
        raise IndexerAccessException("Unknown error while trying to access the indexer.", None)


def test_connection(host, apikey):
    f = furl(host)
    f.path.add("api")
    f.query.add({"apikey": apikey, "t": "tvsearch"})
    try:
        r = requests.get(f.url, verify=False)
        r.raise_for_status()
        check_auth(r.text)
    except RequestException:
        return False, "Unable to connect to host"
    except IndexerAuthException:
        return False, "Wrong credentials"
    except IndexerAccessException:
        return False, "Host reachable but unknown error returned"
    return True, ""

class NewzNab(SearchModule):
    # todo feature: read caps from server on first run and store them in the config/database
    def __init__(self, settings):
        super(NewzNab, self).__init__(settings)
        self.settings = settings  # Already done by super.__init__ but this way PyCharm knows the correct type
        self.module = "newznab"
        self.category_search = True

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
        if search_request.maxage:
            f = f.add({"maxage": search_request.maxage})
        return [f.url]

    def get_showsearch_urls(self, search_request):
        if search_request.category is None:
            search_request.category = "TV"

        url = self.build_base_url("tvsearch", search_request.category, offset=search_request.offset)
        if search_request.identifier_key is not None:
            url.add({search_request.identifier_key: search_request.identifier_value})
        if search_request.episode is not None:
            url.add({"ep": search_request.episode})
        if search_request.season is not None:
            url.add({"season": search_request.season})
        if search_request.query is not None:
            url.add({"q": search_request.query})

        return [url.url]

    def get_moviesearch_urls(self, search_request):
        if search_request.category is None:
            search_request.category = "Movies"

        url = self.build_base_url("movie", search_request.category, offset=search_request.offset)
        if search_request.identifier_key == "imdbid":
            url.add({"imdbid": search_request.identifier_value})
        if search_request.query is not None:
            url.add({"q": search_request.query})

        return [url.url]

    def get_details_link(self, guid):
        f = furl(self.settings.host.get())
        f.path.add("details")
        f.path.add(guid)
        return f.url

    def process_query_result(self, xml_response, query):
        logger.debug("%s started processing results" % self.name)

        entries = []
        queries = []
        grouppattern = re.compile(r"Group:</b> ?([\w\.]+)<br ?/>")
        guidpattern = re.compile(r"(.*/)?([a-zA-Z0-9]+)")

        try:
            tree = ET.fromstring(xml_response)
        except Exception:
            logger.exception("Error parsing XML: %s..." % xml_response[:500])
            raise IndexerResultParsingException("Error parsing XML", self)
        total = int(tree.find("./channel[1]/newznab:response", {"newznab": "http://www.newznab.com/DTD/2010/feeds/attributes/"}).attrib["total"])
        offset = int(tree.find("./channel[1]/newznab:response", {"newznab": "http://www.newznab.com/DTD/2010/feeds/attributes/"}).attrib["offset"])
        if total == 0:
            logger.info("Query at %s returned no results" % self)
            return IndexerProcessingResult(entries=entries, queries=[], total=0, total_known=True, has_more=False)
        for item in tree.find("channel").findall("item"):
            entry = self.create_nzb_search_result()
            entry.title = item.find("title").text
            entry.link = item.find("link").text
            entry.pubDate = item.find("pubDate").text
            pubdate = arrow.get(entry.pubDate, 'ddd, DD MMM YYYY HH:mm:ss Z')
            entry.epoch = pubdate.timestamp
            entry.pubdate_utc = str(pubdate)
            entry.age_days = (arrow.utcnow() - pubdate).days
            entry.precise_date = True
            entry.attributes = []
            entry.guid = item.find("guid").text
            m = guidpattern.search(entry.guid)
            if m:
                entry.guid = m.group(2)

            if entry.details_link is not None and "#comments" in entry.details_link:
                entry.details_link = entry.details_link[:-9]
            description = item.find("description").text
            if "Group:" in description:  # DogNZB has the group in its description
                m = grouppattern.search(description)
                if m:
                    entry.group = m.group(1)

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
                elif attribute_name == "group":
                    entry.group = attribute_value
                # Store all the extra attributes, we will return them later for external apis
                entry.attributes.append({"name": attribute_name, "value": attribute_value})
            entry.details_link = self.get_details_link(entry.guid)
            # Map category. Try to find the most specific category (like 2040), then the more general one (like 2000)
            categories = sorted(categories, reverse=True)  # Sort to make the most specific category appear first
            if len(categories) > 0:
                for k, v in categories_to_newznab.items():
                    for c in categories:
                        if c in v:
                            entry.category = k
                            break

            entries.append(entry)

        return IndexerProcessingResult(entries=entries, queries=[], total=total, total_known=True, has_more=offset + len(entries) < total)

    def check_auth(self, body):
        return check_auth(body)

    def get_nfo(self, guid):
        # try to get raw nfo. if it is xml the indexer doesn't actually return raw nfos (I'm looking at you, DOGNzb)
        url = furl(self.settings.host.get())
        url.path.add("api")
        url.add({"apikey": self.settings.apikey.get(), "t": "getnfo", "o": "xml", "id": guid, "raw": "1"})

        response, papiaccess = self.get_url_with_papi_access(url, "nfo")
        if response is None:
            return False, None, "Unable to access indexer"
      
        nfo = response.content
        if "<?xml" in nfo.decode("utf-8"):  # Hacky but fast
            if 'total="1"' in nfo.decode("utf-8"):
                try:
                    tree = ET.fromstring(nfo)
                    for elem in tree.iter('item'):
                        nfo = elem.find("description").text
                        nfo = nfo.replace("\\n", "\r\n").replace("\/", "/")  # TODO: Not completely correct, looks still a bit werid
                        return True, nfo, None
                except ET.ParseError:
                    logger.error("Error parsing NFO response for indexer %s and GUID %s" % (self.name, guid))
                    return False, None, "Unable to parse response"
            else:
                return False, None, "No NFO available"
        return True, nfo.decode("utf-8"), None #No XML, we just hope it's the NFO
    

    def get_nzb_link(self, guid, title):
        f = furl(self.settings.host.get())
        f.path.add("api")
        f.add({"t": "get", "apikey": self.settings.apikey.get(), "id": guid})
        return f.tostr()


def get_instance(indexer):
    return NewzNab(indexer)
