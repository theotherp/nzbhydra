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
from nzbhydra.indexers import getIndexerSettingByName
from nzbhydra.search import SearchRequest
from nzbhydra.searchmodules.nzbclub import NzbClub
from nzbhydra.tests.UrlTestCase import UrlTestCase
from nzbhydra.tests.db_prepare import set_and_drop



class NzbclubTests(UrlTestCase):
    @pytest.fixture
    def setUp(self):
        set_and_drop()

    def testUrlGeneration(self):
        w = NzbClub(getIndexerSettingByName("nzbclub"))
        self.args = SearchRequest(query="a showtitle", season=1, episode=2)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        
        self.assertEqual('a showtitle s01e02 or a showtitle 1x02', furl(urls[0]).args["q"])

        self.args = SearchRequest(query="a showtitle", season=1, episode=None)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual('a showtitle s01 or a showtitle "season 1"', furl(urls[0]).args["q"])

        self.args = SearchRequest(query="aquery", minage=4)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertUrlEqual("https://www.nzbclub.com/nzbrss.aspx?ig=2&ns=1&q=aquery&rpp=250&sn=1&st=5&ds=4", urls[0])

        self.args = SearchRequest(query="aquery", minage=18 * 31) #Beyond the last defined limit of days
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertUrlEqual("https://www.nzbclub.com/nzbrss.aspx?ig=2&ns=1&q=aquery&rpp=250&sn=1&st=5&ds=27", urls[0])
        
        self.args = SearchRequest(query="aquery", minage=70)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertUrlEqual("https://www.nzbclub.com/nzbrss.aspx?ig=2&ns=1&q=aquery&rpp=250&sn=1&st=5&ds=12", urls[0])

        self.args = SearchRequest(query="aquery", maxage=18 * 31) # Beyond the last defined limit of days, so don't limit
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertUrlEqual("https://www.nzbclub.com/nzbrss.aspx?ig=2&ns=1&q=aquery&rpp=250&sn=1&st=5", urls[0])
        
        self.args = SearchRequest(query="aquery", minage=4, maxage=70)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertUrlEqual("https://www.nzbclub.com/nzbrss.aspx?ig=2&ns=1&q=aquery&rpp=250&sn=1&st=5&de=13&ds=4", urls[0])

        self.args = SearchRequest(query="aquery", minsize=3)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertUrlEqual("https://www.nzbclub.com/nzbrss.aspx?ig=2&ns=1&q=aquery&rpp=250&sn=1&st=5&szs=8", urls[0])
        
        self.args = SearchRequest(query="aquery", minsize=2400)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertUrlEqual("https://www.nzbclub.com/nzbrss.aspx?ig=2&ns=1&q=aquery&rpp=250&sn=1&st=5&szs=23", urls[0])

        self.args = SearchRequest(query="aquery", maxsize=2400)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertUrlEqual("https://www.nzbclub.com/nzbrss.aspx?ig=2&ns=1&q=aquery&rpp=250&sn=1&st=5&sze=24", urls[0])

        self.args = SearchRequest(query="aquery", maxsize=30*1024*1024) #Beyond the last defined limit of size, so don't limit
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertUrlEqual("https://www.nzbclub.com/nzbrss.aspx?ig=2&ns=1&q=aquery&rpp=250&sn=1&st=5", urls[0])
        
        self.args = SearchRequest(query="aquery", minsize=3, maxsize=2400)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertUrlEqual("https://www.nzbclub.com/nzbrss.aspx?ig=2&ns=1&q=aquery&rpp=250&sn=1&st=5&sze=24&szs=8", urls[0])

        self.args = SearchRequest(query="aquery", forbiddenWords=["ignorethis"])
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://www.nzbclub.com/nzbrss.aspx?rpp=250&ns=1&sn=1&ig=2&st=5&q=aquery+-ignorethis", urls[0])

        self.args = SearchRequest(query="a showtitle", season=2016, episode="08/08")
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual('a showtitle "2016 08 08"', furl(urls[0]).args["q"])

        
        

    @freeze_time("2015-09-24 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        w = NzbClub(getIndexerSettingByName("nzbclub"))
        with open("mock/nzbclub--q-testtitle.xml", encoding="latin-1") as f:
            entries = w.process_query_result(f.read(), SearchRequest()).entries
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
        n = NzbClub(getIndexerSettingByName("nzbclub"))
        link = n.get_nzb_link("guid", "title")
        self.assertEqual("https://www.nzbclub.com/nzb_get/guid/title.nzb", link)
    