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


class SearchTests(unittest.TestCase):
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
        set_and_drop()

        getIndexerSettingByName("binsearch").enabled = False
        getIndexerSettingByName("nzbindex").enabled = False
        getIndexerSettingByName("womble").enabled = False
        getIndexerSettingByName("nzbclub").enabled = False

        self.newznab1 = Bunch()
        self.newznab1.enabled = True
        self.newznab1.name = "newznab1"
        self.newznab1.host = "https://indexer.com"
        self.newznab1.apikey = "apikeyindexer.com"
        self.newznab1.timeout = None
        self.newznab1.hitLimit = None
        self.newznab1.score = 0
        self.newznab1.type = "newznab"
        self.newznab1.accessType = "both"
        self.newznab1.search_ids = ["imdbid", "rid", "tvdbid"]
        self.newznab1.searchTypes = ["book", "tvsearch", "movie"]

        self.newznab2 = Bunch()
        self.newznab2.enabled = True
        self.newznab2.name = "newznab2"
        self.newznab2.host = "https://indexer.com"
        self.newznab2.apikey = "apikeyindexer.com"
        self.newznab2.timeout = None
        self.newznab2.hitLimit = None
        self.newznab2.accessType = "both"
        self.newznab2.score = 0
        self.newznab2.type = "newznab"
        self.newznab2.search_ids = ["rid", "tvdbid"]
        self.newznab2.searchTypes = ["tvsearch", "movie"]

        # config.settings.indexers = [self.newznab1, self.newznab2]

        self.oldExecute_search_queries = search.start_search_futures
        database.IndexerStatus.delete().execute()
        database.IndexerSearch.delete().execute()
        infos.convertId = mock

        self.app = flask.Flask(__name__)
        self.response_callbacks = []

    def tearDown(self):
        search.start_search_futures = self.oldExecute_search_queries
        config.settings.searching.requiredWords = None

    def test_pick_indexers(self):
        config.settings.searching.generate_queries = []
        config.settings.indexers.extend([self.newznab1, self.newznab2])
        getIndexerSettingByName("womble").enabled = True
        getIndexerSettingByName("womble").accessType = "both"
        getIndexerSettingByName("nzbclub").enabled = True
        getIndexerSettingByName("nzbclub").accessType = "both"
        read_indexers_from_config()
        search_request = SearchRequest()

        indexers = search.pick_indexers(search_request)
        self.assertEqual(3, len(indexers))

        # Indexers with tv search and which support queries (actually searching for particular releases)
        search_request.query = "bla"
        indexers = search.pick_indexers(search_request)
        self.assertEqual(3, len(indexers))

        # Indexers with tv search, including those that only provide a list of latest releases (womble) but excluding the one that needs a query (nzbclub)
        search_request.query = None
        indexers = search.pick_indexers(search_request)
        self.assertEqual(3, len(indexers))

        search_request.identifier_key = "tvdbid"
        indexers = search.pick_indexers(search_request)
        self.assertEqual(2, len(indexers))
        self.assertEqual("newznab1", indexers[0].name)
        self.assertEqual("newznab2", indexers[1].name)

        search_request.identifier_key = "imdbid"
        search_request.category = getCategoryByName("movies")
        indexers = search.pick_indexers(search_request)
        self.assertEqual(1, len(indexers))
        self.assertEqual("newznab1", indexers[0].name)

        # WIth query generation NZBClub should also be returned
        infos.title_from_id = mock
        config.settings.searching.generate_queries = ["internal"]
        search_request.identifier_key = "tvdbid"
        search_request.query = None
        search_request.category = None
        indexers = search.pick_indexers(search_request)
        self.assertEqual(3, len(indexers))
        self.assertEqual("nzbclub", indexers[0].name)
        self.assertEqual("newznab1", indexers[1].name)
        self.assertEqual("newznab2", indexers[2].name)

        # Test picking depending on internal, external, both
        getIndexerSettingByName("womble").enabled = False
        getIndexerSettingByName("nzbclub").enabled = False

        getIndexerSettingByName("newznab1").accessType = "both"
        search_request.internal = True
        indexers = search.pick_indexers(search_request)
        self.assertEqual(2, len(indexers))
        search_request.internal = False
        indexers = search.pick_indexers(search_request)
        self.assertEqual(2, len(indexers))

        config.settings.indexers = [self.newznab1, self.newznab2]
        getIndexerSettingByName("newznab1").accessType = "external"
        read_indexers_from_config()
        search_request.internal = True
        indexers = search.pick_indexers(search_request)
        self.assertEqual(1, len(indexers))
        search_request.internal = False
        indexers = search.pick_indexers(search_request)
        self.assertEqual(2, len(indexers))

        getIndexerSettingByName("newznab1").accessType = "internal"
        read_indexers_from_config()
        search_request.internal = True
        indexers = search.pick_indexers(search_request)
        self.assertEqual(2, len(indexers))
        search_request.internal = False
        indexers = search.pick_indexers(search_request)
        self.assertEqual(1, len(indexers))

    def testIndexersApiLimits(self):

        config.settings.searching.generate_queries = []
        self.newznab1.hitLimit = 3
        self.newznab1.hitLimitResetTime = None
        config.settings.indexers = [self.newznab1]
        read_indexers_from_config()
        search_request = SearchRequest()
        indexers = search.pick_indexers(search_request)
        self.assertEqual(1, len(indexers))
        dbsearch = Search(internal=True, time=arrow.utcnow().datetime)
        dbsearch.save()
        indexer = Indexer().get(name="newznab1")
        
        #Two accesses one and 12 hours ago
        IndexerApiAccess(indexer=indexer, search=dbsearch, time=arrow.utcnow().replace(hours=-1).datetime, type="search", url="", response_successful=True).save()
        IndexerApiAccess(indexer=indexer, search=dbsearch, time=arrow.utcnow().replace(hours=-12).datetime, type="search", url="", response_successful=True).save()
        self.assertEqual(1, len(search.pick_indexers(search_request)))

        #Another one 20 hours ago, so limit should be reached
        IndexerApiAccess(indexer=indexer, search=dbsearch, time=arrow.utcnow().replace(hours=-20).datetime, type="search", url="", response_successful=True).save()
        self.assertEqual(0, len(search.pick_indexers(search_request)))
        
        
    def testHandleIndexerFailureAndSuccess(self):
        Indexer(module="newznab", name="newznab1").save()
        indexer_model = Indexer.get(Indexer.name == "newznab1")
        with freeze_time("2015-09-20 14:00:00", tz_offset=-4):
            sm = search_module.SearchModule(self.newznab1)
            sm.handle_indexer_failure(indexer_model)
            # First error, so level 1
            self.assertEqual(1, indexer_model.status.get().level)
            now = arrow.utcnow()
            first_failure = arrow.get(arrow.get(indexer_model.status.get().first_failure))
            disabled_until = arrow.get(indexer_model.status.get().disabled_until)
            self.assertEqual(now, first_failure)
            self.assertEqual(now.replace(minutes=+sm.disable_periods[1]), disabled_until)

            sm.handle_indexer_failure()
            self.assertEqual(2, indexer_model.status.get().level)
            disabled_until = arrow.get(indexer_model.status.get().disabled_until)
            self.assertEqual(now.replace(minutes=+sm.disable_periods[2]), disabled_until)

            sm.handle_indexer_success()
            self.assertEqual(1, indexer_model.status.get().level)
            self.assertEqual(arrow.get(0), indexer_model.status.get().disabled_until)
            self.assertIsNone(indexer_model.status.get().reason)

    # For creating test data
    def getMockResponse(self, action, category=None, rid=None, imdbid=None, season=None, episode=None, q=None):
        query = furl("https://newznab1/api").add({"apikey": "", "t": action, "o": "json", "extended": 1})
        if rid is not None:
            query.add({"rid": rid})
        if episode is not None:
            query.add({"ep": episode})
        if season is not None:
            query.add({"season": season})
        if imdbid is not None:
            query.add({"imdbid": imdbid})
        if q is not None:
            query.add({"q": q})
        if category is not None:
            query.add({"cat": category})

        print(query.tostr())
        r = requests.get(query.tostr())
        args = query.args.keys()
        args.remove("apikey")
        args.remove("o")
        args.remove("extended")
        filename = "nzbsorg"
        args = sorted(args)
        for arg in args:
            filename = "%s--%s-%s" % (filename, arg, query.args[arg])
        filename += ".json"
        pprint(args)
        print(filename)
        with open(filename, "w") as file:
            file.write(r.text)

    def testGetMockResponses(self):
        # Enable to create mock responses
        if False:
            self.getMock("search")  # all
            self.getMock("search", q="avengers")  # general search avengers
            self.getMock("search", q="avengers", category="2000")  # general search avengers all movies
            self.getMock("search", category="5030")  # all tv sd
            self.getMock("search", category="5040")  # all tv hd

            self.getMock("tvsearch")  # tvsearch all
            self.getMock("tvsearch", category="5030")  # tvsearch all sd
            self.getMock("tvsearch", category="5040")  # tvsearch all hd
            self.getMock("tvsearch", category="5040", rid=80379)  # bbt hd
            self.getMock("tvsearch", category="5030", rid=80379)  # bbt sd
            self.getMock("tvsearch", category="5040", rid=80379, season=1)  # bbt hd season 1
            self.getMock("tvsearch", category="5040", rid=80379, season=1, episode=2)  # bbt hd season 1 episode 2

            self.getMock("movie")  # moviesearch all
            self.getMock("movie", category="2040")  # moviesearch all hd
            self.getMock("movie", category="2030")  # moviesearch all sd
            self.getMock("movie", imdbid="0169547")  # moviesearch american beauty all
            self.getMock("movie", category="2040", imdbid="0169547")  # moviesearch american beauty all hd

    @responses.activate
    def testLimitAndOffset(self):
        with self.app.test_request_context('/'):
            # Only use newznab indexers
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                # Prepare 12 results
                self.prepareSearchMocks(rsps, 2, 6)
                # Search with a limit of 6        
                searchRequest = SearchRequest(limit=6, type="search", internal=False)
                result = search.search(searchRequest)
                results = result["results"]
                self.assertEqual(6, len(results), "Expected the limit of 6 to be respected")
                self.assertEqual("newznab1result1.title", results[0].title)
                self.assertEqual("newznab1result6.title", results[5].title)

                # Search again with an offset, expect the next (and last ) 6 results
                searchRequest = SearchRequest(offset=6, limit=100, type="search", internal=False)
                result = search.search(searchRequest)
                results = result["results"]
                self.assertEqual(6, len(results), "Expected the limit of 6 to be respected")
                self.assertEqual("newznab2result1.title", results[0].title)

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

    @responses.activate
    def testThatResultsAreSortedByAgeDescending(self):
        with self.app.test_request_context('/'):
            with responses.RequestsMock() as rsps:
                newznabItems = [
                    [mockbuilder.buildNewznabItem(title="title1", pubdate=arrow.get(1000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab1")],
                    [mockbuilder.buildNewznabItem(title="title2", pubdate=arrow.get(0000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab2")],
                    [mockbuilder.buildNewznabItem(title="title3", pubdate=arrow.get(3000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab3")],
                    [mockbuilder.buildNewznabItem(title="title4", pubdate=arrow.get(4000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab4")],
                    [mockbuilder.buildNewznabItem(title="title5", pubdate=arrow.get(2000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab5")]
                ]

                self.prepareSearchMocks(rsps, indexerCount=len(newznabItems), newznabItems=newznabItems)

                searchRequest = SearchRequest(type="search")
                result = search.search(searchRequest)
                results = result["results"]
                self.assertEqual("title4", results[0].title)
                self.assertEqual("title3", results[1].title)
                self.assertEqual("title5", results[2].title)
                self.assertEqual("title1", results[3].title)
                self.assertEqual("title2", results[4].title)

    @responses.activate
    @pytest.mark.current
    @freeze_time("2015-10-12 18:00:00", tz_offset=0)
    def testThatDatabaseValuesAreStored(self):
        with self.app.test_request_context('/'):
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                newznabItems = [
                    [mockbuilder.buildNewznabItem(title="title1", pubdate=arrow.get(1000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab1")],
                    [mockbuilder.buildNewznabItem(title="title2", pubdate=arrow.get(1000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=1000, indexer_name="newznab2")]
                ]

                self.prepareSearchMocks(rsps, indexerCount=len(newznabItems), newznabItems=newznabItems)
                # Make the second access unsuccessful
                rsps._urls.pop(1)
                rsps.add(responses.GET, r".*",
                         body="an error message", status=500,
                         content_type='application/x-html')

                searchRequest = SearchRequest(type="search", query="aquery", category="acategory", identifier_key="imdbid", identifier_value="animdbid", season=1, episode=2, indexers="newznab1|newznab2")
                result = search.search(searchRequest)
                results = result["results"]
                self.assertEqual(1, len(results))

                dbSearch = Search().get()
                self.assertEqual(True, dbSearch.internal)
                self.assertEqual("aquery", dbSearch.query)
                self.assertEqual("All", dbSearch.category)
                self.assertEqual("imdbid", dbSearch.identifier_key)
                self.assertEqual("animdbid", dbSearch.identifier_value)
                self.assertEqual("1", dbSearch.season)
                self.assertEqual("2", dbSearch.episode)
                self.assertEqual("search", dbSearch.type)
                self.assertEqual(18, dbSearch.time.hour)

                indexerSearch1 = IndexerSearch.get(IndexerSearch.indexer == Indexer.get(Indexer.name == "newznab1"))
                self.assertEqual(indexerSearch1.search, dbSearch)
                self.assertEqual(18, indexerSearch1.time.hour)

                indexerSearch2 = IndexerSearch.get(IndexerSearch.indexer == Indexer.get(Indexer.name == "newznab2"))
                self.assertEqual(indexerSearch2.search, dbSearch)
                self.assertEqual(18, indexerSearch2.time.hour)

                calledUrls = sorted([x.request.url for x in rsps.calls])

                indexerApiAccess1 = IndexerApiAccess.get(IndexerApiAccess.indexer == Indexer.get(Indexer.name == "newznab1"))
                self.assertEqual(indexerSearch1, indexerApiAccess1.indexer_search)
                self.assertEqual(18, indexerApiAccess1.time.hour)
                self.assertEqual("search", indexerApiAccess1.type)
                self.assertEqual(calledUrls[0], indexerApiAccess1.url)
                self.assertTrue(indexerApiAccess1.response_successful)
                self.assertEqual(0, indexerApiAccess1.response_time)
                self.assertIsNone(indexerApiAccess1.error)

                indexerApiAccess2 = IndexerApiAccess.get(IndexerApiAccess.indexer == Indexer.get(Indexer.name == "newznab2"))
                self.assertEqual(indexerSearch2, indexerApiAccess2.indexer_search)
                self.assertEqual(18, indexerApiAccess2.time.hour)
                self.assertEqual("search", indexerApiAccess2.type)
                self.assertEqual(calledUrls[1], indexerApiAccess2.url)
                self.assertFalse(indexerApiAccess2.response_successful)
                self.assertIsNone(indexerApiAccess2.response_time)
                self.assertTrue("Connection refused" in indexerApiAccess2.error)

                indexerStatus2 = IndexerStatus.get(IndexerStatus.indexer == Indexer.get(Indexer.name == "newznab2"))
                self.assertEqual(1, indexerStatus2.level)
                self.assertTrue("Connection refused" in indexerStatus2.reason)


    def testSearchCategoryWords(self):
        pi = search.pick_indexers
        sahd = search.search_and_handle_db
        # Set forbidden and required category words if configured and the category matches
        config.settings.categories.categories["movies"].forbiddenWords = "forbidden1, forbidden2"
        config.settings.categories.categories["movies"].requiredWords = "required1, required2"
        searchRequest = SearchRequest(type="search", category="movies")

        search.pick_indexers = MagicMock(return_value=[NewzNab(self.newznab1)])
        search.search_and_handle_db = MagicMock(return_value={"results": {}})

        search.search(searchRequest)

        updatedSearchRequest = search.search_and_handle_db.mock_calls[0][1][1].values()[0]
        self.assertEqual(["forbidden1", "forbidden2"], updatedSearchRequest.forbiddenWords)
        self.assertEqual(["required1", "required2"], updatedSearchRequest.requiredWords)

        # Don't set if category doesn't match
        searchRequest = SearchRequest(type="search", category="audio")
        search.search_and_handle_db.reset_mock()

        search.search(searchRequest)

        updatedSearchRequest = search.search_and_handle_db.mock_calls[0][1][1].values()[0]
        self.assertEqual(0, len(updatedSearchRequest.forbiddenWords))
        self.assertEqual(0, len(updatedSearchRequest.requiredWords))

        # Don't set when fallback to "all" category 
        searchRequest = SearchRequest(type="search", category="7890")
        search.search_and_handle_db.reset_mock()

        search.search(searchRequest)

        updatedSearchRequest = search.search_and_handle_db.mock_calls[0][1][1].values()[0]
        self.assertEqual(0, len(updatedSearchRequest.forbiddenWords))
        self.assertEqual(0, len(updatedSearchRequest.requiredWords))
        self.assertEqual("na", updatedSearchRequest.category.category.name)

        # Use globally configured words and category words
        config.settings.searching.forbiddenWords = "globalforbidden1, globalforbidden2"
        config.settings.searching.requiredWords = "globalrequired1, globalrequired2"
        config.settings.categories.categories["movies"].forbiddenWords = "forbidden1, forbidden2"
        config.settings.categories.categories["movies"].requiredWords = "required1, required2"
        searchRequest = SearchRequest(type="search", category="movies")
        search.search_and_handle_db.reset_mock()
        search.pick_indexers = MagicMock(return_value=[NewzNab(self.newznab1)])
        search.search_and_handle_db = MagicMock(return_value={"results": {}})

        search.search(searchRequest)

        updatedSearchRequest = search.search_and_handle_db.mock_calls[0][1][1].values()[0]

        self.assertEqual(["globalforbidden1", "globalforbidden2", "forbidden1", "forbidden2"], updatedSearchRequest.forbiddenWords)
        self.assertEqual(["globalrequired1", "globalrequired2", "required1", "required2"], updatedSearchRequest.requiredWords)

        search.pick_indexers = pi
        search.search_and_handle_db = sahd
