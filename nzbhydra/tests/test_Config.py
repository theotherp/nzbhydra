from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# standard_library.install_aliases()
import logging
import unittest

import pytest
from builtins import *

from bunch import Bunch

from nzbhydra import config


class TestConfig(unittest.TestCase):
    @pytest.fixture
    def setUp(self):
        formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel("DEBUG")
        stream_handler.setFormatter(formatter)
        logging.getLogger("root").setLevel("DEBUG")

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
                ]
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

    def testMigration25to26(self):
        testCfg = {
            "main":
                {
                    "configVersion": 25,
                },
            "downloaders": [
                {}
            ],
            "indexers": [
                {
                    "hitLimitResetTime": "1970-01-01T00:00:00.000Z",
                    "name": "Indexer1"
                },
                {
                    "hitLimitResetTime": "1970-01-01T08:00:00.000Z",
                    "name": "Indexer2"
                },
                {
                    "hitLimitResetTime": 10,
                    "name": "Indexer3"
                }
            ]
        }
        cfg = config.migrateConfig(testCfg)
        self.assertEqual(0, cfg["indexers"][0]["hitLimitResetTime"])
        self.assertEqual(8, cfg["indexers"][1]["hitLimitResetTime"])
        self.assertEqual(10, cfg["indexers"][2]["hitLimitResetTime"])
