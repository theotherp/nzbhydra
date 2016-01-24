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
from nzbhydra.config import mainSettings, indexerSettings, migrate

print("Loading config from testsettings.cfg")


class TestInfos(unittest.TestCase):
    @pytest.fixture
    def setUp(self):
        if os.path.exists("testsettings.cfg"):
            os.remove("testsettings.cfg")
        shutil.copy("testsettings.cfg.orig", "testsettings.cfg")
        config.load("testsettings.cfg")

    # def testThatGetAndSetWork(self):
    #     # Simple get and set
    #     assert mainSettings.host.get() == "0.0.0.0"
    #     mainSettings.host.set("192.168.0.1")
    #     assert mainSettings.host.get() == "192.168.0.1"
    #     mainSettings.host = "192.168.100.100"  # We can even set the value directly
    #     assert mainSettings.host.get() == "192.168.100.100"
    #     mainSettings.host.set("127.0.0.1")  # Just set back
    # 
    #     # Setting in subcategory
    #     assert mainSettings.logging.logfilelevel.get() == "INFO"
    # 
    #     assert indexerSettings.binsearch.name.get() == "Binsearch"
    # 
    # def testThatWritingSettingsWorks(self):
    #     mainSettings.port.set(5053)
    #     config.save("testsettings.cfg")
    #     mainSettings.port.set(5054)  # Set to another port
    #     config.load("testsettings.cfg")
    #     assert mainSettings.port.get() == 5053
    # 
    # def testNewznabIndexers(self):
    #     indexerSettings.newznab1.host.set("http://127.0.0.1")
    #     config.save("testsettings.cfg")
    #     indexerSettings.newznab1.host.set("http://192.168.0.1")
    #     config.load("testsettings.cfg")
    #     assert indexerSettings.newznab1.host.get() == "http://127.0.0.1"

    def testMigration(self):
        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = {
                u"main":
                    {
                        u"configVersion": 3,
                        u"baseUrl": u"https://www.somedomain.com/nzbhydra"
                
                    }
            }
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(cfg["main"]["externalUrl"], "https://www.somedomain.com/nzbhydra")
        self.assertEqual(cfg["main"]["urlBase"], "/nzbhydra")

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = {
                "main":
                    {
                        "configVersion": 3,
                        "baseUrl": "https://127.0.0.1/nzbhydra/"
            
                    }}
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(cfg["main"]["externalUrl"], "https://127.0.0.1/nzbhydra")
        self.assertEqual(cfg["main"]["urlBase"], "/nzbhydra")

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = {
                "main":
                    {
                        "configVersion": 3,
                        "baseUrl": "https://www.somedomain.com/"
            
                    }}
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertEqual(cfg["main"]["externalUrl"], "https://www.somedomain.com")
        self.assertIsNone(cfg["main"]["urlBase"])

        with open("testsettings.cfg", "wb") as settingsfile:
            cfg = {
                "main":
                    {
                        "configVersion": 3,
                        "baseUrl": None
            
                    }}
            json.dump(cfg, settingsfile)
        cfg = migrate("testsettings.cfg")
        self.assertIsNone(cfg["main"]["externalUrl"])
        self.assertIsNone(cfg["main"]["urlBase"])
        

        # 
        # 
        # def testGetNewznabSettingById():
        #     nsettings = config.get_newznab_setting_by_id(1)
        #     config.set(nsettings.apikey, "123")
        # 
        #     assert config.get_newznab_setting_by_id(1).apikey.get() == "123"
        #     config.get_newznab_setting_by_id(1).apikey.set("456")
        #     config.get(nsettings.apikey, "456")
        # 
        # 
        # def testGetAndSetSettingsAsDict():
        #     config.set(mainSettings.host, "127.0.0.1")
        # 
        #     d = config.get_settings_as_dict_without_lists()
        # 
        #     assert d["downloader"]["nzbaccesstype"] == "serve"
        # 
        #     # Write back changed settings
        #     d["main"]["host"] = "192.168.0.1"
        #     d["downloader"]["nzbaccesstype"] = "nzb"
        #     
        #     config.set_settings_from_dict(d)
        #     assert config.get(mainSettings.host) == "192.168.0.1"
        #     assert d["downloader"]["nzbaccesstype"] == "nzb"
        # 
        #     #Just make sure we can dump it as json
        #     json.dumps(d)
