from enum import Enum
import json
import logging
import os
import collections

from typing import List

logger = logging.getLogger('root')


class Category(object):
    def __init__(self, parent, name, title=None):
        if not title:
            title = name
        self.parent = parent
        self.title = title
        self.categoryname = name
        self.children = []
        self.parent.add_category(self)

    @property
    def path(self):
        return "%s%s." % (self.parent.path, self.categoryname)  # Parent path already includes a dot (or not in case of the category root) 

    def get(self):
        return self.parent.get_category(self)

    def add_category(self, category):
        self.parent.get_category(self)[category.categoryname] = {}
        self.children.append(category)

    def add_setting(self, setting):
        self.parent.get_category(self)[setting.settingname] = setting.default
        if setting not in self.children:
            self.children.append(setting)

    def get_category(self, category):
        return self.get()[category.categoryname]

    def get_setting(self, setting):
        return self.get()[setting.settingname]

    def set_setting(self, setting, value):
        self.get()[setting.settingname] = value

    def __setattr__(self, key, value):
        if key != "children" and hasattr(self, "children") and key in [x.settingname for x in self.children if isinstance(x, Setting)] and not isinstance(value, Setting):
            # Allow setting a setting's value directly instead of using set(value)
            self.get()[key] = value
        else:
            return super().__setattr__(key, value)

    def __getattribute__(self, *args, **kwargs):
        key = args[0]
        # todo maybe, only works with direct subsettings
        # if key != "children" and hasattr(self, "children") and key in [x.settingname for x in self.children if isinstance(x, Setting)]:
        #    return self.get()[key]

        return super().__getattribute__(*args, **kwargs)


cfg = {}
config_file = None


class CategoryRoot(Category):
    def __init__(self):
        self.children = []
        pass

    @property
    def path(self):
        return ""

    def add_category(self, category):
        cfg[category.categoryname] = {}
        self.children.append(category)

    def add_setting(self, setting):
        cfg[setting.settingname] = setting
        self.children.append(setting)

    def get(self):
        return cfg

    def get_category(self, category):
        return cfg[category.categoryname]


config_root = CategoryRoot()


class SettingType(Enum):
    free = "free"
    password = "password"
    select = "select"
    multiselect = "multiselect"


class Setting(object):
    """
    A setting that has a category, name, a default value, a value type and a comment. These will be delegated to profig to read and set the actual config.
    This structure allows us indexed access to the settings anywhere in the code without having to use dictionaries with potentially wrong string keys.
    It also allows us to collect all settings and create a dict with all settings which can be serialized and sent to the GUI.
    """

    def __init__(self, parent: Category, name: str, default: object, valuetype: type, title=None, description: str = None, setting_type: SettingType = SettingType.free):
        self.parent = parent
        self.settingname = name
        self.default = default
        self.valuetype = valuetype
        self.description = description
        self.setting_type = setting_type
        self.title = title
        self.parent.add_setting(self)

    @property
    def path(self):
        return "%s%s" % (self.parent.path, self.settingname)  # Parent path already includes a trailing dot

    def get(self):
        # We delegate the getting of the actual value to the parent
        return self.parent.get_setting(self)

    def get_with_default(self, default):
        return self.get() if not None else default

    def set(self, value):
        self.parent.set_setting(self, value)
        
    def isSetting(self, value):
        return self.get() == value or self.get() == getattr(value, "name")

    def __str__(self):
        return "%s: %s" % (self.settingname, self.get())

    def __eq__(self, other):
        if not isinstance(other, Setting):
            return False
        return self.parent == other.parent and self.settingname == other.settingname


class SelectOption(object):
    def __init__(self, name, title):
        super().__init__()
        self.name = name
        self.title = title

    def __eq__(self, other):
        if isinstance(other, SelectOption):
            return self.name == other.name
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class SelectionSetting(Setting):
    def __init__(self, parent: Category, name: str, default: SelectOption, valuetype: type, options: List[SelectOption], title: str = None, description: str = None, setting_type: SettingType = SettingType.select):  # Warning is a mistake by PyCharm
        super().__init__(parent, name, default, valuetype, title, description, setting_type)
        self.options = options
        self.parent.get()[self.settingname] = self.default.name

    def get(self):
        return super().get()


