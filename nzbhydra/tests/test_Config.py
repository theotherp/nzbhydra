from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# standard_library.install_aliases()
import json
import logging
import unittest
from pprint import pprint

import arrow
import pytest
from builtins import *
import os
import copy
import shutil

from bunch import Bunch

from nzbhydra import config

print("Loading config from testsettings.cfg")


class TestConfig(unittest.TestCase):
    @pytest.fixture
    def setUp(self):
        if os.path.exists("testsettings.cfg"):
            os.remove("testsettings.cfg")
        shutil.copy("testsettings.cfg.orig", "testsettings.cfg")
        
        formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel("DEBUG")
        stream_handler.setFormatter(formatter)
        logging.getLogger("root").setLevel("DEBUG")

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
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(cfg["main"]["externalUrl"], "https://www.somedomain.com/nzbhydra", json.dumps(cfg))
        self.assertEqual(cfg["main"]["urlBase"], "/nzbhydra")

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = testCfg
            cfg["main"]["baseUrl"] = u"https://127.0.0.1/nzbhydra/"
            json.dump(cfg, settingsfile)
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(cfg["main"]["externalUrl"], "https://127.0.0.1/nzbhydra")
        self.assertEqual(cfg["main"]["urlBase"], "/nzbhydra")

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = testCfg
            cfg["main"]["baseUrl"] = u"https://www.somedomain.com/"
            json.dump(cfg, settingsfile)
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(cfg["main"]["externalUrl"], "https://www.somedomain.com")
        self.assertIsNone(cfg["main"]["urlBase"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = testCfg
            cfg["main"]["baseUrl"] = None
            json.dump(cfg, settingsfile)
        cfg = config.migrate("testsettings.cfg")
        self.assertIsNone(cfg["main"]["externalUrl"])
        self.assertIsNone(cfg["main"]["urlBase"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = testCfg
            cfg["main"]["nzbAddingType"] = "direct"
            json.dump(cfg, settingsfile)
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual("redirect", cfg["downloader"]["nzbAddingType"])

    def testMigration7to8(self):
        testCfg = {
            "main":
                {
                    "configVersion": 7,
                    "logging": {
                        "logfile-level": "",
                        "logfile-filename": 22
                    }
                },
            "indexers": {
                "Binsearch": {},
                "NZBClub": {},
                "NZBIndex": {},
                "Womble": {},
                "newznab1": {
                    "accessType": "both",
                    "apikey": "apikey1",
                    "name": "newznab1",
                    "enabled": False
                },
                "newznab2": {
                    "apikey": "apikey2",
                    "name": "newznab2",
                    "enabled": False
                }
            }
        }

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            json.dump(cfg, settingsfile)
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(2, len(cfg["indexers"]["newznab"]), json.dumps(cfg))
        self.assertEqual("newznab1", cfg["indexers"]["newznab"][0]["name"])
        self.assertEqual("newznab2", cfg["indexers"]["newznab"][1]["name"])
        self.assertTrue("accessType" in cfg["indexers"]["newznab"][0].keys())
        self.assertTrue("accessType" in cfg["indexers"]["newznab"][1].keys())

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
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(1, len(cfg["auth"]["users"]), json.dumps(cfg))
        self.assertIsNone(cfg["auth"]["users"][0]["username"])
        self.assertIsNone(cfg["auth"]["users"][0]["password"])
        self.assertTrue(cfg["auth"]["users"][0]["maySeeStats"])
        self.assertTrue(cfg["auth"]["users"][0]["maySeeAdmin"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            cfg["main"]["enableAuth"] = True
            cfg["main"]["username"] = "u"
            cfg["main"]["password"] = "p"
            json.dump(cfg, settingsfile)
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(1, len(cfg["auth"]["users"]))
        self.assertEqual("u", cfg["auth"]["users"][0]["username"])
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
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(2, len(cfg["auth"]["users"]))
        self.assertEqual("u", cfg["auth"]["users"][0]["username"])
        self.assertEqual("p", cfg["auth"]["users"][0]["password"])
        self.assertTrue(cfg["auth"]["users"][0]["maySeeStats"])
        self.assertEqual(False, cfg["auth"]["users"][0]["maySeeAdmin"])
        self.assertEqual("au", cfg["auth"]["users"][1]["username"])
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
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(2, len(cfg["auth"]["users"]))
        self.assertEqual("u", cfg["auth"]["users"][0]["username"])
        self.assertEqual("p", cfg["auth"]["users"][0]["password"])
        self.assertEqual(False, cfg["auth"]["users"][0]["maySeeStats"])
        self.assertEqual(False, cfg["auth"]["users"][0]["maySeeAdmin"])
        self.assertEqual("au", cfg["auth"]["users"][1]["username"])
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
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(2, len(cfg["auth"]["users"]))
        self.assertIsNone(cfg["auth"]["users"][0]["username"])
        self.assertIsNone(cfg["auth"]["users"][0]["password"])
        self.assertTrue(cfg["auth"]["users"][0]["maySeeStats"])
        self.assertFalse(cfg["auth"]["users"][0]["maySeeAdmin"])
        self.assertEqual("au", cfg["auth"]["users"][1]["username"])
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
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(2, len(cfg["auth"]["users"]))
        self.assertIsNone(cfg["auth"]["users"][0]["username"])
        self.assertIsNone(cfg["auth"]["users"][0]["password"])
        self.assertFalse(cfg["auth"]["users"][0]["maySeeStats"])
        self.assertFalse(cfg["auth"]["users"][0]["maySeeAdmin"])
        self.assertEqual("au", cfg["auth"]["users"][1]["username"])
        self.assertEqual("ap", cfg["auth"]["users"][1]["password"])
        self.assertTrue(cfg["auth"]["users"][1]["maySeeStats"])
        self.assertTrue(cfg["auth"]["users"][1]["maySeeAdmin"])

    def testMigration10to11(self):
        testCfg = {
            "main": {
                "configVersion": 10
            },
            "auth": {
                "users": [
                    {
                        "name": None
                    },
                    {
                        "name": "whatever"
                    }
                ]
            }
        }
        self.assertTrue("name" in testCfg["auth"]["users"][0].keys())
        self.assertTrue("name" in testCfg["auth"]["users"][1].keys())

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            json.dump(cfg, settingsfile)
        cfg = config.migrate("testsettings.cfg")
        self.assertEqual(2, len(cfg["auth"]["users"]))
        self.assertIsNone(cfg["auth"]["users"][0]["username"])
        self.assertEqual("whatever", cfg["auth"]["users"][1]["username"])
        self.assertFalse("name" in cfg["auth"]["users"][0].keys())
        self.assertFalse("name" in cfg["auth"]["users"][1].keys())

    def testMigration12to13(self):
        testCfg = {
            "main":
                {
                    "configVersion": 12,
                },
            "indexers": {
                "binsearch": {},
                "nzbclub": {},
                "nzbindex": {},
                "omgwtfnzbs": {},
                "womble": {},
                "newznab": [
                    {},
                    {}

                ]

            }
        }

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            json.dump(cfg, settingsfile)
        cfg = config.migrate("testsettings.cfg")
        print(json.dumps(cfg))
        config.logLogMessages()
        self.assertIsNone(cfg["indexers"]["binsearch"]["hitLimit"])
        self.assertIsNone(cfg["indexers"]["nzbclub"]["hitLimit"])
        self.assertIsNone(cfg["indexers"]["nzbindex"]["hitLimit"])
        self.assertIsNone(cfg["indexers"]["omgwtfnzbs"]["hitLimit"])
        self.assertIsNone(cfg["indexers"]["womble"]["hitLimit"])
        self.assertIsNone(cfg["indexers"]["newznab"][0]["hitLimit"])
        self.assertIsNone(cfg["indexers"]["newznab"][1]["hitLimit"])
        self.assertEqual(arrow.get(0), cfg["indexers"]["newznab"][0]["hitLimitResetTime"])
        self.assertEqual(arrow.get(0), cfg["indexers"]["newznab"][1]["hitLimitResetTime"])

    def testGetAnonymizedConfig(self):
        config.settings = {
            "downloader": {
                "nzbget": {
                    "host": "3.4.5.6",
                    "password": "nzbgetuser",
                    "username": "nzbgetpassword"
                },
                "sabnzbd": {
                    "apikey": "sabnzbdapikey",
                    "password": "sabnzbdpassword",
                    "url": "http://localhost:8080/sabnzbd/",
                    "username": "sabnzbduser"
                }
            },
            "indexers": {
                "newznab": [
                    {
                        "apikey": "newznabapikey",
                    },
                ],
                "omgwtfnzbs": {
                    "apikey": "omgwtfapikey",
                    "username": "omgwtfusername"
                }
            },
            "main": {
                "apikey": "hydraapikey",
                "externalUrl": "http://www.hydradomain.com/nzbhydra",
                "host": "1.2.3.4"
            },
            "auth": {
                "users": [
                    {
                        "username": "someuser",
                        "password": "somepassword"
                    }
                ]
            }
        }
        ac = config.getAnonymizedConfig()
        ac = Bunch.fromDict(ac)
        self.assertEqual("<APIKEY:3f7ccf2fa729e7329f8d2af3ae5b2d00>", ac.indexers.newznab[0].apikey)
        self.assertEqual("<USERNAME:be1cd7618f0bc25e333d996582c037b2>", ac.indexers.omgwtfnzbs.username)
        self.assertEqual("<APIKEY:680eae14a056ebd0d1c71dbfb6c5ebbc>", ac.indexers.omgwtfnzbs.apikey)
        self.assertEqual("<IPADDRESS:6465ec74397c9126916786bbcd6d7601>", ac.main.host)
        self.assertEqual("<APIKEY:b5f0bb7a7671d14f3d79866bcdfac6b5>", ac.main.apikey)
        self.assertEqual("http://<DOMAIN:ea2cbe92bacf786835b93ff2ca78c459>/nzbhydra", ac.main.externalUrl)
        self.assertEqual("<USERNAME:25adeda6f43bf9adf9781d29d1435986>", ac.auth.users[0].username)
        self.assertEqual("<PASSWORD:9c42a1346e333a770904b2a2b37fa7d3>", ac.auth.users[0].password)
        self.assertEqual("<USERNAME:df60a3d2b6cdc05d169e684c0aaa7b20>", ac.downloader.nzbget.username)
        self.assertEqual("<IPADDRESS:c6deeee6bee7ff3d4cc2048843f5678b>", ac.downloader.nzbget.host)
        self.assertEqual("<PASSWORD:78afef0fe4ffe1ed97aff6ab577ef5a4>", ac.downloader.nzbget.password)
        self.assertEqual("http://<NOTIPADDRESSORDOMAIN:421aa90e079fa326b6494f812ad13e79>:8080/sabnzbd/", ac.downloader.sabnzbd.url)
        self.assertEqual("<USERNAME:96c4173454468a77d67b2c813ffe307a>", ac.downloader.sabnzbd.username)
        self.assertEqual("<APIKEY:f5095bc1520183e76be64af1c5f9e7e3>", ac.downloader.sabnzbd.apikey)
        self.assertEqual("<PASSWORD:4c471a175d85451486af666d7eebe4f8>", ac.downloader.sabnzbd.password)

    def testMigration15to16(self):
        testCfg = {
            "main":
                {
                    "configVersion": 15,
                },
            "indexers": {
                "binsearch": {"name": "binsearch", "type": "binsearch"},
                "nzbclub": {"name": "nzbclub", "type": "nzbclub"},
                "nzbindex": {"name": "nzbindex", "type": "nzbindex"},
                "omgwtfnzbs": {"name": "omgwtf", "type": "omgwtf"},
                "womble": {"name": "womble", "type": "womble"},
                "newznab": [
                    {"name": "newznab1", "type": "newznab1"},
                    {"name": "newznab2", "type": "newznab2"}

                ]

            }
        }
        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = copy.copy(testCfg)
            json.dump(cfg, settingsfile)
        cfg = config.migrate("testsettings.cfg")
        pprint(cfg)
        indexers = list(sorted(cfg["indexers"], key=lambda x: x["name"]))
        self.assertEqual(indexers[0]["name"], "binsearch")