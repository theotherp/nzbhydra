from os.path import dirname, join, abspath
from sys import path

import unittest
from nzbhydra.infos import tvdbid_to_rid, rid_to_tvdbid
from nzbhydra.database import init_db



class MyTestCase(unittest.TestCase):
    def testTvdbIdToRid(self):
        init_db("tests.db")
        rid = tvdbid_to_rid("81189")
        assert rid == "18164"
        print(rid)

    def testRidToTvDb(self):
        init_db("tests.db")
        rid = rid_to_tvdbid("18164")
        assert rid == "81189"
        print(rid)
        