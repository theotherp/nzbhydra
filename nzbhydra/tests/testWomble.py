import unittest

from freezegun import freeze_time

from nzbhydra.database import Provider
from nzbhydra.searchmodules.womble import Womble
from nzbhydra.tests.db_prepare import set_and_drop


class MyTestCase(unittest.TestCase):
    def setUp(self):
        set_and_drop()
        womble = Provider(module="womble", name="Womble", settings={"query_url": "http://127.0.0.1:5001/womble", "base_url": "http://127.0.0.1:5001/womble"}, search_types=["general"], search_ids=[])
        womble.save()
        self.w = Womble(womble)

    def testGetTvRssUrls(self):
        urls = self.w.get_showsearch_urls()
        self.assertEqual(1, len(urls))
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false", urls[0])

        urls = self.w.get_showsearch_urls(categories=[5000])
        self.assertEqual(1, len(urls))
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false", urls[0])

        urls = self.w.get_showsearch_urls(categories=[5030])
        self.assertEqual(2, len(urls))
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false&sec=tv-dvd", urls[0])
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false&sec=tv-sd", urls[1])

        urls = self.w.get_showsearch_urls(categories=[5040])
        self.assertEqual(2, len(urls))
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false&sec=tv-x264", urls[0])
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false&sec=tv-hd", urls[1])

        urls = self.w.get_showsearch_urls(categories=[5030, 5040])
        self.assertEqual(4, len(urls))
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false&sec=tv-dvd", urls[0])
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false&sec=tv-sd", urls[1])
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false&sec=tv-x264", urls[2])
        self.assertEqual("http://127.0.0.1:5001/womble?fr=false&sec=tv-hd", urls[3])

    @freeze_time("2015-09-21 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        with open("mock/womble--sec-tv-dvd.xml") as f:
            entries = self.w.process_query_result(f.read(), "aquery")["entries"]
            self.assertEqual("Blackish.S01E24.DVDRip.X264-OSiTV", entries[0].title)
            self.assertEqual("http://www.newshost.co.za/nzb/79d/Blackish.S01E24.DVDRip.X264-OSiTV.nzb", entries[0].link)
            self.assertEqual(336592896, entries[0].size)
            self.assertEqual(5030, entries[0].category)
            self.assertEqual("http://www.newshost.co.za/nzb/79d/Blackish.S01E24.DVDRip.X264-OSiTV.nzb", entries[0].guid)
            self.assertEqual(1442790103, entries[0].epoch)
            self.assertEqual("2015-09-20T23:01:43+00:00", entries[0].pubdate_utc)
            self.assertEqual(0, entries[0].age_days)
