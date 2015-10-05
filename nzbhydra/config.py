from enum import Enum

import profig

cfg = profig.Config(strict=False)


def a(l):
    return ",".join([x.name for x in l])


def b(string):
    if isinstance(string, list):
        return string #Haven't found out yet why this gets called with a list but it does, so we just return it 
    return [SearchIdSelection[x] for x in string.split(",")] if string else []


cfg.coercer.register("SearchIdSelectionList", lambda l: a(l), lambda string: b(string))


class SettingsType(Enum):
    """
    A type of setting that we can use. This mainly determines how it is presented in the GUI
    
    """
    Free = "free"
    Select = "selection"
    Multi = "multi"


class Setting(object):
    """
    A setting that has a category, name, a default value, a value type and a comment. These will be delegated to profig to read and set the actual config.
    This structure allows us indexed access to the settings anywhere in the code without having to use dictionaries with potentially wrong string keys.
    It also allows us to collect all settings and create a dict with all settings which can be serialized and sent to the GUI.
    """

    def __init__(self, name, default, valuetype, comment=None):
        self.name = name
        self.default = default
        self.valuetype = valuetype
        self.comment = comment
        self.category = None  # Is dynamically filled by register_settings later

    def get_settings_dict(self):
        """
        Return the setting definition as a dict, without the actual value.        
        :return: 
        """
        return {
            "name": self.name,
            "default": self.default,
            "valuetype": self.valuetype if isinstance(self.valuetype, str) else self.valuetype.__name__,
            "comment": self.comment,
            "settingtype": self.get_setting_type().value
        }

    def get_setting_type(self):
        return SettingsType.Free

    def get(self):
        return cfg.section(self.category).get(self.name)

    def get_with_default(self, default):
        return cfg.section(self.category).get(self.name, default=default if default is not None else self.default)

    def set(self, value):
        cfg.section(self.category)[self.name] = value


class SettingSelection(object):
    """
    An option for a selection setting. They're added to the SelectSetting and only one of these are allowed to be set to each setting they're assigned to.
    """

    def __init__(self, name, comment):
        self.name = name
        self.comment = comment


class SelectSetting(Setting):
    """
    A setting which only allows one of a predefined number of options (see above).
    """

    def __init__(self, name, default, valuetype, selections, comment=None):
        super().__init__(name, default.value.name, valuetype, comment)
        self.selections = selections

    def get_settings_dict(self):
        d = super().get_settings_dict()
        d["selections"] = [{"name": x.value.name, "comment": x.value.comment} for x in self.selections]
        return d

    def get_setting_type(self):
        return SettingsType.Select

    def isSetting(self, compare: SettingSelection) -> bool:
        return get(self) == compare.name


class MultiSelectSetting(Setting):
    """
    A setting which only allows multiselection of a predefined number of options (see above).
    """

    def __init__(self, name, default, valuetype, selections, comment=None):
        super().__init__(name, default, valuetype, comment)
        self.selections = selections

    def get_settings_dict(self):
        d = super().get_settings_dict()
        d["selections"] = [{"name": x.value.name, "comment": x.value.comment} for x in self.selections]
        return d

    def get_setting_type(self):
        return SettingsType.Multi


all_known_settings = {}


def load(filename):
    global cfg
    cfg.read(filename)
    # Manually set the source to this settings file so that when syncing the settings are written back. If we don't do this it loads the settings but doesn't write them back. Or we would need to store the
    # settings filename and call write(filename)
    cfg.sources = [filename]
    cfg.sync()


def init(path, value, type, comment=None):
    global cfg
    cfg.init(path, value, type, comment)


def get(setting, default=None):
    return cfg.section(setting.category).get(setting.name, default=default if default is not None else setting.default)


def set(setting, value):
    cfg.section(setting.category)[setting.name] = value


def isSettingSelection(setting: Setting, compare: SettingSelection) -> bool:
    return get(setting) == compare.name


def traverse_dict_and_set(d, l, newval, keep=False):
    """
    Traverses the dict by the list of values which describe the path and set the new value.
    Example: d = {"a": {"b": {"c": "newval"}}} with l=["a","b","c"], will set d["a"]["b"]["c"] = "newval" 
    :param d: 
    :param l: 
    :param newval: 
    ;param keep; If true and the key is already set it won't be overwritten
    :return: the updated dictionary
    """
    if len(l) == 1:
        if l[0] not in d.keys() or not keep:
            d[l[0]] = newval
    else:
        d[l[0]] = traverse_dict_and_set(d[l[0]], l[1:], newval, keep)
    return d


