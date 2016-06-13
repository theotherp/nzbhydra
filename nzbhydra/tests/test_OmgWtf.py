from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library

from nzbhydra.categories import getCategoryByAnyInput
from nzbhydra.indexers import getIndexerSettingByName
from nzbhydra.nzb_search_result import NzbSearchResult

#standard_library.install_aliases()
from builtins import *
import unittest
from freezegun import freeze_time

from furl import furl
import pytest
from nzbhydra import config

from nzbhydra.database import Indexer
from nzbhydra.search import SearchRequest
from nzbhydra.searchmodules.omgwtf import OmgWtf
from nzbhydra.tests.db_prepare import set_and_drop


class MyTestCase(unittest.TestCase):
    
    @pytest.fixture
    def setUp(self):
        set_and_drop()
        self.omgwtf = OmgWtf(getIndexerSettingByName("omgwtf"))
        

    def testUrlGeneration(self):
        self.args = SearchRequest(query="aquery")
        urls = self.omgwtf.get_search_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://api.omgwtfnzbs.org/xml/?api=apikey&user=anuser&search=aquery", urls[0])

        self.args = SearchRequest(query="aquery", category=getCategoryByAnyInput("tvhd"))
        urls = self.omgwtf.get_search_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://api.omgwtfnzbs.org/xml/?api=apikey&user=anuser&search=aquery&catid=20", urls[0])

        self.args = SearchRequest(query="aquery", maxage=100)
        urls = self.omgwtf.get_search_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://api.omgwtfnzbs.org/xml/?api=apikey&user=anuser&search=aquery&retention=100", urls[0])

        self.args = SearchRequest(query="aquery", category=getCategoryByAnyInput("tvhd"), maxage=100)
        urls = self.omgwtf.get_search_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://api.omgwtfnzbs.org/xml/?api=apikey&user=anuser&search=aquery&retention=100&catid=20", urls[0])

        self.args = SearchRequest()
        urls = self.omgwtf.get_search_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://rss.omgwtfnzbs.org/rss-download.php?api=apikey&user=anuser", urls[0])
        
        self.args = SearchRequest(category=getCategoryByAnyInput("tvhd"))
        urls = self.omgwtf.get_search_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://rss.omgwtfnzbs.org/rss-download.php?api=apikey&user=anuser&catid=20", urls[0])
    
    def testGetShowSearchUrls(self):
        self.args = SearchRequest(query="aquery")
        urls = self.omgwtf.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://api.omgwtfnzbs.org/xml/?api=apikey&user=anuser&search=aquery&catid=19,20,21", urls[0])

        self.args = SearchRequest(query="aquery", category=getCategoryByAnyInput("tvhd"))
        urls = self.omgwtf.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://api.omgwtfnzbs.org/xml/?api=apikey&user=anuser&search=aquery&catid=20", urls[0])

        self.args = SearchRequest(query="aquery", season=1)
        urls = self.omgwtf.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://api.omgwtfnzbs.org/xml/?api=apikey&user=anuser&search=aquery+s01&catid=19,20,21", urls[0])

        self.args = SearchRequest(query="aquery", season=1, episode=2)
        urls = self.omgwtf.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://api.omgwtfnzbs.org/xml/?api=apikey&user=anuser&search=aquery+s01e02&catid=19,20,21", urls[0])

        self.args = SearchRequest()
        urls = self.omgwtf.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://rss.omgwtfnzbs.org/rss-download.php?api=apikey&user=anuser&catid=19,20,21", urls[0])

    def testGetMovieSearchUrls(self):
        self.args = SearchRequest(identifier_key="imdb", identifier_value="0169547")
        urls = self.omgwtf.get_moviesearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://api.omgwtfnzbs.org/xml/?api=apikey&user=anuser&search=tt0169547&catid=15,16,17,18", urls[0])

        self.args = SearchRequest(identifier_key="tmdb", identifier_value="14", category=getCategoryByAnyInput("movieshd"))
        urls = self.omgwtf.get_moviesearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://api.omgwtfnzbs.org/xml/?api=apikey&user=anuser&search=tt0169547&catid=16", urls[0])

    @freeze_time("2015-12-30 14:00:00", tz_offset=-4)
    def testProcessSearchResults(self):
        with open("mock/omgwtf_search.xml", encoding="latin-1") as f:
            body = f.read()
            result = self.omgwtf.process_query_result(body, SearchRequest())
            entries = result.entries
            self.assertEqual(3, len(entries))
            self.assertEqual('atvshow.S02E09.720p.HDTV.DD5.1.x264-NTb', entries[0].title)
            self.assertEqual("https://api.omgwtfnzbs.org/nzb/?id=x30FI&user=auser&api=apikey", entries[0].link)
            self.assertEqual(2396942366, entries[0].size)
            self.assertEqual("x30FI", entries[0].indexerguid)
            self.assertEqual(1449855118, entries[0].epoch)
            self.assertEqual("2015-12-11T17:31:58+00:00", entries[0].pubdate_utc)
            self.assertEqual(18, entries[0].age_days)
            self.assertTrue(entries[0].age_precise)
            self.assertEqual(NzbSearchResult.HAS_NFO_NO, entries[0].has_nfo)
            self.assertEqual("alt.binaries.hdtv", entries[0].group)
            self.assertEqual(getCategoryByAnyInput("tvhd").category.name, entries[0].category.name)
            self.assertEqual("https://omgwtfnzbs.org/details?id=x30FI", entries[0].details_link)
            self.assertFalse(result.has_more)
            self.assertTrue(result.total_known)
            self.assertEqual(3, result.total)

            self.assertEqual(NzbSearchResult.HAS_NFO_YES, entries[2].has_nfo)
        

                
    def testGetNzbLink(self):
        link = self.omgwtf.get_nzb_link("guid", "title")
        self.assertEqual("https://api.omgwtfnzbs.org/nzb?api=apikey&id=guid&user=anuser", link)
        

