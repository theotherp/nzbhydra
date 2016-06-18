from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import sys
import unittest

from bunch import Bunch

from nzbhydra import config, categories
from nzbhydra.search import SearchRequest
from nzbhydra.search_module import SearchModule, NzbSearchResult

logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")


class SearchModuleTests(unittest.TestCase):
    config.settings = Bunch.fromDict(config.initialConfig)

    def testIgnoreCategories(self):
        sm = SearchModule(None)
        sr = SearchRequest()
        cat = categories.getCategoryByName("movies")
        nsr = NzbSearchResult(pubdate_utc="", category=cat)

        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        cat.ignoreResults = "always"
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("always" in reason)

        cat.ignoreResults = "internal"
        sr = SearchRequest(internal=True)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("internal" in reason)

        cat.ignoreResults = "external"
        sr = SearchRequest(internal=True)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        cat.ignoreResults = "internal"
        sr = SearchRequest(internal=False)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        cat.ignoreResults = "external"
        sr = SearchRequest(internal=False)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("API" in reason)

    def testLimits(self):
        sm = SearchModule(None)

        nsr = NzbSearchResult(pubdate_utc="", size=90 * 1024 * 1024)
        sr = SearchRequest(minsize=100)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("Smaller than" in reason)

        nsr = NzbSearchResult(pubdate_utc="", size=110 * 1024 * 1024)
        sr = SearchRequest(minsize=100)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)


        nsr = NzbSearchResult(pubdate_utc="", size=110 * 1024 * 1024)
        sr = SearchRequest(maxsize=100)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("Bigger than" in reason)

        nsr = NzbSearchResult(pubdate_utc="", size=90 * 1024 * 1024)
        sr = SearchRequest(maxsize=100)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)


        nsr = NzbSearchResult(pubdate_utc="", age_days=90)
        sr = SearchRequest(minage=100)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("Younger than" in reason)

        nsr = NzbSearchResult(pubdate_utc="", age_days=110)
        sr = SearchRequest(minage=100)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", age_days=110)
        sr = SearchRequest(maxage=100)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("Older than" in reason)

        nsr = NzbSearchResult(pubdate_utc="", age_days=90)
        sr = SearchRequest(maxage=100)
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)
        
    
    def testWords(self):
        sm = SearchModule(None)
        sr = SearchRequest(forbiddenWords=["a", "b"], requiredWords=["c", "d"])

        nsr = NzbSearchResult(pubdate_utc="", title="xyz c")
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz d")
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz cd")
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)
        
        nsr = NzbSearchResult(pubdate_utc="", title="xyz")
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("None of the required" in reason)
        

        nsr = NzbSearchResult(pubdate_utc="", title="xyz acd")
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"a\" is in the list" in reason)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz Acd")
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"a\" is in the list" in reason)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz bcd")
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"b\" is in the list" in reason)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz abcd")
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"a\" is in the list" in reason)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz acd")
        sr = SearchRequest(forbiddenWords=["A"])
        accepted, reason = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"a\" is in the list" in reason)
