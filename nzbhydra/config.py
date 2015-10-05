from enum import Enum

import profig

cfg = profig.Config(strict=True)


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


def get_settings_dict() -> dict:
    all_settings_dict = {}
    # Iterate over the enums which are our main categories
    for sectionname, sectionsettings in all_known_settings.items():
        if sectionname not in all_settings_dict.keys():
            all_settings_dict[sectionname] = {}
        for setting in sectionsettings:
            # And add the individual settings as dict with name as key and the whole setting as value
            setting_dict = setting.get_settings_dict()
            # And read and add the actual value
            setting_dict["value"] = cfg.section(setting.category).get(setting.name, setting.default)
            all_settings_dict[setting.category][setting.name] = setting_dict

    return all_settings_dict


def set_settings_from_dict(new_settings: dict):
    for sectionname, settings in new_settings.items():
        for settingname, setting in settings.items():
            cfg.section(sectionname)[settingname] = setting["value"]
    cfg.sync()


def register_settings(cls):
    for i in dir(cls):
        if not i.startswith("_"):
            setting = getattr(cls, i)
            setting.category = cls._path
            if cls._path not in all_known_settings.keys():
                all_known_settings[cls._path] = []
            all_known_settings[cls._path].append(setting)
            print("Initializing %s with default %s and valuetype %s" % (setting.name, setting.default, setting.valuetype))
            if setting.category not in cfg.sections():
                cfg.section(setting.category, create=True)
            cfg.section(setting.category).init(setting.name, setting.default, setting.valuetype, setting.comment)

    return cls


@register_settings
class MainSettings(object):
    _path = "main"

    """
    The main settings of our program.
    """
    host = Setting(name="host", default="127.0.0.1", valuetype=str, comment="Set to 0.0.0.0 to listen on all public IPs. If you do this you should enable SSL.")
    port = Setting(name="port", default=5050, valuetype=int, comment="Port to listen on.")
    debug = Setting(name="debug", default=False, valuetype=bool, comment="Enable debugging functions. Don't do this until you know why you're doing it.")
    ssl = Setting(name="ssl", default=True, valuetype=bool, comment="Use SSL. Strongly recommended if you access via a public network!")
    sslcert = Setting(name="sslcert", default="nzbhydra.crt", valuetype=str, comment="File name of the certificate to use for SSL.")
    sslkey = Setting(name="sslkey", default="nzbhydra.key", valuetype=str, comment="File name of the key to use for SSL.")
    logfile = Setting(name="logging.logfile", default="nzbhydra.log", valuetype=str, comment="File name (relative or absolute) of the log file.")
    logfilelevel = Setting(name="logging.logfile.level", default="INFO", valuetype=str, comment="Log level of the log file")  # TODO change to SelectionSetting
    consolelevel = Setting(name="logging.consolelevel", default="ERROR", valuetype=str, comment="Log level of the console. Only applies if run in console, obviously.")  # TODO change to SelectionSetting
    username = Setting(name="username", default="", valuetype=str, comment=None)
    password = Setting(name="password", default="", valuetype=str, comment=None)
    apikey = Setting(name="apikey", default="", valuetype=str, comment="API key for external tools to authenticate (newznab API)")
    enable_auth = Setting(name="enableAuth", default=True, valuetype=bool, comment="Select if you want to enable autorization via username / password.")


@register_settings
class ResultProcessingSettings(object):
    _path = "resultProcessing"
    """
    Settings which control how search results are processed.
    """
    duplicateSizeThresholdInPercent = Setting(name="duplicateSizeThresholdInPercent", default=0.1, valuetype=float, comment="If the size difference between two search entries with the same title is higher than this they won't be considered dplicates.")
    duplicateAgeThreshold = Setting(name="duplicateAgeThreshold", default=3600, valuetype=int, comment="If the age difference in seconds between two search entries with the same title is higher than this they won't be considered dplicates.")


@register_settings
class SearchingSettings(object):
    _path = "searching"
    """
    How searching is executed.
    """
    timeout = Setting(name="searching.timeout", default=5, valuetype=int, comment="Timeout when accessing providers.")
    ignoreTemporarilyDisabled = Setting(name="searching.ignoreTemporarilyDisabled", default=False, valuetype=bool, comment="Enable if you want to always call all enabled providers even if the connection previously failed.")
    allowQueryGeneration = Setting(name="searching.allowQueryGeneration", default="both", valuetype=str, comment=None)  # todo change to SelctionSetting


class NzbAccessTypeSelection(Enum):
    serve = SettingSelection(name="serve", comment=None)
    redirect = SettingSelection(name="redirect", comment=None)
    direct = SettingSelection(name="direct", comment=None)


class NzbAddingTypeSelection(Enum):
    link = SettingSelection(name="link", comment=None)
    nzb = SettingSelection(name="nzb", comment=None)


@register_settings
class SabnzbdSettings(object):
    _path = "sabnzbd"
    host = Setting(name="host", default="127.0.0.1", valuetype=str, comment=None)
    port = Setting(name="port", default=8086, valuetype=int, comment=None)
    ssl = Setting(name="ssl", default=False, valuetype=bool, comment=None)
    apikey = Setting(name="apikey", default="", valuetype=str, comment=None)
    username = Setting(name="username", default="", valuetype=str, comment=None)
    password = Setting(name="password", default="", valuetype=str, comment=None)


