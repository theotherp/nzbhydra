import unittest

from freezegun import freeze_time

from nzbhydra.database import Provider
from nzbhydra.searchmodules.womble import Womble
from nzbhydra.tests.db_prepare import set_and_drop
from nzbhydra.tests.providerTest import ProviderTestcase


class MyTestCase(ProviderTestcase):
    def setUp(self):
        set_and_drop()
        womble = Provider(module="womble", name="Womble", settings={"query_url": "http://127.0.0.1:5001/womble", "base_url": "http://127.0.0.1:5001/womble"}, search_types=["general"], search_ids=[])
        womble.save()
        self.womble = Womble(womble)

    def testGetTvRssUrls(self):
        urls = self.womble.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false", urls[0])

        self.args.update({"category": "TV"})
        urls = self.womble.get_showsearch_urls(self.args)
        self.assertEqual(4, len(urls))

        self.args.update({"category": "TV HD"})
        urls = self.womble.get_showsearch_urls(self.args)
        self.assertEqual(2, len(urls))
        
        self.args.update({"category": "TV SD"})
        urls = self.womble.get_showsearch_urls(self.args)
        self.assertEqual(2, len(urls))

    @freeze_time("2015-09-21 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        with open("mock/womble--sec-tv-dvd.xml") as f:
            entries = self.womble.process_query_result(f.read(), "aquery")["entries"]
            self.assertEqual("Blackish.S01E24.DVDRip.X264-OSiTV", entries[0].title)
            self.assertEqual("http://www.newshost.co.za/nzb/79d/Blackish.S01E24.DVDRip.X264-OSiTV.nzb", entries[0].link)
            self.assertEqual(336592896, entries[0].size)
            self.assertEqual("TV SD", entries[0].category)
            self.assertEqual("79d/Blackish.S01E24.DVDRip.X264-OSiTV.nzb", entries[0].guid)
            self.assertEqual(1442790103, entries[0].epoch)
            self.assertEqual("2015-09-20T23:01:43+00:00", entries[0].pubdate_utc)
            self.assertEqual(0, entries[0].age_days)
            self.assertEqual("79d/Blackish.S01E24.DVDRip.X264-OSiTV.nzb", entries[0].guid)
            
    
    def testGetNzbLink(self):
        link = self.womble.get_nzb_link("abc/title.nzb", "title") #title is ignored
        self.assertEqual("http://127.0.0.1:5001/womble/nzb/abc/title.nzb", link)
