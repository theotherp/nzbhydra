import json
import unittest

from freezegun import freeze_time
from database import Provider
from exceptions import ProviderIllegalSearchException

from searchmodules.nzbclub import NzbClub
from tests.db_prepare import set_and_drop


class MyTestCase(unittest.TestCase):
    
    def setUp(self):    
        set_and_drop()    
        self.nzbclub = Provider(module="nzbclub", name="nzbclub", query_url="http://127.0.0.1:5001/nzbclub", base_url="http://127.0.0.1:5001/nzbclub", search_types=["general", "tv", "movie"], generate_queries=True)
        self.nzbclub.save()
    
    @freeze_time("2015-09-20 14:00:00", tz_offset=-4)
    def testThatNzbClubOnlySupportsGeneral(self):
        w = NzbClub(self.nzbclub)
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


    @freeze_time("2015-09-24 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        w = NzbClub(self.nzbclub)
        with open("mock/nzbclub--q-avengers.xml", encoding="latin-1") as f:
            entries = w.process_query_result(f.read())
            self.assertEqual('Avengers.Age.of.Ultron.2015.720p.BluRay.x264.YIFY', entries[0].title)
            self.assertEqual("http://www.nzbclub.com/nzb_get/60269450/Avengers Age of Ultron 720p BrRip x264 YIFY Avengers Age of Ultron 2015 720p BluRay x264 YIFY.nzb", entries[0].link)
            self.assertEqual(1075514926, entries[0].size)
            self.assertEqual("http://www.nzbclub.com/nzb_view60269450", entries[0].guid)
            self.assertEqual(1443019463, entries[0].epoch)
            self.assertEqual("2015-09-23T09:44:23-05:00", entries[0].pubdate_utc)
            self.assertEqual(0, entries[0].age_days)
