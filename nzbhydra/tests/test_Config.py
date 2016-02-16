from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# standard_library.install_aliases()
import json
import unittest

import pytest
from builtins import *
import os
import copy
import shutil
from nzbhydra.config import migrate

print("Loading config from testsettings.cfg")


class TestInfos(unittest.TestCase):
    @pytest.fixture
    def setUp(self):
        if os.path.exists("testsettings.cfg"):
            os.remove("testsettings.cfg")
        shutil.copy("testsettings.cfg.orig", "testsettings.cfg")

    def testMigration3to4(self):
        testCfg = {
            "main":
                {
                    "configVersion": 3,
                    u"baseUrl": u"https://www.somedomain.com/nzbhydra"

                },
            "downloader": {
                "nzbAddingType": "redirect"
            }}

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = testCfg
            cfg["main"]["baseUrl"] = u"https://www.somedomain.com/nzbhydra"
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(cfg["main"]["externalUrl"], "https://www.somedomain.com/nzbhydra")
        self.assertEqual(cfg["main"]["urlBase"], "/nzbhydra")

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = testCfg
            cfg["main"]["baseUrl"] = u"https://127.0.0.1/nzbhydra/"
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(cfg["main"]["externalUrl"], "https://127.0.0.1/nzbhydra")
        self.assertEqual(cfg["main"]["urlBase"], "/nzbhydra")

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = testCfg
            cfg["main"]["baseUrl"] = u"https://www.somedomain.com/"
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(cfg["main"]["externalUrl"], "https://www.somedomain.com")
        self.assertIsNone(cfg["main"]["urlBase"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = testCfg
            cfg["main"]["baseUrl"] = None
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertIsNone(cfg["main"]["externalUrl"])
        self.assertIsNone(cfg["main"]["urlBase"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = testCfg
            cfg["main"]["nzbAddingType"] = "direct"
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual("redirect", cfg["downloader"]["nzbAddingType"])

    def testMigration8to9(self):
        testCfg = {
            "main": {
                "adminPassword": None,
                "adminUsername": None,
                "configVersion": 8,
                "enableAdminAuth": False,
                "enableAdminAuthForStats": False,
                "enableAuth": False,
                "password": None,
                "username": None
            }

        }

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(1, len(cfg["auth"]["users"]))
        self.assertIsNone(cfg["auth"]["users"][0]["name"])
        self.assertIsNone(cfg["auth"]["users"][0]["password"])
        self.assertTrue(cfg["auth"]["users"][0]["maySeeStats"])
        self.assertTrue(cfg["auth"]["users"][0]["maySeeAdmin"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            cfg["main"]["enableAuth"] = True
            cfg["main"]["username"] = "u"
            cfg["main"]["password"] = "p"
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(1, len(cfg["auth"]["users"]))
        self.assertEqual("u", cfg["auth"]["users"][0]["name"])
        self.assertEqual("p", cfg["auth"]["users"][0]["password"])
        self.assertTrue(cfg["auth"]["users"][0]["maySeeStats"])
        self.assertTrue(cfg["auth"]["users"][0]["maySeeAdmin"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            cfg["main"]["enableAuth"] = True
            cfg["main"]["username"] = "u"
            cfg["main"]["password"] = "p"
            cfg["main"]["enableAdminAuth"] = True
            cfg["main"]["adminUsername"] = "au"
            cfg["main"]["adminPassword"] = "ap"
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(2, len(cfg["auth"]["users"]))
        self.assertEqual("u", cfg["auth"]["users"][0]["name"])
        self.assertEqual("p", cfg["auth"]["users"][0]["password"])
        self.assertTrue(cfg["auth"]["users"][0]["maySeeStats"])
        self.assertEqual(False, cfg["auth"]["users"][0]["maySeeAdmin"])
        self.assertEqual("au", cfg["auth"]["users"][1]["name"])
        self.assertEqual("ap", cfg["auth"]["users"][1]["password"])
        self.assertTrue(cfg["auth"]["users"][1]["maySeeStats"])
        self.assertTrue(cfg["auth"]["users"][1]["maySeeAdmin"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            cfg["main"]["enableAuth"] = True
            cfg["main"]["username"] = "u"
            cfg["main"]["password"] = "p"
            cfg["main"]["enableAdminAuth"] = True
            cfg["main"]["enableAdminAuthForStats"] = True
            cfg["main"]["adminUsername"] = "au"
            cfg["main"]["adminPassword"] = "ap"
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(2, len(cfg["auth"]["users"]))
        self.assertEqual("u", cfg["auth"]["users"][0]["name"])
        self.assertEqual("p", cfg["auth"]["users"][0]["password"])
        self.assertEqual(False, cfg["auth"]["users"][0]["maySeeStats"])
        self.assertEqual(False, cfg["auth"]["users"][0]["maySeeAdmin"])
        self.assertEqual("au", cfg["auth"]["users"][1]["name"])
        self.assertEqual("ap", cfg["auth"]["users"][1]["password"])
        self.assertTrue(cfg["auth"]["users"][1]["maySeeStats"])
        self.assertTrue(cfg["auth"]["users"][1]["maySeeAdmin"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            cfg["main"]["enableAuth"] = False
            cfg["main"]["enableAdminAuthForStats"] = False
            cfg["main"]["enableAdminAuth"] = True
            cfg["main"]["adminUsername"] = "au"
            cfg["main"]["adminPassword"] = "ap"
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(2, len(cfg["auth"]["users"]))
        self.assertIsNone(cfg["auth"]["users"][0]["name"])
        self.assertIsNone(cfg["auth"]["users"][0]["password"])
        self.assertTrue(cfg["auth"]["users"][0]["maySeeStats"])
        self.assertFalse(cfg["auth"]["users"][0]["maySeeAdmin"])
        self.assertEqual("au", cfg["auth"]["users"][1]["name"])
        self.assertEqual("ap", cfg["auth"]["users"][1]["password"])
        self.assertTrue(cfg["auth"]["users"][1]["maySeeStats"])
        self.assertTrue(cfg["auth"]["users"][1]["maySeeAdmin"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            cfg["main"]["enableAuth"] = False
            cfg["main"]["enableAdminAuth"] = True
            cfg["main"]["enableAdminAuthForStats"] = True
            cfg["main"]["adminUsername"] = "au"
            cfg["main"]["adminPassword"] = "ap"
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(2, len(cfg["auth"]["users"]))
        self.assertIsNone(cfg["auth"]["users"][0]["name"])
        self.assertIsNone(cfg["auth"]["users"][0]["password"])
        self.assertFalse(cfg["auth"]["users"][0]["maySeeStats"])
        self.assertFalse(cfg["auth"]["users"][0]["maySeeAdmin"])
        self.assertEqual("au", cfg["auth"]["users"][1]["name"])
        self.assertEqual("ap", cfg["auth"]["users"][1]["password"])
        self.assertTrue(cfg["auth"]["users"][1]["maySeeStats"])
        self.assertTrue(cfg["auth"]["users"][1]["maySeeAdmin"])
        

