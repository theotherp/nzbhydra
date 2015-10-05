from nzbhydra import config
from nzbhydra.config import mainSettings, downloaderSettings, NzbAccessTypeSelection, SearchIdSelection, traverse_dict_and_set, traverse_dict_and_get, traverse_dict_and_add_to_dict, traverse_dict_and_add_to_list

config.load("testsettings.cfg")


def testThatGetAndSetWork():
    assert config.get(mainSettings.host) == "127.0.0.1"
    assert config.get(mainSettings.port) == 5050
    assert mainSettings.port.get() == 5050  # Direct access

    config.set(mainSettings.host, "192.168.0.1")
    assert config.get(mainSettings.host) == "192.168.0.1"
    # set back for later tests
    config.set(mainSettings.host, "127.0.0.1")

    config.set(mainSettings.port, 5051)
    assert config.get(mainSettings.port) == 5051


def testThatSelectionSettingsWork():
    assert config.cfg.get("downloader.nzbaccesstype") == "serve"  # Do a direct query to be sure that the data we work with is ok
    assert config.get(downloaderSettings.nzbaccesstype) == "serve"

    assert config.isSettingSelection(downloaderSettings.nzbaccesstype, NzbAccessTypeSelection.serve)
    assert downloaderSettings.nzbaccesstype.isSetting(NzbAccessTypeSelection.serve)  # Direct access


def testGetSettingsAsDict():
    config.set(mainSettings.host, "127.0.0.1")

    d = config.get_settings_dict()

    assert d["downloader"]["nzbaccesstype"]["settingtype"] == "selection"
    assert d["downloader"]["nzbaccesstype"]["default"] == "serve"
    assert len(d["downloader"]["nzbaccesstype"]["selections"]) == 3
    assert d["downloader"]["nzbaccesstype"]["selections"][0]["name"] == "serve"

    # Write back changed settings
    d["main"]["host"]["value"] = "192.168.0.1"
    config.set_settings_from_dict(d)
    assert config.get(mainSettings.host) == "192.168.0.1"

    # set back for later tests
    config.set(mainSettings.host, "127.0.0.1")
    config.cfg.sync()


def testThatWritingSettingsWorks():
    config.set(mainSettings.port, 5053)
    config.cfg.sync()
    config.load("testsettings.cfg")
    assert config.get(mainSettings.port) == 5053

    # Set back to restore initial file content
    config.set(mainSettings.port, 5050)
    config.cfg.sync()


def testThatMultiSelectionSettingsWork():
    nsettings = config.get_newznab_setting_by_id(1)
    config.set(nsettings.search_ids, [SearchIdSelection.imdbid])
    assert config.get(nsettings.search_ids) == [SearchIdSelection.imdbid]
    config.cfg.sync()


def testGetNewznabSettingById():
    nsettings = config.get_newznab_setting_by_id(1)
    config.set(nsettings.apikey, "123")

    assert config.get_newznab_setting_by_id(1).apikey.get() == "123"
    config.get_newznab_setting_by_id(1).apikey.set("456")
    config.get(nsettings.apikey, "456")


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
