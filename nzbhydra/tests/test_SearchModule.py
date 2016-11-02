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
        cat = categories.getCategoryByName("movies")
        sr = SearchRequest(category=Bunch({"category": cat}))
        nsr = NzbSearchResult(pubdate_utc="", category=cat)

        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        cat.ignoreResults = "always"
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("always" in reason)

        cat.ignoreResults = "internal"
        sr = SearchRequest(internal=True, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("internal" in reason)

        cat.ignoreResults = "external"
        sr = SearchRequest(internal=True, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        cat.ignoreResults = "internal"
        sr = SearchRequest(internal=False, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        cat.ignoreResults = "external"
        sr = SearchRequest(internal=False, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("API" in reason)

    def testLimits(self):
        sm = SearchModule(None)
        cat = categories.getCategoryByName("movies")

        nsr = NzbSearchResult(pubdate_utc="", size=90 * 1024 * 1024, category=cat)
        sr = SearchRequest(minsize=100, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("Smaller than" in reason)

        nsr = NzbSearchResult(pubdate_utc="", size=110 * 1024 * 1024, category=cat)
        sr = SearchRequest(minsize=100, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)


        nsr = NzbSearchResult(pubdate_utc="", size=110 * 1024 * 1024, category=cat)
        sr = SearchRequest(maxsize=100, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("Bigger than" in reason)

        nsr = NzbSearchResult(pubdate_utc="", size=90 * 1024 * 1024, category=cat)
        sr = SearchRequest(maxsize=100, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)


        nsr = NzbSearchResult(pubdate_utc="", age_days=90, category=cat)
        sr = SearchRequest(minage=100, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("Younger than" in reason)

        nsr = NzbSearchResult(pubdate_utc="", age_days=110, category=cat)
        sr = SearchRequest(minage=100, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", age_days=110, category=cat)
        sr = SearchRequest(maxage=100, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("Older than" in reason)

        nsr = NzbSearchResult(pubdate_utc="", age_days=90, category=cat)
        sr = SearchRequest(maxage=100, category=Bunch({"category": cat}))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)
        
    
    def testWords(self):
        sm = SearchModule(None)

        #Required words
        sr = SearchRequest(forbiddenWords=[], requiredWords=["rqa", "rqb", "rq-c", "rq.d"], category=Bunch({"category": categories.getCategoryByName("all")}))
        
        nsr = NzbSearchResult(pubdate_utc="", title="xyz rqa", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", title="rqa", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", title="a.title.rqa.xyz", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", title="a title rqa xyz", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", title="a-title-rq-c", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", title="a title rq.d", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", title="rqatsch", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz.rqa", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz rqa rqb", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)
        
        nsr = NzbSearchResult(pubdate_utc="", title="xyz", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("None of the required" in reason)

        #Forbidden words
        sr = SearchRequest(forbiddenWords=["fba", "fbb", "fb-c", "fb.d"], requiredWords=[], category=Bunch({"category": categories.getCategoryByName("all")}))
        
        nsr = NzbSearchResult(pubdate_utc="", title="xyz fba")
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"fba\" is in the list" in reason)

        nsr = NzbSearchResult(pubdate_utc="", title="xyzfba")
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)
        

        nsr = NzbSearchResult(pubdate_utc="", title="xyzfb-ca")
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"fb-c\" is in the list" in reason)
        

        #Both
        sr = SearchRequest(forbiddenWords=["fba", "fbb", "fb-c", "fb.d"], requiredWords=["rqa", "rqb", "rq-c", "rq.d"], category=Bunch({"category": categories.getCategoryByName("all")}))

        nsr = NzbSearchResult(pubdate_utc="", title="xyz fba rqa")
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"fba\" is in the list" in reason)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz FBA rqb")
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"fba\" is in the list" in reason)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz rqa.rqb.fbb")
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"fbb\" is in the list" in reason)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz rqa.rqb.fba.fbc")
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"fba\" is in the list" in reason)

        nsr = NzbSearchResult(pubdate_utc="", title="xyz acd")
        sr = SearchRequest(forbiddenWords=["ACD"])
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)
        self.assertTrue("\"ACD\" is in the list" in reason)

        sr = SearchRequest(forbiddenWords=[], requiredWords=[], category=Bunch({"category": categories.getCategoryByName("all")}))
        config.settings.searching.applyRestrictions = "both"
        config.settings.searching.requiredWords = ""
        config.settings.searching.forbiddenWords = ""
        config.settings.searching.requiredRegex = ""
        config.settings.searching.forbiddenRegex = ""
        sr.category.category.applyRestrictions = "both"
        sr.category.category.forbiddenWords = ""
        sr.category.category.requiredWords = ""
        sr.category.category.forbiddenRegex = ""
        sr.category.category.requiredRegex = ""
        
        sr.internal = True
        config.settings.searching.applyRestrictions = "both"
        config.settings.searching.forbiddenRegex = "abc"
        
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)

        config.settings.searching.applyRestrictions = "internal"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)

        config.settings.searching.applyRestrictions = "external"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        sr.internal = False
        config.settings.searching.applyRestrictions = "both"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)

        config.settings.searching.applyRestrictions = "internal"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        config.settings.searching.applyRestrictions = "external"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)

        sr.internal = True
        config.settings.searching.forbiddenRegex = ""
        sr.category.category.forbiddenRegex = "abc"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)

        sr.category.category.applyRestrictions = "internal"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)

        sr.category.category.applyRestrictions = "external"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        sr.internal = False
        sr.category.category.applyRestrictions = "both"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)

        sr.category.category.applyRestrictions = "internal"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertTrue(accepted)

        sr.category.category.applyRestrictions = "external"
        nsr = NzbSearchResult(pubdate_utc="", title="abc", category=categories.getCategoryByName("all"))
        accepted, reason, ri = sm.accept_result(nsr, sr, None)
        self.assertFalse(accepted)