def traverse_dict_and_get(d, l):
    """
    Traverses the dict and gets the value described by the path in the list.
    Example: d = {"a": {"b": {"c": "val"}}} with l=["a","b","c"], will retun "val"  
    :param d: 
    :param l: 
    :return: value described by path
    """
    if len(l) == 1:
        return d[l[0]]
    else:
        return traverse_dict_and_get(d[l[0]], l[1:])


def traverse_dict_and_add_to_list(d, l, toadd):
    """
    Traverses the dict to the list described by the path and adds the element to that list. If no list exists it will be created.
    :rtype : the updated dictionary
    """
    if len(l) == 1:
        if l[0] not in d.keys():
            d[l[0]] = []
        d[l[0]].append(toadd)
        return d
    else:
        if l[0] not in d.keys():
            d[l[0]] = {}
        d[l[0]] = traverse_dict_and_add_to_list(d[l[0]], l[1:], toadd)
    return d


def traverse_dict_and_add_to_dict(d, l, key, value):
    if len(l) == 1:
        if l[0] not in d.keys():
            d[l[0]] = {}
        d[l[0]][key] = value
        return d
    else:
        if l[0] not in d.keys():
            d[l[0]] = {}
        d[l[0]] = traverse_dict_and_add_to_dict(d[l[0]], l[1:], key, value)
    return d


def replace_setting_with_dict(d: dict):
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = replace_setting_with_dict(d[k])
        if isinstance(v, Setting):
            d[k] = v.get_settings_dict()
            d[k]["value"] = v.get()
    return d


def get_settings_dict() -> dict:
    all_settings_dict = all_known_settings.copy()
    all_settings_dict = replace_setting_with_dict(all_settings_dict)

    return all_settings_dict


def traverse_settings_dict_and_transfer(d, section):
    """
    Traverses the given dict and sets the settings to the new values stored in the dict.
    :param section: The section under which the upper level of settings is stored. Should be root cfg for the first call
    :param d: 
    """
    for k, v in d.items():
        if isinstance(v, dict):
            if "value" in v.keys() and "name" in v.keys():  # If we have a "value" and a "name" key we consider this a setting from which we transfer the value to the settings. 
                section[k] = v["value"]
            else:
                traverse_settings_dict_and_transfer(v, section.section(k))  # Otherwise it's just a section with more dicts of sections (we don't support a mix of sections and settings on the same parent path) 


def set_settings_from_dict(new_settings: dict):
    traverse_settings_dict_and_transfer(new_settings, cfg)
    cfg.sync()


def register_settings(cls):
    for i in dir(cls):
        if not i.startswith("_"):
            setting = getattr(cls, i)
            setting.category = cls._path

            path = setting.category
            sectionnames = path.split(".")
            section = cfg
            for s in sectionnames:
                section = section.section(s, create=True)
            print("Initializing %s.%s with default %s and valuetype %s" % (setting.category, setting.name, setting.default, setting.valuetype))
            section.init(setting.name, setting.default, setting.valuetype, setting.comment)

            traverse_dict_and_add_to_dict(all_known_settings, sectionnames, setting.name, setting)

            # traverse_dict_and_set(all_known_settings, sectionnames, setting)

    return cls


class SettingsCategory(object):
    def __init__(self):
        pass


class MainSettings(SettingsCategory):
    """
    The main settings of our program.
    """

    def __init__(self):
        super().__init__()
        self._path = "main"
        self.host = Setting(name="host", default="127.0.0.1", valuetype=str, comment="Set to 0.0.0.0 to listen on all public IPs. If you do this you should enable SSL.")
        self.port = Setting(name="port", default=5050, valuetype=int, comment="Port to listen on.")
        self.debug = Setting(name="debug", default=False, valuetype=bool, comment="Enable debugging functions. Don't do this until you know why you're doing it.")
        self.ssl = Setting(name="ssl", default=True, valuetype=bool, comment="Use SSL. Strongly recommended if you access via a public network!")
        self.sslcert = Setting(name="sslcert", default="nzbhydra.crt", valuetype=str, comment="File name of the certificate to use for SSL.")
        self.sslkey = Setting(name="sslkey", default="nzbhydra.key", valuetype=str, comment="File name of the key to use for SSL.")
        self.logfile = Setting(name="logging.logfile", default="nzbhydra.log", valuetype=str, comment="File name (relative or absolute) of the log file.")
        self.logfilelevel = Setting(name="logging.logfile.level", default="INFO", valuetype=str, comment="Log level of the log file")  # TODO change to SelectionSetting
        self.consolelevel = Setting(name="logging.consolelevel", default="ERROR", valuetype=str, comment="Log level of the console. Only applies if run in console, obviously.")  # TODO change to SelectionSetting
        self.username = Setting(name="username", default="", valuetype=str, comment=None)
        self.password = Setting(name="password", default="", valuetype=str, comment=None)
        self.apikey = Setting(name="apikey", default="", valuetype=str, comment="API key for external tools to authenticate (newznab API)")
        self.enable_auth = Setting(name="enableAuth", default=True, valuetype=bool, comment="Select if you want to enable autorization via username / password.")
        register_settings(self)


