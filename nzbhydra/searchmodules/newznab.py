from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import re
import xml.etree.ElementTree as ET

import arrow
import concurrent
from arrow.parser import ParserError
from builtins import *
from furl import furl
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from nzbhydra import config
from nzbhydra import infos
from nzbhydra import webaccess
from nzbhydra.categories import getByNewznabCats, getCategoryByAnyInput
from nzbhydra.exceptions import IndexerAuthException, IndexerAccessException, IndexerResultParsingException, IndexerApiLimitReachedException
from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule, IndexerProcessingResult

logger = logging.getLogger('root')


def check_auth(body, indexer):
    if '<error code="100"' in body:
        raise IndexerAuthException("The API key seems to be incorrect.", indexer)
    if '<error code="101"' in body:
        raise IndexerAuthException("The account seems to be suspended.", indexer)
    if '<error code="102"' in body:
        raise IndexerAuthException("You're not allowed to use the API.", indexer)
    if '<error code="910"' in body:
        raise IndexerAccessException("The API seems to be disabled for the moment.", indexer)
    if "Site Maintenance" in body:
        raise IndexerAccessException("Site is down for maintenance.", indexer)
    if '<error code=' in body:
        try:
            tree = ET.fromstring(body)
            code = tree.attrib["code"]
            description = tree.attrib["description"]
            if "Request limit reached" in body:
                raise IndexerApiLimitReachedException("API limit reached", indexer)
            logger.error("Indexer %s returned unknown error code %s with description: %s" % (indexer, code, description))
            exception = IndexerAccessException("Unknown error while trying to access the indexer: %s" % description, indexer)
        except Exception:
            logger.error("Indexer %s returned an error page: %s" % (indexer, body))
            exception = IndexerAccessException("Unknown error while trying to access the indexer.", indexer)
        raise exception


def test_connection(host, apikey, username=None, password=None):
    logger.info("Testing connection for host %s" % host)
    f = furl(host)
    f.path.add("api")
    f.query.add({"t": "tvsearch"})
    if apikey:
        f.query.add({"apikey": apikey})
    try:
        headers = {
            'User-Agent': config.settings.searching.userAgent
        }
        r = webaccess.get(f.url, headers=headers, timeout=config.settings.searching.timeout, auth=HTTPBasicAuth(username, password) if username is not None else None)
        r.raise_for_status()
        check_auth(r.text, host)
    except RequestException as e:
        logger.info("Unable to connect to indexer using URL %s: %s" % (f.url, str(e)))
        return False, "Unable to connect to host"
    except IndexerAuthException as e:
        logger.info("Unable to log in to indexer %s due to wrong credentials: %s" % (host, e.message))
        return False, e.message
    except IndexerApiLimitReachedException as e:
        logger.info("Indexer %s due to wrong credentials: %s" % (host, e.message))
        return False, e.message  # Description already contains "API limit reached" so returning the description should suffice
    except IndexerAccessException as e:
        logger.info("Unable to log in to indexer %s. Unknown error %s." % (host, e.message))
        return False, "Host reachable but unknown error returned"
    logger.info("Connection to host %s successful" % host)
    return True, ""


def _testId(host, apikey, t, idkey, idvalue, expectedResult, username=None, password=None):
    logger.info("Testing for ID capability \"%s\"" % idkey)

    try:
        url = _build_base_url(host, apikey, t, None, 50)
        url.query.add({idkey: idvalue})
        headers = {
            'User-Agent': config.settings.searching.userAgent
        }
        logger.debug("Requesting %s" % url)
        r = webaccess.get(url, timeout=config.settings.searching.timeout, headers=headers, auth=HTTPBasicAuth(username, password) if username is not None else None)
        r.raise_for_status()
        logger.debug("Indexer returned: " + r.text[:500])
        check_auth(r.text, None)
        titles = []
        tree = ET.fromstring(r.content)
    except Exception as e:
        if isinstance(e, IndexerAccessException):
            raise
        else:
            logger.error("Error getting or parsing XML: %s" % e)
            raise IndexerAccessException("Error getting or parsing XML", None)
    for item in tree.find("channel").findall("item"):
        titles.append(item.find("title").text)

    if len(titles) == 0:
        logger.debug("Search with t=%s and %s=%s returned no results" % (t, idkey, idvalue))
        return False, t
    countWrong = 0
    for title in titles:
        title = title.lower()
        if expectedResult.lower() not in title:
            logger.debug("Search with t=%s and %s=%s returned \"%s\" which does not contain the expected string \"%s\"" % (t, idkey, idvalue, title, expectedResult))
            countWrong += 1
    percentWrong = (100 * countWrong) / len(titles)
    if percentWrong > 10:
        logger.info("%d%% wrong results, this indexer probably doesn't support %s" % (percentWrong, idkey))
        return False, t
    logger.info("%d%% wrong results, this indexer probably supports %s" % (percentWrong, idkey))

    return True, t


