from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytest
from future import standard_library

from nzbhydra.nzb_search_result import NzbSearchResult
from nzbhydra.search import SearchRequest
from nzbhydra.tests import mockbuilder

standard_library.install_aliases()
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
        for i in range(1, indexerCount + 1):
            # Configure indexer
            indexerName = "newznab%d" % i
            setting = getattr(config.indexerSettings, indexerName)
            setting.name.set(indexerName)
            setting.enabled.set(True)
            setting.search_ids.set(["imdbid", "tvdbid", "rid"])
            indexerHost = "http://www.newznab%d.com" % i
            setting.host.set(indexerHost)
            print("Configured " + setting.name.get() + " with host " + setting.host.get())

    def prepareSearchMocks(self, rsps, indexerCount=2, resultsPerIndexers=1, newznabItems=None):
        testData = []
        self.prepareIndexers(indexerCount)

        for i in range(1, indexerCount + 1):
            # Prepare search results
            if newznabItems is not None:
                indexerNewznabItems = newznabItems[i - 1]
            else:
                indexerNewznabItems = [mockbuilder.buildNewznabItem("newznab%dresult%d.title" % (i, j), "newznab%dresult%d.guid" % (i, j), "newznab%dresult%d.link" % (i, j), arrow.get(0).format("ddd, DD MMM YYYY HH:mm:ss Z"), "newznab%dresult%d.description" % (i, j), 1000, "newznab%d" % i, None) for
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
        # Indexer(module="newznab", name="newznab1", settings={"apikey": "apikeynzbsorg", "query_url": "http://127.0.0.1:5001/nzbsorg", "base_url": "http://127.0.0.1:5001/nzbsorg", "search_types": ["tv", "general", "movie"], "search_ids": ["imdbid", "tvdbid", "rid"]}).save()
        # Indexer(module="newznab", name="newznab2", settings={"apikey": "apikeynewznab2", "query_url": "http://127.0.0.1:5001/newznab2", "base_url": "http://127.0.0.1:5001/newznab2", "search_types": ["tv", "general"], "search_ids": ["tvdbid", "rid"]}).save()
        # Indexer(module="nzbclub", name="NZBClub", settings={"query_url": "http://127.0.0.1:5001/nzbclub", "base_url": "http://127.0.0.1:5001/nzbclub", "search_types": ["general", "tv", "movie"], "search_ids": [], "generate_queries": True}).save()
        # Indexer(module="womble", name="womble", settings={"query_url": "http://www.newshost.co.za/rss", "base_url": "http://127.0.0.1:5001/womble", "search_types": ["tv"]}).save()
        config.indexerSettings.binsearch.enabled.set(False)
        config.indexerSettings.nzbindex.enabled.set(False)
        config.indexerSettings.omgwtf.enabled.set(False)
        config.indexerSettings.womble.enabled.set(False)
        config.indexerSettings.nzbclub.enabled.set(False)

        # Disable all newznab indexers by default
        for i in range(1, 21):
            indexerName = "newznab%d" % i
            getattr(config.indexerSettings, indexerName).enabled.set(False)

        config.indexerSettings.newznab1.name.set("newznab1")
        config.indexerSettings.newznab1.enabled.set(True)
        config.indexerSettings.newznab1.search_ids.set(["imdbid", "tvdbid", "rid"])

        config.indexerSettings.newznab2.name.set("newznab2")
        config.indexerSettings.newznab2.enabled.set(True)
        config.indexerSettings.newznab2.search_ids.set(["tvdbid", "rid"])

        self.oldExecute_search_queries = search.start_search_futures
        database.IndexerStatus.delete().execute()
        database.IndexerSearch.delete().execute()

    def tearDown(self):
        search.start_search_futures = self.oldExecute_search_queries

    def test_pick_indexers(self):
        config.searchingSettings.generate_queries.set([])
        config.indexerSettings.womble.enabled.set(True)
        config.indexerSettings.nzbclub.enabled.set(True)
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
        config.searchingSettings.generate_queries.set([config.InternalExternalSelection.internal.name])
        indexers = search.pick_indexers(identifier_key="tvdbid")
        self.assertEqual(3, len(indexers[0]))
        self.assertEqual("NZBClub", indexers[0][0].name)
        self.assertEqual("newznab1", indexers[0][1].name)
        self.assertEqual("newznab2", indexers[0][2].name)
    
    def testHandleIndexerFailureAndSuccess(self):
        Indexer(module="newznab", name="newznab1").save()
        indexer_model = Indexer.get(Indexer.name == "newznab1")
        with freeze_time("2015-09-20 14:00:00", tz_offset=-4):
            sm = search_module.SearchModule(config.indexerSettings.newznab1)
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
        config.searchingSettings.duplicateAgeThreshold.set(120)
        age_threshold = config.searchingSettings.duplicateAgeThreshold.get()
        config.searchingSettings.duplicateSizeThresholdInPercent.set(1)
    
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
        config.searchingSettings.duplicateAgeThreshold.set(3600)
        config.searchingSettings.duplicateSizeThresholdInPercent.set(0.1)
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="2", guid="2")
        result3 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="3", guid="3")
        result4 = NzbSearchResult(title="Title3", epoch=0, size=1, indexer="4", guid="4")
        result5 = NzbSearchResult(title="TITLE1", epoch=0, size=1, indexer="5", guid="5")
        result6 = NzbSearchResult(title="Title4", epoch=0, size=1, indexer="6", guid="6")
        results = search.find_duplicates([result1, result2, result3, result4, result5, result6])
        self.assertEqual(4, len(results))
        self.assertEqual(2, len(results[0]))
        self.assertEqual(2, len(results[1]))
        self.assertEqual(1, len(results[2]))
        self.assertEqual(1, len(results[3]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", guid="2")
        result3 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="3", guid="3")
        result4 = NzbSearchResult(title="Title1", epoch=100000000, size=1, indexer="4", guid="4")
        results = search.find_duplicates([result1, result2, result3, result4])
        self.assertEqual(2, len(results))
        self.assertEqual(3, len(results[0]))
        self.assertEqual(1, len(results[1]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1a", guid="1", pubdate_utc=arrow.get(0).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result2 = NzbSearchResult(title="Title1", epoch=10000000, size=1, indexer="2a", guid="2", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result3 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1b", guid="3", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result4 = NzbSearchResult(title="Title1", epoch=10000000, size=1, indexer="2b", guid="4", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result5 = NzbSearchResult(title="Title1", epoch=1000000000, size=1, indexer="3", guid="5", pubdate_utc=arrow.get(1000000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        results = search.find_duplicates([result1, result2, result3, result4, result5])
        results = sorted(results, key=lambda x: len(x), reverse=True)
        self.assertEqual(3, len(results))
        self.assertEqual(2, len(results[0]))
        self.assertEqual(2, len(results[1]))
        self.assertEqual(1, len(results[2]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title1", epoch=100000000, size=1, indexer="2", guid="2")
        results = search.find_duplicates([result1, result2])
        results = sorted(results, key=lambda x: len(x), reverse=True)
        self.assertEqual(2, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title1", epoch=1, size=100000000, indexer="2", guid="2")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title1", epoch=1, size=1, indexer="2", guid="2")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))
        self.assertEqual(2, len(results[0]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title1", epoch=30 * 1000 * 60, size=1, indexer="2", guid="2")
        result3 = NzbSearchResult(title="Title1", epoch=60 * 1000 * 60, size=1, indexer="2", guid="3")
        results = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title2", epoch=1000000, size=1, indexer="2", guid="2")
        result3 = NzbSearchResult(title="Title3", epoch=5000000, size=1, indexer="2", guid="3")
        results = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))
    
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="2", guid="2")
        result3 = NzbSearchResult(title="Title3", epoch=0, size=1, indexer="2", guid="3")
        results = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))
    
        # Same poster and group posted inside of 24 hours
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=60 * 60 * 4, size=1, indexer="2", guid="2", poster="postera", group="groupa")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))
        self.assertEqual(2, len(results[0]))
    
        # Same poster and group posted outside of 24 hours
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=1000 * 60 * 25, size=1, indexer="2", guid="2", poster="postera", group="groupa")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
    
        # Same size and age and group but different posters (very unlikely) 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", guid="2", poster="posterb", group="groupa")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
    
        # Same size and age and poster but different groups (very unlikely) 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", guid="2", poster="postera", group="groupb")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
    
        # Same size and age and poster but unknown group inside of 3 hours 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera")
        result2 = NzbSearchResult(title="Title1", epoch=60 * 60 * 2, size=1, indexer="2", guid="2", poster="postera", group="groupb")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))
    
        # Same size and age and poster but unknown group outside of 3 hours 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera")
        result2 = NzbSearchResult(title="Title1", epoch=60 * 60 * 4, size=1, indexer="2", guid="2", poster="postera", group="groupb")
        results = search.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
    
    def testFindDuplicatesNew(self):
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=2, indexer="2", guid="2", poster="postera", group="groupb")
        result3 = NzbSearchResult(title="Title1", epoch=0, size=3, indexer="3", guid="3", poster="postera", group="groupb")
        results = search.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
    
    
    @responses.activate
    def testSimpleSearch(self):
        # Only use newznab indexers
        with responses.RequestsMock() as rsps:
            self.prepareSearchMocks(rsps, 2, 1)
    
            searchRequest = SearchRequest(type="search")
            result = search.search(True, searchRequest)
            results = result["results"]
            self.assertEqual(2, len(results))
            self.assertEqual("newznab1", results[0].indexer)
            self.assertEqual("newznab2", results[1].indexer)
    
    @responses.activate
    def testLimitAndOffset(self):
        # Only use newznab indexers
        with responses.RequestsMock() as rsps:
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
        config.searchingSettings.removeDuplicatesExternal.set(True)
        with responses.RequestsMock() as rsps:
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
            config.indexerSettings.newznab2.score.set(99)
            self.prepareSearchMocks(rsps, indexerCount=len(newznabItems), newznabItems=newznabItems)
            searchRequest = SearchRequest(type="search")
            result = search.search(False, searchRequest)
            results = result["results"]
            self.assertEqual(1, len(results))
            self.assertEqual("newznab2", results[0].indexer)
    
    @responses.activate
    def testDuplicateTaggingForInternalApi(self):
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
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            self.prepareSearchMocks(rsps, indexerCount=20, resultsPerIndexers=1)
    
            searchRequest = SearchRequest(type="search")
            result = search.search(True, searchRequest)
            results = result["results"]
            self.assertEqual(20, len(results))

