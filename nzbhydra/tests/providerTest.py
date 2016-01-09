from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
#standard_library.install_aliases()
from builtins import *
import unittest


class IndexerTestcase(unittest.TestCase):
    args = {
        "apikey": "",
        "t": "",
        "query": "",
        "category": "",
        "title": "",
        "rid": "",
        "imdbid": "",
        "tvdbid": "",
        "season": "",
        "episode": "",
        "minsize": 0,
        "maxsize": 0,
        "minage": 0,
        "maxage": 0,
        "input": ""
    }