class MultiSelectionSetting(Setting):
    def __init__(self, parent: Category, name: str, default: List[SelectOption], valuetype: type, options: List[SelectOption], title: str = None, description: str = None, setting_type: SettingType = SettingType.select):  # Warning is a mistake by PyCharm
        super().__init__(parent, name, default, valuetype, title, description, setting_type)
        self.options = options
        self.parent.get()[self.settingname] = [x.name for x in self.default]

    def get(self):
        return super().get()
    

class OrderedMultiSelectionSetting(Setting):
    def __init__(self, parent: Category, name: str, default: List[SelectOption], valuetype: type, options: List[SelectOption], title: str = None, description: str = None, setting_type: SettingType = SettingType.select):  # Warning is a mistake by PyCharm
        super().__init__(parent, name, default, valuetype, title, description, setting_type)
        self.options = options
        self.parent.get()[self.settingname] = [x.name for x in self.default]

    def get(self):
        return super().get()


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def load(filename):
    global cfg
    global config_file
    config_file = filename
    if os.path.exists(filename):
        with open(filename, "r") as f:
            loaded_config = json.load(f)
            cfg = update(cfg, loaded_config)
            pass


def import_config_data(data):
    global cfg
    global config_file
    cfg = data
    save(config_file)


def save(filename):
    global cfg
    with open(filename, "w") as f:
        json.dump(cfg, f, indent=4)


def get(setting: Setting) -> object:
    """
    Just a legacy way to access the setting 
    """
    return setting.get()


def set(setting: Setting, value: object):
    """
    Just a legacy way to set the setting 
    """
    setting.set(value)


def get_schema_infos(d):
    current_level_schema_infos = {}
    for child in d.children:
        if isinstance(child, Category):
            schema_entry = {"type": "object", "title": child.title, "properties": get_schema_infos(child)}
            current_level_schema_infos[child.categoryname] = schema_entry
        if isinstance(child, Setting):
            # todo category arrays
            schema_entry = {"title": child.title}
            if child.description:
                schema_entry["description"] = child.description
            if child.setting_type == SettingType.multiselect:
                schema_entry["type"] = "array"
                schema_entry["items"] = {"type": "string"}
            else:
                if child.valuetype == float:
                    schematype = "number"
                elif child.valuetype == int:
                    schematype = "integer"
                elif child.valuetype == str:
                    schematype = "string"
                elif child.valuetype == bool:
                    schematype = "boolean"
                else:
                    schematype = "text"
                schema_entry["type"] = schematype
            current_level_schema_infos[child.settingname] = schema_entry
    return current_level_schema_infos


def get_settings_schema():
    global config_root
    schema = {"$schema": "http://json-schema.org/draft-04/schema#", "id": "NZBHydra", "type": "object", "properties": get_schema_infos(config_root)}
    return schema


def get_settings_form():
    # return ["*"]
    # Create a tab for every category
    tabs = []
    for category in config_root.children:
        tabs.append(get_form_items(category, "tab"))
    return ["tabs", {"type": "tabs", "tabs": tabs}, {"type": "submit", "style": "btn-info", "title": "Save"}]


def get_form_items(category: Category, grouptype="section"):
    items = []
    for child in category.children:
        if isinstance(child, Category):
            items.append(get_form_items(child))
        if isinstance(child, Setting):
            items.append(create_form_item(child))

    if grouptype == "section":
        main_element = {"type": "section", "htmlClass": "panel panel-default",
                        "items": [
                            {"type": "help", "helpvalue": '<div class="panel-title>' + category.title + '</div>'},
                            {"type": "section", "htmlClass": "panel-body",
                             "items": items}]
                        }
    else:
        main_element = {"type": "tab", "title": category.title, "items": [{"type": "section", "htmlClass": "config-tab-content", "items": items}]}

    return main_element


