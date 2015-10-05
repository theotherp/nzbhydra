from profig import InvalidSectionError
import pytest
from nzbhydra import config
from nzbhydra.config import MainSettings, DownloaderSettings, NzbAccessTypeSelection, ProviderBinsearchSettings, ProviderNewznab1Settings, SearchIdSelection

config.load("testsettings.cfg")


def testThatGetAndSetWork():
    assert config.get(MainSettings.host) == "127.0.0.1"
    assert config.get(MainSettings.port) == 5050
    
    config.set(MainSettings.host, "192.168.0.1")
    assert config.get(MainSettings.host) == "192.168.0.1"
    #set back for later tests
    config.set(MainSettings.host, "127.0.0.1")
    
    config.set(MainSettings.port, 5051)
    assert config.get(MainSettings.port) == 5051
    
def testThatSelectionSettingsWork():
    assert config.cfg.get("downloader.nzbaccesstype") == "serve" #Do a direct query to be sure that the data we work with is ok
    assert config.get(DownloaderSettings.nzbaccesstype) == "serve"
    
    assert config.isSettingSelection(DownloaderSettings.nzbaccesstype, NzbAccessTypeSelection.serve)
        

def testGetSettingsAsDict():
    d = config.get_settings_dict()
    assert "main" in d.keys()
    assert "host" in d["main"].keys()
    assert d["main"]["host"]["value"] == "127.0.0.1"
    
    assert d["downloader"]["nzbaccesstype"]["settingtype"] == "selection"
    assert d["downloader"]["nzbaccesstype"]["default"] == "serve"
    assert len(d["downloader"]["nzbaccesstype"]["selections"]) == 3
    assert d["downloader"]["nzbaccesstype"]["selections"][0]["name"] == "serve"
    
    #Write back changed settings
    d["main"]["host"]["value"] = "192.168.0.1"
    config.set_settings_from_dict(d)
    assert config.get(MainSettings.host) == "192.168.0.1"
    
    #set back for later tests
    config.set(MainSettings.host, "127.0.0.1")
    config.cfg.sync()
    

def testThatWritingSettingsWorks():
    config.set(MainSettings.port, 5053)
    config.cfg.sync()
    config.load("testsettings.cfg")
    assert config.get(MainSettings.port) == 5053
    
    #Set back to restore initial file content
    config.set(MainSettings.port, 5050)
    config.cfg.sync()
    

def testThatMultiSelectionSettingsWork():
    config.set(ProviderNewznab1Settings.search_ids, [SearchIdSelection.imdbid])
    assert config.get(ProviderNewznab1Settings.search_ids) == [SearchIdSelection.imdbid]
    config.cfg.sync()
    
    
