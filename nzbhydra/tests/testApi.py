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
        
        config.resultProcessingSettings.duplicateAgeThreshold.set(120)
        age_threshold = config.resultProcessingSettings.duplicateAgeThreshold.get()
        config.resultProcessingSettings.duplicateSizeThresholdInPercent.set(1)

        # same title, age and size
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, provider="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=1, provider="b")
        assert api.test_for_duplicate(result1, result2)
        
        # same title with differing case, age and size
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, provider="a")
        result2 = NzbSearchResult(title="A TITLE", epoch=0, size=1, provider="b")
        assert api.test_for_duplicate(result1, result2)

        # different title, same age and size
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, provider="a")
        result2 = NzbSearchResult(title="Another title", epoch=0, size=1, provider="b")
        assert not api.test_for_duplicate(result1, result2)

        # same title and age, size different in threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=100, provider="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=101, provider="b")
        assert api.test_for_duplicate(result1, result2)

        # same title and size, age in threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, provider="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 - 1, size=1, provider="b")
        assert api.test_for_duplicate(result1, result2)

        # same title and age, size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, provider="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=2, provider="b")
        assert not api.test_for_duplicate(result1, result2)

        # same title and size, age outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, provider="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 + 1, size=0, provider="b")
        assert not api.test_for_duplicate(result1, result2)

        # same title, age and size inside of threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=101, provider="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 - 1, size=101, provider="b")
        assert api.test_for_duplicate(result1, result2)

        # same title, age and size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, provider="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 + 1, size=200, provider="b")
        assert not api.test_for_duplicate(result1, result2)


    def testFindDuplicates(self):
        config.resultProcessingSettings.duplicateAgeThreshold.set(120)
        config.resultProcessingSettings.duplicateSizeThresholdInPercent.set(1)
    
        
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
        
        
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, provider="1")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, provider="2")
        result3 = NzbSearchResult(title="Title1", epoch=0, size=1, provider="3") # same as the one before
        result4 = NzbSearchResult(title="Title1", epoch=100000000, size=1, provider="4")
        results = api.find_duplicates([result1, result2, result3, result4])
        self.assertEqual(2, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(3, len(results[1]))
        
        
