from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from nzbhydra.nzb_search_result import NzbSearchResult

# standard_library.install_aliases()
from builtins import *
import unittest
import sys
import logging


from nzbhydra import search, config
from nzbhydra.tests.db_prepare import set_and_drop


class DuplicateDetectionTests(unittest.TestCase):
    
    
    @pytest.fixture
    def setUp(self):
        set_and_drop()
        
   
    # def testFindDuplicates(self):
    #     config.settings.searching.duplicateAgeThreshold = 3600
    #     config.settings.searching.duplicateSizeThresholdInPercent = 0.1
    # 
    #     
    #     results = []
    #     for i in range(1, 1000):
    #         indexer = "%d" % (i % 5)
    #         results.append(NzbSearchResult(title="Title1", epoch=i, size=i, indexer=indexer, indexerguid=indexer))
    #     
    #     search.find_duplicates(results)
        