def create_form_item(setting: Setting):
    item = {"key": setting.path, "title": setting.title, "htmlClass": "config-field-container", "fieldHtmlClass": "config-field", "labelHtmlCLass": "config-field-label"}
    if setting.setting_type == SettingType.password:
        item["type"] = "password"
    elif isinstance(setting, OrderedMultiSelectionSetting):
        item["type"] = "uiselectmulti"
        item["htmlClass"] = "config-select"
        item["labelHtmlClass"] = "config-select-label"
        item["fieldHtmlClass"] = "config-select-field"
    elif isinstance(setting, SelectionSetting) or isinstance(setting, MultiSelectionSetting):
        item["type"] = "strapselect"
        item["titleMap"] = []
        item["add"] = None
        item["remove"] = None
        item["htmlClass"] = "config-select"
        item["labelHtmlClass"] = "config-select-label"
        item["fieldHtmlClass"] = "config-select-field"
        item["placeholder"] = "None"
        for option in setting.options:
            item["titleMap"].append({"value": option.name, "name": option.title})
        if setting.setting_type == SettingType.multiselect:
            item["options"] = {"multiple": "true"}
    if setting.valuetype in (str, int, float):
        item["feedback"] = False
    elif setting.valuetype == bool:
        item["fieldHtmlClass"] += " checkbox-field"

    return item


class LoglevelSelection(object):
    critical = SelectOption("CRITICAL", "Critical")
    error = SelectOption("ERROR", "Error")
    warning = SelectOption("WARNING", "Warning")
    info = SelectOption("INFO", "Info")
    debug = SelectOption("DEBUG", "Debug")

    options = [critical, error, warning, info, debug]


class LoggingSettings(Category):
    def __init__(self, parent):
        super().__init__(parent, "logging", "Logging")
        self.logfilename = Setting(self, name="logfile-filename", default="nzbhydra.log", valuetype=str, title="Log file name", description="File name (relative or absolute) of the log file.")
        self.logfilelevel = SelectionSetting(self, name="logfile-level", default=LoglevelSelection.info, valuetype=str, options=LoglevelSelection.options, title="Log file level", description="Log level of the log file")
        self.consolelevel = SelectionSetting(self, name="consolelevel", default=LoglevelSelection.error, valuetype=str, options=LoglevelSelection.options, title="Console log level", description="Log level of the console. Only applies if run in console, obviously.")  # TODO change to SelectionSetting


class CacheTypeSelection(object):
    file = SelectOption("file", "Cache on the file system")
    memory = SelectOption("memory", "Cache in the memory during runtime")


class MainSettings(Category):
    """
    The main settings of our program.
    """

    def __init__(self):
        super().__init__(config_root, "main", "Main")
        self.host = Setting(self, name="host", default="127.0.0.1", valuetype=str, title="Host", description="Set to 0.0.0.0 to listen on all public IPs. If you do this you should enable SSL.")
        self.port = Setting(self, name="port", default=5050, valuetype=int, title="Port", description="Port to listen on.")

        self.username = Setting(self, name="username", default="", valuetype=str, title="Username", description=None)
        self.password = Setting(self, name="password", default="", valuetype=str, title="Password", description=None, setting_type=SettingType.password)
        self.apikey = Setting(self, name="apikey", default="hailhydra", valuetype=str, title="API key", description="API key for external tools to authenticate (newznab API)")
        self.enable_auth = Setting(self, name="enableAuth", default=True, valuetype=bool, title="HTTP Auth", description="Select if you want to enable autorization via username / password.")

        self.ssl = Setting(self, name="ssl", default=True, valuetype=bool, title="SSL", description="Use SSL. Strongly recommended if you access via a public network!")
        self.sslcert = Setting(self, name="sslcert", default="nzbhydra.crt", valuetype=str, title="SSL cert file name", description="File name of the certificate to use for SSL.")
        self.sslkey = Setting(self, name="sslkey", default="nzbhydra.key", valuetype=str, title="SSL key file name", description="File name of the key to use for SSL.")

        self.debug = Setting(self, name="debug", default=False, valuetype=bool, title="Debug", description="Enable debugging functions. Don't do this until you know why you're doing it.")
        self.cache_enabled = Setting(self, name="enableCache", default=True, valuetype=bool, title="Caching", description="Select if you want to cache results.")
        self.cache_type = SelectionSetting(self, name="cacheType", default=CacheTypeSelection.memory, valuetype=str, title="Cache type", description="Select the of cache you want to use.", options=[CacheTypeSelection.memory, CacheTypeSelection.file], setting_type=SettingType.select)
        self.cache_timeout = Setting(self, name="cacheTimeout", default=30, valuetype=int, title="Cache timeout", description="Cache timeout in minutes.")
        self.cache_threshold = Setting(self, name="cachethreshold", default=25, valuetype=int, title="Cache threshold", description="Maximum amount of cached items.")
        self.cache_folder = Setting(self, name="cacheFolder", default="cache", valuetype=str, title="Cache folder", description="Name of the folder where cache items should be stored. Only applies for file cache.")

        self.logging = LoggingSettings(self)


