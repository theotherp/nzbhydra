from freezegun import freeze_time

from furl import furl

from nzbhydra.database import Provider
from nzbhydra.searchmodules.nzbindex import NzbIndex
from nzbhydra.tests.db_prepare import set_and_drop
from nzbhydra.tests.providerTest import ProviderTestcase


class MyTestCase(ProviderTestcase):
    def setUp(self):
        set_and_drop()
        self.nzbindex = Provider(module="nzbindex", name="NZBIndex", query_url="http://127.0.0.1:5001/nzbindex", base_url="http://127.0.0.1:5001/nzbindex", settings={}, search_types=["general"], search_ids=[])
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

    @freeze_time("2015-09-28 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        w = NzbIndex(self.nzbindex)
        with open("mock/nzbindex--q-avengers.xml") as f:
            entries = w.process_query_result(f.read(), "aquery")["entries"]
            self.assertEqual('Avengers_Age_of_Ultron_2015_1080p_BluRay_x264-SPARKS 20_10_2015', entries[0].title)
            self.assertEqual("http://nzbindex.com/download/125731784/Avengers-Age-of-Ultron-2015-1080p-BluRay-x264-SPARKS-20-10-2015.nzb", entries[0].link)
            self.assertEqual(1024268, entries[0].size)
            self.assertEqual("http://nzbindex.com/release/125731784/Avengers-Age-of-Ultron-2015-1080p-BluRay-x264-SPARKS-20-10-2015.nzb", entries[0].guid)
            self.assertEqual(1443237605, entries[0].epoch)
            self.assertEqual("2015-09-26T05:20:05+02:00", entries[0].pubdate_utc)
            self.assertEqual(2, entries[0].age_days)

            self.assertEqual("Hulk.Smash.Avengers.Limited.Series.4.of.5.Jul.2012.SCAN.Comic.eBook-iNTENSiTY [COMPRESSED]", entries[1].title)

            self.assertEqual("avengers.assemble.s02e25.new.frontier.720p.hdtv.x264-w4f", entries[2].title)
