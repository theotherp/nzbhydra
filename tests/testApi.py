import unittest

from nzb_search_result import NzbSearchResult


class MyTestCase(unittest.TestCase):
    def testTestForDuplicate(self):
        from config import cfg
        from api import test_for_duplicate

        cfg.section("ResultProcessing")["duplicateSizeThresholdInPercent"] = 1
        age_threshold = cfg.section("ResultProcessing").get("duplicateAgeThreshold", 36000)

        # same title, age and size
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="A title", age=0, size=1)
        assert test_for_duplicate(result1, result2)

        # different title, same age and size
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="Another title", age=0, size=1)
        assert not test_for_duplicate(result1, result2)

        # same title and age, size different in threshold
        result1 = NzbSearchResult(title="A title", age=0, size=100)
        result2 = NzbSearchResult(title="A title", age=0, size=101)
        assert test_for_duplicate(result1, result2)

        # same title and size, age in threshold
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="A title", age=age_threshold - 1, size=1)
        assert test_for_duplicate(result1, result2)

        # same title and age, size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="A title", age=0, size=2)
        assert not test_for_duplicate(result1, result2)

        # same title and size, age outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="A title", age=age_threshold + 1, size=0)
        assert not test_for_duplicate(result1, result2)

        # same title, age and size inside of threshold
        result1 = NzbSearchResult(title="A title", age=0, size=101)
        result2 = NzbSearchResult(title="A title", age=age_threshold - 1, size=101)
        assert test_for_duplicate(result1, result2)

        # same title, age and size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="A title", age=age_threshold + 1, size=200)
        assert not test_for_duplicate(result1, result2)


    def testFindDuplicates(self):
        from config import cfg
        from api import find_duplicates
    
        cfg.section("ResultProcessing")["duplicateSizeThresholdInPercent"] = 1
        age_threshold = cfg.section("ResultProcessing").get("duplicateAgeThreshold", 36000)
    
        # same title, age and size
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="A title", age=0, size=1)
        results, duplicates = find_duplicates([result1, result2])
        assert len(results) == 1
        assert len(duplicates) == 1
        self.assertEqual(results[0], result1)
        self.assertEqual(duplicates[0], result2)
    
        # different title, same age and size
        result1 = NzbSearchResult(title="A title", age=0, size=0)
        result2 = NzbSearchResult(title="Another title", age=0, size=0)
        results, duplicates = find_duplicates([result1, result2])
        assert len(results) == 2
        assert len(duplicates) == 0
        self.assertEqual(results[0], result1)
        self.assertEqual(results[1], result2)
    
        # same title and age, size in threshold
        result1 = NzbSearchResult(title="A title", age=0, size=101)
        result2 = NzbSearchResult(title="A title", age=0, size=100)
        results, duplicates = find_duplicates([result1, result2])
        assert len(results) == 1
        assert len(duplicates) == 1
        self.assertEqual(results[0], result1)
        self.assertEqual(duplicates[0], result2)
    
        # same title and size, age in threshold
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="A title", age=age_threshold - 1, size=1)
        results, duplicates = find_duplicates([result1, result2])
        assert len(results) == 1
        assert len(duplicates) == 1
        self.assertEqual(results[0], result1)
        self.assertEqual(duplicates[0], result2)
    
        # same title and age, size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="A title", age=0, size=2)
        results, duplicates = find_duplicates([result1, result2])
        assert len(results) == 2
        assert len(duplicates) == 0
        self.assertEqual(results[0], result1)
        self.assertEqual(results[1], result2)
    
        # same title and size, age outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="A title", age=age_threshold + 1, size=1)
        results, duplicates = find_duplicates([result1, result2])
        assert len(results) == 2
        assert len(duplicates) == 0
        self.assertEqual(results[0], result1)
        self.assertEqual(results[1], result2)
    
        # same title, age and size inside of threshold
        result1 = NzbSearchResult(title="A title", age=0, size=101)
        result2 = NzbSearchResult(title="A title", age=age_threshold - 1, size=100)
        results, duplicates = find_duplicates([result1, result2])
        assert len(results) == 1
        assert len(duplicates) == 1
        self.assertEqual(results[0], result1)
        self.assertEqual(duplicates[0], result2)
    
        # same title, age and size outside of threshold -> duplicate
        result1 = NzbSearchResult(title="A title", age=0, size=1)
        result2 = NzbSearchResult(title="A title", age=age_threshold + 1, size=2)
        results, duplicates = find_duplicates([result1, result2])
        assert len(results) == 2
        assert len(duplicates) == 0
        self.assertEqual(results[0], result1)
        self.assertEqual(results[1], result2)