mainSettings = MainSettings()


class ResultProcessingSettings(SettingsCategory):
    """
    Settings which control how search results are processed.
    """

    def __init__(self):
        super().__init__()
        self._path = "resultProcessing"
        self.duplicateSizeThresholdInPercent = Setting(name="duplicateSizeThresholdInPercent", default=0.1, valuetype=float, comment="If the size difference between two search entries with the same title is higher than this they won't be considered dplicates.")
        self.duplicateAgeThreshold = Setting(name="duplicateAgeThreshold", default=3600, valuetype=int, comment="If the age difference in seconds between two search entries with the same title is higher than this they won't be considered dplicates.")
        register_settings(self)


resultProcessingSettings = ResultProcessingSettings()


class SearchingSettings(SettingsCategory):
    """
    How searching is executed.
    """

    def __init__(self):
        super().__init__()
        self._path = "searching"
        self.timeout = Setting(name="searching.timeout", default=5, valuetype=int, comment="Timeout when accessing providers.")
        self.ignoreTemporarilyDisabled = Setting(name="searching.ignoreTemporarilyDisabled", default=False, valuetype=bool, comment="Enable if you want to always call all enabled providers even if the connection previously failed.")
        self.allowQueryGeneration = Setting(name="searching.allowQueryGeneration", default="both", valuetype=str, comment=None)  # todo change to SelctionSetting
        register_settings(self)


searchingSettings = SearchingSettings()


class NzbAccessTypeSelection(Enum):
    serve = SettingSelection(name="serve", comment=None)
    redirect = SettingSelection(name="redirect", comment=None)
    direct = SettingSelection(name="direct", comment=None)


class NzbAddingTypeSelection(Enum):
    link = SettingSelection(name="link", comment=None)
    nzb = SettingSelection(name="nzb", comment=None)


class SabnzbdSettings(SettingsCategory):
    def __init__(self):
        super().__init__()
        self._path = "sabnzbd"
        self.host = Setting(name="host", default="127.0.0.1", valuetype=str, comment=None)
        self.port = Setting(name="port", default=8086, valuetype=int, comment=None)
        self.ssl = Setting(name="ssl", default=False, valuetype=bool, comment=None)
        self.apikey = Setting(name="apikey", default="", valuetype=str, comment=None)
        self.username = Setting(name="username", default="", valuetype=str, comment=None)
        self.password = Setting(name="password", default="", valuetype=str, comment=None)
        register_settings(self)


sabnzbdSettings = SabnzbdSettings()


class NzbgetSettings(SettingsCategory):
    def __init__(self):
        super().__init__()
        self._path = "nzbget"
        self.host = Setting(name="host", default="127.0.0.1", valuetype=str, comment=None)
        self.port = Setting(name="port", default=6789, valuetype=int, comment=None)
        self.ssl = Setting(name="ssl", default=False, valuetype=bool, comment=None)
        self.username = Setting(name="username", default="nzbget", valuetype=str, comment=None)
        self.password = Setting(name="password", default="tegbzn6789", valuetype=str, comment=None)
        register_settings(self)


nzbgetSettings = NzbgetSettings()


class DownloaderSettings(SettingsCategory):
    def __init__(self):
        super().__init__()
        self._path = "downloader"
        self.nzbaccesstype = SelectSetting(name="nzbaccesstype", default=NzbAccessTypeSelection.serve, selections=NzbAccessTypeSelection, valuetype=str,
                                           comment="Determines how we provide access to NZBs  ""Serve"": Provide a link to NZBHydra via which the NZB is downloaded and returned. ""Redirect"": Provide a link to NZBHydra which redirects to the provider. ""Direct"": Create direct links (as returned by the provider=. Not recommended.")
        self.nzbAddingType = SelectSetting(name="nzbAddingType", default=NzbAddingTypeSelection.nzb, selections=NzbAddingTypeSelection, valuetype=str,
                                           comment="Determines how NZBs are added to downloaders. Either by sending a link to the downloader (""link"") or by sending the actual NZB (""nzb"").")
        register_settings(self)


downloaderSettings = DownloaderSettings()


