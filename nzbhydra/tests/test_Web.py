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

from bunch import Bunch
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
            
            #No users configured
            config.settings.auth.users = Bunch.fromDict([{"name": None, "password": None, "maySeeStats": True, "maySeeAdmin": True}])
            flask.request.authorization = None
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            # User required for everything
            config.settings.auth.users = Bunch.fromDict([{"name": "u", "password": "p", "maySeeStats": True, "maySeeAdmin": True}])
            flask.request.authorization = None
            assert not web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")
            flask.request.authorization = {"username": "u", "password": "p"}
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            #User required for stats and admin 
            config.settings.auth.users = Bunch.fromDict([{"name": None, "password": None, "maySeeStats": False, "maySeeAdmin": False}, {"name": "au", "password": "ap", "maySeeStats": True, "maySeeAdmin": True}])
            flask.request.authorization = None
            assert web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")
            flask.request.authorization = {"username": "au", "password": "ap"}
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            #User required for admin only
            config.settings.auth.users = Bunch.fromDict([{"name": None, "password": None, "maySeeStats": True, "maySeeAdmin": False}, {"name": "au", "password": "ap", "maySeeStats": True, "maySeeAdmin": True}])
            flask.request.authorization = None
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert not web.isAllowed("admin")
            flask.request.authorization = {"username": "au", "password": "ap"}
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            #Basic required user for main, admin user required for stats and admin
            config.settings.auth.users = Bunch.fromDict([{"name": "u", "password": "p", "maySeeStats": False, "maySeeAdmin": False}, {"name": "au", "password": "ap", "maySeeStats": True, "maySeeAdmin": True}])
            flask.request.authorization = None
            assert not web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")
            flask.request.authorization = {"username": "u", "password": "p"}
            assert web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")
            flask.request.authorization = {"username": "au", "password": "ap"}
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")

            # Basic user required for main and stats, admin user required for admin
            config.settings.auth.users = Bunch.fromDict([{"name": "u", "password": "p", "maySeeStats": True, "maySeeAdmin": False}, {"name": "au", "password": "ap", "maySeeStats": True, "maySeeAdmin": True}])
            flask.request.authorization = None
            assert not web.isAllowed("main")
            assert not web.isAllowed("stats")
            assert not web.isAllowed("admin")
            flask.request.authorization = {"username": "u", "password": "p"}
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert not web.isAllowed("admin")
            flask.request.authorization = {"username": "au", "password": "ap"}
            assert web.isAllowed("main")
            assert web.isAllowed("stats")
            assert web.isAllowed("admin")


            
            

            

            