mainSettings = MainSettings()


class HtmlParserSelection(object):
    html = SelectOption("html.parser", "Default BS (slow)")
    lxml = SelectOption("lxml", "LXML (faster, needs to be installed separately)")

    options = [html, lxml]


class ResultProcessingSettings(Category):
    """
    Settings which control how search results are processed.
    """

    def __init__(self):
        super().__init__(config_root, "resultProcessing", "Result processing")
        self.duplicateSizeThresholdInPercent = Setting(self, name="duplicateSizeThresholdInPercent", default=0.1, valuetype=float, title="Duplicate size threshold",
                                                       description="If the size difference between two search entries with the same title is higher than this they won't be considered dplicates.")
        self.duplicateAgeThreshold = Setting(self, name="duplicateAgeThreshold", default=3600, valuetype=int, title="Duplicate age threshold", description="If the age difference in seconds between two search entries with the same title is higher than this they won't be considered dplicates.")
        self.htmlParser = SelectionSetting(self, name="htmlParser", default=HtmlParserSelection.html, valuetype=str, options=HtmlParserSelection.options, title="HTML Parser", description="Used to parse HTML from indexers like binsearch. If possible use LXML")



resultProcessingSettings = ResultProcessingSettings()


class InternalExternalSelection(object):
    internal = SelectOption("internal", "Internal searches")
    external = SelectOption("external", "API searches")
    options = [internal, external]


