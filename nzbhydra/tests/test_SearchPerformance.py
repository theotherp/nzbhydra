from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
from random import randint

import flask
import pytest
from bunch import Bunch

from nzbhydra.search import SearchRequest
from nzbhydra.tests import mockbuilder

# standard_library.install_aliases()
from builtins import *
import re
import unittest
import sys
import logging
from pprint import pprint

import arrow
import requests
import responses
from furl import furl

from nzbhydra import search, config, database, infos
from nzbhydra.indexers import read_indexers_from_config, getIndexerSettingByName
from nzbhydra.tests.db_prepare import set_and_drop

logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")


def mock(x, y, z=True):
    return True


class SearchPerformanceTests(unittest.TestCase):
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

    @responses.activate
    def testDuplicateTaggingForInternalApi(self):
        with self.app.test_request_context('/'):
            with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
                newznabItems = [[mockbuilder.buildNewznabItem(title="title%d" % i, pubdate=arrow.get(4000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=i, indexer_name="newznab1", guid="newznab1result%d" % i) for i in range(1, 250)],
                                [mockbuilder.buildNewznabItem(title="title%d" % i, pubdate=arrow.get(4000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=i, indexer_name="newznab2", guid="newznab2result%d" % i) for i in range(1, 250)],
                                [mockbuilder.buildNewznabItem(title="title%d" % i, pubdate=arrow.get(4000).format("ddd, DD MMM YYYY HH:mm:ss Z"), size=i, indexer_name="newznab3", guid="newznab3result%d" % i) for i in range(1, 250)]]
    
                self.prepareSearchMocks(rsps, indexerCount=len(newznabItems), newznabItems=newznabItems)
    
                searchRequest = SearchRequest(type="search")
                result = search.search(searchRequest)
