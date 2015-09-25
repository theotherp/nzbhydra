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
        self.nzbclub = Provider(module="nzbclub", name="nzbclub", query_url="https://member.nzbclub.com/nzbfeeds.aspx", base_url="http://127.0.0.1:5001/nzbclub", search_types=json.dumps(["general", "tv", "movie"]), generate_queries=True)
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


    @freeze_time("2015-09-21 14:00:00", tz_offset=-4)
    def testProcess_results(self):
        w = NzbClub(self.nzbclub)
        with open("tests/mock/nzbclub--q-avengers.xml") as f:
            entries = w.process_query_result(f.read())
            self.assertEqual('AMS The.Avengers.2012.720p.BluRay.DTS.x264-LEGi0N "The.Avengers.2012.720p.BluRay.DTS.x264-LEGi0N" ', entries[0].title)
            self.assertEqual("http://member.nzbclub.com/nzb_get/58210213/AMS The Avengers 2012 720p BluRay DTS x264 LEGi0N.nzb", entries[0].link)
            self.assertEqual(5966947065, entries[0].size)
            self.assertEqual("http://member.nzbclub.com/nzb_view58210213", entries[0].guid)
            self.assertEqual(1442183217, entries[0].epoch)
            self.assertEqual("2015-09-13T17:26:57-05:00", entries[0].pubdate_utc)
            self.assertEqual(7, entries[0].age_days)