class ProviderSettings(SettingsCategory):
    def __init__(self):
        super().__init__()
        self.enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)
        self.dbid = Setting(name="dbid", default=0, valuetype=int, comment=None)  # TODO: hide in GUI


class ProviderBinsearchSettings(ProviderSettings):
    def __init__(self):
        super(ProviderBinsearchSettings, self).__init__()
        self.dbid = Setting(name="dbid", default=1, valuetype=int, comment=None)  # TODO: hide in GUI
        self._path = "providers.binsearch"
        register_settings(self)


providerBinsearchSettings = ProviderBinsearchSettings()


class ProviderNzbclubSettings(ProviderSettings):
    def __init__(self):
        super(ProviderSettings, self).__init__()
        self._path = "providers.nzbclub"
        self.dbid = Setting(name="dbid", default=2, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


providerNzbclubSettings = ProviderNzbclubSettings


class ProviderNzbindexSettings(ProviderSettings):
    def __init__(self):
        super(ProviderSettings, self).__init__()
        self._path = "providers.nzbindex"
        self.dbid = Setting(name="dbid", default=3, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


providerNzbindexSettings = ProviderNzbindexSettings()


class ProviderWombleSettings(ProviderSettings):
    def __init__(self):
        super().__init__()
        self._path = "providers.womble"
        self.dbid = Setting(name="dbid", default=4, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


class SearchIdSelection(Enum):
    rid = SettingSelection(name="rid", comment=None)
    tvdbid = SettingSelection(name="tvdbid", comment=None)
    imdbid = SettingSelection(name="imdbid", comment=None)


# I would like to have solved this more generically but got stuck. This way it works and I hope nobody uses / actually needs for than 6 of these.
# As we only need the attributes to contain information on what setting to get we can create instances and pass them around and still don't need
# to worry about synchronization of settings

class ProviderNewznabSettings(ProviderSettings):
    def __init__(self):
        super(ProviderNewznabSettings, self).__init__()
        self.ssl = Setting(name="ssl", default=True, valuetype=bool, comment=None)
        self.host = Setting(name="host", default=None, valuetype=str, comment=None)
        self.apikey = Setting(name="apikey", default=None, valuetype=str, comment=None)
        self.search_ids = MultiSelectSetting(name="search_ids", default=[SearchIdSelection.imdbid, SearchIdSelection.rid, SearchIdSelection.tvdbid], selections=SearchIdSelection, valuetype="SearchIdSelectionList", comment=None)


class ProviderNewznab1Settings(ProviderNewznabSettings):
    def __init__(self):
        super().__init__()
        self._path = "providers.newznab.1"
        self.dbid = Setting(name="dbid", default=5, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


class ProviderNewznab2Settings(ProviderNewznabSettings):
    def __init__(self):
        super().__init__()
        self._path = "providers.newznab.2"
        self.dbid = Setting(name="dbid", default=6, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


class ProviderNewznab3Settings(ProviderNewznabSettings):
    def __init__(self):
        super().__init__()
        self._path = "providers.newznab.3"
        self.dbid = Setting(name="dbid", default=7, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


class ProviderNewznab4Settings(ProviderNewznabSettings):
    def __init__(self):
        super().__init__()
        self._path = "providers.newznab.4"
        self.dbid = Setting(name="dbid", default=8, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


class ProviderNewznab5Settings(ProviderNewznabSettings):
    def __init__(self):
        super().__init__()
        self._path = "providers.newznab.5"
        self.dbid = Setting(name="dbid", default=9, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


class ProviderNewznab6Settings(ProviderNewznabSettings):
    def __init__(self):
        super().__init__()
        self._path = "providers.newznab.6"
        self.dbid = Setting(name="dbid", default=10, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


class ProviderNewznab7Settings(ProviderNewznabSettings):
    def __init__(self):
        super().__init__()
        self._path = "providers.newznab.7"
        self.dbid = Setting(name="dbid", default=11, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


class ProviderNewznab8Settings(ProviderNewznabSettings):
    def __init__(self):
        super().__init__()
        self._path = "providers.newznab.8"
        self.dbid = Setting(name="dbid", default=12, valuetype=int, comment=None)  # TODO: hide in GUI
        register_settings(self)


def get_newznab_setting_by_id(id):
    id = str(id)
    return {
        "1": ProviderNewznab1Settings(),
        "2": ProviderNewznab2Settings(),
        "3": ProviderNewznab3Settings(),
        "4": ProviderNewznab4Settings(),
        "5": ProviderNewznab5Settings(),
        "6": ProviderNewznab6Settings(),
        "7": ProviderNewznab5Settings(),
        "8": ProviderNewznab6Settings(),
    }[id]
