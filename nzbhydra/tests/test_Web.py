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

from mock import Mock

from nzbhydra import config
from nzbhydra import web
from nzbhydra.tests.UrlTestCase import UrlTestCase


class TestWeb(UrlTestCase):
    @pytest.fixture
    def setUp(self):
        if os.path.exists("testsettings.cfg"):
            os.remove("testsettings.cfg")
        shutil.copy("testsettings.cfg.orig", "testsettings.cfg")
        config.load("testsettings.cfg")
        config.mainSettings.apikey.set("apikey")

    def testAuth(self):
        app = flask.Flask(__name__)

        with app.test_request_context('/'):
            # No user logged in
            web.isLoggedIn = Mock(return_value=False)
            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(False)
            config.mainSettings.enableAdminAuthForStats.set(False)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(False)
            config.mainSettings.enableAdminAuthForStats.set(True)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.mainSettings.enableAuth.set(True)
            config.mainSettings.enableAdminAuth.set(False)
            config.mainSettings.enableAdminAuthForStats.set(False)
            assert not web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")

            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(True)
            config.mainSettings.enableAdminAuthForStats.set(False)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert not web.isAllowed("admin")

            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(True)
            config.mainSettings.enableAdminAuthForStats.set(True)
            assert web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")
            
            
            #Normal user logged in
            web.isAdminLoggedIn = Mock(return_value=False)
            web.isLoggedIn = Mock(return_value=True)
            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuthForStats.set(False)
            config.mainSettings.enableAdminAuth.set(False)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(False)
            config.mainSettings.enableAdminAuthForStats.set(True)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")
            
            config.mainSettings.enableAuth.set(True)
            config.mainSettings.enableAdminAuth.set(False)
            config.mainSettings.enableAdminAuthForStats.set(False)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.mainSettings.enableAuth.set(True)
            config.mainSettings.enableAdminAuth.set(False)
            config.mainSettings.enableAdminAuthForStats.set(True)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(True)
            config.mainSettings.enableAdminAuthForStats.set(False)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert not web.isAllowed("admin")

            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(True)
            config.mainSettings.enableAdminAuthForStats.set(True)
            assert web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")


            #Admin logged in
            web.isAdminLoggedIn = Mock(return_value=True)
            web.isLoggedIn = Mock(return_value=False)
            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(False)
            config.mainSettings.enableAdminAuthForStats.set(False)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(True)
            config.mainSettings.enableAdminAuthForStats.set(False)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(True)
            config.mainSettings.enableAdminAuthForStats.set(False)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.mainSettings.enableAuth.set(False)
            config.mainSettings.enableAdminAuth.set(True)
            config.mainSettings.enableAdminAuthForStats.set(True)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.mainSettings.enableAuth.set(True)
            config.mainSettings.enableAdminAuth.set(True)
            config.mainSettings.enableAdminAuthForStats.set(True)
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")


            