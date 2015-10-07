import profig

cfg = profig.Config(strict=True)


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
        }

    def get(self):
        return cfg.section(self.category).get(self.name)

    def get_with_default(self, default):
        return cfg.section(self.category).get(self.name, default=default if default is not None else self.default)

    def set(self, value):
        cfg.section(self.category)[self.name] = value

    def __str__(self):
        return "%s: %s" % (self.name, self.get())


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


def replace_lists_with_strings(d):
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = replace_lists_with_strings(d[k])
        if isinstance(v, list):
            d[k] = ",".join(v)
    return d


def get_settings_as_dict_without_lists() -> dict:
    settings_dict = cfg.as_dict(flat=True, dict_type=dict)
    return replace_lists_with_strings(settings_dict)


def set_settings_from_dict(new_settings: dict):
    for cat in new_settings.items():
        for setting in cat[1].items():
            cfg.section(cat[0])[setting[0]] = setting[1]

    cfg.sync()


def get_s(d):
    subdic = {}
    for k, v in d.items():
        if isinstance(v, dict):
            subdic[k] = {"type": "object", "title": k, "properties": get_s(v)}
        else:
            subdic[k] = {"type": "string"} # to expand
    return subdic


def get_settings_schema():
    schema = {}
    schema["type"] = "object"
    properties = {}
    settingsdict = cfg.as_dict(dict_type=dict)
    settingsdict = replace_lists_with_strings(settingsdict)
    
    schema["properties"] = get_s(settingsdict)
    return schema


class SettingsCategory(object):
    _path = ""

    def __init__(self):
        cfg.section(self._path, create=True)

    def addSetting(self, name, default, valuetype, comment):
        setting_path = "%s.%s" % (self._path, name)
        cfg.init(setting_path, default, valuetype)
        if self._path not in all_known_settings.keys():
            all_known_settings[self._path] = []

        setting = Setting(name, default, valuetype, comment)
        setting.category = self._path
        return setting


class CacheTypeSelection(object):
    file = "file"
    memory = "memory"


class MainSettings(SettingsCategory):
    """
    The main settings of our program.
    """

    def __init__(self):
        super().__init__()
        self._path = "main"
        self.host = self.addSetting(name="host", default="127.0.0.1", valuetype=str, comment="Set to 0.0.0.0 to listen on all public IPs. If you do this you should enable SSL.")
        self.port = self.addSetting(name="port", default=5050, valuetype=int, comment="Port to listen on.")
        self.debug = self.addSetting(name="debug", default=False, valuetype=bool, comment="Enable debugging functions. Don't do this until you know why you're doing it.")
        self.ssl = self.addSetting(name="ssl", default=True, valuetype=bool, comment="Use SSL. Strongly recommended if you access via a public network!")
        self.sslcert = self.addSetting(name="sslcert", default="nzbhydra.crt", valuetype=str, comment="File name of the certificate to use for SSL.")
        self.sslkey = self.addSetting(name="sslkey", default="nzbhydra.key", valuetype=str, comment="File name of the key to use for SSL.")
        self.logfilename = self.addSetting(name="logging.logfile.name", default="nzbhydra.log", valuetype=str, comment="File name (relative or absolute) of the log file.")
        self.logfilelevel = self.addSetting(name="logging.logfile.level", default="INFO", valuetype=str, comment="Log level of the log file")  # TODO change to SelectionSetting
        self.consolelevel = self.addSetting(name="logging.consolelevel", default="ERROR", valuetype=str, comment="Log level of the console. Only applies if run in console, obviously.")  # TODO change to SelectionSetting
        self.username = self.addSetting(name="username", default="", valuetype=str, comment=None)
        self.password = self.addSetting(name="password", default="", valuetype=str, comment=None)
        self.apikey = self.addSetting(name="apikey", default="", valuetype=str, comment="API key for external tools to authenticate (newznab API)")
        self.enable_auth = self.addSetting(name="enableAuth", default=True, valuetype=bool, comment="Select if you want to enable autorization via username / password.")
        self.cache_enabled = self.addSetting(name="enableCache", default=True, valuetype=bool, comment="Select if you want to enable cache results.")
        self.cache_type = self.addSetting(name="cacheType", default=CacheTypeSelection.memory, valuetype=str, comment="Select the of cache you want to use.")
        self.cache_timeout = self.addSetting(name="cacheTimeout", default=30, valuetype=int, comment="Cache timeout in minutes.")
        self.cache_threshold = self.addSetting(name="cachethreshold", default=25, valuetype=int, comment="Maximum amount of cached items.")
        self.cache_folder = self.addSetting(name="cacheFolder", default="cache", valuetype=str, comment="Name of the folder where cache items should be stored. Only applies for file cache.")


