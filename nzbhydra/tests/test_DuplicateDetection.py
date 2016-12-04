from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
from random import shuffle, randint

import flask
import pytest
from bunch import Bunch
from mock import MagicMock

from nzbhydra.categories import getCategoryByName
from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search import SearchRequest
from nzbhydra.searchmodules.newznab import NewzNab
from nzbhydra.tests import mockbuilder

# standard_library.install_aliases()
from builtins import *
import re
import unittest
import sys
import logging
from pprint import pprint

import arrow
from freezegun import freeze_time
import requests
import responses
from furl import furl

from nzbhydra import search, config, search_module, database, infos
from nzbhydra.indexers import read_indexers_from_config, getIndexerSettingByName
from nzbhydra.database import Indexer, Search, IndexerApiAccess, IndexerSearch, IndexerStatus
from nzbhydra.tests.db_prepare import set_and_drop

logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")


def mock(x, y, z=True):
    return True


class DuplicateDetectionTests(unittest.TestCase):
    
    def prepareIndexers(self, indexerCount):
        config.settings.indexers = []
        for i in range(1, indexerCount + 1):
            nn = Bunch()
            nn.enabled = True
            nn.name = "newznab%d" % i
            nn.type = "newznab"
            nn.host = "http://www.newznab%d.com" % i
            nn.apikey = "apikeyindexer.com"
            nn.hitLimit = None
            nn.timeout = None
            nn.score = 0
            nn.accessType = "both"
            nn.search_ids = ["imdbid", "tvdbid", "rid"]
            config.settings.indexers.append(nn)

    def rsps_callback(self, request):
        for x in self.response_callbacks:
            nn = x[0]
            if nn in request.url:
                print("sleeping %d seconds" % x[1])
                time.sleep(x[1])
                return 200, {}, x[2]

    def prepareSearchMocks(self, rsps, indexerCount=2, resultsPerIndexers=1, newznabItems=None, title="newznab%dresult%d.title", sleep=0):
        testData = []
        self.response_callbacks = []
        self.prepareIndexers(indexerCount)

        for i in range(1, indexerCount + 1):
            # Prepare search results
            if newznabItems is not None:
                indexerNewznabItems = newznabItems[i - 1]
            else:
                indexerNewznabItems = [mockbuilder.buildNewznabItem(title % (i, j), "newznab%dresult%d.guid" % (i, j), "newznab%dresult%d.link" % (i, j), arrow.get(0).format("ddd, DD MMM YYYY HH:mm:ss Z"), "newznab%dresult%d.description" % (i, j), 1000, "newznab%d" % i, None) for
                                       j in
                                       range(1, resultsPerIndexers + 1)]
            xml = mockbuilder.buildNewznabResponse("newznab%dResponse" % i, indexerNewznabItems, 0, len(indexerNewznabItems))
            self.response_callbacks.append(('newznab%d' % i, randint(0, sleep), xml))

            # Prepare response mock
            url_re = re.compile(r'.*newznab%d.*' % i)
            rsps.add_callback(responses.GET, url_re,
                              callback=self.rsps_callback,
                              content_type='application/x-html')
        read_indexers_from_config()

        return testData

    @pytest.fixture
    def setUp(self):
        pass
        set_and_drop()
        #
        # getIndexerSettingByName("binsearch").enabled = False
        # getIndexerSettingByName("nzbindex").enabled = False
        # getIndexerSettingByName("womble").enabled = False
        # getIndexerSettingByName("nzbclub").enabled = False
        #
        # self.newznab1 = Bunch()
        # self.newznab1.enabled = True
        # self.newznab1.name = "newznab1"
        # self.newznab1.host = "https://indexer.com"
        # self.newznab1.apikey = "apikeyindexer.com"
        # self.newznab1.timeout = None
        # self.newznab1.hitLimit = None
        # self.newznab1.score = 0
        # self.newznab1.type = "newznab"
        # self.newznab1.accessType = "both"
        # self.newznab1.search_ids = ["imdbid", "rid", "tvdbid"]
        # self.newznab1.searchTypes = ["book", "tvsearch", "movie"]
        #
        # self.newznab2 = Bunch()
        # self.newznab2.enabled = True
        # self.newznab2.name = "newznab2"
        # self.newznab2.host = "https://indexer.com"
        # self.newznab2.apikey = "apikeyindexer.com"
        # self.newznab2.timeout = None
        # self.newznab2.hitLimit = None
        # self.newznab2.accessType = "both"
        # self.newznab2.score = 0
        # self.newznab2.type = "newznab"
        # self.newznab2.search_ids = ["rid", "tvdbid"]
        # self.newznab2.searchTypes = ["tvsearch", "movie"]
        #
        # # config.settings.indexers = [self.newznab1, self.newznab2]
        #
        # self.oldExecute_search_queries = search.start_search_futures
        # database.IndexerStatus.delete().execute()
        # database.IndexerSearch.delete().execute()
        # infos.convertId = mock
        #
        # self.app = flask.Flask(__name__)
        # self.response_callbacks = []

    def tearDown(self):
        pass
        #search.start_search_futures = self.oldExecute_search_queries
        #config.settings.searching.requiredWords = None

   


    

    def testTestForDuplicate(self):
        config.settings.searching.duplicateAgeThreshold = 120
        age_threshold = config.settings.searching.duplicateAgeThreshold
        size_threshold = config.settings.searching.duplicateSizeThresholdInPercent
        config.settings.searching.duplicateSizeThresholdInPercent = 1

        # same title, age and size
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="b")
        assert search.test_for_duplicate_age(result1, result2, age_threshold)
        assert search.test_for_duplicate_size(result1, result2, size_threshold)

        # size in threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=100, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=101, indexer="b")
        assert search.test_for_duplicate_size(result1, result2, size_threshold)

        # age in threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 - 1, size=1, indexer="b")
        assert search.test_for_duplicate_age(result1, result2, age_threshold)

        # size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=2, indexer="b")
        assert not search.test_for_duplicate_size(result1, result2, size_threshold)

        # age outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 * 1000 + 1, size=0, indexer="b")
        assert not search.test_for_duplicate_age(result1, result2, age_threshold)

        # age and size inside of threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=101, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 - 1, size=101, indexer="b")
        assert search.test_for_duplicate_size(result1, result2, size_threshold)
        assert search.test_for_duplicate_age(result1, result2, age_threshold)

        # age and size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 * 1000 + 1, size=200, indexer="b")
        assert not search.test_for_duplicate_size(result1, result2, size_threshold)
        assert not search.test_for_duplicate_age(result1, result2, age_threshold)

    def testFindDuplicates(self):
        config.settings.searching.duplicateAgeThreshold = 3600
        config.settings.searching.duplicateSizeThresholdInPercent = 0.1

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="2", indexerguid="2")
        result3 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="3", indexerguid="3")
        result4 = NzbSearchResult(title="Title3", epoch=0, size=1, indexer="4", indexerguid="4")
        result5 = NzbSearchResult(title="TITLE1", epoch=0, size=1, indexer="5", indexerguid="5")
        result6 = NzbSearchResult(title="Title4", epoch=0, size=1, indexer="6", indexerguid="6")
        results, _ = search.find_duplicates([result1, result2, result3, result4, result5, result6])
        self.assertEqual(4, len(results))
        self.assertEqual(2, len(results[0]))
        self.assertEqual(2, len(results[1]))
        self.assertEqual(1, len(results[2]))
        self.assertEqual(1, len(results[3]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", indexerguid="2")
        result3 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="3", indexerguid="3")
        result4 = NzbSearchResult(title="Title1", epoch=100000000, size=1, indexer="4", indexerguid="4")
        results, _ = search.find_duplicates([result1, result2, result3, result4])
        self.assertEqual(2, len(results))
        self.assertEqual(3, len(results[0]))
        self.assertEqual(1, len(results[1]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1a", indexerguid="1", pubdate_utc=arrow.get(0).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result2 = NzbSearchResult(title="Title1", epoch=10000000, size=1, indexer="2a", indexerguid="2", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result3 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1b", indexerguid="3", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result4 = NzbSearchResult(title="Title1", epoch=10000000, size=1, indexer="2b", indexerguid="4", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result5 = NzbSearchResult(title="Title1", epoch=1000000000, size=1, indexer="3", indexerguid="5", pubdate_utc=arrow.get(1000000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        results, _ = search.find_duplicates([result1, result2, result3, result4, result5])
        results = sorted(results, key=lambda x: len(x), reverse=True)
        self.assertEqual(3, len(results))
        self.assertEqual(2, len(results[0]))
        self.assertEqual(2, len(results[1]))
        self.assertEqual(1, len(results[2]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title1", epoch=100000000, size=1, indexer="2", indexerguid="2")
        results, _ = search.find_duplicates([result1, result2])
        results = sorted(results, key=lambda x: len(x), reverse=True)
        self.assertEqual(2, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title1", epoch=1, size=100000000, indexer="2", indexerguid="2")
        results, _ = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title1", epoch=1, size=1, indexer="2", indexerguid="2")
        results, _ = search.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))
        self.assertEqual(2, len(results[0]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title1", epoch=30 * 1000 * 60, size=1, indexer="2", indexerguid="2")
        result3 = NzbSearchResult(title="Title1", epoch=60 * 1000 * 60, size=1, indexer="2", indexerguid="3")
        results, _ = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title2", epoch=1000000, size=1, indexer="2", indexerguid="2")
        result3 = NzbSearchResult(title="Title3", epoch=5000000, size=1, indexer="2", indexerguid="3")
        results, _ = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="2", indexerguid="2")
        result3 = NzbSearchResult(title="Title3", epoch=0, size=1, indexer="2", indexerguid="3")
        results, _ = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))

        # Same size and age and group but different posters (very unlikely) 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", indexerguid="2", poster="posterb", group="groupa")
        results, _ = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))

        # Same size and age and poster but different groups (very unlikely) 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", indexerguid="2", poster="postera", group="groupb")
        results, _ = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))

        # Same size and age and poster but unknown group inside of 3 hours 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera")
        result2 = NzbSearchResult(title="Title1", epoch=60 * 60 * 2, size=1, indexer="2", indexerguid="2", poster="postera", group="groupb")
        results, _ = search.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))

    def testFindDuplicatesNew(self):
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=2, indexer="2", indexerguid="2", poster="postera", group="groupb")
        result3 = NzbSearchResult(title="Title1", epoch=0, size=3, indexer="3", indexerguid="3", poster="postera", group="groupb")
        results, _ = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))

    

    @responses.activate
    def testDuplicateRemovalForExternalApi(self):
        with self.app.test_request_context('/'):
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                newznabItems = [
                    [mockbuilder.buildNewznabItem(title="title", pubdate=arrow.get(0000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab1")],
                    [mockbuilder.buildNewznabItem(title="title", pubdate=arrow.get(1000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab2")],
                    [mockbuilder.buildNewznabItem(title="title", pubdate=arrow.get(3000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab3")],
                    [mockbuilder.buildNewznabItem(title="title", pubdate=arrow.get(2000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab4")]
                ]

                self.prepareSearchMocks(rsps, indexerCount=len(newznabItems), newznabItems=newznabItems)

                # Test that the newest result is chosen if all scores are equal
                searchRequest = SearchRequest(type="search", internal=False)
                result = search.search(searchRequest)
                results = result["results"]
                self.assertEqual(1, len(results))
                self.assertEqual("newznab3", results[0].indexer)

                # Test that results from an indexer with a higher score are preferred
                self.prepareSearchMocks(rsps, indexerCount=len(newznabItems), newznabItems=newznabItems)
                getIndexerSettingByName("newznab2").score = 99
                searchRequest = SearchRequest(type="search", internal=False)
                result = search.search(searchRequest)
                results = result["results"]
                self.assertEqual(1, len(results))
                self.assertEqual("newznab2", results[0].indexer)

    @responses.activate
    def testDuplicateTaggingForInternalApi(self):
        with self.app.test_request_context('/'):
            with responses.RequestsMock() as rsps:
                newznabItems = [
                    [mockbuilder.buildNewznabItem(title="title1", pubdate=arrow.get(1000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab1", guid="newznab1result1"),
                     mockbuilder.buildNewznabItem(title="title2", pubdate=arrow.get(3000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab1", guid="newznab1result2")],
                    [mockbuilder.buildNewznabItem(title="title1", pubdate=arrow.get(2000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab2", guid="newznab1result1"),
                     mockbuilder.buildNewznabItem(title="title2", pubdate=arrow.get(4000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab2", guid="newznab2result2")]
                ]

                self.prepareSearchMocks(rsps, indexerCount=len(newznabItems), newznabItems=newznabItems)

                searchRequest = SearchRequest(type="search")
                result = search.search(searchRequest)
                results = result["results"]
                self.assertEqual(4, len(results))
                results = sorted(results, key=lambda x: x.hash)
                self.assertEqual(results[0].hash, results[1].hash)
                self.assertEqual(results[2].hash, results[3].hash)

    
    def testFindDuplicatesWithDD(self):
        import jsonpickle
        results = jsonpickle.decode(
            '[{"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.hdtv.x264", "pubDate": "Sat, 23 Jan 2016 11:08:46 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:08:46-06:00"]}}, "comments": null, "epoch": 1453568926, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [708754823]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/634c0a68d89548be7778e8eea43a949e/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "708754823"}, {"name": "grabs", "value": "9"}, {"name": "guid", "value": "634c0a68d89548be7778e8eea43a949e"}, {"name": "info", "value": "https://dognzb.cr/details/634c0a68d89548be7778e8eea43a949e"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "634c0a68d89548be7778e8eea43a949e", "details_link": "https://dognzb.cr/details/634c0a68d89548be7778e8eea43a949e", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.hdtv.x264", "pubDate": "Sat, 23 Jan 2016 11:06:56 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:06:56-06:00"]}}, "comments": null, "epoch": 1453568816, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [708766534]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/634c329e9cbbe405668f25a9e893e5a1/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "708766534"}, {"name": "grabs", "value": "5"}, {"name": "guid", "value": "634c329e9cbbe405668f25a9e893e5a1"}, {"name": "info", "value": "https://dognzb.cr/details/634c329e9cbbe405668f25a9e893e5a1"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "634c329e9cbbe405668f25a9e893e5a1", "details_link": "https://dognzb.cr/details/634c329e9cbbe405668f25a9e893e5a1", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.misc", "pubDate": "Sat, 23 Jan 2016 10:53:08 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T10:53:08-06:00"]}}, "comments": null, "epoch": 1453567988, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [708817306]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/5a2d7b27b157293ebc3ce25ee3ece9ae/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "708817306"}, {"name": "grabs", "value": "10"}, {"name": "guid", "value": "5a2d7b27b157293ebc3ce25ee3ece9ae"}, {"name": "info", "value": "https://dognzb.cr/details/5a2d7b27b157293ebc3ce25ee3ece9ae"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "5a2d7b27b157293ebc3ce25ee3ece9ae", "details_link": "https://dognzb.cr/details/5a2d7b27b157293ebc3ce25ee3ece9ae", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.misc", "pubDate": "Sat, 23 Jan 2016 10:47:19 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T10:47:19-06:00"]}}, "comments": null, "epoch": 1453567639, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [708029193]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/62826294c691d71331f5f5a2f7c97fab/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "708029193"}, {"name": "grabs", "value": "4"}, {"name": "guid", "value": "62826294c691d71331f5f5a2f7c97fab"}, {"name": "info", "value": "https://dognzb.cr/details/62826294c691d71331f5f5a2f7c97fab"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "62826294c691d71331f5f5a2f7c97fab", "details_link": "https://dognzb.cr/details/62826294c691d71331f5f5a2f7c97fab", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.boneless", "pubDate": "Sat, 23 Jan 2016 10:34:53 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-aAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T10:34:53-06:00"]}}, "comments": null, "epoch": 1453566893, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [707518680]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/596a884fae6c619ed9451f494dbcdc0f/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "707518680"}, {"name": "grabs", "value": "15"}, {"name": "guid", "value": "596a884fae6c619ed9451f494dbcdc0f"}, {"name": "info", "value": "https://dognzb.cr/details/596a884fae6c619ed9451f494dbcdc0f"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "596a884fae6c619ed9451f494dbcdc0f", "details_link": "https://dognzb.cr/details/596a884fae6c619ed9451f494dbcdc0f", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.teevee", "pubDate": "Sat, 23 Jan 2016 10:32:51 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-aAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T10:32:51-06:00"]}}, "comments": null, "epoch": 1453566771, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [746142045]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/59adfcfcf37d547edd950c9fbb0c1ce6/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "746142045"}, {"name": "grabs", "value": "18"}, {"name": "guid", "value": "59adfcfcf37d547edd950c9fbb0c1ce6"}, {"name": "info", "value": "https://dognzb.cr/details/59adfcfcf37d547edd950c9fbb0c1ce6"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "59adfcfcf37d547edd950c9fbb0c1ce6", "details_link": "https://dognzb.cr/details/59adfcfcf37d547edd950c9fbb0c1ce6", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.teevee", "pubDate": "Sat, 23 Jan 2016 10:32:13 -0600", "title": "Duck.Dynasty.S09E02.HDTV.x264-aAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T10:32:13-06:00"]}}, "comments": null, "epoch": 1453566733, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [261743919]}}, "category": "TV SD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/59adba189d51a27c8e9751dbd7022d43/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5030"}, {"name": "size", "value": "261743919"}, {"name": "grabs", "value": "46"}, {"name": "guid", "value": "59adba189d51a27c8e9751dbd7022d43"}, {"name": "info", "value": "https://dognzb.cr/details/59adba189d51a27c8e9751dbd7022d43"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "59adba189d51a27c8e9751dbd7022d43", "details_link": "https://dognzb.cr/details/59adba189d51a27c8e9751dbd7022d43", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 8, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.boneless", "pubDate": "Wed, 20 Jan 2016 09:59:50 -0600", "title": "Duck.Dynasty.S09E02.Flock.And.Key.REPACK.720p.AE.WEBRip.AAC2.0.H.264-BTW", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-20T09:59:50-06:00"]}}, "comments": null, "epoch": 1453305590, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [479760097]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/cc9365e19cc0963b48725e44ac4799ce/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "479760097"}, {"name": "grabs", "value": "49"}, {"name": "guid", "value": "cc9365e19cc0963b48725e44ac4799ce"}, {"name": "info", "value": "https://dognzb.cr/details/cc9365e19cc0963b48725e44ac4799ce"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "cc9365e19cc0963b48725e44ac4799ce", "details_link": "https://dognzb.cr/details/cc9365e19cc0963b48725e44ac4799ce", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 13, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.boneless", "pubDate": "Fri, 15 Jan 2016 09:29:10 -0600", "title": "Duck.Dynasty.S09E02.Flock.And.Key.720p.AE.WEBRip.AAC2.0.H.264-BTW", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-15T09:29:10-06:00"]}}, "comments": null, "epoch": 1452871750, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [467457289]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/bb0ff779cffb5c47e72bdfbb977811f2/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "467457289"}, {"name": "grabs", "value": "502"}, {"name": "guid", "value": "bb0ff779cffb5c47e72bdfbb977811f2"}, {"name": "info", "value": "https://dognzb.cr/details/bb0ff779cffb5c47e72bdfbb977811f2"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "bb0ff779cffb5c47e72bdfbb977811f2", "details_link": "https://dognzb.cr/details/bb0ff779cffb5c47e72bdfbb977811f2", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 9, "indexer": "https://api.nzb.su", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": null, "pubDate": "Sat, 23 Jan 2016 12:15:16 -0500", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:53:08-05:00"]}}, "comments": null, "epoch": 1453567988, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [708817306]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": "sam7462672 <sam7462672@misc.my>", "search_types": [], "link": "https://api.nzb.su/getnzb/607ff20c82d7212f30e1e93153da386b.nzb&i=905&r=apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "708817306"}, {"name": "guid", "value": "607ff20c82d7212f30e1e93153da386b"}, {"name": "files", "value": "49"}, {"name": "poster", "value": "sam7462672 <sam7462672@misc.my>"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "rageid", "value": "30870"}, {"name": "grabs", "value": "67"}, {"name": "comments", "value": "0"}, {"name": "password", "value": "0"}, {"name": "usenetdate", "value": "Sat, 23 Jan 2016 11:53:08 -0500"}, {"name": "group", "value": "not available"}], "precise_date": true, "search_ids": [], "indexerguid": "607ff20c82d7212f30e1e93153da386b", "details_link": "https://api.nzb.su/details/607ff20c82d7212f30e1e93153da386b", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 9, "indexer": "https://api.nzb.su", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": null, "pubDate": "Sat, 23 Jan 2016 15:05:47 -0500", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:47:19-05:00"]}}, "comments": null, "epoch": 1453567639, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [707925918]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": "sam7462672 <sam7462672@misc.my>", "search_types": [], "link": "https://api.nzb.su/getnzb/9bfe6e0508f267a9997d3a05a08b6e87.nzb&i=905&r=apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "707925918"}, {"name": "guid", "value": "9bfe6e0508f267a9997d3a05a08b6e87"}, {"name": "files", "value": "49"}, {"name": "poster", "value": "sam7462672 <sam7462672@misc.my>"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "rageid", "value": "30870"}, {"name": "grabs", "value": "10"}, {"name": "comments", "value": "0"}, {"name": "password", "value": "0"}, {"name": "usenetdate", "value": "Sat, 23 Jan 2016 11:47:19 -0500"}, {"name": "group", "value": "not available"}], "precise_date": true, "search_ids": [], "indexerguid": "9bfe6e0508f267a9997d3a05a08b6e87", "details_link": "https://api.nzb.su/details/9bfe6e0508f267a9997d3a05a08b6e87", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 9, "indexer": "https://api.nzb.su", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": null, "pubDate": "Sat, 23 Jan 2016 11:46:11 -0500", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-aAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:32:51-05:00"]}}, "comments": null, "epoch": 1453566771, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [746142045]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": "r@ndom.tv (r@ndom)", "search_types": [], "link": "https://api.nzb.su/getnzb/ba9ee73da913a6c1394e8c8672f70be2.nzb&i=905&r=apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "746142045"}, {"name": "guid", "value": "ba9ee73da913a6c1394e8c8672f70be2"}, {"name": "files", "value": "32"}, {"name": "poster", "value": "r@ndom.tv (r@ndom)"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "rageid", "value": "30870"}, {"name": "grabs", "value": "86"}, {"name": "comments", "value": "0"}, {"name": "password", "value": "0"}, {"name": "usenetdate", "value": "Sat, 23 Jan 2016 11:32:51 -0500"}, {"name": "group", "value": "not available"}], "precise_date": true, "search_ids": [], "indexerguid": "ba9ee73da913a6c1394e8c8672f70be2", "details_link": "https://api.nzb.su/details/ba9ee73da913a6c1394e8c8672f70be2", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 9, "indexer": "https://api.nzb.su", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": null, "pubDate": "Sat, 23 Jan 2016 11:46:11 -0500", "title": "Duck.Dynasty.S09E02.HDTV.x264-aAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:32:13-05:00"]}}, "comments": null, "epoch": 1453566733, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [261743919]}}, "category": "TV SD", "hash": -958854479, "description": null, "poster": "provide@4u.net (yeahsure)", "search_types": [], "link": "https://api.nzb.su/getnzb/65406ecbc72254946f5fb6bdd376d3e1.nzb&i=905&r=apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5030"}, {"name": "size", "value": "261743919"}, {"name": "guid", "value": "65406ecbc72254946f5fb6bdd376d3e1"}, {"name": "files", "value": "28"}, {"name": "poster", "value": "provide@4u.net (yeahsure)"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "rageid", "value": "30870"}, {"name": "grabs", "value": "75"}, {"name": "comments", "value": "0"}, {"name": "password", "value": "0"}, {"name": "usenetdate", "value": "Sat, 23 Jan 2016 11:32:13 -0500"}, {"name": "group", "value": "not available"}], "precise_date": true, "search_ids": [], "indexerguid": "65406ecbc72254946f5fb6bdd376d3e1", "details_link": "https://api.nzb.su/details/65406ecbc72254946f5fb6bdd376d3e1", "passworded": false, "has_nfo": 2}]')

        shuffle(results)
        a, _ = search.find_duplicates(results)
        assert 6 == len(a)
        shuffle(results)
        a, _ = search.find_duplicates(results)
        assert 6 == len(a)
        shuffle(results)
        a, _ = search.find_duplicates(results)
        assert 6 == len(a)
        shuffle(results)
        a, _ = search.find_duplicates(results)
        assert 6 == len(a)
        shuffle(results)
        a, _ = search.find_duplicates(results)
        assert 6 == len(a)
        print(a)

    