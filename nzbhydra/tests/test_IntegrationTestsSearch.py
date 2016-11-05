from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import random
import threading
from time import sleep

import pytest
import requests_mock
from bunch import Bunch
from playhouse.sqlite_ext import SqliteExtDatabase
from retry import retry

from nzbhydra import database
from nzbhydra.tests import mockbuilder
# standard_library.install_aliases()
from builtins import *
import re
import unittest
import sys
import logging

import arrow

from nzbhydra import config, web
from nzbhydra.indexers import read_indexers_from_config
from nzbhydra.tests.db_prepare import set_and_drop
from nzbhydra.searchmodules import newznab
from urltools import compare

logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")


class AbstractSearchTestCase(unittest.TestCase):

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
            nn.backend = "newznab"
            nn.categories = []
            nn.timeout = None
            nn.score = 0
            nn.accessType = "both"
            nn.search_ids = ["imdbid", "tvdbid", "rid"]
            config.settings.indexers.append(nn)

    def prepareSearchMocks(self, requestsMock, indexerCount=2, resultsPerIndexers=1, newznabItems=None, title="newznab%dresult%d.title", categories=None, skip=None):
        """

        :param requestsMock: 
        :param indexerCount: 
        :param resultsPerIndexers: 
        :param newznabItems: 
        :param title: 
        :param categories: 
        :param skip: List of tuples with indexer and result index which will not be returned
        :return: 
        """
        if skip is None:
            skip = []
        allNewznabItems = []
        self.response_callbacks = []
        self.prepareIndexers(indexerCount)

        for i in range(1, indexerCount + 1):
            # Prepare search results
            if newznabItems is not None:
                indexerNewznabItems = newznabItems[i - 1]
            else:
                indexerNewznabItems = [mockbuilder.buildNewznabItem(title % (i, j), "newznab%dresult%d.guid" % (i, j), " http://newznab%dresult%d.link" % (i, j), arrow.get(0).format("ddd, DD MMM YYYY HH:mm:ss Z"), "newznab%dresult%d.description" % (i, j), 1000, "newznab%d" % i, categories) for
                                       j in
                                       range(1, resultsPerIndexers + 1)
                                       if not (i, j) in skip
                                       ]
            allNewznabItems.extend(indexerNewznabItems)
            xml = mockbuilder.buildNewznabResponse("newznab%dResponse" % i, indexerNewznabItems, 0, len(indexerNewznabItems))

            requestsMock.register_uri('GET', re.compile(r'.*newznab%d.*' % i), text=xml)
        read_indexers_from_config()

        allNewznabItems = sorted(allNewznabItems, key=lambda x: x.title)
        return allNewznabItems

    def assertSearchResults(self, results, expectedItems):
        """
        Checks the results against the expected items. Because every item should have a unique title we can compare values of each item in the sorted lists of results  
        :param results: NzbSearchResults
        :param expectedItems:  NewznabItems from mockbuilder
        """
        self.assertEqual(len(expectedItems), len(results))

        results = [Bunch.fromDict(x) for x in results]

        results = sorted(results, key=lambda x: x.title)
        for i, expected in enumerate(expectedItems):
            result = results[i]
            self.assertEqual(expected.title, result.title)

    #@pytest.fixture
    def setUp(self):
        set_and_drop()
        config.settings = Bunch.fromDict(config.initialConfig)
        self.app = web.app.test_client()
        config.settings.main.apikey = None

        self.newznab1 = Bunch()
        self.newznab1.enabled = True
        self.newznab1.name = "newznab1"
        self.newznab1.host = "https://indexer1.com"
        self.newznab1.apikey = "apikeyindexer1.com"
        self.newznab1.timeout = None
        self.newznab1.hitLimit = None
        self.newznab1.backend = ""
        self.newznab1.categories = []
        self.newznab1.score = 0
        self.newznab1.type = "newznab"
        self.newznab1.accessType = "both"
        self.newznab1.search_ids = ["imdbid", "rid", "tvdbid"]
        self.newznab1.searchTypes = ["book", "tvsearch", "movie"]

        self.newznab2 = Bunch()
        self.newznab2.enabled = True
        self.newznab2.name = "newznab2"
        self.newznab2.host = "https://indexer2.com"
        self.newznab2.apikey = "apikeyindexer2.com"
        self.newznab2.timeout = None
        self.newznab2.hitLimit = None
        self.newznab2.backend = ""
        self.newznab2.categories = []
        self.newznab2.accessType = "both"
        self.newznab2.score = 0
        self.newznab2.type = "newznab"
        self.newznab2.search_ids = ["rid", "tvdbid"]
        self.newznab2.searchTypes = ["tvsearch", "movie"]

        config.settings.indexers = [self.newznab1, self.newznab2]

        read_indexers_from_config()

    @retry(AssertionError, delay=1, tries=10)
    def tryDatabaseShutown(self):
        database.db.stop()
        database.db.close()
        if not database.db.is_closed():
            raise AssertionError("Database not closed")

    def tearDown(self):
        try:
            self.tryDatabaseShutown()
        except AssertionError:
            print("DB not shut down")


