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
from nzbhydra import api, web
from nzbhydra.tests.UrlTestCase import UrlTestCase


class TestApi(UrlTestCase):
    @pytest.fixture
    def setUp(self):
        if os.path.exists("testsettings.cfg"):
            os.remove("testsettings.cfg")
        shutil.copy("testsettings.cfg.orig", "testsettings.cfg")
        config.load("testsettings.cfg")
        config.settings.main.apikey = "apikey"

    def testGetNzbLinkAndGuidWithExternalUrlStuff(self):
        app = flask.Flask(__name__)

        with app.test_request_context('/'):
            
            #With external URL
            config.settings.main.externalUrl = "https://192.168.1.1/nzbhydra"
            config.settings.main.useLocalUrlForApiAccess = False
            link = api.get_nzb_link_and_guid(1, external=True)
            self.assertApiUrl(link, shouldBeExternal=True, shouldbeLocal=False)
            link = api.get_nzb_link_and_guid(1, external=False)
            self.assertApiUrl(link, shouldBeExternal=False, shouldbeLocal=False)
    
            config.settings.main.useLocalUrlForApiAccess = True
            link = api.get_nzb_link_and_guid(1, external=True)
            self.assertApiUrl(link, shouldBeExternal=True, shouldbeLocal=True)
            link = api.get_nzb_link_and_guid(1, external=False)
            self.assertApiUrl(link, shouldBeExternal=False, shouldbeLocal=False)

            #Without external URL
            config.settings.main.externalUrl = None

            config.settings.main.useLocalUrlForApiAccess = False
            link = api.get_nzb_link_and_guid(1, external=True)
            self.assertApiUrl(link, shouldBeExternal=True, shouldbeLocal=True)
            link = api.get_nzb_link_and_guid(1, external=False)
            self.assertApiUrl(link, shouldBeExternal=False, shouldbeLocal=True)

            config.settings.main.useLocalUrlForApiAccess = True
            link = api.get_nzb_link_and_guid(1, external=True)
            self.assertApiUrl(link, shouldBeExternal=True, shouldbeLocal=True)
            link = api.get_nzb_link_and_guid(1, external=False)
            self.assertApiUrl(link, shouldBeExternal=False, shouldbeLocal=True)
            
    def assertApiUrl(self, url, shouldBeExternal, shouldbeLocal):
        self.assertTrue("getnzb" in url, "Doesn't use getnzb")
        if shouldBeExternal:
            self.assertTrue("apikey" in url, "Doesn't use API key")
            if shouldbeLocal:
                self.assertTrue("localhost" in url, "Uses API key but not local")
            else:
                self.assertTrue("192.168.1.1" in url, "Uses API key but not external IP")
        else:
            self.assertFalse("apikey" in url, "Exposes API key")
            if shouldbeLocal:
                self.assertTrue("localhost" in url, "Uses getnzb but not local")
            else:
                self.assertTrue("192.168.1.1" in url, "Uses getnzb but not external IP")
           
        
    
    def testGetRootUrl(self):
        with web.app.test_request_context('/nzbhydra/'):
            config.settings.main.urlBase = None
            config.settings.main.port = 5075
            self.assertEqual("http://localhost:5075/", api.get_root_url())

            config.settings.main.urlBase = "/nzbhydra"
            self.assertEqual("http://localhost:5075/nzbhydra/", api.get_root_url())