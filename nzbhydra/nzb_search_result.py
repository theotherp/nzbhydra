from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
#standard_library.install_aliases()
from builtins import *
from builtins import object

from nzbhydra import categories


class NzbSearchResult(object):
    HAS_NFO_NO = 0
    HAS_NFO_YES = 1
    HAS_NFO_MAYBE = 2


    def __init__(self, title=None, link=None, indexer=None, guid=None, size=None, category=None, attributes=None, epoch=None, pubDate=None, pubdate_utc=None, age_days=None, poster=None, has_nfo=HAS_NFO_YES, indexerguid=None, details_link=None, group=None, indexerscore=0, dbsearchid=None, passworded=False,
                 downloadType="nzb"):
        self.title = title
        self.link = link
        self.epoch = epoch
        self.pubdate_utc = pubdate_utc
        self.age_days = age_days
        self.age_precise = True #Set to false if the age is not received from a pubdate but from an age. That might influence duplicity check
        self.indexer = indexer
        self.guid = guid
        self.indexerguid = indexerguid #The GUID of the indexer which we will later need to download the actual NZB 
        self.size = size
        self.category = category if category is not None else categories.getUnknownCategory()
        self.description = None
        self.comments = None
        self.attributes = attributes if attributes is not None else []
        self.search_types = [] #"general", "tv", "movie"
        self.supports_queries = True #Indexers might only provide a feed of the latest releases, e.g. womble
        self.search_ids = [] #"tvdbid", "rid", "imdbid"
        self.poster = poster
        self.has_nfo = has_nfo 
        self.details_link = details_link
        self.group = group
        self.indexerscore = indexerscore
        self.dbsearchid = dbsearchid
        self.passworded = passworded
        self.pubDate = pubDate
        self.downloadType = downloadType
        

    def __repr__(self):
        return "Title: {}. Size: {}. Indexer: {}".format(self.title, self.size, self.indexer)
    
    def __eq__(self, other_nzb_search_result):
        return self.title == other_nzb_search_result.title and self.link == other_nzb_search_result.link and self.indexer == other_nzb_search_result.indexer and self.indexerguid == other_nzb_search_result.indexerguid
    
    def __hash__(self):
        return hash(self.title) ^ hash(self.indexer) ^ hash(self.indexerguid)