class IntegrationApiSearchTests(AbstractSearchTestCase):
        
    @requests_mock.Mocker()
    def testSimpleQuerySearch(self, m):
        web.app.template_folder = "../templates"
    
        # Query only
        expectedItems = self.prepareSearchMocks(m, 1, 1)
        with web.app.test_request_context('/api?t=search&q=query&apikey=%s' % config.settings.main.apikey):
            response = web.api()
            entries, _, _ = newznab.NewzNab(Bunch.fromDict({"name": "forTest", "score": 0, "host": "host"})).parseXml(response.data)
            self.assertSearchResults(entries, expectedItems)
            calledUrls = sorted([x.url for x in m.request_history])
            self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query', calledUrls[0]))
    
        # Query with category
        expectedItems = self.prepareSearchMocks(m, 1, 1)
        with web.app.test_request_context('/api?t=search&q=query&apikey=%s&cat=2000' % config.settings.main.apikey):
            response = web.api()
            entries, _, _ = newznab.NewzNab(Bunch.fromDict({"name": "forTest", "score": 0, "host": "host"})).parseXml(response.data)
            self.assertSearchResults(entries, expectedItems)
            calledUrls = sorted([x.url for x in m.request_history])
            self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query&cat=2000', calledUrls[0]))
    
    # Scenario: Some words are required and forbidden globally as well as per category. Supplied newznab category is mapped to internal category and where possible forbidden words are excluded in query 
    @requests_mock.Mocker()
    def testRequiredAndForbiddenWords(self, m):
        web.app.template_folder = "../templates"
    
        config.settings.searching.forbiddenWords = "newznab1result1"  # Will be removed from parsed results
        config.settings.categories.categories["movies"].forbiddenWords = "newznab1result2"  # Will be removed from parsed results
        config.settings.searching.forbiddenWords = "newznab1result3"  # Will be excluded in query
        config.settings.categories.categories["movies"].forbiddenWords = "newznab1result4"  # Will be excluded in query
        config.settings.categories.categories["movies"].requiredWords = "newznab1result6"  # Will be left
        config.settings.searching.requiredWords = "newznab1result7"  # Will be left
    
        config.settings.categories.categories["movies"].applyRestrictions = "external"
    
        expectedItems = self.prepareSearchMocks(m, 1, 7, categories=[2000], skip=[(1, 3,), (1, 4,)])
        expectedItems.pop(0)  # The result with globally forbidden word
        expectedItems.pop(0)  # The result with category forbidden word 
        expectedItems.pop(0)  # The result with neither globally nor category required word (newznab1result5)
        with web.app.test_request_context('/api?t=search&q=query&apikey=%s&cat=2000' % config.settings.main.apikey):
            response = web.api()
            entries, _, _ = newznab.NewzNab(Bunch.fromDict({"name": "forTest", "score": 0, "host": "host"})).parseXml(response.data)
            self.assertSearchResults(entries, expectedItems)
            calledUrls = sorted([x.url for x in m.request_history])
            self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query+!newznab1result3+!newznab1result4&cat=2000', calledUrls[0]), calledUrls[0])
    
    
    
    # Scenario: Results from some categories are dismissed because the category is configured to be ignored. 
    @requests_mock.Mocker()
    def testIgnoreByCategories(self, m):
        web.app.template_folder = "../templates"
    
        config.settings.categories.categories["moviessd"].ignoreResults = "always"
        config.settings.categories.categories["xxx"].ignoreResults = "always"
        config.settings.categories.categories["pc"].ignoreResults = "internal"
        
        movieSdResult = mockbuilder.buildNewznabItem(title="result1", indexer_name="newznab1", categories=[2030]) #MoviesSD: Is dismissed because its specific category is ignored
        xxxResult = mockbuilder.buildNewznabItem(title="result2", indexer_name="newznab1", categories=[6000]) #XXX: Is dismissed because its category is ignored (no more or less specific category exists)
        movieResult = mockbuilder.buildNewznabItem(title="result3", indexer_name="newznab1", categories=[2000]) #Is kept because more specific category Movies SD is ignored but not movies in general
        movieHdResult = mockbuilder.buildNewznabItem(title="result4", indexer_name="newznab1", categories=[2040]) #MoviesHD: Is kept because the other specific category is ignored but not this one
        tvResult = mockbuilder.buildNewznabItem(title="result5", indexer_name="newznab1", categories=[5000]) #TV: Is kept because its category (tv) is never ignored 
        pcResult = mockbuilder.buildNewznabItem(title="result6", indexer_name="newznab1", categories=[4000])  # PC: Is kept because its category (tv) is only ignored for internal searches (but this is API)
    
        expectedItems = self.prepareSearchMocks(m, 1, newznabItems=[[movieSdResult, xxxResult, movieResult, movieHdResult, tvResult, pcResult]])
        expectedItems = expectedItems[2:] #First two results will be dismissed 
        
        with web.app.test_request_context('/api?t=search&q=query&apikey=%s' % config.settings.main.apikey):
            response = web.api()
            entries, _, _ = newznab.NewzNab(Bunch.fromDict({"name": "forTest", "score": 0, "host": "host"})).parseXml(response.data)
            self.assertSearchResults(entries, expectedItems)
            calledUrls = sorted([x.url for x in m.request_history])
            self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query', calledUrls[0]), calledUrls[0])

    @requests_mock.Mocker()
    def testFullStack(self, requestsMock):
        web.app.template_folder = "../templates"
        
        expectedItems = self.prepareSearchMocks(requestsMock, 1, 1)
        with web.app.test_request_context('/'):
            response = self.app.get("/api?t=search&q=query&cat=5030")
            entries, _, _ = newznab.NewzNab(Bunch.fromDict({"name": "forTest", "score": 0, "host": "host"})).parseXml(response.data)
            self.assertSearchResults(entries, expectedItems)
            calledUrls = sorted([x.url for x in requestsMock.request_history])
            self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query&cat=5030', calledUrls[0]))
            self.assertEqual("http://localhost:5075/getnzb?searchresultid=1", entries[0].link)
        
            #Download NZB
            config.settings.searching.nzbAccessType = "redirect"
            response = self.app.get("/getnzb?searchresultid=1")
            self.assertTrue("redirect" in response.data)
            
            config.settings.searching.nzbAccessType = "serve"
            requestsMock.register_uri('GET', re.compile(r'.*newznab1result1.link*'), text="NZB Data")
            response = self.app.get("/getnzb?searchresultid=1")
            self.assertEquals("NZB Data", response.data)

            #Download via API
            requestsMock.register_uri('GET', re.compile(r'.*newznab1result1.link*'), text="NZB Data")
            response = self.app.get("/api?t=get&id=%s" % entries[0].indexerguid)
            self.assertEquals("NZB Data", response.data)
            
            #Find downloaded NZBs in stats
            downloads = json.loads(self.app.get("/internalapi/getnzbdownloads").data)["nzbDownloads"]
            print(downloads)
            self.assertEqual(3, len(downloads))
            self.assertEqual("http://www.newznab1.com/details/newznab1result1.guid", downloads[0]["detailsLink"])
            self.assertTrue(downloads[0]["response_successful"])
            self.assertIsNone(downloads[2]["response_successful"]) #Don't know if redirection went well

    @requests_mock.Mocker()
    def testFullStackTvSearch(self, requestsMock):
        #Same as above but just with tvsearch, makes sure default sonarr searches work (breaking that is the worst...)
        web.app.template_folder = "../templates"

        expectedItems = self.prepareSearchMocks(requestsMock, 1, 1)
        with web.app.test_request_context('/'):
            response = self.app.get("/api?t=tvsearch&q=query&cat=5030")
            entries, _, _ = newznab.NewzNab(Bunch.fromDict({"name": "forTest", "score": 0, "host": "host"})).parseXml(response.data)
            self.assertSearchResults(entries, expectedItems)
            calledUrls = sorted([x.url for x in requestsMock.request_history])
            self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=tvsearch&extended=1&offset=0&limit=100&q=query&cat=5030', calledUrls[0]))
            self.assertEqual("http://localhost:5075/getnzb?searchresultid=1", entries[0].link)

            # Download NZB
            config.settings.searching.nzbAccessType = "redirect"
            response = self.app.get("/getnzb?searchresultid=1")
            self.assertTrue("redirect" in response.data)

            config.settings.searching.nzbAccessType = "serve"
            requestsMock.register_uri('GET', re.compile(r'.*newznab1result1.link*'), text="NZB Data")
            response = self.app.get("/getnzb?searchresultid=1")
            self.assertEquals("NZB Data", response.data)

            # Download via API
            requestsMock.register_uri('GET', re.compile(r'.*newznab1result1.link*'), text="NZB Data")
            response = self.app.get("/api?t=get&id=%s" % entries[0].indexerguid)
            self.assertEquals("NZB Data", response.data)

            # Find downloaded NZBs in stats
            downloads = json.loads(self.app.get("/internalapi/getnzbdownloads").data)["nzbDownloads"]
            print(downloads)
            self.assertEqual(3, len(downloads))
            self.assertEqual("http://www.newznab1.com/details/newznab1result1.guid", downloads[0]["detailsLink"])
            self.assertTrue(downloads[0]["response_successful"])
            self.assertIsNone(downloads[2]["response_successful"])  # Don't know if redirection went well


    # @requests_mock.Mocker()
    # def testBaseUrl(self, requestsMock):
    #     web.app.template_folder = "../templates"
    #     config.settings.main.urlBase = "/nzbhydra"
    #
    #     expectedItems = self.prepareSearchMocks(requestsMock, 1, 1)
    #     with web.app.test_request_context('/nzbhydra/'):
    #         response = self.app.get("/nzbhydra/api?t=search&q=query")
    #         entries, _, _ = newznab.NewzNab(Bunch.fromDict({"name": "forTest", "score": 0, "host": "host"})).parseXml(response.data)
    #         self.assertSearchResults(entries, expectedItems)
    #         calledUrls = sorted([x.url for x in requestsMock.request_history])
    #         self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query', calledUrls[0]))
    #         self.assertEqual("http://localhost:5075/nzbhydra/getnzb?searchresultid=1", entries[0].link)

    @requests_mock.Mocker()
    def testExcludeWordsInQuery(self, requestsMock):
        web.app.template_folder = "../templates"

        expectedItems = self.prepareSearchMocks(requestsMock, 1, 1)
        with web.app.test_request_context('/'):
            response = self.app.get("/api?t=search&q=query+!excluded")
            entries, _, _ = newznab.NewzNab(Bunch.fromDict({"name": "forTest", "score": 0, "host": "host", "backend": ""})).parseXml(response.data)
            self.assertSearchResults(entries, expectedItems)
            calledUrls = sorted([x.url for x in requestsMock.request_history])
            self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query+!excluded', calledUrls[0]))

            response = self.app.get("/api?t=search&q=query+--excluded")
            entries, _, _ = newznab.NewzNab(Bunch.fromDict({"name": "forTest", "score": 0, "host": "host", "backend": ""})).parseXml(response.data)
            self.assertSearchResults(entries, expectedItems)
            calledUrls = sorted([x.url for x in requestsMock.request_history])
            self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query+!excluded', calledUrls[0]))

            self.app.get("/internalapi/search?query=query+!excluded&category=all")
            calledUrls = sorted([x.url for x in requestsMock.request_history])
            self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query+!excluded', calledUrls[0]))

            self.app.get("/internalapi/search?query=query+--excluded&category=all")
            calledUrls = sorted([x.url for x in requestsMock.request_history])
            self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query+!excluded', calledUrls[0]))