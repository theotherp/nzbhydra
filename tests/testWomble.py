import config
import unittest
from freezegun import freeze_time

from searchmodules.newznab import NewzNab
from searchmodules.womble import Womble


class MyTestCase(unittest.TestCase):
    
    
    config.cfg["search_providers.1.search_module"] = "womble"
    config.cfg["search_providers.1.query_url"] = "http://127.0.0.1:5051/womble"
    
    
    @freeze_time("2015-09-20 14:00:00", tz_offset=-4)
    def testThatWombleOnlySupportsTvRss(self):
        w = Womble(config.cfg.section("search_providers.1"))
        try:
            w.get_moviesearch_urls()
            self.fail("Expected an error")
        except NotImplementedError:
            pass
        
        try:
            w.get_search_urls("aquery")
            self.fail("Expected an error")
        except NotImplementedError:
            pass
        
        
        w.get_showsearch_urls()
        
    def testGetTvRssUrls(self):
        w = Womble(config.cfg.section("search_providers.1"))
        urls = w.get_showsearch_urls()
        self.assertEqual(1, len(urls))
        self.assertEqual("http://127.0.0.1:5051/womble?fr=false", urls[0])
        
        urls = w.get_showsearch_urls(categories=[5000])
        self.assertEqual(1, len(urls))
        self.assertEqual("http://127.0.0.1:5051/womble?fr=false", urls[0])
        
        urls = w.get_showsearch_urls(categories=[5030])
        self.assertEqual(1, len(urls))
        self.assertEqual("http://127.0.0.1:5051/womble?fr=false&sec=tv-dvd", urls[0])
        
        urls = w.get_showsearch_urls(categories=[5040])
        self.assertEqual(1, len(urls))
        self.assertEqual("http://127.0.0.1:5051/womble?fr=false&sec=tv-x264", urls[0])
        
        urls = w.get_showsearch_urls(categories=[5030, 5040])
        self.assertEqual(2, len(urls))
        self.assertEqual("http://127.0.0.1:5051/womble?fr=false&sec=tv-dvd", urls[0])
        self.assertEqual("http://127.0.0.1:5051/womble?fr=false&sec=tv-x264", urls[1])
        
    
    @freeze_time("2015-09-21 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        w = Womble(config.cfg.section("search_providers.1"))
        with open("tests/mock/womble--sec-tv-dvd.xml") as f:
            entries = w.process_query_result(f.read())
            self.assertEqual("Blackish.S01E24.DVDRip.X264-OSiTV", entries[0].title)
            self.assertEqual("http://www.newshost.co.za/nzb/79d/Blackish.S01E24.DVDRip.X264-OSiTV.nzb", entries[0].link)
            self.assertEqual(336592896, entries[0].size)
            self.assertEqual(5030, entries[0].category)
            self.assertEqual("http://www.newshost.co.za/nzb/79d/Blackish.S01E24.DVDRip.X264-OSiTV.nzb", entries[0].guid)
            self.assertEqual(1442790103, entries[0].epoch)
            self.assertEqual("2015-09-20T23:01:43+00:00", entries[0].pubdate_utc)
            self.assertEqual(0, entries[0].age_days)
            
        
        
        
        
        
    
    