def checkCapsBruteForce(supportedTypes, toCheck, host, apikey, username=None, password=None):
    supportedIds = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=toCheck) as executor:
        futures_to_ids = {executor.submit(_testId, host, apikey, x["t"], x["id"], x["key"], x["expected"], username=username, password=password): x["id"] for x in toCheck}
        for future in concurrent.futures.as_completed(futures_to_ids):
            id = futures_to_ids[future]
            try:
                supported, t = future.result()
                if supported:
                    supportedIds.append(id)
                    supportedTypes.append(t)
            except Exception as e:
                logger.error("An error occurred while trying to test the caps of host %s: %s" % (host, e))
                raise
    return sorted(list(set(supportedIds))), sorted(list(set(supportedTypes)))


def getCategoryNumberOrNone(categories, ids, names):
    for id in ids:
        if id in categories.keys() and categories[id].lower() in names:
            logger.debug("Found category ID for %s: %s" % (names[0], id))
            return id
    return None


def check_caps(host, apikey, username=None, password=None, userAgent=None, timeout=None, skipIdsAndTypes=False):
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
    supportedIds = []
    supportedTypes = []

    try:
        url = _build_base_url(host, apikey, "caps", None)
        headers = {
            'User-Agent': userAgent if userAgent is not None else config.settings.searching.userAgent
        }
        logger.debug("Requesting %s" % url)
        r = webaccess.get(url, timeout=timeout if timeout is not None else config.settings.searching.timeout, headers=headers, auth=HTTPBasicAuth(username, password) if username is not None else None)
        r.raise_for_status()
        logger.debug("Indexer returned: " + r.text[:500])
    except Exception as e:
        logger.error("Error getting caps XML. Error message: %s" % e)
        return False, e.message, None

    try:
        check_auth(r.content, host)
    except IndexerAccessException as e:
        return False, e.message, None

    try:
        tree = ET.fromstring(r.content)
    except Exception as e:
        logger.error("Unable to parse indexer response")
        return False, e.message, None

    try:
        categories = []
        subCategories = {}
        for xmlMainCategory in tree.find("categories").findall("category"):
            categories.append(xmlMainCategory.attrib["name"].lower())
            for subcat in xmlMainCategory.findall("subcat"):
                subCategories[subcat.attrib["id"]] = subcat.attrib["name"]
        animeCategory = getCategoryNumberOrNone(subCategories, ["5070", "7040"], ["anime", "tv/anime", "tv->anime"])
        comicCategory = getCategoryNumberOrNone(subCategories, ["7030"], ["comic", "comics", "books/comics"])
        magazineCategory = getCategoryNumberOrNone(subCategories, ["7010"], ["magazine", "mags", "magazines"])
        audiobookCategory = getCategoryNumberOrNone(subCategories, ["3030"], ["audiobook", "audio", "audio/audiobook"])
        ebookCategory = getCategoryNumberOrNone(subCategories, ["7020", "4050"], ["ebook"])
        supportedCategories = []
        if "movies" in categories:
            supportedCategories.extend(["movies", "movieshd", "moviessd"])
        if "tv" in categories:
            supportedCategories.extend(["tv", "tvhd", "tvsd"])
        if "audio" in categories or "music" in categories:
            supportedCategories.extend(["audio", "flac", "mp3"])
        if "xxx" in categories or "adult" in categories:
            supportedCategories.append("xxx")
        if "console" in categories or "gaming" in categories or "games" in categories:
            supportedCategories.append("console")
        if "apps" in categories or "pc" in categories:
            supportedCategories.append("pc")
        if animeCategory:
            supportedCategories.append("anime")
        if comicCategory:
            supportedCategories.append("comic")
        if audiobookCategory:
            supportedCategories.append("audiobook")
        if ebookCategory:
            supportedCategories.append("ebook")

        searching = tree.find("searching")
        if searching is not None and not skipIdsAndTypes:
            book_search = searching.find("book-search")
            if book_search is not None and book_search.attrib["available"] == "yes":
                supportedTypes.append("movie")
                logger.debug("Found supported book search")

            can_handle = [y["id"] for y in toCheck]
            supportedIds = [x for x in supportedIds if x in can_handle]  # Only use those we can handle

        if not skipIdsAndTypes:
            logger.info("Checking capabilities of indexer by brute force to make sure supported search types are correctly recognized")
            supportedIds, supportedTypes = checkCapsBruteForce(supportedTypes, toCheck, host, apikey, username=username, password=password)

        # Check indexer type (nzedb, newznab, nntmux)
        try:
            url = _build_base_url(host, apikey, "tvsearch", None)
            headers = {
                'User-Agent': userAgent if userAgent is not None else config.settings.searching.userAgent
            }
            logger.debug("Requesting %s" % url)
            r = webaccess.get(url, timeout=timeout if timeout is not None else config.settings.searching.timeout, headers=headers, auth=HTTPBasicAuth(username, password) if username is not None else None)
            r.raise_for_status()
        except Exception as e:
            logger.error("Unable to connect to indexer to findout indexer backend type: %s" % e)
            return False, "Unable to connect to indexer to findout indexer backend type", None

        logger.debug("Indexer returned: " + r.text[:500])
        generator = ET.fromstring(r.content).find("channel/generator")
        if generator is not None:
            backend = generator.text
            logger.info("Found generator tag indicating that indexer %s is a %s based indexer" % (host, backend))
        else:
            logger.info("Assuming indexer %s is a newznab based indexer" % host)
            backend = "newznab"

        return True, None, {
            "animeCategory": animeCategory,
            "comicCategory": comicCategory,
            "magazineCategory": magazineCategory,
            "audiobookCategory": audiobookCategory,
            "ebookCategory": ebookCategory,
            "supportedIds": sorted(list(set(supportedIds))),
            "supportedTypes": sorted(list(set(supportedTypes))),
            "supportedCategories": supportedCategories,
            "supportsAllCategories": True,
            "backend": backend
        }
    except Exception as e:
        message = e.message if hasattr(e, "message") else str(e)
        logger.error("Error getting or parsing caps XML. Error message: %s" % message)
        return False, "Unable to check caps: %s" % message, None