mainSettings = MainSettings()


class ResultProcessingSettings(SettingsCategory):
    """
    Settings which control how search results are processed.
    """

    def __init__(self):
        super().__init__()
        self._path = "resultProcessing"
        self.duplicateSizeThresholdInPercent = self.addSetting(name="duplicateSizeThresholdInPercent", default=0.1, valuetype=float, comment="If the size difference between two search entries with the same title is higher than this they won't be considered dplicates.")
        self.duplicateAgeThreshold = self.addSetting(name="duplicateAgeThreshold", default=3600, valuetype=int, comment="If the age difference in seconds between two search entries with the same title is higher than this they won't be considered dplicates.")


resultProcessingSettings = ResultProcessingSettings()


class SearchingSettings(SettingsCategory):
    """
    How searching is executed.
    """

    def __init__(self):
        super().__init__()
        self._path = "searching"
        self.timeout = self.addSetting(name="timeout", default=5, valuetype=int, comment="Timeout when accessing providers.")
        self.ignoreTemporarilyDisabled = self.addSetting(name="ignoreTemporarilyDisabled", default=False, valuetype=bool, comment="Enable if you want to always call all enabled providers even if the connection previously failed.")
        self.allowQueryGeneration = self.addSetting(name="allowQueryGeneration", default="both", valuetype=str, comment=None)  # todo change to SelctionSetting


searchingSettings = SearchingSettings()


class NzbAccessTypeSelection(object):
    serve = "serve"
    redirect = "redirect"
    direct = "direct"


class NzbAddingTypeSelection(object):
    link = "link"
    nzb = "nzb"


class SabnzbdSettings(SettingsCategory):
    def __init__(self):
        super().__init__()
        self._path = "downloader.sabnzbd"
        self.host = self.addSetting(name="host", default="127.0.0.1", valuetype=str, comment=None)
        self.port = self.addSetting(name="port", default=8086, valuetype=int, comment=None)
        self.ssl = self.addSetting(name="ssl", default=False, valuetype=bool, comment=None)
        self.apikey = self.addSetting(name="apikey", default=None, valuetype=str, comment=None)
        self.username = Setting(name="username", default=None, valuetype=str, comment=None)
        self.password = self.addSetting(name="password", default=None, valuetype=str, comment=None)


sabnzbdSettings = SabnzbdSettings()


class NzbgetSettings(SettingsCategory):
    def __init__(self):
        super().__init__()
        self._path = "downloader.nzbget"
        self.host = self.addSetting(name="host", default="127.0.0.1", valuetype=str, comment=None)
        self.port = self.addSetting(name="port", default=6789, valuetype=int, comment=None)
        self.ssl = self.addSetting(name="ssl", default=False, valuetype=bool, comment=None)
        self.username = self.addSetting(name="username", default="nzbget", valuetype=str, comment=None)
        self.password = self.addSetting(name="password", default="tegbzn6789", valuetype=str, comment=None)


nzbgetSettings = NzbgetSettings()


class DownloaderSelection(object):
    sabnzbd = "sabnzbd"
    nzbget = "nzbget"


class DownloaderSettings(SettingsCategory):
    def __init__(self):
        super().__init__()
        self._path = "downloader"
        self.nzbaccesstype = self.addSetting(name="nzbaccesstype", default=NzbAccessTypeSelection.serve, valuetype=str,
                                             comment="Determines how we provide access to NZBs  ""Serve"": Provide a link to NZBHydra via which the NZB is downloaded and returned. ""Redirect"": Provide a link to NZBHydra which redirects to the provider. ""Direct"": Create direct links (as returned by the provider=. Not recommended.")
        self.nzbAddingType = self.addSetting(name="nzbAddingType", default=NzbAddingTypeSelection.nzb, valuetype=str,
                                             comment="Determines how NZBs are added to downloaders. Either by sending a link to the downloader (""link"") or by sending the actual NZB (""nzb"").")
        self.downloader = self.addSetting(name="downloader", default=DownloaderSelection.nzbget, valuetype=str, comment="Choose the downloader you want to use when adding NZBs via the GUI.")


downloaderSettings = DownloaderSettings()


class SearchIdSelection(object):
    rid = "rid"
    tvdbid = "tvdbid"
    imdbid = "imdbid"


class GenerateQueriesSelection(object):
    internal = "internal"
    external = "external"
    both = "both"
    never = "never"


