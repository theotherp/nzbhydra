from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from future import standard_library

from nzbhydra import config

#standard_library.install_aliases()
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
from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.datestuff import now
from nzbhydra import infos
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


def check_auth(body, indexer):
    if '<error code="100"' in body:
        raise IndexerAuthException("The API key seems to be incorrect.", indexer)
    if '<error code="101"' in body:
        raise IndexerAuthException("The account seems to be suspended.", indexer)
    if '<error code="102"' in body:
        raise IndexerAuthException("You're not allowed to use the API.", indexer)
    if '<error code="910"' in body:
        raise IndexerAccessException("The API seems to be disabled for the moment.", indexer)
    if '<error code=' in body:
        raise IndexerAccessException("Unknown error while trying to access the indexer.", indexer)


def test_connection(host, apikey):
    logger.info("Testing connection for host %s" % host)
    f = furl(host)
    f.path.add("api")
    f.query.add({"apikey": apikey, "t": "tvsearch"})
    try:
        headers = {
            'User-Agent': config.searchingSettings.user_agent.get()
        }
        r = requests.get(f.url, verify=False, headers=headers, timeout=config.searchingSettings.timeout.get())
        r.raise_for_status()
        check_auth(r.text, None)
    except RequestException as e:
        logger.info("Unable to connect to indexer using URL %s: %s" % (f.url, str(e)))
        return False, "Unable to connect to host"
    except IndexerAuthException:
        logger.info("Unable to log in to indexer %s due to wrong credentials" % host)
        return False, "Wrong credentials"
    except IndexerAccessException as e:
        logger.info("Unable to log in to indexer %s. Unknown error %s." % (host, str(e)))
        return False, "Host reachable but unknown error returned"
    return True, ""


def _testId(host, apikey, t, idkey, idvalue, expectedResult):
    logger.info("Testing for ID capability \"%s\"" % idkey)

    try:
        url = _build_base_url(host, apikey, t, None, 25)
        url.query.add({idkey: idvalue})
        headers = {
            'User-Agent': config.searchingSettings.user_agent.get()
        }
        logger.debug("Requesting %s" % url)
        r = requests.get(url, verify=False, timeout=config.searchingSettings.timeout.get(), headers=headers)
        r.raise_for_status()
        titles = []
        tree = ET.fromstring(r.content)
    except Exception:
        logger.exception("Error getting or parsing XML")
        raise IndexerAccessException("Error getting or parsing XML", None)
    for item in tree.find("channel").findall("item"):
        titles.append(item.find("title").text)
    
    
    if len(titles) == 0:
        logger.debug("Search with t=%s and %s=%s returned no results" % (t, idkey, idvalue))
        return False
    countWrong = 0
    for title in titles:
        title = title.lower()
        if expectedResult.lower() not in title:
            logger.debug("Search with t=%s and %s=%s returned \"%s\" which does not contain the expected string \"%s\"" % (t, idkey, idvalue, title, expectedResult))
            countWrong += 1
    percentWrong = (100 * countWrong) / len(titles)
    if percentWrong > 30:
        logger.info("%d%% wrong results, this indexer probably doesn't support %s" % (percentWrong, idkey))
        return False
    logger.info("%d%% wrong results, this indexer probably supports %s" % (percentWrong, idkey))

    return True


def check_caps(host, apikey):
    toCheck = [
        {"t": "tvsearch",
         "id": "tvdbid",
         "key": "121361",
         "expected": "Thrones"
         },
        {"t": "movie",
         "id": "imdbid",
         "key": "0848228",
         "expected": "Avengers"
         },
        {"t": "tvsearch",
         "id": "rid",
         "key": "24493",
         "expected": "Thrones"
         },
        {"t": "tvsearch",
         "id": "tvmazeid",
         "key": "82",
         "expected": "Thrones"
         },
        {"t": "tvsearch",
         "id": "traktid",
         "key": "1390",
         "expected": "Thrones"
         },
        {"t": "tvsearch",
         "id": "tmdbid",
         "key": "1399",
         "expected": "Thrones"
         }

    ]
    result = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(toCheck)) as executor:
        futures_to_ids = {executor.submit(_testId, host, apikey, x["t"], x["id"], x["key"], x["expected"]): x["id"] for x in toCheck}
        for future in concurrent.futures.as_completed(futures_to_ids):
            id = futures_to_ids[future]
            try:
                supported = future.result()
                if supported:
                    result.append(id)
            except Exception as e:
                logger.error("An error occurred while trying to test the caps of host %s" % host)
                raise IndexerResultParsingException("Unable to check caps: %s" % str(e), None)
    return result


