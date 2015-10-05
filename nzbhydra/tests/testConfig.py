from nzbhydra import config
from nzbhydra.config import MainSettings, DownloaderSettings, NzbAccessTypeSelection, ProviderNewznab1Settings, SearchIdSelection, traverse_dict_and_set, traverse_dict_and_get, traverse_dict_and_add_to_dict, traverse_dict_and_add_to_list

config.load("testsettings.cfg")


def testThatGetAndSetWork():
    assert config.get(MainSettings.host) == "127.0.0.1"
    assert config.get(MainSettings.port) == 5050
    assert MainSettings.port.get() == 5050  # Direct access

    config.set(MainSettings.host, "192.168.0.1")
    assert config.get(MainSettings.host) == "192.168.0.1"
    # set back for later tests
    config.set(MainSettings.host, "127.0.0.1")

    config.set(MainSettings.port, 5051)
    assert config.get(MainSettings.port) == 5051


def testThatSelectionSettingsWork():
    assert config.cfg.get("downloader.nzbaccesstype") == "serve"  # Do a direct query to be sure that the data we work with is ok
    assert config.get(DownloaderSettings.nzbaccesstype) == "serve"

    assert config.isSettingSelection(DownloaderSettings.nzbaccesstype, NzbAccessTypeSelection.serve)
    assert DownloaderSettings.nzbaccesstype.isSetting(NzbAccessTypeSelection.serve)  # Direct access


def testGetSettingsAsDict():
    config.set(MainSettings.host, "127.0.0.1")
    
    d = config.get_settings_dict()
    

    assert d["downloader"]["nzbaccesstype"]["settingtype"] == "selection"
    assert d["downloader"]["nzbaccesstype"]["default"] == "serve"
    assert len(d["downloader"]["nzbaccesstype"]["selections"]) == 3
    assert d["downloader"]["nzbaccesstype"]["selections"][0]["name"] == "serve"

    # Write back changed settings
    d["main"]["host"]["value"] = "192.168.0.1"
    config.set_settings_from_dict(d)
    assert config.get(MainSettings.host) == "192.168.0.1"

    # set back for later tests
    config.set(MainSettings.host, "127.0.0.1")
    config.cfg.sync()


def testThatWritingSettingsWorks():
    config.set(MainSettings.port, 5053)
    config.cfg.sync()
    config.load("testsettings.cfg")
    assert config.get(MainSettings.port) == 5053

    # Set back to restore initial file content
    config.set(MainSettings.port, 5050)
    config.cfg.sync()


def testThatMultiSelectionSettingsWork():
    config.set(ProviderNewznab1Settings.search_ids, [SearchIdSelection.imdbid])
    assert config.get(ProviderNewznab1Settings.search_ids) == [SearchIdSelection.imdbid]
    config.cfg.sync()


def testGetNewznabSettingById():
    config.set(ProviderNewznab1Settings.apikey, "123")

    assert config.get_newznab_setting_by_id(1).apikey.get() == "123"
    config.get_newznab_setting_by_id(1).apikey.set("456")
    config.get(ProviderNewznab1Settings.apikey, "456")



def testTraversal():
    config.cfg.section("a").section("b").section("c")["ckey"] = "cvalue"
    assert len(list(config.cfg.section("a").sections())) == 1
    assert len(list(config.cfg.section("a").section("b").sections())) == 1

    assert config.cfg.section("a").section("b").section("c")["ckey"] == "cvalue"
    path = "a.b.c"
    sectionnames = path.split(".")
    section = config.cfg
    for s in sectionnames:
        section = section.section(s, create=False)
    assert section["ckey"] == "cvalue"

    d = {"a": {"b": {"c": "val"}}}
    d = traverse_dict_and_set(d, ["a", "b", "c"], "newval")
    assert d["a"]["b"]["c"] == "newval"
    
    assert traverse_dict_and_get(d, ["a", "b", "c"]) == "newval"
    
    d = traverse_dict_and_set(d, ["a", "b", "c"], "anothernewval", keep=True)
    assert d["a"]["b"]["c"] == "newval"
    
    d = {"a": {"b": {"c": {}}}}
    traverse_dict_and_add_to_dict(d, ["a", "b", "c"], "key", "value")
    assert d["a"]["b"]["c"]["key"] == "value"
    
    d = {"a": {"b": {"c": ["existtinglist"]}}}
    traverse_dict_and_add_to_list(d, ["a", "b", "c"], "added")
    assert len(d["a"]["b"]["c"]) == 2
    
    d = {"a": {"b": {"c": []}}}
    traverse_dict_and_add_to_list(d, ["a", "b", "c"], "added")
    assert len(d["a"]["b"]["c"]) == 1
    
    d = {"a": {}}
    traverse_dict_and_add_to_list(d, ["a", "b", "c"], "added")
    assert len(d["a"]["b"]["c"]) == 1
    
    d = {}
    traverse_dict_and_add_to_list(d, ["a", "b", "c"], "added")
    assert len(d["a"]["b"]["c"]) == 1
    
    d = {}
    traverse_dict_and_add_to_list(d, ["a"], "added")
    assert len(d["a"]) == 1