from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from arrow.parser import ParserError
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
import concurrent
from requests.exceptions import RequestException, HTTPError

from nzbhydra.categories import getByNewznabCats, getCategoryByName, getCategoryByAnyInput
from nzbhydra.config import getCategorySettingByName
from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.datestuff import now
from nzbhydra import infos
from nzbhydra.exceptions import IndexerAuthException, IndexerAccessException, IndexerResultParsingException
from nzbhydra.search_module import SearchModule, IndexerProcessingResult
from nzbhydra.searchmodules import newznab

logger = logging.getLogger('root')


def get_age_from_pubdate(pubdate):
    timepub = datetime.datetime.fromtimestamp(email.utils.mktime_tz(email.utils.parsedate_tz(pubdate)))
    timenow = now()
    dt = timenow - timepub
    epoch = calendar.timegm(time.gmtime(email.utils.mktime_tz(email.utils.parsedate_tz(pubdate))))
    pubdate_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(email.utils.mktime_tz(email.utils.parsedate_tz(pubdate))))
    age_days = int(dt.days)
    return epoch, pubdate_utc, int(age_days)





class Jackett(newznab.NewzNab):
    
    # todo feature: read caps from server on first run and store them in the config/database
    def __init__(self, settings):
        super(newznab.NewzNab, self).__init__(settings)
        super(Jackett, self).__init__(settings)
        self.settings = settings  # Already done by super.__init__ but this way PyCharm knows the correct type
        self.module = "jackett"
        self.category_search = True
        self.supportedFilters = ["maxage"]
        self.supportsNot = False

    def get_details_link(self, guid):
        return guid

    def get_entry_by_id(self, guid, title):
        self.error("Function not supported")
        return None

    def get_search_urls(self, search_request, search_type="search"):
        f = self.build_base_url(search_type, search_request.category, offset=search_request.offset)
        query = search_request.query
        if query:
            f = f.add({"q": query})
        if search_request.maxage:
            f = f.add({"maxage": search_request.maxage})

        return [f.url]
        
    def process_query_result(self, xml_response, searchRequest, maxResults=None):
        self.debug("Started processing results")
        countRejected = 0
        acceptedEntries = []
        entries, total, offset = self.parseXml(xml_response, maxResults)
        
        for entry in entries:
            accepted, reason = self.accept_result(entry, searchRequest, self.supportedFilters)
            if accepted:
                acceptedEntries.append(entry)
            else:
                countRejected += 1
                self.debug("Rejected search result. Reason: %s" % reason)
       
        if total == 0 or len(acceptedEntries) == 0:
            self.info("Query returned no results")
            return IndexerProcessingResult(entries=acceptedEntries, queries=[], total=0, total_known=True, has_more=False, rejected=countRejected)
        else:
            return IndexerProcessingResult(entries=acceptedEntries, queries=[], total=total, total_known=True, has_more=False, rejected=countRejected)
    
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
        return entries, len(entries), 0

    def parseItem(self, item):
        entry = self.create_nzb_search_result()
        # These are the values that absolutely must be contained in the response
        entry.title = item.find("title").text
        entry.link = item.find("link").text
        entry.details_link = item.find("comments").text
        entry.indexerguid = item.find("guid").text
        size = item.find("size")
        if size:
            entry.size = int(size.text)
        entry.attributes = []
        entry.has_nfo = NzbSearchResult.HAS_NFO_NO
        categories = item.find("category")            
        if categories is not None:
            categories = categories.text
        entry.category = getByNewznabCats(categories)
        
        for i in item.findall("./newznab:attr", {"newznab": "http://www.newznab.com/DTD/2010/feeds/attributes/"}):
            attribute_name = i.attrib["name"]
            attribute_value = i.attrib["value"]
            entry.attributes.append({"name": attribute_name, "value": attribute_value})
            if attribute_name == "size":
                entry.size = int(attribute_value)
        
        entry.pubDate = item.find("pubDate").text
        pubDate = arrow.get(entry.pubDate, 'ddd, DD MMM YYYY HH:mm:ss Z')
        entry.epoch = pubDate.timestamp
        entry.pubdate_utc = str(pubDate)
        entry.age_days = (arrow.utcnow() - pubDate).days
        entry.precise_date = True 
        entry.downloadType = "torrent"
        return entry


    def get_nfo(self, guid):
        return False, None, "NFOs not supported by indexer"



def get_instance(indexer):
    return Jackett(indexer)
