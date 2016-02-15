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
from nzbhydra.tests.db_prepare import set_and_drop


class TestWeb(UrlTestCase):
    @pytest.fixture
    def setUp(self):
        set_and_drop()

    def testAuth(self):
        app = flask.Flask(__name__)

        with app.test_request_context('/'):
            # No user logged in
            web.isLoggedIn = Mock(return_value=False)
            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = False
            config.settings.main.enableAdminAuthForStats = False
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = False
            config.settings.main.enableAdminAuthForStats = True
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.settings.main.enableAuth = True
            config.settings.main.enableAdminAuth = False
            config.settings.main.enableAdminAuthForStats = False
            assert not web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")

            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = True
            config.settings.main.enableAdminAuthForStats = False
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert not web.isAllowed("admin")

            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = True
            config.settings.main.enableAdminAuthForStats = True
            assert web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")
            
            
            #Normal user logged in
            web.isAdminLoggedIn = Mock(return_value=False)
            web.isLoggedIn = Mock(return_value=True)
            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuthForStats = False
            config.settings.main.enableAdminAuth = False
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = False
            config.settings.main.enableAdminAuthForStats = True
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")
            
            config.settings.main.enableAuth = True
            config.settings.main.enableAdminAuth = False
            config.settings.main.enableAdminAuthForStats = False
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.settings.main.enableAuth = True
            config.settings.main.enableAdminAuth = False
            config.settings.main.enableAdminAuthForStats = True
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = True
            config.settings.main.enableAdminAuthForStats = False
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert not web.isAllowed("admin")

            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = True
            config.settings.main.enableAdminAuthForStats = True
            assert web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")


            #Admin logged in
            web.isAdminLoggedIn = Mock(return_value=True)
            web.isLoggedIn = Mock(return_value=False)
            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = False
            config.settings.main.enableAdminAuthForStats = False
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = True
            config.settings.main.enableAdminAuthForStats = False
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = True
            config.settings.main.enableAdminAuthForStats = False
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.settings.main.enableAuth = False
            config.settings.main.enableAdminAuth = True
            config.settings.main.enableAdminAuthForStats = True
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            config.settings.main.enableAuth = True
            config.settings.main.enableAdminAuth = True
            config.settings.main.enableAdminAuthForStats = True
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")


            