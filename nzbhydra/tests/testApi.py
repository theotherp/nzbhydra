import unittest
import arrow

from nzbhydra import config
from nzbhydra import api
from nzbhydra.nzb_search_result import NzbSearchResult


class MyTestCase(unittest.TestCase):
    def testTestForDuplicate(self):
        config.searchingSettings.duplicateAgeThreshold.set(120)
        age_threshold = config.searchingSettings.duplicateAgeThreshold.get()
        config.searchingSettings.duplicateSizeThresholdInPercent.set(1)

        # same title, age and size
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="b")
        assert api.test_for_duplicate_age(result1, result2)
        assert api.test_for_duplicate_size(result1, result2)

        # size in threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=100, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=101, indexer="b")
        assert api.test_for_duplicate_size(result1, result2)

        # age in threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 - 1, size=1, indexer="b")
        assert api.test_for_duplicate_age(result1, result2)

        # size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=0, size=2, indexer="b")
        assert not api.test_for_duplicate_size(result1, result2)

        # age outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 * 1000 + 1, size=0, indexer="b")
        assert not api.test_for_duplicate_age(result1, result2)

        # age and size inside of threshold
        result1 = NzbSearchResult(title="A title", epoch=0, size=101, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 - 1, size=101, indexer="b")
        assert api.test_for_duplicate_size(result1, result2)
        assert api.test_for_duplicate_age(result1, result2)

        # age and size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", epoch=0, size=1, indexer="a")
        result2 = NzbSearchResult(title="A title", epoch=age_threshold * 120 * 1000 + 1, size=200, indexer="b")
        assert not api.test_for_duplicate_size(result1, result2)
        assert not api.test_for_duplicate_age(result1, result2)

    def testFindDuplicates(self):
        config.searchingSettings.duplicateAgeThreshold.set(1)
        config.searchingSettings.duplicateSizeThresholdInPercent.set(0.1)

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="2", guid="2")
        result3 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="3", guid="3")
        result4 = NzbSearchResult(title="Title3", epoch=0, size=1, indexer="4", guid="4")
        result5 = NzbSearchResult(title="TITLE1", epoch=0, size=1, indexer="5", guid="5")
        result6 = NzbSearchResult(title="Title4", epoch=0, size=1, indexer="6", guid="6")
        results = api.find_duplicates([result1, result2, result3, result4, result5, result6])
        self.assertEqual(4, len(results))
        self.assertEqual(2, len(results[0]))
        self.assertEqual(2, len(results[1]))
        self.assertEqual(1, len(results[2]))
        self.assertEqual(1, len(results[3]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", guid="2")
        result3 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="3", guid="3")
        result4 = NzbSearchResult(title="Title1", epoch=100000000, size=1, indexer="4", guid="4")
        results = api.find_duplicates([result1, result2, result3, result4])
        self.assertEqual(2, len(results))
        self.assertEqual(3, len(results[0]))
        self.assertEqual(1, len(results[1]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1a", guid="1", pubdate_utc=arrow.get(0).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result2 = NzbSearchResult(title="Title1", epoch=10000000, size=1, indexer="2a", guid="2", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result3 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1b", guid="3", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result4 = NzbSearchResult(title="Title1", epoch=10000000, size=1, indexer="2b", guid="4", pubdate_utc=arrow.get(10000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        result5 = NzbSearchResult(title="Title1", epoch=1000000000, size=1, indexer="3", guid="5", pubdate_utc=arrow.get(1000000000).format('YYYY-MM-DD HH:mm:ss ZZ'))
        results = api.find_duplicates([result1, result2, result3, result4, result5])
        results = sorted(results, key=lambda x: len(x), reverse=True)
        self.assertEqual(3, len(results))
        self.assertEqual(2, len(results[0]))
        self.assertEqual(2, len(results[1]))
        self.assertEqual(1, len(results[2]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title1", epoch=100000000, size=1, indexer="2", guid="2")
        results = api.find_duplicates([result1, result2])
        results = sorted(results, key=lambda x: len(x), reverse=True)
        self.assertEqual(2, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title1", epoch=1, size=100000000, indexer="2", guid="2")
        results = api.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title1", epoch=1, size=1, indexer="2", guid="2")
        results = api.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))
        self.assertEqual(2, len(results[0]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title1", epoch=30 * 1000 * 60, size=1, indexer="2", guid="2")
        result3 = NzbSearchResult(title="Title1", epoch=60 * 1000 * 60, size=1, indexer="2", guid="3")
        results = api.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title2", epoch=1000000, size=1, indexer="2", guid="2")
        result3 = NzbSearchResult(title="Title3", epoch=5000000, size=1, indexer="2", guid="3")
        results = api.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))

        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1")
        result2 = NzbSearchResult(title="Title2", epoch=0, size=1, indexer="2", guid="2")
        result3 = NzbSearchResult(title="Title3", epoch=0, size=1, indexer="2", guid="3")
        results = api.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        self.assertEqual(1, len(results[0]))
        self.assertEqual(1, len(results[1]))
        self.assertEqual(1, len(results[2]))


        # Same poster and group posted inside of 24 hours
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=1000 * 60 * 23, size=1, indexer="2", guid="2", poster="postera", group="groupa")
        results = api.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))
        self.assertEqual(2, len(results[0]))

        # Same poster and group posted outside of 24 hours
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=1000 * 60 * 25, size=1, indexer="2", guid="2", poster="postera", group="groupa")
        results = api.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))

        # Same size and age and group but different posters (very unlikely) 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", guid="2", poster="posterb", group="groupa")
        results = api.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))

        # Same size and age and poster but different groups (very unlikely) 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="2", guid="2", poster="postera", group="groupb")
        results = api.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))

        # Same size and age and poster but unknown group inside of 12 hours 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera")
        result2 = NzbSearchResult(title="Title1", epoch=1000 * 60 * 11, size=1, indexer="2", guid="2", poster="postera", group="groupb")
        results = api.find_duplicates([result1, result2])
        self.assertEqual(1, len(results))

        # Same size and age and poster but unknown group outside of 12 hours 
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera")
        result2 = NzbSearchResult(title="Title1", epoch=1000 * 60 * 13, size=1, indexer="2", guid="2", poster="postera", group="groupb")
        results = api.find_duplicates([result1, result2])
        self.assertEqual(2, len(results))
        
    def testFindDuplicatesNew(self):
        result1 = NzbSearchResult(title="Title1", epoch=0, size=1, indexer="1", guid="1", poster="postera", group="groupa")
        result2 = NzbSearchResult(title="Title1", epoch=0, size=2, indexer="2", guid="2", poster="postera", group="groupb")
        result3 = NzbSearchResult(title="Title1", epoch=0, size=3, indexer="3", guid="3", poster="postera", group="groupb")
        results = api.find_duplicates([result1, result2, result3])
        self.assertEqual(3, len(results))
        