@register_settings
class NzbgetSettings(object):
    _path = "nzbget"
    host = Setting(name="host", default="127.0.0.1", valuetype=str, comment=None)
    port = Setting(name="port", default=6789, valuetype=int, comment=None)
    ssl = Setting(name="ssl", default=False, valuetype=bool, comment=None)
    username = Setting(name="username", default="nzbget", valuetype=str, comment=None)
    password = Setting(name="password", default="tegbzn6789", valuetype=str, comment=None)


@register_settings
class DownloaderSettings(object):
    _path = "downloader"
    # see comment
    nzbaccesstype = SelectSetting(name="nzbaccesstype", default=NzbAccessTypeSelection.serve, selections=NzbAccessTypeSelection, valuetype=str,
                                  comment="Determines how we provide access to NZBs  ""Serve"": Provide a link to NZBHydra via which the NZB is downloaded and returned. ""Redirect"": Provide a link to NZBHydra which redirects to the provider. ""Direct"": Create direct links (as returned by the provider=. Not recommended.")

    # see comment
    nzbAddingType = SelectSetting(name="nzbAddingType", default=NzbAddingTypeSelection.nzb, selections=NzbAddingTypeSelection, valuetype=str,
                                  comment="Determines how NZBs are added to downloaders. Either by sending a link to the downloader (""link"") or by sending the actual NZB (""nzb"").")


@register_settings
class ProviderBinsearchSettings(object):
    _path = "providers.binsearch"

    enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)


@register_settings
class ProviderNzbclubSettings(object):
    _path = "providers.nzbclub"

    enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)


@register_settings
class ProviderNzbindexSettings(object):
    _path = "providers.nzbindex"

    enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)


@register_settings
class ProviderWombleSettings(object):
    _path = "providers.womble"

    enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)


class SearchIdSelection(Enum):
    rid = SettingSelection(name="rid", comment=None)
    tvdbid = SettingSelection(name="tvdbid", comment=None)
    imdbid = SettingSelection(name="imdbid", comment=None)


# Convert list of SearchIdSelections to string and back
cfg.coercer.register("SearchIdSelectionList", lambda l: ",".join([x.name for x in l]), lambda string: [SearchIdSelection[x] for x in string.split(",")])


#I would like to have solved this more generically but got stuck. This way it works and I hope nobody uses / actually needs for than 6 of these.

@register_settings
class ProviderNewznab1Settings(object):
    _path = "providers.newznab.1"
    enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)
    ssl = Setting(name="ssl", default=True, valuetype=bool, comment=None)
    host = Setting(name="host", default=None, valuetype=str, comment=None)
    apikey = Setting(name="apikey", default=None, valuetype=str, comment=None)
    search_ids = MultiSelectSetting(name="search_ids", default=[], selections=SearchIdSelection, valuetype="SearchIdSelectionList", comment=None)


@register_settings
class ProviderNewznab2Settings(object):
    _path = "providers.newznab.2"
    enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)
    ssl = Setting(name="ssl", default=True, valuetype=bool, comment=None)
    host = Setting(name="host", default=None, valuetype=str, comment=None)
    apikey = Setting(name="apikey", default=None, valuetype=str, comment=None)
    search_ids = MultiSelectSetting(name="search_ids", default=[], selections=SearchIdSelection, valuetype="SearchIdSelectionList", comment=None)


@register_settings
class ProviderNewznab3Settings(object):
    _path = "providers.newznab.3"
    enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)
    ssl = Setting(name="ssl", default=True, valuetype=bool, comment=None)
    host = Setting(name="host", default=None, valuetype=str, comment=None)
    apikey = Setting(name="apikey", default=None, valuetype=str, comment=None)
    search_ids = MultiSelectSetting(name="search_ids", default=[], selections=SearchIdSelection, valuetype="SearchIdSelectionList", comment=None)


@register_settings
class ProviderNewznab4Settings(object):
    _path = "providers.newznab.4"
    enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)
    ssl = Setting(name="ssl", default=True, valuetype=bool, comment=None)
    host = Setting(name="host", default=None, valuetype=str, comment=None)
    apikey = Setting(name="apikey", default=None, valuetype=str, comment=None)
    search_ids = MultiSelectSetting(name="search_ids", default=[], selections=SearchIdSelection, valuetype="SearchIdSelectionList", comment=None)


@register_settings
class ProviderNewznab5Settings(object):
    _path = "providers.newznab.5"
    enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)
    ssl = Setting(name="ssl", default=True, valuetype=bool, comment=None)
    host = Setting(name="host", default=None, valuetype=str, comment=None)
    apikey = Setting(name="apikey", default=None, valuetype=str, comment=None)
    search_ids = MultiSelectSetting(name="search_ids", default=[], selections=SearchIdSelection, valuetype="SearchIdSelectionList", comment=None)


@register_settings
class ProviderNewznab6Settings(object):
    _path = "providers.newznab.6"
    enabled = Setting(name="enabled", default=True, valuetype=bool, comment=None)
    ssl = Setting(name="ssl", default=True, valuetype=bool, comment=None)
    host = Setting(name="host", default=None, valuetype=str, comment=None)
    apikey = Setting(name="apikey", default=None, valuetype=str, comment=None)
    search_ids = MultiSelectSetting(name="search_ids", default=[], selections=SearchIdSelection, valuetype="SearchIdSelectionList", comment=None)


def get_newznab_setting_by_id(id):
    return {
        "1": ProviderNewznab1Settings,
        "2": ProviderNewznab1Settings,
        "3": ProviderNewznab1Settings,
        "4": ProviderNewznab1Settings,
        "5": ProviderNewznab1Settings,
        "6": ProviderNewznab1Settings,
    }[id]
