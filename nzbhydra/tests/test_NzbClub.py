from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

import unittest

import pytest
from builtins import open
from future import standard_library
#standard_library.install_aliases()
from builtins import *
from freezegun import freeze_time

from furl import furl
from nzbhydra import config

from nzbhydra.database import Indexer
from nzbhydra.search import SearchRequest
from nzbhydra.searchmodules.nzbclub import NzbClub
from nzbhydra.tests.db_prepare import set_and_drop



class NzbclubTests(unittest.TestCase):
    @pytest.fixture
    def setUp(self):
        set_and_drop()

    def testUrlGeneration(self):
        w = NzbClub(config.settings.indexers.nzbclub)
        self.args = SearchRequest(query="a showtitle", season=1, episode=2)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        print(urls[0])
        self.assertEqual('a showtitle s01e02 or a showtitle 1x02', furl(urls[0]).args["q"])

        self.args = SearchRequest(query="a showtitle", season=1, episode=None)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual('a showtitle s01 or a showtitle "season 1"', furl(urls[0]).args["q"])

    @freeze_time("2015-09-24 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        w = NzbClub(config.settings.indexers.nzbclub)
        with open("mock/nzbclub--q-testtitle.xml", encoding="latin-1") as f:
            entries = w.process_query_result(f.read(), "aquery").entries
            self.assertEqual('testtitle1', entries[0].title)
            self.assertEqual("http://www.nzbclub.com/nzb_get/60269450/testtitle1.nzb", entries[0].link)
            self.assertEqual(1075514926, entries[0].size)
            self.assertEqual("60269450", entries[0].indexerguid)
            self.assertEqual(1443019463, entries[0].epoch)
            self.assertEqual("2015-09-23T09:44:23-05:00", entries[0].pubdate_utc)
            self.assertEqual("Wed, 23 Sep 2015 09:44:23 -0500", entries[0].pubDate)
            self.assertEqual(0, entries[0].age_days)
            self.assertEqual("http://www.nzbclub.com/nzb_view/60269450/testtitle1", entries[0].details_link)
            self.assertEqual("YIFY@gmail.com (YIFY)", entries[0].poster)
            self.assertEqual("alt.binaries.movies", entries[0].group)

    
    def testGetNzbLink(self):
        n = NzbClub(config.settings.indexers.nzbclub)
        link = n.get_nzb_link("guid", "title")
        self.assertEqual("https://www.nzbclub.com/nzb_get/guid/title.nzb", link)
    