class ProviderSettings(SettingsCategory):
    def __init__(self):
        super().__init__()
        self.name = self.addSetting(name="name", default=None, valuetype=str, comment="Name of the provider. Used when displayed. If changed all references, history and stats get lost!")
        self.host = self.addSetting(name="host", default=None, valuetype=str, comment="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.enabled = self.addSetting(name="enabled", default=True, valuetype=bool, comment="")
        self.search_ids = self.addSetting(name="search_ids", default=[], valuetype=list, comment=None)
        self.generate_queries = self.addSetting(name="generate_queries", default=GenerateQueriesSelection.internal, valuetype=str, comment=None)


class ProviderBinsearchSettings(ProviderSettings):
    def __init__(self):
        self._path = "providers.binsearch"
        super(ProviderBinsearchSettings, self).__init__()
        self.host = self.addSetting(name="host", default="https://binsearch.com", valuetype=str, comment="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = self.addSetting(name="name", default="binsearch", valuetype=str, comment="Name of the provider. Used when displayed. If changed all references, history and stats get lost!")


providerBinsearchSettings = ProviderBinsearchSettings()


class ProviderNzbclubSettings(ProviderSettings):
    def __init__(self):
        self._path = "providers.nzbclub"
        super(ProviderNzbclubSettings, self).__init__()
        self.host = self.addSetting(name="host", default="http://nzbclub.com", valuetype=str, comment="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = self.addSetting(name="name", default="nzbclub", valuetype=str, comment="Name of the provider. Used when displayed. If changed all references, history and stats get lost!")


providerNzbclubSettings = ProviderNzbclubSettings()


class ProviderNzbindexSettings(ProviderSettings):
    def __init__(self):
        self._path = "providers.nzbindex"
        super(ProviderNzbindexSettings, self).__init__()
        self.host = self.addSetting(name="host", default="https://nzbindex.com", valuetype=str, comment="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = self.addSetting(name="name", default="nzbindex", valuetype=str, comment="Name of the provider. Used when displayed. If changed all references, history and stats get lost!")


providerNzbindexSettings = ProviderNzbindexSettings()


class ProviderWombleSettings(ProviderSettings):
    def __init__(self):
        self._path = "providers.womble"
        super(ProviderWombleSettings, self).__init__()
        self.host = self.addSetting(name="womble", default="https://newshost.co.za", valuetype=str, comment="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = self.addSetting(name="name", default="womble", valuetype=str, comment="Name of the provider. Used when displayed. If changed all references, history and stats get lost!")

        # todo make settings hideable in GUI and hide generate_queries for this (and others which don't match the particular provider)


providerWombleSettings = ProviderWombleSettings()


# I would like to have solved this more generically but got stuck. This way it works and I hope nobody uses / actually needs for than 6 of these.
# As we only need the attributes to contain information on what setting to get we can create instances and pass them around and still don't need
# to worry about synchronization of settings

class ProviderNewznabSettings(ProviderSettings):
    def __init__(self):
        super(ProviderNewznabSettings, self).__init__()
        self.apikey = self.addSetting(name="apikey", default=None, valuetype=str, comment=None)
        self.search_ids = self.addSetting(name="search_ids", default=[SearchIdSelection.imdbid, SearchIdSelection.rid, SearchIdSelection.tvdbid], valuetype=list, comment=None)
        self.enabled = self.addSetting(name="enabled", default=False, valuetype=bool, comment="")  # Disable by default because we have no meaningful initial data


class ProviderNewznab1Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab1"
        super().__init__()


providerNewznab1Settings = ProviderNewznab1Settings()


class ProviderNewznab2Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab2"
        super().__init__()


providerNewznab2Settings = ProviderNewznab2Settings()


class ProviderNewznab3Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab3"
        super().__init__()


providerNewznab3Settings = ProviderNewznab3Settings()


class ProviderNewznab4Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab4"
        super().__init__()


providerNewznab4Settings = ProviderNewznab4Settings()


class ProviderNewznab5Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab5"
        super().__init__()


providerNewznab5Settings = ProviderNewznab5Settings()


class ProviderNewznab6Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab6"
        super().__init__()


providerNewznab6Settings = ProviderNewznab6Settings()


class ProviderNewznab7Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab7"
        super().__init__()


providerNewznab7Settings = ProviderNewznab7Settings()


class ProviderNewznab8Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab8"
        super().__init__()


providerNewznab8Settings = ProviderNewznab8Settings()


def get_newznab_setting_by_id(id):
    id = str(id)
    return {
        "1": providerNewznab1Settings,
        "2": providerNewznab2Settings,
        "3": providerNewznab3Settings,
        "4": providerNewznab4Settings,
        "5": providerNewznab5Settings,
        "6": providerNewznab6Settings,
        "7": providerNewznab5Settings,
        "8": providerNewznab6Settings,
    }[id]
