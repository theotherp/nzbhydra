import json
import shutil

from nzbhydra import config
from nzbhydra.config import mainSettings, CacheTypeSelection

print("Loading config from testsettings.cfg")
shutil.copy("testsettings.cfg.orig", "testsettings.cfg")
config.load("testsettings.cfg")


def testThatGetAndSetWork():
    assert config.get(mainSettings.host) == "127.0.0.1"
    assert config.get(mainSettings.port) == 5050
    assert mainSettings.port.get() == 5050  # Direct access

    config.set(mainSettings.host, "192.168.0.1")
    assert config.get(mainSettings.host) == "192.168.0.1"

    assert str(mainSettings.host) == "host: 192.168.0.1"

    # set back for later tests
    config.set(mainSettings.host, "127.0.0.1")

    config.set(mainSettings.port, 5051)
    assert config.get(mainSettings.port) == 5051

    assert mainSettings.cache_type.get() == CacheTypeSelection.memory


def testThatWritingSettingsWorks():
    config.set(mainSettings.port, 5053)
    config.cfg.sync()
    config.load("testsettings.cfg")
    assert config.get(mainSettings.port) == 5053

    # Set back to restore initial file content
    config.set(mainSettings.port, 5050)
    config.cfg.sync()


def testGetNewznabSettingById():
    nsettings = config.get_newznab_setting_by_id(1)
    config.set(nsettings.apikey, "123")

    assert config.get_newznab_setting_by_id(1).apikey.get() == "123"
    config.get_newznab_setting_by_id(1).apikey.set("456")
    config.get(nsettings.apikey, "456")


def testGetSettingsAsDict():
    config.set(mainSettings.host, "127.0.0.1")

    # d = config.get_settings_as_dict()
    # 
    # assert d["downloader"]["nzbaccesstype"] == "serve"
    # 
    # assert config.get(mainSettings.host) == "127.0.0.1"
    # # Write back changed settings
    # d["main"]["host"] = "192.168.0.1"
    # config.set_settings_from_dict(d)
    # assert config.get(mainSettings.host) == "192.168.0.1"
    # 
    # # set back for later tests
    # config.set(mainSettings.host, "127.0.0.1")
    # config.cfg.sync()
    # 
    # json.dumps(d)

    d = config.cfg.as_dict(flat=True)
    d = config.cfg.as_dict(dict_type=dict)
    pass