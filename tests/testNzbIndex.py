import json
import unittest

from freezegun import freeze_time
from database import Provider
from exceptions import ProviderIllegalSearchException

from searchmodules.nzbclub import NzbClub
from searchmodules.nzbindex import NzbIndex
from tests.db_prepare import set_and_drop


class MyTestCase(unittest.TestCase):
    
    def setUp(self):    
        set_and_drop()    
        self.nzbindex = Provider(module="nzbindex", name="NZBIndex", query_url="http://127.0.0.1:5001/nzbindex", base_url="http://127.0.0.1:5001/nzbindex", settings={}, search_types=["general"], search_ids=[])
        self.nzbindex.save()
    
    @freeze_time("2015-09-20 14:00:00", tz_offset=-4)
    def testThatNzbIndexnlySupportsGeneral(self):
        w = NzbClub(self.nzbindex)
        try:
            w.get_moviesearch_urls(None, "akey", "avalue", [])
            self.fail("Expected an error")
        except ProviderIllegalSearchException:
            pass

        try:
            w.get_showsearch_urls()
            self.fail("Expected an error")
        except ProviderIllegalSearchException:
            pass

    def testGetGeneralUrls(self):
        pass

    # todo


    @freeze_time("2015-09-28 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        w = NzbIndex(self.nzbindex)
        with open("mock/nzbindex--q-avengers.xml") as f:
            entries = w.process_query_result(f.read())
            self.assertEqual('Avengers_Age_of_Ultron_2015_1080p_BluRay_x264-SPARKS 20_10_2015', entries[0].title)
            self.assertEqual("http://nzbindex.com/download/125731784/Avengers-Age-of-Ultron-2015-1080p-BluRay-x264-SPARKS-20-10-2015.nzb", entries[0].link)
            self.assertEqual(1024268, entries[0].size)
            self.assertEqual("http://nzbindex.com/release/125731784/Avengers-Age-of-Ultron-2015-1080p-BluRay-x264-SPARKS-20-10-2015.nzb", entries[0].guid)
            self.assertEqual(1443237605, entries[0].epoch)
            self.assertEqual("2015-09-26T05:20:05+02:00", entries[0].pubdate_utc)
            self.assertEqual(2, entries[0].age_days)
            
            self.assertEqual("Hulk.Smash.Avengers.Limited.Series.4.of.5.Jul.2012.SCAN.Comic.eBook-iNTENSiTY [COMPRESSED]", entries[1].title)
            
            self.assertEqual("avengers.assemble.s02e25.new.frontier.720p.hdtv.x264-w4f", entries[2].title)
            