class CategorySizeSettings(Category):
    def __init__(self, parent):
        super().__init__(parent, "categorysizes", "Category sizes")
        self.enable_category_sizes = Setting(self, name="enable_category_sizes", default=True, valuetype=bool, title="Category sizes",
                                             description="If enabled when selecting a category size the limit inputs will be prefilled with the category limits.")

        self.movieMin = Setting(self, name="Movies min", default=500, valuetype=int, title="Movies min size", description="")
        self.movieMax = Setting(self, name="Movies max", default=20000, valuetype=int, title="Movies max size", description="")

        self.moviehdMin = Setting(self, name="Movies HD min", default=2000, valuetype=int, title="Movies HD min size", description="")
        self.moviehdMax = Setting(self, name="Movies HD max", default=20000, valuetype=int, title="Movies HD max size", description="")

        self.moviesdMin = Setting(self, name="Movies SD min", default=500, valuetype=int, title="Movies SD min size", description="")
        self.moviesdMax = Setting(self, name="Movies SD max", default=3000, valuetype=int, title="Movies SD max size", description="")

        self.tvMin = Setting(self, name="TV min", default=50, valuetype=int, title="TV min size", description="")
        self.tvMax = Setting(self, name="TV max", default=5000, valuetype=int, title="TV max size", description="")

        self.tvhdMin = Setting(self, name="TV HD min", default=300, valuetype=int, title="TV HD min size", description="")
        self.tvhdMax = Setting(self, name="TV HD max", default=3000, valuetype=int, title="TV HD max size", description="")

        self.tvsdMin = Setting(self, name="TV SD min", default=50, valuetype=int, title="TV SD min size", description="")
        self.tvsdMax = Setting(self, name="TV SD max", default=1000, valuetype=int, title="TV SD max size", description="")

        self.audioMin = Setting(self, name="Audio min", default=1, valuetype=int, title="Audio min size", description="")
        self.audioMax = Setting(self, name="Audio max", default=2000, valuetype=int, title="Audio max size", description="")

        self.audioflacmin = Setting(self, name="Audio FLAC min", default=10, valuetype=int, title="Audio FLAC min size", description="")
        self.audioflacmax = Setting(self, name="Audio FLAC max", default=2000, valuetype=int, title="Audio FLAC max size", description="")

        self.audiomp3min = Setting(self, name="Audio MP3 min", default=1, valuetype=int, title="Audio MP3 min size", description="")
        self.audiomp3max = Setting(self, name="Audio MP3 max", default=500, valuetype=int, title="Audio MP3 max size", description="")

        self.consolemin = Setting(self, name="Console min", default=100, valuetype=int, title="Console min size", description="")
        self.consolemax = Setting(self, name="Console max", default=40000, valuetype=int, title="Console max size", description="")

        self.pcmin = Setting(self, name="PC min", default=100, valuetype=int, title="PC min size", description="")
        self.pcmax = Setting(self, name="PC max", default=50000, valuetype=int, title="PC max size", description="")

        self.xxxmin = Setting(self, name="XXX min", default=100, valuetype=int, title="XXX min size", description="")
        self.xxxmax = Setting(self, name="XXX max", default=10000, valuetype=int, title="XXX max size", description="")


class SearchingSettings(Category):
    """
    How searching is executed.
    """

    def __init__(self):
        super().__init__(config_root, "searching", "Searching")
        self.timeout = Setting(self, name="timeout", default=5, valuetype=int, title="Timeout", description="Timeout when accessing indexers.")
        self.temporarilyDisableProblemIndexers = Setting(self, name="ignoreTemporarilyDisabled", default=False, valuetype=bool, title="Pause indexers after problems", description="Enable if you want to pause access to indexers for a time after there was a problem.")
        self.generate_queries = MultiSelectionSetting(self, name="generate_queries", default=[InternalExternalSelection.internal], options=InternalExternalSelection.options, valuetype=str, title="Query generation",
                                                      description="Decide if you want to generate queries for indexers in case of ID based searches. The results will probably contain a lot of crap.",
                                                      setting_type=SettingType.multiselect)

        self.category_sizes = CategorySizeSettings(self)


searchingSettings = SearchingSettings()


class NzbAccessTypeSelection(object):
    serve = SelectOption("serve", "Proxy the NZBs from the indexer")
    redirect = SelectOption("redirect", "Redirect to the indexer")
    direct = SelectOption("direct", "Use direct links to the indexer")


class NzbAddingTypeSelection(object):
    link = SelectOption("link", "Send link to NZB")
    nzb = SelectOption("nzb", "Upload NZB")


class DownloaderSelection(object):
    sabnzbd = SelectOption("sabnzbd", "SabNZBd")
    nzbget = SelectOption("nzbget", "NZBGet")


class DownloaderSettings(Category):
    def __init__(self):
        super().__init__(config_root, "downloader", "Downloader")
        self.nzbaccesstype = SelectionSetting(self, name="nzbaccesstype", default=NzbAccessTypeSelection.serve, valuetype=str, options=[NzbAccessTypeSelection.direct, NzbAccessTypeSelection.redirect, NzbAccessTypeSelection.serve], setting_type=SettingType.select,
                                              title="NZB access type",
                                              description="Determines how we provide access to NZBs  ""Serve"": Provide a link to NZBHydra via which the NZB is downloaded and returned. ""Redirect"": Provide a link to NZBHydra which redirects to the indexer. ""Direct"": Create direct links (as returned by the indexer). Not recommended.")
        self.nzbAddingType = SelectionSetting(self, name="nzbAddingType", default=NzbAddingTypeSelection.nzb, valuetype=str, options=[NzbAddingTypeSelection.link, NzbAddingTypeSelection.nzb], setting_type=SettingType.select,
                                              title="NZB adding type", description="Determines how NZBs are added to downloaders. Either by sending a link to the downloader or by sending the actual NZB.")
        self.downloader = SelectionSetting(self, name="downloader", default=DownloaderSelection.nzbget, valuetype=str, title="Downloader", description="Choose the downloader you want to use when adding NZBs via the GUI.", options=[DownloaderSelection.nzbget, DownloaderSelection.sabnzbd],
                                           setting_type=SettingType.select)


