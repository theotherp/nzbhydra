from enum import Enum

import profig


class SettingsType(Enum):
    """
    A type of setting that we can use. This mainly determines how it is presented in the GUI
    
    """
    Free = "free"
    Select = "selection"


class SettingsClass(object):
    """
    A setting that has a category, name, a default value, a value type and a comment. These will be delegated to profig to read and set the actual config.
    This structure allows us indexed access to the settings anywhere in the code without having to use dictionaries with potentially wrong string keys.
    It also allows us to collect all settings and create a dict with all settings which can be serialized and sent to the GUI.
    """

    def __init__(self, category, name, default, valuetype, comment=None):
        self.category = category
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
            "valuetype": self.valuetype,
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


class SelectSettingsClass(SettingsClass):
    """
    A setting which only allows one of a predefined number of options (see above).
    """

    def __init__(self, category, name, default, valuetype, selections, comment=None):
        super().__init__(category, name, default.value.name, valuetype, comment)
        self.selections = selections

    def get_settings_dict(self):
        d = super().get_settings_dict()
        d["selections"] = [{"name": x.value.name, "comment": x.value.comment} for x in self.selections]
        return d

    def get_setting_type(self):
        return SettingsType.Select


cfg = profig.Config()

all_known_settings = []


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
    return cfg.section(setting.value.category).get(setting.value.name, default=default if default is not None else setting.value.default)


def set(setting, value):
    cfg.section(setting.value.category)[setting.value.name] = value


def isSettingSelection(setting: SettingsClass, compare: SettingSelection) -> bool:
    return get(setting) == compare.value.name


def get_settings_dict():
    all_settings_dict = {}
    # Iterate over the enums which are our main categories
    for setting in all_known_settings:
        if setting.category not in all_settings_dict.keys():
            all_settings_dict[setting.category] = {}
        # And add the individual settings as dict with name as key and the whole setting as value
        setting_dict = setting.get_settings_dict()
        # And read and add the actual value
        setting_dict["value"] = cfg.section(setting.category).get(setting.name, setting.default)
        all_settings_dict[setting.category][setting.name] = setting_dict

    return all_settings_dict


def register_settings(cls):
    for i in cls:
        setting = i.value
        all_known_settings.append(setting)
        print("Initializing %s with default %s and valuetype %s" % (setting.name, setting.default, setting.valuetype))
        cfg.section(setting.category).init(setting.name, setting.default, setting.valuetype, setting.comment)

    return cls


@register_settings
class MainSettings(Enum):
    """
    The main settings of our program.
    """
    host = SettingsClass(category="main", name="host", default="127.0.0.1", valuetype=str, comment=None)
    port = SettingsClass(category="main", name="port", default=5050, valuetype=int, comment=None)
    logfile = SettingsClass(category="main", name="logging.logfile", default="nzbhydra.log", valuetype=str, comment=None)
    logfilelevel = SettingsClass(category="main", name="logging.logfile.level", default="INFO", valuetype=str, comment=None)
    consolelevel = SettingsClass(category="main", name="logging.consolelevel", default="ERROR", valuetype=str, comment=None)
    username = SettingsClass(category="main", name="username", default="", valuetype=str, comment=None)
    password = SettingsClass(category="main", name="password", default="", valuetype=str, comment=None)
    apikey = SettingsClass(category="main", name="apikey", default="", valuetype=str, comment=None)
    enable_auth = SettingsClass(category="main", name="enableAuth", default="", valuetype=bool, comment=None)


@register_settings
class ResultProcessingSettings(Enum):
    """
    Settings which control how search results are processed.
    """
    duplicateSizeThresholdInPercent = SettingsClass(category="resultProcessing", name="duplicateSizeThresholdInPercent", default=0.1, valuetype=float)
    duplicateAgeThreshold = SettingsClass(category="resultProcessing", name="duplicateAgeThreshold", default=3600, valuetype=int)


@register_settings
class SearchingSettings(Enum):
    """
    How searching is executed.
    """
    timeout = SettingsClass(category="searching", name="searching.timeout", default=5, valuetype=int, comment=None)
    ignoreTemporarilyDisabled = SettingsClass(category="searching", name="searching.ignoreTemporarilyDisabled", default=False, valuetype=bool, comment=None)
    allowQueryGeneration = SettingsClass(category="searching", name="searching.allowQueryGeneration", default="both", valuetype=str, comment=None)


class NzbAccessTypeSelection(Enum):
    serve = SettingSelection(name="serve", comment=None)
    redirect = SettingSelection(name="redirect", comment=None)
    direct = SettingSelection(name="direct", comment=None)


class NzbAddingTypeSelection(Enum):
    link = SettingSelection(name="link", comment=None)
    nzb = SettingSelection(name="nzb", comment=None)


@register_settings
class DownloaderSettings(Enum):
    # sabnzbd setings
    host = SettingsClass(category="downloader", name="sabnzbd.host", default="127.0.0.1", valuetype=str, comment=None)
    port = SettingsClass(category="downloader", name="sabnzbd.port", default=8086, valuetype=int, comment=None)

    # see comment
    nzbaccesstype = SelectSettingsClass(category="downloader", name="nzbaccesstype", default=NzbAccessTypeSelection.serve, selections=NzbAccessTypeSelection, valuetype=str,
                                        comment="Determines how we provide access to NZBs  ""Serve"": Provide a link to NZBHydra via which the NZB is downloaded and returned. ""Redirect"": Provide a link to NZBHydra which redirects to the provider. ""Direct"": Create direct links (as returned by the provider=. Not recommended.")

    # see comment
    nzbAddingType = SelectSettingsClass(category="downloader", name="nzbAddingType", default=NzbAddingTypeSelection.nzb, selections=NzbAddingTypeSelection, valuetype=str,
                                        comment="Determines how NZBs are added to downloaders. Either by sending a link to the downloader (""link"") or by sending the actual NZB (""nzb"").")
