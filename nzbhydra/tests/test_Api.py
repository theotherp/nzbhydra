from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil

import flask
import pytest
# standard_library.install_aliases()
import unittest

from nzbhydra import config
from nzbhydra import api
from nzbhydra.tests.UrlTestCase import UrlTestCase


class TestApi(UrlTestCase):
    @pytest.fixture
    def setUp(self):
        if os.path.exists("testsettings.cfg"):
            os.remove("testsettings.cfg")
        shutil.copy("testsettings.cfg.orig", "testsettings.cfg")
        config.load("testsettings.cfg")
        config.mainSettings.apikey.set("apikey")

    def testGetNzbLinkAndGuidWithExternalUrlStuff(self):
        app = flask.Flask(__name__)

        with app.test_request_context('/'):
            #With external URL
            config.mainSettings.externalUrl.set("https://127.0.0.1/nzbhydra")
            
            config.mainSettings.useLocalUrlForApiAccess.set(False)
            link, _ = api.get_nzb_link_and_guid("indexer", "guid", 1, "title", True)
            self.assertUrlEqual(link, "https://127.0.0.1/nzbhydra/api?apikey=apikey&id=%28guid%3Aguid%2Cindexer%3Aindexer%2Csearchid%3A1%2Ctitle%3Atitle%29&t=get")
            link, _ = api.get_nzb_link_and_guid("indexer", "guid", 1, "title", False)
            self.assertUrlEqual(link, "https://127.0.0.1/nzbhydra/api?apikey=apikey&id=%28guid%3Aguid%2Cindexer%3Aindexer%2Csearchid%3A1%2Ctitle%3Atitle%29&t=get")
    
            config.mainSettings.useLocalUrlForApiAccess.set(True)
            link, _ = api.get_nzb_link_and_guid("indexer", "guid", 1, "title", True)
            self.assertUrlEqual(link, "http://localhost/api?apikey=apikey&id=%28guid%3Aguid%2Cindexer%3Aindexer%2Csearchid%3A1%2Ctitle%3Atitle%29&t=get")
            link, _ = api.get_nzb_link_and_guid("indexer", "guid", 1, "title", False)
            self.assertUrlEqual(link, "https://127.0.0.1/nzbhydra/api?apikey=apikey&id=%28guid%3Aguid%2Cindexer%3Aindexer%2Csearchid%3A1%2Ctitle%3Atitle%29&t=get")

            #Without external URL
            config.mainSettings.externalUrl.set(None)

            config.mainSettings.useLocalUrlForApiAccess.set(False)
            link, _ = api.get_nzb_link_and_guid("indexer", "guid", 1, "title", True)
            self.assertUrlEqual(link, "http://localhost/api?apikey=apikey&id=%28guid%3Aguid%2Cindexer%3Aindexer%2Csearchid%3A1%2Ctitle%3Atitle%29&t=get")
            link, _ = api.get_nzb_link_and_guid("indexer", "guid", 1, "title", False)
            self.assertUrlEqual(link, "http://localhost/api?apikey=apikey&id=%28guid%3Aguid%2Cindexer%3Aindexer%2Csearchid%3A1%2Ctitle%3Atitle%29&t=get")

            config.mainSettings.useLocalUrlForApiAccess.set(True)
            link, _ = api.get_nzb_link_and_guid("indexer", "guid", 1, "title", True)
            self.assertUrlEqual(link, "http://localhost/api?apikey=apikey&id=%28guid%3Aguid%2Cindexer%3Aindexer%2Csearchid%3A1%2Ctitle%3Atitle%29&t=get")
            link, _ = api.get_nzb_link_and_guid("indexer", "guid", 1, "title", False)
            self.assertUrlEqual(link, "http://localhost/api?apikey=apikey&id=%28guid%3Aguid%2Cindexer%3Aindexer%2Csearchid%3A1%2Ctitle%3Atitle%29&t=get")
        
        