downloaderSettings = DownloaderSettings()


class SabnzbdSettings(Category):
    def __init__(self):
        super().__init__(downloaderSettings, "sabnzbd", "SabNZBD")
        self.host = Setting(self, name="host", default="127.0.0.1", valuetype=str, title="Host name", description=None)
        self.port = Setting(self, name="port", default=8086, valuetype=int, title="Port", description=None)
        self.ssl = Setting(self, name="ssl", default=False, valuetype=bool, title="SSL", description=None)
        self.apikey = Setting(self, name="apikey", default=None, valuetype=str, title="API key", description=None)
        self.username = Setting(self, name="username", default=None, valuetype=str, title="Username", description=None)
        self.password = Setting(self, name="password", default=None, valuetype=str, title="password", description=None, setting_type=SettingType.password)


sabnzbdSettings = SabnzbdSettings()


class NzbgetSettings(Category):
    def __init__(self):
        super().__init__(downloaderSettings, "nzbget", "NZBGet")
        self.host = Setting(self, name="host", default="127.0.0.1", valuetype=str, title="Host name", description=None)
        self.port = Setting(self, name="port", default=6789, valuetype=int, title="Port", description=None)
        self.ssl = Setting(self, name="ssl", default=False, valuetype=bool, title="SSL", description=None)
        self.username = Setting(self, name="username", default="nzbget", valuetype=str, title="Username", description=None)
        self.password = Setting(self, name="password", default="tegbzn6789", valuetype=str, title="Password", description=None, setting_type=SettingType.password)


nzbgetSettings = NzbgetSettings()


class SearchIdSelection(object):
    rid = SelectOption("rid", "TvRage ID")
    tvdbid = SelectOption("tvdbid", "TVDB ID")
    imdbid = SelectOption("imdbid", "IMDB ID")


