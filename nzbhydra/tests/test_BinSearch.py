from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
#standard_library.install_aliases()
from builtins import *
import unittest
from freezegun import freeze_time

from furl import furl
import pytest
from nzbhydra import config

from nzbhydra.database import Indexer
from nzbhydra.indexers import getIndexerSettingByName
from nzbhydra.search import SearchRequest
from nzbhydra.searchmodules.binsearch import Binsearch
from nzbhydra.tests.UrlTestCase import UrlTestCase
from nzbhydra.tests.db_prepare import set_and_drop


class TestBinsearch(UrlTestCase):
    
    @pytest.fixture
    def setUp(self):
        set_and_drop()
    

    def testUrlGeneration(self):
        w = Binsearch(getIndexerSettingByName("binsearch"))
        self.args = SearchRequest(query="a showtitle", season=1, episode=2)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(2, len(urls))
        self.assertEqual('a showtitle s01e02', furl(urls[0]).args["q"])
        self.assertEqual('a showtitle 1x02', furl(urls[1]).args["q"])

        self.args = SearchRequest(query="a showtitle", season=1, episode=None)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(2, len(urls))
        self.assertEqual('a showtitle s01', furl(urls[0]).args["q"])
        self.assertEqual('a showtitle "season 1"', furl(urls[1]).args["q"])

        self.args = SearchRequest(query="a showtitle", season=2016, episode="08/08")
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual('a showtitle "2016 08 08"', furl(urls[0]).args["q"])
        
    def testEbookUrlGeneration(self):
        getIndexerSettingByName("binsearch").searchTypes = []
        w = Binsearch(getIndexerSettingByName("binsearch"))
        self.args = SearchRequest(query="anauthor atitle")
        urls = w.get_ebook_urls(self.args)
        self.assertEqual(4, len(urls))
        self.assertEqual("https://binsearch.info/index.php?max=100&postdate=date&min=0&adv_sort=date&adv_col=on&q=anauthor+atitle+ebook", urls[0])
        self.assertEqual("https://binsearch.info/index.php?max=100&postdate=date&min=0&adv_sort=date&adv_col=on&q=anauthor+atitle+mobi", urls[1])

        self.args = SearchRequest(author="anauthor", title="atitle")
        urls = w.get_ebook_urls(self.args)
        self.assertEqual(4, len(urls))
        self.assertEqual("https://binsearch.info/index.php?max=100&postdate=date&min=0&adv_sort=date&adv_col=on&q=anauthor+atitle+ebook", urls[0])
        self.assertEqual("https://binsearch.info/index.php?max=100&postdate=date&min=0&adv_sort=date&adv_col=on&q=anauthor+atitle+mobi", urls[1])
        
        

    @freeze_time("2015-09-30 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        w = Binsearch(getIndexerSettingByName("binsearch"))
        with open("mock/binsearch--q-testtitle.html", encoding="latin-1") as f:
            body = f.read()
            result = w.process_query_result(body, SearchRequest())
            entries = list(result.entries)
            self.assertEqual('testtitle1.TrueFrench.1080p.X264.AC3.5.1-JKF.mkv', entries[0].title)
            self.assertEqual("https://binsearch.info?action=nzb&176073735=1", entries[0].link)
            self.assertEqual(13110387671, entries[0].size)
            self.assertEqual("176073735", entries[0].indexerguid)
            self.assertEqual(1443312000, entries[0].epoch)
            self.assertEqual("2015-09-27T00:00:00+00:00", entries[0].pubdate_utc)
            self.assertEqual("Sun, 27 Sep 2015 00:00:00 -0000", entries[0].pubDate)
            self.assertEqual(3, entries[0].age_days)
            self.assertFalse(entries[0].age_precise)
            self.assertEqual("Ramer@marmer.com (Clown_nez)", entries[0].poster)
            self.assertEqual("alt.binaries.movies.mkv", entries[0].group)
            self.assertUrlEqual("https://binsearch.info/?b=testtitle1.3D.TOPBOT.TrueFrench.1080p.X264.A&g=alt.binaries.movies.mkv&p=Ramer%40marmer.com+%28Clown_nez%29&max=250", entries[0].details_link)
            self.assertTrue(result.has_more)
            self.assertFalse(result.total_known)
        
    def testProcess_results_totalknown(self):
        w = Binsearch(getIndexerSettingByName("binsearch"))
        with open("mock/binsearch--q-testtitle3results.html", encoding="latin-1") as f:
            body = f.read()
            result = w.process_query_result(body, SearchRequest())
            self.assertFalse(result.has_more)
            self.assertEqual(3, result.total)  
                
    def testGetNzbLink(self):
        n = Binsearch(getIndexerSettingByName("binsearch"))
        link = n.get_nzb_link("guid", "title")
        assert "action=nzb" in link
        assert "guid=1" in link
        
