from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64
import json

import flask
import pytest

# standard_library.install_aliases()

from bunch import Bunch

from nzbhydra import config
from nzbhydra import web
from nzbhydra.tests.UrlTestCase import UrlTestCase
from nzbhydra.tests.db_prepare import set_and_drop


class TestWeb(UrlTestCase):
    @pytest.fixture
    def setUp(self):
        set_and_drop()
        web.app.template_folder = "../templates"
        self.app = web.app.test_client()

     

    def checkAreaAccess(self, area, checkisAllowed=True, username=None, password=None, method="get"):
        flask.request.authorization = None
        web.failedLogins = {}  # Don't block self after too many failed logins
        path = self.getPath(area)

        if username and password:
            if method == "get":
                resp = self.app.get(path, headers={
                    'Authorization': 'Basic ' + base64.b64encode(bytes(username + ":" + password)).decode('ascii')
                })
            else:
                resp = self.app.post("/auth/login", data=json.dumps({"username": username, "password": password}), headers={"Content-Type": "application/json"})
                if not checkisAllowed and method == "post" and resp.status_code == 401:
                    return
                token = "Bearer " + json.loads(list(resp.response)[0])["token"]
                resp = self.app.get(path, headers={"TokenAuthorization": token})
        else:
            resp = self.app.get(path)
            
        self.checkResponse(area, checkisAllowed, resp)

    def checkResponse(self, area, checkisAllowed, resp):
        if resp.status_code not in (200, 401):
            self.fail("Status code from response is %d - %s" % (resp.status_code, resp.status))
        if checkisAllowed:
            self.assertEqual(200, resp.status_code, "Access to %s area should be allowed but status code is %d" % (area, resp.status_code))
        else:
            self.assertEqual(401, resp.status_code, "Access to %s area should be forbidden but status code is %d" % (area, resp.status_code))

    def getPath(self, area):
        if area == "stats":
            path = "/internalapi/getindexerstatuses"
        elif area == "admin":
            path = "/internalapi/getconfig"
        else:
            path = "/"
        return path

    def testAuth(self):
        with web.app.test_request_context('/'):
            config.settings.auth = Bunch.fromDict({
                "authType": "none",
                "restrictAdmin": True,
                "restrictSearch": True,
                "restrictStats": True,
                "users": [
                    {
                        "maySeeAdmin": True,
                        "maySeeStats": True,
                        "username": "a",
                        "password": "b"
                    }
                ]
            })
            flask.request.authorization = None

            # No auth configured, access to all areas is free even if access is configured as restricted
            self.checkAreaAccess("main", True)
            self.checkAreaAccess("stats", True)
            self.checkAreaAccess("admin", True)

            # All restricted 
            config.settings.auth.authType = "basic"
            self.checkAreaAccess("main", False)
            self.checkAreaAccess("stats", False)
            self.checkAreaAccess("admin", False)
            self.checkAreaAccess("main", True, "a", "b")
            self.checkAreaAccess("stats", True, "a", "b")
            self.checkAreaAccess("admin", True, "a", "b")
            self.checkAreaAccess("main", False, "doesnt", "exist")
            self.checkAreaAccess("stats", False, "doesnt", "exist")
            self.checkAreaAccess("admin", False, "doesnt", "exist")

            # None restricted but user still configured
            config.settings.auth = Bunch.fromDict({
                "authType": "basic",
                "restrictAdmin": False,
                "restrictSearch": False,
                "restrictStats": False,
                "users": [
                    {
                        "maySeeAdmin": True,
                        "maySeeStats": True,
                        "username": "a",
                        "password": "b"
                    }
                ]
            })
            self.checkAreaAccess("main", True)
            self.checkAreaAccess("stats", True)
            self.checkAreaAccess("admin", True)
            self.checkAreaAccess("main", True, "a", "b")
            self.checkAreaAccess("stats", True, "a", "b")
            self.checkAreaAccess("admin", True, "a", "b")

            # Main free but others restricted, user only needed for stats and admin
            config.settings.auth = Bunch.fromDict({
                "authType": "basic",
                "restrictSearch": False,
                "restrictAdmin": True,
                "restrictStats": True,
                "users": [
                    {
                        "maySeeAdmin": True,
                        "maySeeStats": True,
                        "username": "a",
                        "password": "b"
                    }
                ]
            })
            self.checkAreaAccess("main", True)
            self.checkAreaAccess("stats", False)
            self.checkAreaAccess("admin", False)
            self.checkAreaAccess("main", True, "a", "b")
            self.checkAreaAccess("stats", True, "a", "b")
            self.checkAreaAccess("admin", True, "a", "b")

            # User for main, user for stats and admin
            config.settings.auth = Bunch.fromDict({
                "authType": "basic",
                "restrictSearch": True,
                "restrictAdmin": True,
                "restrictStats": True,
                "users": [
                    {
                        "maySeeAdmin": True,
                        "maySeeStats": True,
                        "username": "a",
                        "password": "b"
                    },
                    {
                        "maySeeAdmin": False,
                        "maySeeStats": False,
                        "username": "x",
                        "password": "y"
                    }
                ]
            })
            self.checkAreaAccess("main", False)
            self.checkAreaAccess("stats", False)
            self.checkAreaAccess("admin", False)
            self.checkAreaAccess("main", True, "a", "b")
            self.checkAreaAccess("stats", True, "a", "b")
            self.checkAreaAccess("admin", True, "a", "b")
            self.checkAreaAccess("main", True, "x", "y")
            self.checkAreaAccess("admin", False, "x", "y")
            self.checkAreaAccess("stats", False, "x", "y")

    def testFormAuth(self):
        with web.app.test_request_context('/'):
            config.settings.auth = Bunch.fromDict({
                "authType": "form",
                "restrictAdmin": True,
                "restrictSearch": True,
                "restrictStats": True,
                "users": [
                    {
                        "maySeeAdmin": True,
                        "maySeeStats": True,
                        "username": "a",
                        "password": "b"
                    }
                ]
            })
            flask.request.authorization = None
            self.checkAreaAccess("main", True, method="post") #Access to main area needs to be free with form access so the user can actually load the form to login
            self.checkAreaAccess("main", True, "a", "b", "post")
            self.checkAreaAccess("admin", True, "a", "b", "post")
            self.checkAreaAccess("stats", True, "a", "b", "post")
            self.checkAreaAccess("main", False, "a", "wrong", "post")
            self.checkAreaAccess("admin", False, "a", "wrong", "post")
            self.checkAreaAccess("stats", False, "a", "wrong", "post")
            self.checkAreaAccess("main", False, "doesnt", "exist", "post")
            self.checkAreaAccess("admin", False, "doesnt", "exist", "post")
            self.checkAreaAccess("stats", False, "doesnt", "exist", "post")

            #Restrict none
            config.settings.auth = Bunch.fromDict({
                "authType": "form",
                "restrictAdmin": False,
                "restrictSearch": False,
                "restrictStats": False,
                "users": [
                    {
                        "maySeeAdmin": True,
                        "maySeeStats": True,
                        "username": "a",
                        "password": "b"
                    }
                ]
            })
            flask.request.authorization = None
            self.checkAreaAccess("main", True, method="post")  
            self.checkAreaAccess("main", True, "a", "b", "post")
            self.checkAreaAccess("admin", True, "a", "b", "post")
            self.checkAreaAccess("stats", True, "a", "b", "post")
            #Providing a bad token/password should be detected even if the area access is not restricted
            self.checkAreaAccess("main", False, "a", "wrong", "post")
            self.checkAreaAccess("admin", False, "a", "wrong", "post")
            self.checkAreaAccess("stats", False, "a", "wrong", "post")
            self.checkAreaAccess("main", False, "doesnt", "exist", "post")
            self.checkAreaAccess("admin", False, "doesnt", "exist", "post")
            self.checkAreaAccess("stats", False, "doesnt", "exist", "post")


            # Restrict only access to admin and stats
            config.settings.auth = Bunch.fromDict({
                "authType": "form",
                "restrictAdmin": False,
                "restrictSearch": True,
                "restrictStats": True,
                "users": [
                    {
                        "maySeeAdmin": True,
                        "maySeeStats": True,
                        "username": "a",
                        "password": "b"
                    }
                ]
            })
            flask.request.authorization = None
            self.checkAreaAccess("main", True, method="post")
            self.checkAreaAccess("main", True, "a", "b", "post")
            self.checkAreaAccess("admin", True, "a", "b", "post")
            self.checkAreaAccess("stats", True, "a", "b", "post")
            self.checkAreaAccess("main", False, "a", "wrong", "post")
            self.checkAreaAccess("admin", False, "a", "wrong", "post")
            self.checkAreaAccess("stats", False, "a", "wrong", "post")
            self.checkAreaAccess("main", False, "doesnt", "exist", "post")
            self.checkAreaAccess("admin", False, "doesnt", "exist", "post")
            self.checkAreaAccess("stats", False, "doesnt", "exist", "post")

            # Simple user for search, admin user for other
            config.settings.auth = Bunch.fromDict({
                "authType": "form",
                "restrictAdmin": True,
                "restrictSearch": True,
                "restrictStats": True,
                "users": [
                    {
                        "maySeeAdmin": True,
                        "maySeeStats": True,
                        "username": "a",
                        "password": "b"
                    },
                    {
                        "maySeeAdmin": False,
                        "maySeeStats": False,
                        "username": "x",
                        "password": "y"
                    }
                ]
            })
            flask.request.authorization = None
            self.checkAreaAccess("main", True, method="post")
            self.checkAreaAccess("main", True, "a", "b", "post")
            self.checkAreaAccess("admin", True, "a", "b", "post")
            self.checkAreaAccess("stats", True, "a", "b", "post")
            self.checkAreaAccess("main", True, "x", "y", "post")
            self.checkAreaAccess("admin", False, "x", "y", "post")
            self.checkAreaAccess("stats", False, "x", "y", "post")