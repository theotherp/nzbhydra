from pprint import pprint
import unittest
import flask
from furl import furl
from mock import MagicMock
from nzbhydra import config
from nzbhydra import api

from nzbhydra.nzb_search_result import NzbSearchResult


class MyTestCase(unittest.TestCase):
    
    def testTestForDuplicate(self):
        

        config.cfg.section("ResultProcessing")["duplicateSizeThresholdInPercent"] = 1
        age_threshold = config.cfg.section("ResultProcessing").get("duplicateAgeThreshold", 120) #three hours in ms

        # same title, age and size
        result1 = NzbSearchResult(title="A title", epoch=0, size=1)
        result2 = NzbSearchResult(title="A title", epoch=0, size=1)
        assert api.test_for_duplicate(result1, result2)
        
        # same title with differing case, age and size
        result1 = NzbSearchResult(title="A title", epoch=0, size=1)
        result2 = NzbSearchResult(title="A TITLE", epoch=0, size=1)
        assert api.test_for_duplicate(result1, result2)

        # different title, same age and size
        result1 = NzbSearchResult(title="A title", epoch=0, size=1)
        result2 = NzbSearchResult(title="Another title", epoch=0, size=1)
        assert not api.test_for_duplicate(result1, result2)

        # same title and age, size different in threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=100)
        result2 = NzbSearchResult(title="A title", epoch=0, size=101)
        assert api.test_for_duplicate(result1, result2)

        # same title and size, age in threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=1)
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 - 1, size=1)
        assert api.test_for_duplicate(result1, result2)

        # same title and age, size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1)
        result2 = NzbSearchResult(title="A title", epoch=0, size=2)
        assert not api.test_for_duplicate(result1, result2)

        # same title and size, age outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1)
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 + 1, size=0)
        assert not api.test_for_duplicate(result1, result2)

        # same title, age and size inside of threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=101)
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 - 1, size=101)
        assert api.test_for_duplicate(result1, result2)

        # same title, age and size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1)
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 + 1, size=200)
        assert not api.test_for_duplicate(result1, result2)


    def testFindDuplicates(self):
        config.cfg.section("ResultProcessing")["duplicateSizeThresholdInPercent"] = 1
        age_threshold = 120
        config.cfg["ResultProcessing.duplicateAgeThreshold"] = age_threshold
    
        
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, provider="1")
        result2 = NzbSearchResult(title="Title2", epoch=0, size=1, provider="2")
        result3 = NzbSearchResult(title="Title2", epoch=0, size=1, provider="3") # same as the one before
        result4 = NzbSearchResult(title="Title3", epoch=0, size=1, provider="4")
        result5 = NzbSearchResult(title="TITLE1", epoch=0, size=1, provider="5") # same as the first but with different case
        result6 = NzbSearchResult(title="Title4", epoch=0, size=1, provider="6")
        results = api.find_duplicates([result1, result2, result3, result4, result5, result6])
        self.assertEqual(4, len(results))
        self.assertEqual(2, len(results[0]))
        self.assertEqual(2, len(results[1]))
        self.assertEqual(1, len(results[2]))
        self.assertEqual(1, len(results[3]))
        
    def testTransformLinks(self):
        mock = MagicMock()
        mock.return_value = "http://127.0.0.1:5050"
        api.get_root_url = mock
        
        config.cfg["downloader.add_type"] = "direct"
        result = NzbSearchResult(provider="provider", guid="guid", link="oldlink")
        results = [result]
        results = api.transform_results(results)
        self.assertEqual("oldlink", results[0].link)
        
        config.cfg["downloader.add_type"] = "nzb"
        result = NzbSearchResult(provider="provider", guid="guid", link="oldlink")
        results = [result]
        results = api.transform_results(results)        
        assert "provider=provider" in results[0].link
        assert "t=getnzb" in  results[0].link
        assert "guid=guid" in  results[0].link
        
        
    

        