def _build_base_url(host, apikey, action, category, limit, offset=0):
    f = furl(host)
    f.path.add("api")
    url = f.add({"apikey": apikey, "extended": 1, "t": action, "limit": limit, "offset": offset})

    if category is not None:
        categories = map_category(category)
        if len(categories) > 0:
            url.add({"cat": ",".join(str(x) for x in categories)})
    return url


class NewzNab(SearchModule):
    # todo feature: read caps from server on first run and store them in the config/database
    def __init__(self, settings):
        super(NewzNab, self).__init__(settings)
        self.settings = settings  # Already done by super.__init__ but this way PyCharm knows the correct type
        self.module = "newznab"
        self.category_search = True
    

    def build_base_url(self, action, category, offset=0):
        return _build_base_url(self.settings.host.get(), self.settings.apikey.get(), action, category, self.limit, offset)

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
            canBeConverted, toType, id = infos.convertIdToAny(search_request.identifier_key, self.search_ids, search_request.identifier_value)
            if canBeConverted:
                search_request.identifier_key = toType.replace("tvrage", "rid").replace("tvdb", "tvdbid")
                search_request.identifier_value = id
            else:
                self.info("Unable to search using ID type %s" % search_request.identifier_key)
                return []

            url.add({search_request.identifier_key: search_request.identifier_value})
        if search_request.episode is not None:
            url.add({"ep": search_request.episode})
        if search_request.season is not None:
            url.add({"season": search_request.season})
        if search_request.query is not None and search_request.query != "":
            url.add({"q": search_request.query})

        return [url.url]

    def get_moviesearch_urls(self, search_request):
        if search_request.category is None:
            search_request.category = "Movies"
        
        #A lot of indexers seem to disregard the "q" parameter for "movie" search, so if we have a query use regular search instead 
        if search_request.query is not None:
            url = self.build_base_url("search", search_request.category, offset=search_request.offset)
            url.add({"q": search_request.query})
        else:
            url = self.build_base_url("movie", search_request.category, offset=search_request.offset)
            if search_request.identifier_key is not None:
                canBeConverted, toType, id = infos.convertIdToAny(search_request.identifier_key, self.search_ids, search_request.identifier_value)
                if canBeConverted:
                    search_request.identifier_key = toType.replace("tvrage", "rid").replace("tvdb", "tvdbid").replace("imdb", "imdbid")
                    search_request.identifier_value = id
                else:
                    self.info("Unable to search using ID type %s" % search_request.identifier_key)
                    return []
                
                url.add({search_request.identifier_key: search_request.identifier_value})

        return [url.url]

    def get_ebook_urls(self, search_request):
        search_request.query += " ebook|mobi|pdf|epub"
        return self.get_search_urls(search_request)

    def get_details_link(self, guid):
        f = furl(self.settings.host.get())
        f.path.add("details")
        f.path.add(guid)
        return f.url

    def process_query_result(self, xml_response, maxResults=None):
        self.debug("Started processing results")

        entries = []
        grouppattern = re.compile(r"Group:</b> ?([\w\.]+)<br ?/>")
        guidpattern = re.compile(r"(.*/)?([a-zA-Z0-9]+)")

        try:
            tree = ET.fromstring(xml_response)
        except Exception:
            self.exception("Error parsing XML: %s..." % xml_response[:500])
            raise IndexerResultParsingException("Error parsing XML", self)
        for item in tree.find("channel").findall("item"):
            usenetdate = None
            entry = self.create_nzb_search_result()
            # These are the values that absolutely must be contained in the response
            entry.title = item.find("title").text
            entry.link = item.find("link").text
            entry.attributes = []
            entry.pubDate = item.find("pubDate").text
            entry.guid = item.find("guid").text
            entry.has_nfo = NzbSearchResult.HAS_NFO_MAYBE
            m = guidpattern.search(entry.guid)
            if m:
                entry.guid = m.group(2)

            description = item.find("description").text
            if description is not None and "Group:" in description:  # DogNZB has the group in its description
                m = grouppattern.search(description)
                if m and m.group(1) != "not available":
                    entry.group = m.group(1)

            categories = []
            for i in item.findall("./newznab:attr", {"newznab": "http://www.newznab.com/DTD/2010/feeds/attributes/"}):
                attribute_name = i.attrib["name"]
                attribute_value = i.attrib["value"]
                if attribute_name == "size":
                    entry.size = int(attribute_value)
                elif attribute_name == "guid":
                    entry.guid = attribute_value
                elif attribute_name == "category" and attribute_value != "":
                    try:
                        categories.append(int(attribute_value))
                    except ValueError:
                        self.error("Unable to parse category %s" % attribute_value)
                elif attribute_name == "poster":
                    entry.poster = attribute_value
                elif attribute_name == "info":
                    entry.details_link = attribute_value
                elif attribute_name == "group" and attribute_value != "not available":
                    entry.group = attribute_value
                elif attribute_name == "usenetdate":
                    usenetdate = arrow.get(attribute_value, 'ddd, DD MMM YYYY HH:mm:ss Z')
                # Store all the extra attributes, we will return them later for external apis
                entry.attributes.append({"name": attribute_name, "value": attribute_value})
            if entry.details_link is None:
                entry.details_link = self.get_details_link(entry.guid)

            if usenetdate is None:
                # Not provided by attributes, use pubDate instead
                usenetdate = arrow.get(entry.pubDate, 'ddd, DD MMM YYYY HH:mm:ss Z')
            entry.epoch = usenetdate.timestamp
            entry.pubdate_utc = str(usenetdate)
            entry.age_days = (arrow.utcnow() - usenetdate).days
            entry.precise_date = True

            # Map category. Try to find the most specific category (like 2040), then the more general one (like 2000)
            categories = sorted(categories, reverse=True)  # Sort to make the most specific category appear first
            if len(categories) > 0:
                for k, v in categories_to_newznab.items():
                    for c in categories:
                        if c in v:
                            entry.category = k
                            break

            entries.append(entry)
            if maxResults is not None and len(entries) == maxResults:
                break

        response_total_offset = tree.find("./channel[1]/newznab:response", {"newznab": "http://www.newznab.com/DTD/2010/feeds/attributes/"})
        if response_total_offset is None or response_total_offset.attrib["total"] == "" or response_total_offset.attrib["offset"] == "":
            self.warn("Indexer returned a result page without total results and offset. Shame! *rings bell*")
            offset = 0
            total = len(entries)
        else:
            total = int(response_total_offset.attrib["total"])
            offset = int(response_total_offset.attrib["offset"])
        if total == 0 or len(entries) == 0:
            self.info("Query returned no results")
            return IndexerProcessingResult(entries=entries, queries=[], total=0, total_known=True, has_more=False)

        return IndexerProcessingResult(entries=entries, queries=[], total=total, total_known=True, has_more=offset + len(entries) < total)

    def check_auth(self, body):
        return check_auth(body, self)

    def get_nfo(self, guid):
        # try to get raw nfo. if it is xml the indexer doesn't actually return raw nfos (I'm looking at you, DOGNzb)
        url = furl(self.settings.host.get())
        url.path.add("api")
        url.add({"apikey": self.settings.apikey.get(), "t": "getnfo", "o": "xml", "id": guid, "raw": "1"})

        response, papiaccess, _ = self.get_url_with_papi_access(url, "nfo")
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
                    self.error("Error parsing NFO response for GUID %s" % guid)
                    return False, None, "Unable to parse response"
            else:
                return False, None, "No NFO available"
        return True, nfo.decode("utf-8"), None  # No XML, we just hope it's the NFO

    def get_nzb_link(self, guid, title):
        f = furl(self.settings.host.get())
        f.path.add("api")
        f.add({"t": "get", "apikey": self.settings.apikey.get(), "id": guid})
        return f.tostr()


def get_instance(indexer):
    return NewzNab(indexer)
