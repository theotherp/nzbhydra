from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

import pytest
from builtins import open
from future import standard_library

from nzbhydra.nzb_search_result import NzbSearchResult

standard_library.install_aliases()
from builtins import *
import re
import unittest
import sys
import logging
from pprint import pprint
import json

import arrow
from freezegun import freeze_time
import requests
import responses
from furl import furl

from nzbhydra import search, config, search_module, database
from nzbhydra.indexers import  read_indexers_from_config
from nzbhydra.database import Indexer
from nzbhydra.tests.db_prepare import set_and_drop

logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")

set_and_drop()
# Indexer(module="newznab", name="NZBs.org", settings={"apikey": "apikeynzbsorg", "query_url": "http://127.0.0.1:5001/nzbsorg", "base_url": "http://127.0.0.1:5001/nzbsorg", "search_types": ["tv", "general", "movie"], "search_ids": ["imdbid", "tvdbid", "rid"]}).save()
# Indexer(module="newznab", name="DOGNzb", settings={"apikey": "apikeydognzb", "query_url": "http://127.0.0.1:5001/dognzb", "base_url": "http://127.0.0.1:5001/dognzb", "search_types": ["tv", "general"], "search_ids": ["tvdbid", "rid"]}).save()
# Indexer(module="nzbclub", name="NZBClub", settings={"query_url": "http://127.0.0.1:5001/nzbclub", "base_url": "http://127.0.0.1:5001/nzbclub", "search_types": ["general", "tv", "movie"], "search_ids": [], "generate_queries": True}).save()
# Indexer(module="womble", name="womble", settings={"query_url": "http://www.newshost.co.za/rss", "base_url": "http://127.0.0.1:5001/womble", "search_types": ["tv"]}).save()
config.indexerSettings.binsearch.enabled.set(False)
config.indexerSettings.nzbindex.enabled.set(False)
config.indexerSettings.omgwtf.enabled.set(False)

config.indexerSettings.womble.enabled.set(True)
config.indexerSettings.nzbclub.enabled.set(True)

config.indexerSettings.newznab1.name.set("NZBs.org")
config.indexerSettings.newznab1.enabled.set(True)
config.indexerSettings.newznab1.search_ids.set(["imdbid", "tvdbid", "rid"])

config.indexerSettings.newznab2.name.set("DOGNzb")
config.indexerSettings.newznab2.enabled.set(True)
config.indexerSettings.newznab2.search_ids.set(["tvdbid", "rid"])


class SearchTests(unittest.TestCase):
    @pytest.fixture
    def setUp(self):
        self.oldExecute_search_queries = search.start_search_futures
        database.IndexerStatus.delete().execute()
        database.IndexerSearch.delete().execute()

    def tearDown(self):
        search.start_search_futures = self.oldExecute_search_queries


    def test_pick_indexers(self):
        config.searchingSettings.generate_queries.set([])
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
        self.assertEqual("NZBs.org", indexers[0][0].name)
        self.assertEqual("DOGNzb", indexers[0][1].name)

        indexers = search.pick_indexers("tv", identifier_key="imdbid")
        self.assertEqual(1, len(indexers[0]))
        self.assertEqual("NZBs.org", indexers[0][0].name)

        #WIth query generation NZBClub should also be returned
        config.searchingSettings.generate_queries.set([config.InternalExternalSelection.internal.name])
        indexers = search.pick_indexers(identifier_key="tvdbid")
        self.assertEqual(3, len(indexers[0]))
        self.assertEqual("NZBClub", indexers[0][0].name)
        self.assertEqual("NZBs.org", indexers[0][1].name)
        self.assertEqual("DOGNzb", indexers[0][2].name)
        

        


    def testHandleIndexerFailureAndSuccess(self):
        Indexer(module="newznab", name="NZBs.org").save()
        indexer_model = Indexer.get(Indexer.name == "NZBs.org")
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
        query = furl("https://nzbs.org/api").add({"apikey": "", "t": action, "o": "json", "extended": 1})
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