def _build_base_url(host, apikey, action, category, limit=None, offset=0):
    f = furl(host)
    f.path.add("api")
    f.query.add({"extended": 1, "t": action, "offset": offset})
    if apikey:
        f.query.add({"apikey": apikey})
    if limit is not None:
        f.query.add({"limit": limit})

    if category is not None:
        # If the categories were originally provided as newznab categories use that one
        if category.type == "newznab":
            categories = category.original
        else:
            # Instead use the ones configured for this hydra category
            categories = category.category.newznabCategories
        if len(categories) > 0:
            f.query.add({"cat": ",".join(str(x) for x in categories)})
    return f


class NewzNab(SearchModule):
    grouppattern = re.compile(r"Group:</b> ?([\w\.]+)<br ?/>")
    guidpattern = re.compile(r"(.*/)?([a-zA-Z0-9@\.]+)")

    # todo feature: read caps from server on first run and store them in the config/database
    def __init__(self, settings):
        super(NewzNab, self).__init__(settings)
        self.settings = settings  # Already done by super.__init__ but this way PyCharm knows the correct type
        self.module = "newznab"
        self.category_search = True
        self.supportedFilters = ["maxage"]
        self.supportsNot = True

    def build_base_url(self, action, category, offset=0):
        url = _build_base_url(self.settings.host, self.settings.apikey, action, category, self.limit, offset)
        if config.settings.searching.ignorePassworded:
            url.query.add({"password": "0"})
        return url

    def get_search_urls(self, search_request, search_type="search"):
        f = self.build_base_url(search_type, search_request.category, offset=search_request.offset)
        query = search_request.query
        if query:
            query = self.addExcludedWords(query, search_request)
            f = f.add({"q": query})
        if search_request.maxage:
            f = f.add({"maxage": search_request.maxage})

        return [f.url]

    def addExcludedWords(self, query, search_request):
        if not search_request.forbiddenWords:
            return query
        if "nzbgeek" in self.settings.host:  # NZBGeek isn't newznab but sticks to its standards in most ways but not in this. Instead of adding a new search module just for this small part I added this small POC here
            forbiddenWords = search_request.forbiddenWords
            if len(forbiddenWords) + len(query.split(" ")) > 12:
                self.info("NZBGeek does not support queries with more than 12 included / excluded words. Will limit the query accordingly")
                forbiddenWords = forbiddenWords[:max(12 - len(query.split(" ")), 0)]
            query += "--" + " ".join(["%s" % x for x in forbiddenWords if not (" " in x or "-" in x or "." in x)])
        else:
            for word in search_request.forbiddenWords:
                if " " in word or "-" in word or "." in word:
                    self.debug('Not using ignored word "%s" in query because it contains a space, dash or dot which is not supported by newznab queries' % word)
                    continue
                if self.settings.backend.lower() in ["nntmux", "nzedb"] or "omgwtf" in self.settings.host:
                    query += ",!" + word
                else:
                    query += " --" + word
        return query

    def get_showsearch_urls(self, search_request):
        if search_request.category is None:
            search_request.category = getCategoryByAnyInput("tv")

        url = self.build_base_url("tvsearch", search_request.category, offset=search_request.offset)
        if search_request.identifier_key:
            canBeConverted, toType, id = infos.convertIdToAny(search_request.identifier_key, self.search_ids, search_request.identifier_value)
            if canBeConverted:
                search_request.identifier_key = toType.replace("tvrage", "rid").replace("tvdb", "tvdbid")
                search_request.identifier_value = id
            else:
                self.info("Unable to search using ID type %s" % search_request.identifier_key)
                return []

            url.add({search_request.identifier_key: search_request.identifier_value})
        if search_request.episode:
            url.add({"ep": search_request.episode})
        if search_request.season:
            url.add({"season": search_request.season})
        if search_request.query:
            url.add({"q": search_request.query})
        if search_request.maxage:
            url.add({"maxage": search_request.maxage})

        return [url.url]

    def get_moviesearch_urls(self, search_request):
        if search_request.category is None:
            search_request.category = getCategoryByAnyInput("movies")

        # A lot of indexers seem to disregard the "q" parameter for "movie" search, so if we have a query use regular search instead 
        if search_request.query:
            url = self.build_base_url("search", search_request.category, offset=search_request.offset)
            url.add({"q": search_request.query})
        else:
            url = self.build_base_url("movie", search_request.category, offset=search_request.offset)
            if search_request.identifier_key:
                canBeConverted, toType, id = infos.convertIdToAny(search_request.identifier_key, self.search_ids, search_request.identifier_value)
                if canBeConverted:
                    search_request.identifier_key = toType.replace("tvrage", "rid").replace("tvdb", "tvdbid").replace("imdb", "imdbid")
                    search_request.identifier_value = id
                else:
                    self.info("Unable to search using ID type %s" % search_request.identifier_key)
                    return []

                url.add({search_request.identifier_key: search_request.identifier_value})
        if search_request.maxage:
            url.add({"maxage": search_request.maxage})

        return [url.url]

    def get_ebook_urls(self, search_request):
        if not search_request.category:
            search_request.category = getCategoryByAnyInput("ebook")
        if hasattr(self.settings, "ebookCategory") and self.settings.ebookCategory:
            self.debug("Using %s as determinted newznab ebook category" % self.settings.ebookCategory)
            search_request.category.category.newznabCategories = [self.settings.ebookCategory]
        if search_request.author or search_request.title:
            if "book" in self.searchTypes:
                # API search
                url = self.build_base_url("book", search_request.category, offset=search_request.offset)
                if search_request.author:
                    url.add({"author": search_request.author})
                if search_request.title:
                    url.add({"title": search_request.title})
                return [url.url]
            else:
                search_request.query = "%s %s" % (search_request.author if search_request.author else "", search_request.title if search_request.title else "")
                return self.get_search_urls(search_request)
        else:
            # internal search
            return self.get_search_urls(search_request)

    def get_audiobook_urls(self, search_request):
        if not search_request.category:
            search_request.category = getCategoryByAnyInput("audiobook")
        if hasattr(self.settings, "audiobookCategory") and self.settings.audiobookCategory:
            self.debug("Using %s as determinted newznab audiobook category" % self.settings.audiobookCategory)
            search_request.category.category.newznabCategories = [self.settings.audiobookCategory]
        return self.get_search_urls(search_request)

    def get_comic_urls(self, search_request):
        if not search_request.category:
            search_request.category = getCategoryByAnyInput("comic")
        if hasattr(self.settings, "comicCategory") and self.settings.comicCategory:
            self.debug("Using %s as determinted newznab comic category" % self.settings.comicCategory)
            search_request.category.category.newznabCategories = [self.settings.comicCategory]
        return self.get_search_urls(search_request)

    def get_anime_urls(self, search_request):
        if not search_request.category:
            search_request.category = getCategoryByAnyInput("anime")
        if hasattr(self.settings, "animeCategory") and self.settings.animeCategory:
            self.debug("Using %s as determinted newznab anime category" % self.settings.animeCategory)
            search_request.category.category.newznabCategories = [self.settings.animeCategory]
        return self.get_search_urls(search_request)

    def get_details_link(self, guid):
        if "nzbgeek" in self.settings.host:
            f = furl(self.settings.host)
        else:
            f = furl(self.settings.host.replace("api.", "www."))  # Quick and dirty fix so it doesn't link to the API

        f.path.add("details")
        f.path.add(guid)
        return f.url

    def get_entry_by_id(self, guid, title):
        url = furl(self.settings.host)
        url.path.add("api")
        url.add({"t": "details", "o": "xml", "id": guid})
        if self.settings.apikey:
            url.add({"apikey": self.settings.apikey, "t": "details", "o": "xml", "id": guid})

        response, papiaccess, _ = self.get_url_with_papi_access(url, "nfo")
        if response is None:
            return None
        try:
            tree = ET.fromstring(response.content)
            item = tree.find("channel").find("item")
            return self.parseItem(item)
        except ET.ParseError:
            self.error("Error parsing response for GUID %s" % guid)
            return None

    def process_query_result(self, xml_response, searchRequest, maxResults=None):
        self.debug("Started processing results")
        countRejected = self.getRejectedCountDict()
        acceptedEntries = []
        entries, total, offset = self.parseXml(xml_response, maxResults)

        for entry in entries:
            accepted, reason, ri = self.accept_result(entry, searchRequest, self.supportedFilters)
            if accepted:
                acceptedEntries.append(entry)
            else:
                countRejected[ri] += 1
                self.debug("Rejected search result. Reason: %s" % reason)

        if total == 0 or len(acceptedEntries) == 0:
            self.info("Query returned no results")
            return IndexerProcessingResult(entries=acceptedEntries, queries=[], total=0, total_known=True, has_more=False, rejected=countRejected)
        else:
            return IndexerProcessingResult(entries=acceptedEntries, queries=[], total=total, total_known=True, has_more=offset + len(entries) < total, rejected=countRejected)

    def parseXml(self, xmlResponse, maxResults=None):
        entries = []

        try:
            tree = ET.fromstring(xmlResponse)
        except Exception:
            self.exception("Error parsing XML: %s..." % xmlResponse[:500])
            raise IndexerResultParsingException("Error parsing XML", self)
        for item in tree.find("channel").findall("item"):
            entry = self.parseItem(item)
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
        return entries, total, offset

    def parseItem(self, item):
        usenetdate = None
        entry = self.create_nzb_search_result()
        # These are the values that absolutely must be contained in the response
        entry.title = item.find("title").text
        if entry.title and "nzbgeek" in self.settings.host and config.settings.searching.removeObfuscated:
            entry.title = entry.title.replace("-Obfuscated", "")
        if config.settings.searching.removeLanguage:
            for word in [" English", " Korean", " Spanish", " French", " German", " Italian", " Danish", " Dutch", " Japanese", " Cantonese", " Mandarin", " Russian", " Polish", " Vietnamese", " Swedish", " Norwegian", " Finnish", " Turkish", " Portuguese", " Flemish", " Greek", " Hungarian"]:
                if entry.title.endswith(word):
                    self.debug("Removing trailing%s from title %s" % (word, entry.title))
                    entry.title = entry.title[:-len(word)]
                    break
        entry.link = item.find("link").text
        entry.pubDate = item.find("pubDate").text
        guid = item.find("guid")
        entry.indexerguid = guid.text
        if "isPermaLink" in guid.attrib.keys() and guid.attrib["isPermaLink"] == "true":
            entry.details_link = entry.indexerguid
            m = self.guidpattern.search(entry.indexerguid)
            if m:
                # Extract GUID from link
                entry.indexerguid = m.group(2)
        if not entry.details_link:
            comments = item.find("comments")
            # Example: https://nzbfinder.ws/details/1234567jagkshsg72hs8whgs6#comments
            if comments is not None:
                entry.details_link = comments.text.replace("#comments", "")
        entry.has_nfo = NzbSearchResult.HAS_NFO_MAYBE
        description = item.find("description")
        if description is not None:
            description = description.text
            if description is not None and "Group:" in description:  # DogNZB has the group in its description
                m = self.grouppattern.search(description)
                if m and m.group(1) != "not available":
                    entry.group = m.group(1)
        categories = []
        for i in item.findall("./newznab:attr", {"newznab": "http://www.newznab.com/DTD/2010/feeds/attributes/"}):
            attribute_name = i.attrib["name"]
            attribute_value = i.attrib["value"]
            if attribute_name == "guid":
                entry.indexerguid = attribute_value
            elif attribute_name == "category" and attribute_value != "":
                try:
                    categories.append(int(attribute_value))
                except ValueError:
                    self.error("Unable to parse category %s" % attribute_value)
            elif attribute_name == "password" and attribute_value != "0":
                entry.passworded = True
            elif attribute_name == "nfo":
                entry.has_nfo = NzbSearchResult.HAS_NFO_YES if int(attribute_value) == 1 else NzbSearchResult.HAS_NFO_NO
            elif attribute_name == "info" and self.settings.backend.lower() in ["nzedb", "nntmux"]:
                entry.has_nfo = NzbSearchResult.HAS_NFO_YES
            elif attribute_name == "group" and attribute_value != "not available":
                entry.group = attribute_value
            elif attribute_name == "usenetdate":
                try:
                    usenetdate = arrow.get(attribute_value, ['ddd, DD MMM YYYY HH:mm:ss Z', 'ddd, DD MMM YYYY HH:mm:ss ZZZ', 'ddd, DD MMM YYYY HH:mm Z', 'ddd, DD MMM YYYY HH:mm A Z'])
                except ParserError:
                    self.debug("Unable to parse usenet date format: %s" % attribute_value)
                    usenetdate = None
            else:
                for x in ["size", "files", "comments", "grabs"]:
                    if attribute_name == x:
                        setattr(entry, x, int(attribute_value))
                    else:
                        for x in ["guid", "poster"]:
                            if attribute_name == x:
                                setattr(entry, x, attribute_value)

            # Store all the attributes, we will return them later for external apis
            entry.attributes.append({"name": attribute_name, "value": attribute_value})
        if self.settings.backend.lower() in ["nzedb", "nntmux"] and entry.has_nfo == NzbSearchResult.HAS_NFO_MAYBE:
            # If the "info" attribute wasn't found this entry doesn't have an NFO
            entry.has_nfo = NzbSearchResult.HAS_NFO_NO
        if not entry.details_link:
            entry.details_link = self.get_details_link(entry.indexerguid)
        if usenetdate is None:
            # Not provided by attributes, use pubDate instead
            usenetdate = arrow.get(entry.pubDate, ['ddd, DD MMM YYYY HH:mm:ss Z', 'ddd, DD MMM YYYY HH:mm:ss ZZZ', 'ddd, DD MMM YYYY HH:mm Z', 'ddd, DD MMM YYYY HH:mm A Z'])
        self.getDates(entry, usenetdate)
        entry.category = getByNewznabCats(categories)
        return entry

    def check_auth(self, body):
        return check_auth(body, self)

    def get_nfo(self, guid):
        # try to get raw nfo. if it is xml the indexer doesn't actually return raw nfos (I'm looking at you, DOGNzb)
        url = furl(self.settings.host)
        url.path.add("api")
        if self.settings.backend.lower() in ["nzedb", "nntmux"]:
            logger.debug("Using t=info for nzedb or nntmux based indexer")
            t = "info"
        else:
            logger.debug("Using t=getnfo for non-nzedb based indexer")
            t = "getnfo"
        url.add({"t": t, "o": "xml", "id": guid, "raw": "1"})
        if self.settings.apikey:
            url.add({"apikey": self.settings.apikey})

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
        f = furl(self.settings.host)
        f.path.add("api")
        f.add({"t": "get", "id": guid})
        if self.settings.apikey:
            f.add({"apikey": self.settings.apikey})
        return f.tostr()


def get_instance(indexer):
    return NewzNab(indexer)
