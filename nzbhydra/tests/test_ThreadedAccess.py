from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import threading
from time import sleep

import requests_mock
from bunch import Bunch

# standard_library.install_aliases()
from builtins import *
import sys
import logging

from nzbhydra import web
from nzbhydra.searchmodules import newznab
from urltools import compare
from nzbhydra.tests.db_prepare import set_and_drop

from nzbhydra.tests.test_IntegrationTestsSearch import AbstractSearchTestCase

logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")

#This test is not expected to run through, it's just for reproducing the databse is locked error.

class ThreadedAccessTests(AbstractSearchTestCase):
    def testReproduceDatabaseIsLocked(self):
        set_and_drop()
        web.app.template_folder = "../templates"
        threads = []
        for i in range(15):
            t = threading.Thread(target=self.startTest)
            threads.append(t)
            t.start()
        sleep(10)

    def startTest(self):
        with web.app.test_request_context('/'):
            with requests_mock.mock() as requestsMock:
                expectedItems = self.prepareSearchMocks(requestsMock, 1, 1)
                response = self.app.get("/api?t=search&q=query&cat=5030")
                entries, _, _ = newznab.NewzNab(Bunch.fromDict({"name": "forTest", "score": 0, "host": "host"})).parseXml(response.data)
                self.assertSearchResults(entries, expectedItems)
                calledUrls = sorted([x.url for x in requestsMock.request_history])
                self.assertTrue(compare('http://www.newznab1.com/api?apikey=apikeyindexer.com&t=search&extended=1&offset=0&limit=100&q=query&cat=5030', calledUrls[0]))
                self.assertEqual("http://localhost:5075/getnzb?searchresultid=1", entries[0].link)