from freezegun import freeze_time

from furl import furl
import requests

from nzbhydra.database import Provider
from nzbhydra.searchmodules.nzbindex import NzbIndex
from nzbhydra.tests.db_prepare import set_and_drop
from nzbhydra.tests.providerTest import ProviderTestcase


class MyTestCase(ProviderTestcase):
    def setUp(self):
        set_and_drop()
        self.nzbindex = Provider(module="nzbindex", name="NZBIndex", settings={"query_url": "http://127.0.0.1:5001/nzbindex", "base_url": "http://127.0.0.1:5001/nzbindex", "search_ids": []})
        self.nzbindex.save()

    def testUrlGeneration(self):
        w = NzbIndex(self.nzbindex)
        self.args.update({"query": "a showtitle", "season": 1, "episode": 2})
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        print(urls[0])
        self.assertEqual('a showtitle s01e02 | 1x02', furl(urls[0]).args["q"])

        self.args.update({"query": "a showtitle", "season": 1, "episode": None})
        urls = w.get_showsearch_urls(args=self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual('a showtitle s01 | "season 1"', furl(urls[0]).args["q"])

    @freeze_time("2015-10-03 20:15:00", tz_offset=+2)
    def testProcess_results(self):
        w = NzbIndex(self.nzbindex)
        with open("mock/nzbindex--q-avengers.html") as f:
            entries = w.process_query_result(f.read(), "aquery")["entries"]
            self.assertEqual('114143855', entries[0].guid)
            self.assertEqual('Avengers.Assemble.S02E05.Beneath.the.Surface.WEB-DL.x264.AAC', entries[0].title)
            self.assertFalse(entries[0].has_nfo)
            self.assertEqual('bowibow@gmail.com (senior)', entries[0].poster)
            self.assertEqual("https://nzbindex.com/download/114143855/Avengers.Assemble.S02E05.Beneath.the.Surface.WEB-DL.x264.AAC-Avengers.Assemble.S02E05.Beneath.the.Surface.WEB-DL.x264.AAC.nzb", entries[0].link)
            self.assertEqual(169103851, entries[0].size)
            self.assertEqual("2014-11-04T10:39:00+01:00", entries[0].pubdate_utc) # would be perfect, that is the exact pubdate 
            self.assertEqual(1415093940, entries[0].epoch)
            self.assertEqual(333, entries[0].age_days)
    #         

    def testCookies(self):
        url = "https://nzbindex.com/search/?q=avengers&age=&max=250&minage=&sort=agedesc&minsize=1&maxsize=&dq=&poster=&nfo=&hidecross=1&complete=1&hidespam=0&hidespam=1&more=1"
        r = requests.get(url, cookies={"agreed": "true"})
        text = r.text
        assert "I agree" not in text

    def testGetNzbLink(self):
        n = NzbIndex(self.nzbindex)
        link = n.get_nzb_link("guid", "title")
        self.assertEqual("http://127.0.0.1:5001/nzbindex/download/guid/title.nzb", link)
