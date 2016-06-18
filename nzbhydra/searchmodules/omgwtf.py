from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import json

from builtins import super
from builtins import str
from builtins import int
from future import standard_library
#standard_library.install_aliases()
from builtins import *
import logging
import re

import arrow
import xml.etree.ElementTree as ET

from furl import furl
from requests.exceptions import RequestException
import requests
from nzbhydra import config
from nzbhydra.categories import getUnknownCategory, getCategoryByAnyInput, getCategoryByName

from nzbhydra.exceptions import IndexerResultParsingException, IndexerAccessException, IndexerAuthException, IndexerResultParsingRowException
from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import SearchModule, IndexerProcessingResult
from nzbhydra import infos

logger = logging.getLogger('root')

categories_to_omgwtf = { 
    'all': [],
    'movies': ["15", "16", "17", "18"],
    'movieshd': ["16"],
    'moviessd': ["15"],
    'tv': ["19", "20", "21"],
    'tvsd': ["19"],
    'tvhd': ["20"],
    'audio': ["3", "7", "8", "22"],
    'flac': ["22"],
    'mp3': ["7"],
    'audiobook': ["29"],
    'console': ["14"],
    'pc': ["1", "12"],
    'xxx': ["23", "24", "25", "26", "27", "28"],
    'na': ["11"],
    'ebook': ["9"],
    'comic': ["9"]
}

omgwtf_to_categories = {
    "1": "pc",
    "2": "other",
    "3": "audio",
    "4": "na",
    "5": "na",
    "6": "na",
    "7": "mp3",
    "8": "audio",
    "9": "ebook",
    "10": "na",
    "11": "na",
    "12": "pc",
    "13": "na",
    "14": "na",
    "15": "moviessd",
    "16": "movieshd",
    "17": "movies",
    "18": "movies",
    "19": "tvsd",
    "20": "tvhd",
    "21": "tv",
    "22": "flac",
    "23": "xxx",
    "24": "xxx",
    "25": "xxx",
    "26": "xxx",
    "27": "xxx",
    "28": "xxx",
    "29": "audiobook",
}

newznab_to_omgwtf = {
    "2000": ["15", "16", "17", "18"],
    '2040': ["16"],
    '2030': ["15"],
    '5000': ["19", "20", "21"],
    '5030': ["19"],
    '5040': ["20"],
    '3000': ["3", "7", "8", "22", "29"],
    '3040': ["22"],
    '3030': ["29"],
    '3010': ["7"],
    '1000': ["14"],
    '4000': ["1", "12"],
    '6000': ["23", "24", "25", "26", "27", "28"],
    '7000': ["11"],
    '7020': ["9"],
    '7030': ["9"]
}


def map_category(category):
    if not category:
        return []
    
    if category.type == "hydra":
        if category.category.name == "all":
            return []
        logger.debug("Mapped category %s to %s" % (category.category.name, categories_to_omgwtf[category.category.name]))
        return categories_to_omgwtf[category.category.name]
    cats = []
    for x in category.category.newznabCategories:
        if str(x) in newznab_to_omgwtf.keys():
            cats.extend(newznab_to_omgwtf[str(x)])
    return cats

def test_connection(apikey, username):
    logger.info("Testing connection for omgwtfnzbs")
    from nzbhydra.indexers import getIndexerSettingByType
    f = furl(getIndexerSettingByType("omgwtf").host)
    f.path.add("xml")
    f = f.add({"api": apikey, "user": username})
    try:
        headers = {
            'User-Agent': config.settings.searching.userAgent
        }
        r = requests.get(f.url, verify=False, headers=headers, timeout=config.settings.searching.timeout)
        r.raise_for_status()
        if "your user/api information is incorrect" in r.text:
            raise IndexerAuthException("Wrong credentials", None)
    except RequestException as e:
        logger.info("Unable to connect to indexer using URL %s: %s" % (f.url, str(e)))
        return False, "Unable to connect to host"
    except IndexerAuthException:
        logger.info("Unable to log in to indexer omgwtfnzbs due to wrong credentials")
        return False, "Wrong credentials"
    except IndexerAccessException as e:
        logger.info("Unable to log in to indexer omgwtfnzbs. Unknown error %s." % str(e))
        return False, "Host reachable but unknown error returned"
    return True, ""


