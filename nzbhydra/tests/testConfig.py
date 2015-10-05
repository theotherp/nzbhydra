from nzbhydra import config
from nzbhydra.config import MainSettings, SabnzbdSettings

config.load("testsettings.cfg")


def testThatGetWorks():
    # Read a string
    assert config.cfg.get("main.host") == "127.0.0.1"
    assert config.get(MainSettings.host) == "127.0.0.1"

    assert config.get(MainSettings.host) == "127.0.0.1"

    # Read an int
    assert config.cfg.get("main.port") == 5050
    assert config.get(MainSettings.port) == 5050


def testThatSetWorks():
    # Set using profig
    config.cfg["main.port"] = 5051
    assert config.cfg.get("main.port") == 5051
    assert config.get(MainSettings.port) == 5051

    # Set using custom config and setting class
    config.set(MainSettings.port, 5052)
    assert config.cfg.get("main.port") == 5052
    assert config.get(MainSettings.port) == 5052


def testThatWritingSettingsWorks():
    config.set(MainSettings.port, 5053)
    config.cfg.sync()
    config.load("testsettings.cfg")
    assert config.get(MainSettings.port) == 5053
    
    #Set back to restore initial file content
    config.set(MainSettings.port, 5050)
    config.cfg.sync()
    

def testBla():
    assert config.cfg.get("downloader.sabnzbd.host") == "127.0.0.1"
    assert config.get(SabnzbdSettings.host) == "127.0.0.1"

    assert config.cfg.get("downloader.sabnzbd.port") == 8086
    assert config.get(SabnzbdSettings.port) == 8086
