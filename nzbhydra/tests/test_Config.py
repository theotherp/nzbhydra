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
import shutil
from nzbhydra import config
from nzbhydra.config import migrate

print("Loading config from testsettings.cfg")


class TestInfos(unittest.TestCase):
    @pytest.fixture
    def setUp(self):
        if os.path.exists("testsettings.cfg"):
            os.remove("testsettings.cfg")
        shutil.copy("testsettings.cfg.orig", "testsettings.cfg")
        config.settings.load("testsettings.cfg")

    # def testThatGetAndSetWork(self):
    #     # Simple get and set
    #     assert mainSettings.host == "0.0.0.0"
    #     mainSettings.host.set("192.168.0.1")
    #     assert mainSettings.host == "192.168.0.1"
    #     mainSettings.host = "192.168.100.100"  # We can even set the value directly
    #     assert mainSettings.host == "192.168.100.100"
    #     mainSettings.host.set("127.0.0.1")  # Just set back
    # 
    #     # Setting in subcategory
    #     assert mainSettings.logging.logfilelevel == "INFO"
    # 
    #     assert indexer.binsearch.name == "Binsearch"
    # 
    # def testThatWritingSettingsWorks(self):
    #     mainSettings.port = 5053
    #     config.settings.save("testsettings.cfg")
    #     mainSettings.port = 5054  # Set to another port
    #     config.settings.load("testsettings.cfg")
    #     assert mainSettings.port == 5053
    # 
    # def testNewznabIndexers(self):
    #     indexer.newznab1.host.set("http://127.0.0.1")
    #     config.settings.save("testsettings.cfg")
    #     indexer.newznab1.host.set("http://192.168.0.1")
    #     config.settings.load("testsettings.cfg")
    #     assert indexer.newznab1.host == "http://127.0.0.1"

    def testMigration(self):
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


        # 
        # 
        # def testGetNewznabSettingById():
        #     nsettings = config.settings.get_newznab_setting_by_id(1)
        #     config.settings.set(nsettings.apikey, "123")
        # 
        #     assert config.settings.get_newznab_setting_by_id(1).apikey == "123"
        #     config.settings.get_newznab_setting_by_id(1).apikey = "456"
        #     config.settings.get(nsettings.apikey, "456")
        # 
        # 
        # def testGetAndSetSettingsAsDict():
        #     config.settings.set(mainSettings.host, "127.0.0.1")
        # 
        #     d = config.settings.get_settings_as_dict_without_lists()
        # 
        #     assert d["downloader"]["nzbaccesstype"] == "serve"
        # 
        #     # Write back changed settings
        #     d["main"]["host"] = "192.168.0.1"
        #     d["downloader"]["nzbaccesstype"] = "nzb"
        #     
        #     config.settings.set_settings_from_dict(d)
        #     assert config.settings.get(mainSettings.host) == "192.168.0.1"
        #     assert d["downloader"]["nzbaccesstype"] == "nzb"
        # 
        #     #Just make sure we can dump it as json
        #     json.dumps(d)