class OmgWtf(SearchModule):
    
    regexGuid = re.compile(r".*\?id=(\w+)&.*")
    regexGroup = re.compile(r".*Group:<\/b> ([\w\.\-]+)<br \/>.*")
    
    def __init__(self, indexer):
        super(OmgWtf, self).__init__(indexer)
        self.module = "omgwtfnzbs.org"

        self.supports_queries = True  # We can only search using queries
        self.needs_queries = False
        self.category_search = True
        self.supportedFilters = ["maxage"]
        self.supportsNot = False #Why does anybody use this POS

    def build_base_url(self):
        f = furl(self.host)
        f = f.add({"api": self.settings.apikey, "user": self.settings.username})
        return f

    def get_search_urls(self, search_request):
        if search_request.offset > 0:
            return []
        f = self.build_base_url()
        cats = map_category(search_request.category)
        if search_request.query:
            #Query based XML search
            f.path.add("xml/")
            f = f.add({"search": search_request.query})
            if search_request.maxage:
                f = f.add({"retention": search_request.maxage})        
            if len(cats) > 0:
                f = f.add({"catid": ",".join(cats)})
        else:
            #RSS
            f.host = f.host.replace("api", "rss") #Haaaaacky
            f.path.add("rss-download.php")
            if len(cats) > 0:
                f = f.add({"catid": ",".join(cats)})
            
        return [f.tostr()]

    def get_showsearch_urls(self, search_request):
        if search_request.category is None:
            search_request.category = getCategoryByAnyInput("tv")
        #Should get most results, apparently there is no way of using "or" searches
        if search_request.query:
            query = search_request.query
        elif search_request.title:
            query = search_request.title
        else:
            query = ""
        if search_request.season:
            if search_request.episode:
                search_request.query = "{0} s{1:02d}e{2:02d}".format(query, int(search_request.season), int(search_request.episode))
            else:
                search_request.query = "{0} s{1:02d}".format(query, int(search_request.season))
            
        return self.get_search_urls(search_request)

    def get_moviesearch_urls(self, search_request):
        if search_request.category is None:
            search_request.category = getCategoryByAnyInput("movies")
        if search_request.identifier_key:
            canBeConverted, toType, id = infos.convertIdToAny(search_request.identifier_key, ["imdb"], search_request.identifier_value)
            if canBeConverted:
                search_request.query = "tt%s" % id
            
        return self.get_search_urls(search_request)
    
    def get_details_link(self, guid):
        f = furl(self.host)
        f.path.add("details.php")
        f = f.add({"id": guid})
        return f.tostr()

    def get(self, query, timeout=None, cookies=None):
        # overwrite for special handling, e.g. cookies
        if timeout is None:
            timeout = self.settings.timeout
        if timeout is None:
            timeout = config.settings.searching.timeout
        return requests.get(query, timeout=timeout, verify=False)

    def get_ebook_urls(self, search_request):
        if not search_request.query and (search_request.author or search_request.title):
            search_request.query = "%s %s" % (search_request.author if search_request.author else "", search_request.title if search_request.title else "")
        if search_request.category is None:
            search_request.category = getCategoryByAnyInput("ebook")
        return self.get_search_urls(search_request)

    def get_audiobook_urls(self, search_request):
        if search_request.category is None:
            search_request.category = getCategoryByAnyInput("audiobook")
        return self.get_search_urls(search_request)

    def get_comic_urls(self, search_request):
        if not search_request.category:
            search_request.category = getCategoryByAnyInput("comic")
        logger.info("Searching for comics in ebook category")
        return self.get_search_urls(search_request)

    def process_query_result(self, xml_response, searchRequest, maxResults=None):
        self.debug("Started processing results")

        if "0 results found" in xml_response:
            return IndexerProcessingResult(entries=[], queries=[], total=0, total_known=True, has_more=False, rejected=0)
        if "search to short" in xml_response:
            self.info("omgwtf says the query was too short")
            return IndexerProcessingResult(entries=[], queries=[], total=0, total_known=True, has_more=False, rejected=0)
            
        entries = []
        countRejected = 0
        try:
            tree = ET.fromstring(xml_response)
        except Exception:
            self.exception("Error parsing XML: %s..." % xml_response[:500])
            raise IndexerResultParsingException("Error parsing XML", self)
        
        if tree.tag == "xml":
            total = int(tree.find("info").find("results").text)
            current_page = int(tree.find("info").find("current_page").text)
            total_pages = int(tree.find("info").find("pages").text)
            has_more = current_page < total_pages
            for item in tree.find("search_req").findall("post"):
                entry = self.parseItem(item)
                accepted, reason = self.accept_result(entry, searchRequest, self.supportedFilters)
                if accepted:
                    entries.append(entry)
                else:
                    countRejected += 1
                    self.debug("Rejected search result. Reason: %s" % reason)
            return IndexerProcessingResult(entries=entries, queries=[], total=total, total_known=True, has_more=has_more, rejected=countRejected)      
        elif tree.tag == "rss":
            for item in tree.find("channel").findall("item"):
                entry = self.create_nzb_search_result()
                indexerguid = item.find("guid").text
                m = self.regexGuid.match(indexerguid)
                if m:
                    entry.indexerguid = m.group(1)
                else:
                    self.warn("Unable to find GUID in " + indexerguid)
                    raise IndexerResultParsingRowException("Unable to find GUID")
                entry.title = item.find("title").text
                description = item.find("description").text
                m = self.regexGroup.match(description)
                if m:
                    entry.group = m.group(1)
                else:
                    self.warn("Unable to find group in " + description)
                    raise IndexerResultParsingRowException("Unable to find usenet group")
                entry.size = long(item.find("enclosure").attrib["length"])
                entry.pubDate = item.find("pubDate").text
                pubdate = arrow.get(entry.pubDate, 'ddd, DD MMM YYYY HH:mm:ss Z')
                entry.epoch = pubdate.timestamp
                entry.pubdate_utc = str(pubdate)
                entry.age_days = (arrow.utcnow() - pubdate).days
                entry.precise_date = True
                entry.link = item.find("link").text
                entry.has_nfo = NzbSearchResult.HAS_NFO_MAYBE
                categoryid = item.find("categoryid").text
                entry.details_link = self.get_details_link(entry.indexerguid)
                if categoryid in omgwtf_to_categories.keys():
                    entry.category = getCategoryByName(omgwtf_to_categories[categoryid])
                else:
                    entry.category = getUnknownCategory()
                accepted, reason = self.accept_result(entry, searchRequest, self.supportedFilters)
                if accepted:
                    entries.append(entry)
                else:
                    countRejected += 1
                    self.debug("Rejected search result. Reason: %s" % reason)
            return IndexerProcessingResult(entries=entries, queries=[], total=len(entries), total_known=True, has_more=False, rejected=countRejected)
        else:
            self.warn("Unknown response type: %s" % xml_response[:100])
            return IndexerProcessingResult(entries=[], queries=[], total=0, total_known=True, has_more=False, rejected=countRejected)

    def parseItem(self, item):
        entry = self.create_nzb_search_result()
        entry.indexerguid = item.find("nzbid").text
        entry.title = item.find("release").text
        entry.group = item.find("group").text
        entry.link = item.find("getnzb").text
        entry.size = long(item.find("sizebytes").text)
        entry.epoch = long(item.find("usenetage").text)
        pubdate = arrow.get(entry.epoch)
        entry.pubdate_utc = str(pubdate)
        entry.pubDate = pubdate.format("ddd, DD MMM YYYY HH:mm:ss Z")
        entry.age_days = (arrow.utcnow() - pubdate).days
        entry.age_precise = True
        entry.details_link = item.find("details").text
        entry.has_nfo = NzbSearchResult.HAS_NFO_YES if item.find("getnfo") is not None else NzbSearchResult.HAS_NFO_NO
        categoryid = item.find("categoryid").text
        if categoryid in omgwtf_to_categories.keys():
            entry.category = getCategoryByName(omgwtf_to_categories[categoryid])
        else:
            entry.category = getUnknownCategory()
        return entry

    def get_nfo(self, guid):
        f = furl(self.host)
        f.path.add("nfo")
        f = f.add({"id": guid, "api": self.settings.apikey, "user": self.settings.username, "send": "1"})
        r, papiaccess, _ = self.get_url_with_papi_access(f.tostr(), "nfo")
        return True, r.text, None
        

    def get_nzb_link(self, guid, title):
        f = furl(self.host)
        f.path.add("nzb")
        f = f.add({"id": guid, "api": self.settings.apikey, "user": self.settings.username})
        return f.tostr()

    def check_auth(self, xml):
        if "your user/api information is incorrect.. check and try again" in xml:
            raise IndexerAuthException("Wrong API key or username", None)
        if "applying some updates please try again later." in xml:
            raise IndexerAccessException("Indexer down for maintenance", None)
        


def get_instance(indexer):
    return OmgWtf(indexer)
