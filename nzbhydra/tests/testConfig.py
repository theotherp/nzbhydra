from pprint import pprint
from nzbhydra import config
from nzbhydra.config import mainSettings, providerSettings, SettingType, ProviderNewznabSettings

print("Loading config from testsettings.cfg")


# shutil.copy("testsettings.cfg.orig", "testsettings.cfg")
# config.load("testsettings.cfg")


def testThatGetAndSetWork():
    # Simple get and set
    assert mainSettings.host.get() == "127.0.0.1"
    mainSettings.host.set("192.168.0.1")
    assert mainSettings.host.get() == "192.168.0.1"
    mainSettings.host.set("127.0.0.1")  # Just set back

    # Setting in subcategory
    assert mainSettings.logging.logfilelevel.get() == "INFO"

    # Setting with a SettingType  
    assert mainSettings.password.setting_type == SettingType.password

    assert providerSettings.binsearch.name.get() == "binsearch"


def testThatWritingSettingsWorks():
    mainSettings.port.set(5053)
    config.save("testsettings.cfg")
    mainSettings.port.set(5054)  # Set to another port
    config.load("testsettings.cfg")
    assert mainSettings.port.get() == 5053


def testNewznabProviders():
    providerSettings.newznab1.host.set("http://127.0.0.1")
    config.save("testsettings.cfg")
    providerSettings.newznab1.host.set("http://192.168.0.1")
    config.load("testsettings.cfg")
    assert providerSettings.newznab1.host.get() == "http://127.0.0.1" 


def testSchema():
    assert mainSettings.host.path == "main.host"
    schema = config.get_settings_schema()
    form = config.get_settings_form()
    print(schema)
    pass

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
