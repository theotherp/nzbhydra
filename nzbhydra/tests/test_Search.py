from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from contextlib import contextmanager
from random import shuffle

import flask
import pytest
from bunch import Bunch
from future import standard_library

from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search import SearchRequest
from nzbhydra.tests import mockbuilder

#standard_library.install_aliases()
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

from nzbhydra import search, config, search_module, database
from nzbhydra.indexers import read_indexers_from_config
from nzbhydra.database import Indexer, Search, IndexerApiAccess, IndexerSearch, IndexerStatus
from nzbhydra.tests.db_prepare import set_and_drop

logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")



class SearchTests(unittest.TestCase):
    def prepareIndexers(self, indexerCount):
        config.settings.indexers.newznab = []
        for i in range(1, indexerCount + 1):
            nn = Bunch()
            nn.enabled = True
            nn.name = "newznab%d" % i
            nn.host = "http://www.newznab%d.com" % i
            nn.apikey = "apikeyindexer.com"
            nn.timeout = None
            nn.score = 0
            nn.accessType = "both"
            nn.search_ids = ["imdbid", "tvdbid", "rid"]
            config.settings.indexers.newznab.append(nn)

    def prepareSearchMocks(self, rsps, indexerCount=2, resultsPerIndexers=1, newznabItems=None, title="newznab%dresult%d.title"):
        testData = []
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

            # Prepare response mock
            url_re = re.compile(r'.*newznab%d.*' % i)
            rsps.add(responses.GET, url_re,
                     body=xml, status=200,
                     content_type='application/x-html')
        read_indexers_from_config()

        return testData
    
    @pytest.fixture
    def setUp(self):
        set_and_drop()
        config.settings.indexers.binsearch.enabled = False
        config.settings.indexers.nzbindex.enabled = False
        config.settings.indexers.omgwtfnzbs.enabled = False
        config.settings.indexers.womble.enabled = False
        config.settings.indexers.nzbclub.enabled = False

        self.newznab1 = Bunch()
        self.newznab1.enabled = True
        self.newznab1.name = "newznab1"
        self.newznab1.host = "https://indexer.com"
        self.newznab1.apikey = "apikeyindexer.com"
        self.newznab1.timeout = None
        self.newznab1.score = 0
        self.newznab1.accessType = "both"
        self.newznab1.search_ids = ["imdbid", "rid", "tvdbid"]

        self.newznab2 = Bunch()
        self.newznab2.enabled = True
        self.newznab2.name = "newznab2"
        self.newznab2.host = "https://indexer.com"
        self.newznab2.apikey = "apikeyindexer.com"
        self.newznab2.timeout = None
        self.newznab2.accessType = "both"
        self.newznab2.score = 0
        self.newznab2.search_ids = ["rid", "tvdbid"]
        
        config.settings.indexers.newznab = [self.newznab1, self.newznab2]

        self.oldExecute_search_queries = search.start_search_futures
        database.IndexerStatus.delete().execute()
        database.IndexerSearch.delete().execute()

        self.app = flask.Flask(__name__)

    def tearDown(self):
        search.start_search_futures = self.oldExecute_search_queries    
            
            

    def test_pick_indexers(self):
        config.settings.searching.generate_queries= []
        config.settings.indexers.womble.enabled = True
        config.settings.indexers.womble.accessType = "both"
        config.settings.indexers.nzbclub.enabled = True
        read_indexers_from_config()
    
        indexers = search.pick_indexers()
        self.assertEqual(3, len(indexers[0]))
    
        # Indexers with tv search and which support queries (actually searching for particular releases)
        indexers = search.pick_indexers(query_supplied=True)
        self.assertEqual(3, len(indexers[0]))
        
        # Indexers with tv search, including those that only provide a list of latest releases (womble) but excluding the one that needs a query (nzbclub) 
        indexers = search.pick_indexers(query_supplied=False)
        self.assertEqual(3, len(indexers[0]))
    
        indexers = search.pick_indexers(identifier_key="tvdbid")
        self.assertEqual(2, len(indexers[0]))
        self.assertEqual("newznab1", indexers[0][0].name)
        self.assertEqual("newznab2", indexers[0][1].name)
    
        indexers = search.pick_indexers("tv", identifier_key="imdbid")
        self.assertEqual(1, len(indexers[0]))
        self.assertEqual("newznab1", indexers[0][0].name)
    
        # WIth query generation NZBClub should also be returned
        config.settings.searching.generate_queries = ["internal"]
        indexers = search.pick_indexers(identifier_key="tvdbid")
        self.assertEqual(3, len(indexers[0]))
        self.assertEqual("nzbclub", indexers[0][0].name)
        self.assertEqual("newznab1", indexers[0][1].name)
        self.assertEqual("newznab2", indexers[0][2].name)
        
        
        #Test picking depending on internal, external, both
        config.settings.indexers.womble.enabled = False
        config.settings.indexers.nzbclub.enabled = False

        config.settings.indexers.newznab[1].accessType = "both"
        indexers = search.pick_indexers(internal=True)
        self.assertEqual(2, len(indexers[0]))
        indexers = search.pick_indexers(internal=False)
        self.assertEqual(2, len(indexers[0]))

        config.settings.indexers.newznab[1].accessType = "external"
        indexers = search.pick_indexers(internal=True)
        self.assertEqual(1, len(indexers[0]))
        indexers = search.pick_indexers(internal=False)
        self.assertEqual(2, len(indexers[0]))

        config.settings.indexers.newznab[1].accessType = "internal"
        indexers = search.pick_indexers(internal=True)
        self.assertEqual(2, len(indexers[0]))
        indexers = search.pick_indexers(internal=False)
        self.assertEqual(1, len(indexers[0]))

        
    
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
    
    def testTestForDuplicate(self):
        config.settings.searching.duplicateAgeThreshold = 120
        age_threshold = config.settings.searching.duplicateAgeThreshold
        config.settings.searching.duplicateSizeThresholdInPercent = 1
    
        # same title, age and size
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="b")
        assert search.test_for_duplicate_age(result1, result2)
        assert search.test_for_duplicate_size(result1, result2)
    
        # size in threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=100, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=101, indexer="b")
        assert search.test_for_duplicate_size(result1, result2)
    
        # age in threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 - 1, size=1, indexer="b")
        assert search.test_for_duplicate_age(result1, result2)
    
        # size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=2, indexer="b")
        assert not search.test_for_duplicate_size(result1, result2)
    
        # age outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 * 1000 + 1, size=0, indexer="b")
        assert not search.test_for_duplicate_age(result1, result2)
    
        # age and size inside of threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=101, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 - 1, size=101, indexer="b")
        assert search.test_for_duplicate_size(result1, result2)
        assert search.test_for_duplicate_age(result1, result2)
    
        # age and size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 * 1000 + 1, size=200, indexer="b")
        assert not search.test_for_duplicate_size(result1, result2)
        assert not search.test_for_duplicate_age(result1, result2)
    
    def testFindDuplicates(self):
        config.settings.searching.duplicateAgeThreshold = 3600
        config.settings.searching.duplicateSizeThresholdInPercent = 0.1
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="2", indexerguid="2")
        result3 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="3", indexerguid="3")
        result4 = NzbSearchResult(title="Title3", epoch=0, size=1, indexer="4", indexerguid="4")
        result5 = NzbSearchResult(title="TITLE1", epoch=0, size=1, indexer="5", indexerguid="5")
        result6 = NzbSearchResult(title="Title4", epoch=0, size=1, indexer="6", indexerguid="6")
        results = search.find_duplicates([result1, result2, result3, result4, result5, result6])
        self.assertEqual(4, len(results))
        self.assertEqual(2, len(results[0]))
        self.assertEqual(2, len(results[1]))
        self.assertEqual(1, len(results[2]))
        self.assertEqual(1, len(results[3]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", indexerguid="2")
        result3 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="3", indexerguid="3")
        result4 = NzbSearchResult(title="Title1", epoch=100000000, size=1, indexer="4", indexerguid="4")
        results = search.find_duplicates([result1, result2, result3, result4])
        self.assertEqual(2, len(results))
        self.assertEqual(3, len(results[0]))
        self.assertEqual(1, len(results[1]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1a", indexerguid="1", pubdate_utc=arrow.get(0).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result2 = NzbSearchResult(title="Title1", epoch=10000000, size=1, indexer="2a", indexerguid="2", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result3 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1b", indexerguid="3", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result4 = NzbSearchResult(title="Title1", epoch=10000000, size=1, indexer="2b", indexerguid="4", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result5 = NzbSearchResult(title="Title1", epoch=1000000000, size=1, indexer="3", indexerguid="5", pubdate_utc=arrow.get(1000000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        results = search.find_duplicates([result1, result2, result3, result4, result5])
        results = sorted(results, key=lambda x: len(x), reverse=True)
        self.assertEqual(3, len(results))
        self.assertEqual(2, len(results[0]))
        self.assertEqual(2, len(results[1]))
        self.assertEqual(1, len(results[2]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title1", epoch=100000000, size=1, indexer="2", indexerguid="2")
        results = search.find_duplicates([result1, result2])
        results = sorted(results, key=lambda x: len(x), reverse=True)
        self.assertEqual(2, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title1", epoch=1, size=100000000, indexer="2", indexerguid="2")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title1", epoch=1, size=1, indexer="2", indexerguid="2")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))
        self.assertEqual(2, len(results[0]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title1", epoch=30 * 1000 * 60, size=1, indexer="2", indexerguid="2")
        result3 = NzbSearchResult(title="Title1", epoch=60 * 1000 * 60, size=1, indexer="2", indexerguid="3")
        results = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title2", epoch=1000000, size=1, indexer="2", indexerguid="2")
        result3 = NzbSearchResult(title="Title3", epoch=5000000, size=1, indexer="2", indexerguid="3")
        results = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1")
        result2 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="2", indexerguid="2")
        result3 = NzbSearchResult(title="Title3", epoch=0, size=1, indexer="2", indexerguid="3")
        results = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))
    
        # Same poster and group posted inside of 24 hours
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=60 * 60 * 4, size=1, indexer="2", indexerguid="2", poster="postera", group="groupa")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))
        self.assertEqual(2, len(results[0]))
    
        # Same poster and group posted outside of 24 hours
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=1000 * 60 * 25, size=1, indexer="2", indexerguid="2", poster="postera", group="groupa")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
    
        # Same size and age and group but different posters (very unlikely) 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", indexerguid="2", poster="posterb", group="groupa")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
    
        # Same size and age and poster but different groups (very unlikely) 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", indexerguid="2", poster="postera", group="groupb")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
    
        # Same size and age and poster but unknown group inside of 3 hours 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera")
        result2 = NzbSearchResult(title="Title1", epoch=60 * 60 * 2, size=1, indexer="2", indexerguid="2", poster="postera", group="groupb")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))
    
        # Same size and age and poster but unknown group outside of 3 hours 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera")
        result2 = NzbSearchResult(title="Title1", epoch=60 * 60 * 4, size=1, indexer="2", indexerguid="2", poster="postera", group="groupb")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
    
    def testFindDuplicatesNew(self):
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", indexerguid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=2, indexer="2", indexerguid="2", poster="postera", group="groupb")
        result3 = NzbSearchResult(title="Title1", epoch=0, size=3, indexer="3", indexerguid="3", poster="postera", group="groupb")
        results = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
    
    
    @responses.activate
    def testSimpleSearch(self):
        with self.app.test_request_context('/'):
            # Only use newznab indexers
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                self.prepareSearchMocks(rsps, 2, 1)
        
                searchRequest = SearchRequest(type="search")
                result = search.search(True, searchRequest)
                results = result["results"]
                self.assertEqual(2, len(results))
                self.assertEqual("newznab1", results[0].indexer)
                self.assertEqual("newznab2", results[1].indexer)
    
    @responses.activate
    def testLimitAndOffset(self):
        with self.app.test_request_context('/'):
            # Only use newznab indexers
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                # Prepare 12 results
                self.prepareSearchMocks(rsps, 2, 6)
                # Search with a limit of 6        
                searchRequest = SearchRequest(limit=6, type="search")
                result = search.search(False, searchRequest)
                results = result["results"]
                self.assertEqual(6, len(results), "Expected the limit of 6 to be respected")
                self.assertEqual("newznab1result1.title", results[0].title)
                self.assertEqual("newznab1result6.title", results[5].title)
        
                # Search again with an offset, expect the next (and last ) 6 results
                searchRequest = SearchRequest(offset=6, limit=100, type="search")
                result = search.search(False, searchRequest)
                results = result["results"]
                self.assertEqual(6, len(results), "Expected the limit of 6 to be respected")
                self.assertEqual("newznab2result1.title", results[0].title)
    
    @responses.activate
    def testDuplicateRemovalForExternalApi(self):
        config.settings.searching.removeDuplicatesExternal = True
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
                searchRequest = SearchRequest(type="search")
                result = search.search(False, searchRequest)
                results = result["results"]
                self.assertEqual(1, len(results))
                self.assertEqual("newznab3", results[0].indexer)            
        
                # Test that results from an indexer with a higher score are preferred
                self.prepareSearchMocks(rsps, indexerCount=len(newznabItems), newznabItems=newznabItems)
                config.settings.indexers.newznab[1].score = 99
                searchRequest = SearchRequest(type="search")
                result = search.search(False, searchRequest)
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
                result = search.search(True, searchRequest)
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
                result = search.search(True, searchRequest)
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
                #Make the second access unsuccessful
                rsps._urls.pop(1)
                rsps.add(responses.GET, r".*",
                         body="an error message", status=500,
                         content_type='application/x-html')
        
                searchRequest = SearchRequest(type="search", query="aquery", category="acategory", identifier_key="imdbid", identifier_value="animdbid", season=1, episode=2, indexers="newznab1|newznab2")
                result = search.search(True, searchRequest)
                results = result["results"]
                self.assertEqual(1, len(results))
                
                dbSearch = Search().get()
                self.assertEqual(True, dbSearch.internal)
                self.assertEqual("aquery", dbSearch.query)
                self.assertEqual("acategory", dbSearch.category)
                self.assertEqual("imdbid", dbSearch.identifier_key)
                self.assertEqual("animdbid", dbSearch.identifier_value)
                self.assertEqual(1, dbSearch.season)
                self.assertEqual(2, dbSearch.episode)
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
    
    @responses.activate
    @pytest.mark.current
    def test20Searches(self):
        with self.app.test_request_context('/'):
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                self.prepareSearchMocks(rsps, indexerCount=20, resultsPerIndexers=1)
        
                searchRequest = SearchRequest(type="search")
                result = search.search(True, searchRequest)
                results = result["results"]
                self.assertEqual(20, len(results))
    
    
    @responses.activate
    def testIgnoreWords(self):
        with self.app.test_request_context('/'):
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                self.prepareSearchMocks(rsps, 2, 2)
                config.settings.searching.ignoreWords = "newznab1"
                searchRequest = SearchRequest(type="search")
                result = search.search(True, searchRequest)
                config.settings.searching.ignoreWords = None
                results = result["results"]
                self.assertEqual(2, len(results))
            
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                self.prepareSearchMocks(rsps, 2, 2)
                config.settings.searching.ignoreWords= "newznab1, something, else"
                searchRequest = SearchRequest(type="search")
                result = search.search(True, searchRequest)
                config.settings.searching.ignoreWords = None
                results = result["results"]
                self.assertEqual(2, len(results))
        
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                self.prepareSearchMocks(rsps, 2, 2)
                config.settings.searching.ignoreWords= "newznab1, newznab2"
                searchRequest = SearchRequest(type="search")
                result = search.search(True, searchRequest)
                config.settings.searching.ignoreWords = None
                results = result["results"]
                self.assertEqual(0, len(results))
        
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                self.prepareSearchMocks(rsps, 2, 2, "newznab %d result%d.title")
                config.settings.searching.ignoreWords= "newznab 1, newznab 2" #Ignore both
                searchRequest = SearchRequest(type="search")
                result = search.search(True, searchRequest)
                config.settings.searching.ignoreWords = None
                results = result["results"]
                self.assertEqual(0, len(results))

    def testFindDuplicatesWithDD(self):
        import jsonpickle
        results = jsonpickle.decode(
                '[{"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.hdtv.x264", "pubDate": "Sat, 23 Jan 2016 11:08:46 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:08:46-06:00"]}}, "comments": null, "epoch": 1453568926, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [708754823]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/634c0a68d89548be7778e8eea43a949e/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "708754823"}, {"name": "grabs", "value": "9"}, {"name": "guid", "value": "634c0a68d89548be7778e8eea43a949e"}, {"name": "info", "value": "https://dognzb.cr/details/634c0a68d89548be7778e8eea43a949e"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "634c0a68d89548be7778e8eea43a949e", "details_link": "https://dognzb.cr/details/634c0a68d89548be7778e8eea43a949e", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.hdtv.x264", "pubDate": "Sat, 23 Jan 2016 11:06:56 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:06:56-06:00"]}}, "comments": null, "epoch": 1453568816, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [708766534]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/634c329e9cbbe405668f25a9e893e5a1/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "708766534"}, {"name": "grabs", "value": "5"}, {"name": "guid", "value": "634c329e9cbbe405668f25a9e893e5a1"}, {"name": "info", "value": "https://dognzb.cr/details/634c329e9cbbe405668f25a9e893e5a1"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "634c329e9cbbe405668f25a9e893e5a1", "details_link": "https://dognzb.cr/details/634c329e9cbbe405668f25a9e893e5a1", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.misc", "pubDate": "Sat, 23 Jan 2016 10:53:08 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T10:53:08-06:00"]}}, "comments": null, "epoch": 1453567988, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [708817306]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/5a2d7b27b157293ebc3ce25ee3ece9ae/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "708817306"}, {"name": "grabs", "value": "10"}, {"name": "guid", "value": "5a2d7b27b157293ebc3ce25ee3ece9ae"}, {"name": "info", "value": "https://dognzb.cr/details/5a2d7b27b157293ebc3ce25ee3ece9ae"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "5a2d7b27b157293ebc3ce25ee3ece9ae", "details_link": "https://dognzb.cr/details/5a2d7b27b157293ebc3ce25ee3ece9ae", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.misc", "pubDate": "Sat, 23 Jan 2016 10:47:19 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T10:47:19-06:00"]}}, "comments": null, "epoch": 1453567639, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [708029193]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/62826294c691d71331f5f5a2f7c97fab/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "708029193"}, {"name": "grabs", "value": "4"}, {"name": "guid", "value": "62826294c691d71331f5f5a2f7c97fab"}, {"name": "info", "value": "https://dognzb.cr/details/62826294c691d71331f5f5a2f7c97fab"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "62826294c691d71331f5f5a2f7c97fab", "details_link": "https://dognzb.cr/details/62826294c691d71331f5f5a2f7c97fab", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.boneless", "pubDate": "Sat, 23 Jan 2016 10:34:53 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-aAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T10:34:53-06:00"]}}, "comments": null, "epoch": 1453566893, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [707518680]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/596a884fae6c619ed9451f494dbcdc0f/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "707518680"}, {"name": "grabs", "value": "15"}, {"name": "guid", "value": "596a884fae6c619ed9451f494dbcdc0f"}, {"name": "info", "value": "https://dognzb.cr/details/596a884fae6c619ed9451f494dbcdc0f"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "596a884fae6c619ed9451f494dbcdc0f", "details_link": "https://dognzb.cr/details/596a884fae6c619ed9451f494dbcdc0f", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.teevee", "pubDate": "Sat, 23 Jan 2016 10:32:51 -0600", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-aAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T10:32:51-06:00"]}}, "comments": null, "epoch": 1453566771, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [746142045]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/59adfcfcf37d547edd950c9fbb0c1ce6/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "746142045"}, {"name": "grabs", "value": "18"}, {"name": "guid", "value": "59adfcfcf37d547edd950c9fbb0c1ce6"}, {"name": "info", "value": "https://dognzb.cr/details/59adfcfcf37d547edd950c9fbb0c1ce6"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "59adfcfcf37d547edd950c9fbb0c1ce6", "details_link": "https://dognzb.cr/details/59adfcfcf37d547edd950c9fbb0c1ce6", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.teevee", "pubDate": "Sat, 23 Jan 2016 10:32:13 -0600", "title": "Duck.Dynasty.S09E02.HDTV.x264-aAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T10:32:13-06:00"]}}, "comments": null, "epoch": 1453566733, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [261743919]}}, "category": "TV SD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/59adba189d51a27c8e9751dbd7022d43/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5030"}, {"name": "size", "value": "261743919"}, {"name": "grabs", "value": "46"}, {"name": "guid", "value": "59adba189d51a27c8e9751dbd7022d43"}, {"name": "info", "value": "https://dognzb.cr/details/59adba189d51a27c8e9751dbd7022d43"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "59adba189d51a27c8e9751dbd7022d43", "details_link": "https://dognzb.cr/details/59adba189d51a27c8e9751dbd7022d43", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 8, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.boneless", "pubDate": "Wed, 20 Jan 2016 09:59:50 -0600", "title": "Duck.Dynasty.S09E02.Flock.And.Key.REPACK.720p.AE.WEBRip.AAC2.0.H.264-BTW", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-20T09:59:50-06:00"]}}, "comments": null, "epoch": 1453305590, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [479760097]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/cc9365e19cc0963b48725e44ac4799ce/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "479760097"}, {"name": "grabs", "value": "49"}, {"name": "guid", "value": "cc9365e19cc0963b48725e44ac4799ce"}, {"name": "info", "value": "https://dognzb.cr/details/cc9365e19cc0963b48725e44ac4799ce"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "cc9365e19cc0963b48725e44ac4799ce", "details_link": "https://dognzb.cr/details/cc9365e19cc0963b48725e44ac4799ce", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 13, "indexerscore": 10, "indexer": "DogNZB", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": "alt.binaries.boneless", "pubDate": "Fri, 15 Jan 2016 09:29:10 -0600", "title": "Duck.Dynasty.S09E02.Flock.And.Key.720p.AE.WEBRip.AAC2.0.H.264-BTW", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-15T09:29:10-06:00"]}}, "comments": null, "epoch": 1452871750, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [467457289]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": null, "search_types": [], "link": "https://dognzb.cr/fetch/bb0ff779cffb5c47e72bdfbb977811f2/apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "467457289"}, {"name": "grabs", "value": "502"}, {"name": "guid", "value": "bb0ff779cffb5c47e72bdfbb977811f2"}, {"name": "info", "value": "https://dognzb.cr/details/bb0ff779cffb5c47e72bdfbb977811f2"}, {"name": "comments", "value": "0"}, {"name": "tvdbid", "value": "256825"}, {"name": "rageid", "value": "30870"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "tvtitle", "value": "Duck Dynasty"}, {"name": "rating", "value": "63"}, {"name": "genre", "value": "Reality"}], "precise_date": true, "search_ids": [], "indexerguid": "bb0ff779cffb5c47e72bdfbb977811f2", "details_link": "https://dognzb.cr/details/bb0ff779cffb5c47e72bdfbb977811f2", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 9, "indexer": "https://api.nzb.su", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": null, "pubDate": "Sat, 23 Jan 2016 12:15:16 -0500", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:53:08-05:00"]}}, "comments": null, "epoch": 1453567988, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [708817306]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": "sam7462672 <sam7462672@misc.my>", "search_types": [], "link": "https://api.nzb.su/getnzb/607ff20c82d7212f30e1e93153da386b.nzb&i=905&r=apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "708817306"}, {"name": "guid", "value": "607ff20c82d7212f30e1e93153da386b"}, {"name": "files", "value": "49"}, {"name": "poster", "value": "sam7462672 <sam7462672@misc.my>"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "rageid", "value": "30870"}, {"name": "grabs", "value": "67"}, {"name": "comments", "value": "0"}, {"name": "password", "value": "0"}, {"name": "usenetdate", "value": "Sat, 23 Jan 2016 11:53:08 -0500"}, {"name": "group", "value": "not available"}], "precise_date": true, "search_ids": [], "indexerguid": "607ff20c82d7212f30e1e93153da386b", "details_link": "https://api.nzb.su/details/607ff20c82d7212f30e1e93153da386b", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 9, "indexer": "https://api.nzb.su", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": null, "pubDate": "Sat, 23 Jan 2016 15:05:47 -0500", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-AAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:47:19-05:00"]}}, "comments": null, "epoch": 1453567639, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [707925918]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": "sam7462672 <sam7462672@misc.my>", "search_types": [], "link": "https://api.nzb.su/getnzb/9bfe6e0508f267a9997d3a05a08b6e87.nzb&i=905&r=apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "707925918"}, {"name": "guid", "value": "9bfe6e0508f267a9997d3a05a08b6e87"}, {"name": "files", "value": "49"}, {"name": "poster", "value": "sam7462672 <sam7462672@misc.my>"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "rageid", "value": "30870"}, {"name": "grabs", "value": "10"}, {"name": "comments", "value": "0"}, {"name": "password", "value": "0"}, {"name": "usenetdate", "value": "Sat, 23 Jan 2016 11:47:19 -0500"}, {"name": "group", "value": "not available"}], "precise_date": true, "search_ids": [], "indexerguid": "9bfe6e0508f267a9997d3a05a08b6e87", "details_link": "https://api.nzb.su/details/9bfe6e0508f267a9997d3a05a08b6e87", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 9, "indexer": "https://api.nzb.su", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": null, "pubDate": "Sat, 23 Jan 2016 11:46:11 -0500", "title": "Duck.Dynasty.S09E02.720p.HDTV.x264-aAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:32:51-05:00"]}}, "comments": null, "epoch": 1453566771, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [746142045]}}, "category": "TV HD", "hash": -958854479, "description": null, "poster": "r@ndom.tv (r@ndom)", "search_types": [], "link": "https://api.nzb.su/getnzb/ba9ee73da913a6c1394e8c8672f70be2.nzb&i=905&r=apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5040"}, {"name": "size", "value": "746142045"}, {"name": "guid", "value": "ba9ee73da913a6c1394e8c8672f70be2"}, {"name": "files", "value": "32"}, {"name": "poster", "value": "r@ndom.tv (r@ndom)"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "rageid", "value": "30870"}, {"name": "grabs", "value": "86"}, {"name": "comments", "value": "0"}, {"name": "password", "value": "0"}, {"name": "usenetdate", "value": "Sat, 23 Jan 2016 11:32:51 -0500"}, {"name": "group", "value": "not available"}], "precise_date": true, "search_ids": [], "indexerguid": "ba9ee73da913a6c1394e8c8672f70be2", "details_link": "https://api.nzb.su/details/ba9ee73da913a6c1394e8c8672f70be2", "passworded": false, "has_nfo": 2}, {"age_precise": true, "age_days": 5, "indexerscore": 9, "indexer": "https://api.nzb.su", "guid": null, "supports_queries": true, "dbsearchid": null, "py/object": "nzbhydra.nzb_search_result.NzbSearchResult", "group": null, "pubDate": "Sat, 23 Jan 2016 11:46:11 -0500", "title": "Duck.Dynasty.S09E02.HDTV.x264-aAF", "pubdate_utc": {"py/object": "future.types.newstr.newstr", "py/newargs": {"py/tuple": ["2016-01-23T11:32:13-05:00"]}}, "comments": null, "epoch": 1453566733, "size": {"py/object": "future.types.newint.newint", "py/newargs": {"py/tuple": [261743919]}}, "category": "TV SD", "hash": -958854479, "description": null, "poster": "provide@4u.net (yeahsure)", "search_types": [], "link": "https://api.nzb.su/getnzb/65406ecbc72254946f5fb6bdd376d3e1.nzb&i=905&r=apikey", "attributes": [{"name": "category", "value": "5000"}, {"name": "category", "value": "5030"}, {"name": "size", "value": "261743919"}, {"name": "guid", "value": "65406ecbc72254946f5fb6bdd376d3e1"}, {"name": "files", "value": "28"}, {"name": "poster", "value": "provide@4u.net (yeahsure)"}, {"name": "season", "value": "S09"}, {"name": "episode", "value": "E02"}, {"name": "rageid", "value": "30870"}, {"name": "grabs", "value": "75"}, {"name": "comments", "value": "0"}, {"name": "password", "value": "0"}, {"name": "usenetdate", "value": "Sat, 23 Jan 2016 11:32:13 -0500"}, {"name": "group", "value": "not available"}], "precise_date": true, "search_ids": [], "indexerguid": "65406ecbc72254946f5fb6bdd376d3e1", "details_link": "https://api.nzb.su/details/65406ecbc72254946f5fb6bdd376d3e1", "passworded": false, "has_nfo": 2}]')

        shuffle(results)
        a = search.find_duplicates(results)
        assert 6 == len(a)
        shuffle(results)
        a = search.find_duplicates(results)
        assert 6 == len(a)
        shuffle(results)
        a = search.find_duplicates(results)
        assert 6 == len(a)
        shuffle(results)
        a = search.find_duplicates(results)
        assert 6 == len(a)
        shuffle(results)
        a = search.find_duplicates(results)
        assert 6 == len(a)
        print(a)