class IndexerSettingsAbstract(Category):
    def __init__(self, parent, name, title):
        super().__init__(parent, name, title)
        self.name = Setting(self, name="name", default=None, valuetype=str, title="Name", description="Name of the indexer. Used when displayed. If changed all references, history and stats get lost!")
        self.host = Setting(self, name="host", default=None, valuetype=str, title="Host name", description="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.enabled = Setting(self, name="enabled", default=True, valuetype=bool, title="Enabled", description="")
        self.search_ids = MultiSelectionSetting(self, name="search_ids", default=[], valuetype=list, title="Search IDs", description="By which IDs the indexer can search releases",
                                                options=[SearchIdSelection.imdbid, SearchIdSelection.rid, SearchIdSelection.tvdbid],
                                                setting_type=SettingType.multiselect)
        self.score = Setting(self, name="score", default=0, valuetype=str, title="Score", description="Used to decide how results are picked when duplicates are found. Higher is \"better\".")
        # self.generate_queries = MultiSelectionSetting(self, name="generate_queries", default=[GenerateQueriesSelection.internal], options=GenerateQueriesSelection.options, valuetype=str, title="Query generation",
        #                                          description="Decide if you want to generate queries for indexers in case of ID based searches. The results will probably contain a lot of crap.",
        #                                          setting_type=SettingType.multiselect)


class IndexerBinsearchSettings(IndexerSettingsAbstract):
    def __init__(self, parent):
        super(IndexerBinsearchSettings, self).__init__(parent, "binsearch", "Binsearch")
        self.host = Setting(self, name="host", default="https://binsearch.com", valuetype=str, title="Host name", description="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = Setting(self, name="name", default="binsearch", valuetype=str, title="Name", description="Name of the indexer. Used when displayed. If changed all references, history and stats get lost!")


class IndexerNewznabSettings(IndexerSettingsAbstract):
    def __init__(self, parent, name, title):
        super(IndexerNewznabSettings, self).__init__(parent, name, title)
        self.apikey = Setting(self, name="apikey", default=None, valuetype=str, title="API key", description=None)
        self.search_ids = MultiSelectionSetting(self, name="search_ids", default=[SearchIdSelection.imdbid, SearchIdSelection.rid, SearchIdSelection.tvdbid], valuetype=list, title="Search IDs", description="By which IDs the indexer can search releases",
                                                options=[SearchIdSelection.imdbid, SearchIdSelection.rid, SearchIdSelection.tvdbid],
                                                setting_type=SettingType.multiselect)
        self.enabled = Setting(self, name="enabled", default=False, valuetype=bool, title="Enabled", description="")  # Disable by default because we have no meaningful initial data


class IndexerNzbclubSettings(IndexerSettingsAbstract):
    def __init__(self, parent):
        super(IndexerNzbclubSettings, self).__init__(parent, "nzbclub", "NZBClub")
        self.host = Setting(self, name="host", default="http://nzbclub.com", valuetype=str, title="Host name", description="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = Setting(self, name="name", default="nzbclub", valuetype=str, title="", description="Name of the indexer. Used when displayed. If changed all references, history and stats get lost!")


class IndexerNzbindexSettings(IndexerSettingsAbstract):
    def __init__(self, parent):
        super(IndexerNzbindexSettings, self).__init__(parent, "nzbindex", "NZBIndex")
        self.host = Setting(self, name="host", default="https://nzbindex.com", valuetype=str, title="Host name", description="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = Setting(self, name="name", default="nzbindex", valuetype=str, title="NZBIndex", description="Name of the indexer. Used when displayed. If changed all references, history and stats get lost!")


class IndexerWombleSettings(IndexerSettingsAbstract):
    def __init__(self, parent):
        super(IndexerWombleSettings, self).__init__(parent, "womble", "Womble")
        self.host = Setting(self, name="host", default="https://newshost.co.za", valuetype=str, title="Host name", description="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = Setting(self, name="name", default="womble", valuetype=str, title="Name ", description="Name of the indexer. Used when displayed. If changed all references, history and stats get lost!")


class IndexerSettings(Category):
    def __init__(self):
        super().__init__(config_root, "indexers", "Indexer")
        self.binsearch = IndexerBinsearchSettings(self)
        self.nzbclub = IndexerNzbclubSettings(self)
        self.nzbindex = IndexerNzbindexSettings(self)
        self.womble = IndexerWombleSettings(self)
        self.newznab1 = IndexerNewznabSettings(self, "newznab1", "Newznab 1")
        self.newznab2 = IndexerNewznabSettings(self, "newznab2", "Newznab 2")
        self.newznab3 = IndexerNewznabSettings(self, "newznab3", "Newznab 3")
        self.newznab4 = IndexerNewznabSettings(self, "newznab4", "Newznab 4")
        self.newznab5 = IndexerNewznabSettings(self, "newznab5", "Newznab 5")
        self.newznab6 = IndexerNewznabSettings(self, "newznab6", "Newznab 6")


indexerSettings = IndexerSettings()


class IndexerNewznab1Settings(IndexerNewznabSettings):
    def __init__(self):
        self._path = "indexers.newznab1"
        super().__init__("Newznab 1", "", "")


def get_newznab_setting_by_id(id):
    id = str(id)
    return {
        "1": indexerSettings.newznab1,
        "2": indexerSettings.newznab2,
        "3": indexerSettings.newznab3,
        "4": indexerSettings.newznab4,
        "5": indexerSettings.newznab5,
        "6": indexerSettings.newznab6}[id]
