from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import xml.etree.ElementTree as ET

import arrow
from builtins import *

from nzbhydra.categories import getByNewznabCats
from nzbhydra.exceptions import IndexerResultParsingException
from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search_module import IndexerProcessingResult
from nzbhydra.searchmodules import newznab

logger = logging.getLogger('root')


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
        countRejected = self.getRejectedCountDict()
        acceptedEntries = []
        entries, total, offset = self.parseXml(xml_response, maxResults)
        
        for entry in entries:
            accepted, reason,ri = self.accept_result(entry, searchRequest, self.supportedFilters)
            if accepted:
                acceptedEntries.append(entry)
            else:
                countRejected[ri] += 1
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
        entry.comments = 0
        size = item.find("size")
        if size is not None:
            entry.size = int(size.text)
        entry.attributes = []
        entry.has_nfo = NzbSearchResult.HAS_NFO_NO
        categories = item.find("category")            
        if categories is not None:
            categories = categories.text
        entry.category = getByNewznabCats(categories)

        attributes = item.findall("torznab:attr", {"torznab": "http://torznab.com/schemas/2015/feed"})
        attributes.extend(item.findall("newznab:attr", {"newznab": "http://www.newznab.com/DTD/2010/feeds/attributes/"}))
        for i in attributes:
            attribute_name = i.attrib["name"]
            attribute_value = i.attrib["value"]
            entry.attributes.append({"name": attribute_name, "value": attribute_value})
            if attribute_name == "size":
                entry.size = int(attribute_value)
            if attribute_name == "grabs":
                entry.grabs = int(attribute_value)
        
        entry.pubDate = item.find("pubDate").text
        pubDate = arrow.get(entry.pubDate, 'ddd, DD MMM YYYY HH:mm:ss Z')
        self.getDates(entry, pubDate)
        entry.downloadType = "torrent"
        # For some trackers several results with the same ID are returned (e.g. PTP so we need to make sure the ID is unique)
        entry.indexerguid += str(entry.size)
        return entry


    def get_nfo(self, guid):
        return False, None, "NFOs not supported by indexer"



def get_instance(indexer):
    return Jackett(indexer)
