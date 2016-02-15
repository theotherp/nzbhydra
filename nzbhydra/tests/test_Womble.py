from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import pytest
from builtins import open
from future import standard_library

from nzbhydra.search import SearchRequest

#standard_library.install_aliases()
from builtins import *
import unittest

from freezegun import freeze_time

from nzbhydra.database import Indexer
from nzbhydra.searchmodules.womble import Womble
from nzbhydra.tests.db_prepare import set_and_drop
from nzbhydra import config


class MyTestCase(unittest.TestCase):
    @pytest.fixture
    def setUp(self):
        set_and_drop()
        config.settings.load("testsettings.cfg")
        self.womble = Womble(config.settings.indexers.womble)
        
    def testGetTvRssUrls(self):
        searchRequest = SearchRequest(type="tv")
        urls = self.womble.get_showsearch_urls(searchRequest)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://newshost.co.za/rss?fr=false", urls[0])

        searchRequest.category = "TV"
        urls = self.womble.get_showsearch_urls(searchRequest)
        self.assertEqual(4, len(urls))

        searchRequest.category = "TV HD"
        urls = self.womble.get_showsearch_urls(searchRequest)
        self.assertEqual(2, len(urls))

        searchRequest.category = "TV SD"
        urls = self.womble.get_showsearch_urls(searchRequest)
        self.assertEqual(2, len(urls))

    @freeze_time("2015-09-21 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        with open("mock/womble--sec-tv-dvd.xml") as f:
            entries = self.womble.process_query_result(f.read(), "aquery").entries
            self.assertEqual("testtitle1", entries[0].title)
            self.assertEqual("http://www.newshost.co.za/nzb/79d/testtitle1.nzb", entries[0].link)
            self.assertEqual(336592896, entries[0].size)
            self.assertEqual("TV SD", entries[0].category)
            self.assertEqual("79d/testtitle1.nzb", entries[0].indexerguid)
            self.assertEqual(1442790103, entries[0].epoch)
            self.assertEqual("2015-09-20T23:01:43+00:00", entries[0].pubdate_utc)
            self.assertEqual(0, entries[0].age_days)
            self.assertEqual("79d/testtitle1.nzb", entries[0].indexerguid)
            
    
    def testGetNzbLink(self):
        link = self.womble.get_nzb_link("abc/title.nzb", "title") #title is ignored
        self.assertEqual("https://newshost.co.za/nzb/abc/title.nzb", link)
