from enum import Enum

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


settings_infos = {}
form_infos = {}


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


def replace_lists_with_strings(d):
    """
    Traverses the dictionary and replaces all lists with comma separated strings
    :param d: 
    :return: 
    """
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = replace_lists_with_strings(d[k])
        if isinstance(v, list):
            d[k] = ",".join(v)
    return d


def get_settings_as_dict_without_lists() -> dict:
    """
    Returns the settings as dict with all lists replaced with comma separated strings
    
    :return: 
    """
    settings_dict = cfg.as_dict(dict_type=dict)
    return replace_lists_with_strings(settings_dict)


def traverse_settings_dict_and_transfer(d: dict, section: profig.ConfigSection):
    """
    Traverses the given dict and sets the settings to the new values stored in the dict.
    :param section: The section under which the upper level of settings is stored. Should be root cfg for the first call
    :param d: 
    """
    for key, value in d.items():
        if isinstance(value, dict):
            traverse_settings_dict_and_transfer(value, section.section(key))
        else:
            section[key] = value


def set_settings_from_dict(new_settings: dict):
    traverse_settings_dict_and_transfer(new_settings, cfg)
    cfg.sync()


class SettingsTypes(Enum):
    free = "free"
    password = "password"
    select = "select"
    multiselect = "multiselect"


def get_schema_infos(d, schema_infos_subdic):
    """
    :type schema_infos_subdic: dict[SettingsInfo]
    """
    current_level_schema_infos = {}
    for k, v in d.items():
        if isinstance(v, dict):  # Go deeper
            schema_entry = {"type": "object", "title": k, "properties": get_schema_infos(v, schema_infos_subdic[k])}
        else:
            if not k:
                continue  # Only happens in some cases which I didn't analyze but it works and it's late...
            # Build the actual schema entry depending on the type, options, etc
            schema_info = schema_infos_subdic[k]

            schema_entry = {"title": schema_info.title}
            if schema_info.description:
                schema_entry["description"] = schema_info.description
            if schema_info.setting_type == SettingsTypes.multiselect:
                schema_entry["type"] = "array"
                schema_entry["items"] = {"type": "string"}
            else:
                if schema_info.valuetype == float:
                    schematype = "number"
                elif schema_info.valuetype == int:
                    schematype = "integer"
                elif schema_info.valuetype == str:
                    schematype = "string"
                elif schema_info.valuetype == bool:
                    schematype = "boolean"
                else:
                    schematype = "text"
                schema_entry["type"] = schematype

        current_level_schema_infos[k] = schema_entry
    return current_level_schema_infos


def get_settings_schema():
    schema = {"$schema": "http://json-schema.org/draft-04/schema#", "id": "NZBHydra", "type": "object"}
    settingsdict = cfg.as_dict(dict_type=dict)
    settingsdict = replace_lists_with_strings(settingsdict)

    schema["properties"] = get_schema_infos(settingsdict, settings_infos)
    return schema


def get_setting_infos_with_path(d, current_path):
    infos = {}
    for k, v in d.items():
        if isinstance(v, dict):
            for k2, v2 in get_setting_infos_with_path(v, current_path + "." + k).items():
                infos[current_path + "." + k2] = v2
        else:
            infos[current_path + "." + k] = v
    return infos


def get_settings_form():
    # Create a tab for every category
    tabs = []
    for category, subsetting_infos in settings_infos.items():
        tabs.append(get_items(category, subsetting_infos, "tab"))
        # The category may be "main", the subsettings may either a setting or another level. We want to add the settings directly to the tab but create a fieldgroup for each subcategory
        items = []
        # for k, v in subsetting_infos.items():
        #     if isinstance(v, SettingsInfo):
        #         items.append(create_form_item("%s.%s" % (category, v.name), v))
        #         print("%s is a settingsinfo" % v)               
        #     else:
        #         items = []
        #         fieldset = {"type": "fieldset"}



        # setting_infos_with_path = get_setting_infos_with_path(setting_infos, category)
        # items = []
        # for key, setting_info in setting_infos_with_path.items():
        #     # The problem is that for all subcategories like "providers.nzbindex" the resulting key is "providers.providers.nzbindex" so we remove the first part of the key path. Not elegant, but hey...
        #     if len(key.split(".")) > 2:
        #         key = key.split(".", 1)[1]
        #     
        #     if len(key.split(".")) > 1: #If we still have multiple dots we create a fieldset for the subcategory
        #         fieldset = {"type": "fieldset", "items": []}
        #         
        #         pass
        #     else:
        #         item = create_form_item(key, setting_info)
        #     
        #     items.append(item)
        # tab = {"title": category}
        # tab["items"] = items
        # tabs.append(tab)
    return ["tabs", {"type": "tabs", "tabs": tabs}]


def get_items(path, d, grouptype="section"):
    items = []
    for k, v in d.items():
        if isinstance(v, SettingsInfo):
            print("Creating new item for path %s.%s" % (path, v.name))
            items.append(create_form_item("%s.%s" % (path, v.name), v))
        else:
            print("Creating new subgroup for path %s.%s" % (path, k))
            items.append(get_items("%s.%s" % (path, k), v))
    if grouptype == "section":
        return {"type": "section", "htmlClass": "panel panel-default",
                "items": [
                    {"type": "help", "helpvalue": '<div class="panel-title>' + d.title + '</div>'},
                    {"type": "section", "htmlClass": "panel-body",
                     "items": items}]
                }
    else:
        return {"type": "tab", "title": d.title, "items": items}


def create_form_item(key, setting_info):
    item = {}
    item["key"] = key
    if setting_info.setting_type == SettingsTypes.password:
        item["type"] = "password"

    elif setting_info.setting_type == SettingsTypes.select or setting_info.setting_type == SettingsTypes.multiselect:
        item["type"] = "strapselect"
        item["titleMap"] = []
        for option in setting_info.options:
            item["titleMap"].append({"value": option.name, "name": option.title})
        if setting_info.setting_type == SettingsTypes.multiselect:
            item["options"] = {"multiple": "true"}
    return item


class CategoryInfo(dict):
    def __init__(self, title, **kwargs):
        super().__init__(**kwargs)
        self.title = title


class SettingsInfo(object):
    def __init__(self, name, title, valuetype, setting_type: SettingsTypes, description: str = None, options: list = None):
        self.name = name
        self.title = title
        self.valuetype = valuetype
        self.setting_type = setting_type
        self.description = description
        self.options = options


def create_category_info_entry(d, pathkeys, title):
    if len(pathkeys) == 1:
        if pathkeys[0] in d.keys():
            print("Category entry already exists")
        else:
            d[pathkeys[0]] = CategoryInfo(title)
    else:
        if pathkeys[0] not in d:
            pass
        create_category_info_entry(d[pathkeys[0]], pathkeys[1:], title)


class SettingsCategory(object):
    _path = ""

    def __init__(self, title=None):
        cfg.section(self._path, create=True)

        # Add the category to the form infos so we can build tabs for every one of them
        if title is None:
            title = self._path
        global settings_infos

        create_category_info_entry(settings_infos, self._path.split("."), title)

    def addSetting(self, name, default, valuetype, description, settingtype=SettingsTypes.free, title=None, options=None):
        # Init the setting and create the object
        setting_path = "%s.%s" % (self._path, name)
        cfg.init(setting_path, default, valuetype)
        setting = Setting(name, default, valuetype, description)
        setting.category = self._path

        self.create_settings_info(name, valuetype, setting_path, title, description, options, settingtype)

        return setting

    def create_settings_info(self, name, valuetype, setting_path, title, description, options, setting_type):
        # Save all the data that is not needed for the config but for the schema (title, type, etc)
        if title is None:
            title = name
        schema_info = SettingsInfo(name=name, title=title, valuetype=valuetype, setting_type=setting_type, description=description, options=options)
        # Traverse the saved schema infos by path and save it
        path_keys = setting_path.split(".")
        global settings_infos
        settings_infos = traverse_dict_and_add_to_dict(settings_infos, path_keys, schema_info)


def traverse_dict_and_add_to_dict(d: dict, l: list, value: object):
    """
    Go through the given dict by the list of items and set the value. Example: d={a:{b:{}} with [a,b,c] will return d={a:{b:{c:value}}
    :param d: dictionary
    :param l: list of keys that describe the path in the dict
    :param value: value to set
    :return: Modified dict
    """
    if len(l) == 1:
        d[l[0]] = value
        return d
    else:
        if l[0] not in d.keys():
            d[l[0]] = {}
        d[l[0]] = traverse_dict_and_add_to_dict(d[l[0]], l[1:], value)
    return d


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


class CacheTypeSelection(object):
    file = SelectOption("file", "Cache on the file system")
    memory = SelectOption("memory", "Cache in the memory during runtime")


class MainSettings(SettingsCategory):
    """
    The main settings of our program.
    """

    def __init__(self):
        self._path = "main"
        super().__init__("Main")
        self.host = self.addSetting(name="host", default="127.0.0.1", valuetype=str, description="Set to 0.0.0.0 to listen on all public IPs. If you do this you should enable SSL.")
        self.port = self.addSetting(name="port", default=5050, valuetype=int, description="Port to listen on.")
        self.debug = self.addSetting(name="debug", default=False, valuetype=bool, description="Enable debugging functions. Don't do this until you know why you're doing it.")
        self.ssl = self.addSetting(name="ssl", default=True, valuetype=bool, description="Use SSL. Strongly recommended if you access via a public network!")
        self.sslcert = self.addSetting(name="sslcert", default="nzbhydra.crt", valuetype=str, description="File name of the certificate to use for SSL.")
        self.sslkey = self.addSetting(name="sslkey", default="nzbhydra.key", valuetype=str, description="File name of the key to use for SSL.")
        create_category_info_entry(settings_infos, "main.logging".split("."), "Logging")
        self.logfilename = self.addSetting(name="logging.logfile-filename", default="nzbhydra.log", valuetype=str, description="File name (relative or absolute) of the log file.")
        self.logfilelevel = self.addSetting(name="logging.logfile-level", default="INFO", valuetype=str, description="Log level of the log file")  # TODO change to SelectionSetting
        self.consolelevel = self.addSetting(name="logging.consolelevel", default="ERROR", valuetype=str, description="Log level of the console. Only applies if run in console, obviously.")  # TODO change to SelectionSetting
        self.username = self.addSetting(name="username", default="", valuetype=str, description=None)
        self.password = self.addSetting(name="password", default="", valuetype=str, description=None, settingtype=SettingsTypes.password)
        self.apikey = self.addSetting(name="apikey", default="", valuetype=str, description="API key for external tools to authenticate (newznab API)")
        self.enable_auth = self.addSetting(name="enableAuth", default=True, valuetype=bool, description="Select if you want to enable autorization via username / password.")
        self.cache_enabled = self.addSetting(name="enableCache", default=True, valuetype=bool, description="Select if you want to enable cache results.")
        self.cache_type = self.addSetting(name="cacheType", default=CacheTypeSelection.memory.name, valuetype=str, description="Select the of cache you want to use.", options=[CacheTypeSelection.memory, CacheTypeSelection.file], settingtype=SettingsTypes.select)
        self.cache_timeout = self.addSetting(name="cacheTimeout", default=30, valuetype=int, description="Cache timeout in minutes.")
        self.cache_threshold = self.addSetting(name="cachethreshold", default=25, valuetype=int, description="Maximum amount of cached items.")
        self.cache_folder = self.addSetting(name="cacheFolder", default="cache", valuetype=str, description="Name of the folder where cache items should be stored. Only applies for file cache.")


mainSettings = MainSettings()


class ResultProcessingSettings(SettingsCategory):
    """
    Settings which control how search results are processed.
    """

    def __init__(self):
        self._path = "resultProcessing"
        super().__init__("Result processing")
        self.duplicateSizeThresholdInPercent = self.addSetting(name="duplicateSizeThresholdInPercent", default=0.1, valuetype=float, description="If the size difference between two search entries with the same title is higher than this they won't be considered dplicates.")
        self.duplicateAgeThreshold = self.addSetting(name="duplicateAgeThreshold", default=3600, valuetype=int, description="If the age difference in seconds between two search entries with the same title is higher than this they won't be considered dplicates.")


resultProcessingSettings = ResultProcessingSettings()


class SearchingSettings(SettingsCategory):
    """
    How searching is executed.
    """

    def __init__(self):
        self._path = "searching"
        super().__init__("Searching")
        self.timeout = self.addSetting(name="timeout", default=5, valuetype=int, description="Timeout when accessing providers.")
        self.ignoreTemporarilyDisabled = self.addSetting(name="ignoreTemporarilyDisabled", default=False, valuetype=bool, description="Enable if you want to always call all enabled providers even if the connection previously failed.")
        self.allowQueryGeneration = self.addSetting(name="allowQueryGeneration", default="both", valuetype=str, description=None)  # todo change to SelctionSetting


searchingSettings = SearchingSettings()


class NzbAccessTypeSelection(object):
    serve = SelectOption("serve", "Proxy the NZBs from the provider")
    redirect = SelectOption("redirect", "Redirect to the provider")
    direct = SelectOption("direct", "Use direct links to the provider")


class NzbAddingTypeSelection(object):
    link = SelectOption("link", "Send link to NZB")
    nzb = SelectOption("nzb", "Upload NZB")


class DownloaderSelection(object):
    sabnzbd = SelectOption("sabnzbd", "SabNZBd")
    nzbget = SelectOption("nzbget", "NZBGet")


# Note: if you define a subcategory (like downloader.sabnzd to the super-category downloader) always init the super-category first and make sure the path doesn't overwrite extending classes' paths 
class DownloaderSettings(SettingsCategory):
    def __init__(self):
        if not self._path:  # This is important for any category that has settings but also subcategories because otherwise the subcategory calls this init and its path is overwritten
            self._path = "downloader"
        super().__init__("Downloader")
        self.nzbaccesstype = self.addSetting(name="nzbaccesstype", default=NzbAccessTypeSelection.serve.name, valuetype=str, options=[NzbAccessTypeSelection.direct, NzbAccessTypeSelection.redirect, NzbAccessTypeSelection.serve], settingtype=SettingsTypes.select,
                                             description="Determines how we provide access to NZBs  ""Serve"": Provide a link to NZBHydra via which the NZB is downloaded and returned. ""Redirect"": Provide a link to NZBHydra which redirects to the provider. ""Direct"": Create direct links (as returned by the provider=. Not recommended.")
        self.nzbAddingType = self.addSetting(name="nzbAddingType", default=NzbAddingTypeSelection.nzb.name, valuetype=str, options=[NzbAddingTypeSelection.link, NzbAddingTypeSelection.nzb], settingtype=SettingsTypes.select,
                                             description="Determines how NZBs are added to downloaders. Either by sending a link to the downloader (""link"") or by sending the actual NZB (""nzb"").")
        self.downloader = self.addSetting(name="downloader", default=DownloaderSelection.nzbget.name, valuetype=str, description="Choose the downloader you want to use when adding NZBs via the GUI.", options=[DownloaderSelection.nzbget, DownloaderSelection.sabnzbd], settingtype=SettingsTypes.select)


downloaderSettings = DownloaderSettings()


class SabnzbdSettings(SettingsCategory):
    def __init__(self):
        self._path = "downloader.sabnzbd"
        super().__init__("SabNZBD")
        self.host = self.addSetting(name="host", default="127.0.0.1", valuetype=str, description=None)
        self.port = self.addSetting(name="port", default=8086, valuetype=int, description=None)
        self.ssl = self.addSetting(name="ssl", default=False, valuetype=bool, description=None)
        self.apikey = self.addSetting(name="apikey", default=None, valuetype=str, description=None)
        self.username = Setting(name="username", default=None, valuetype=str, comment=None)
        self.password = self.addSetting(name="password", default=None, valuetype=str, description=None, settingtype=SettingsTypes.password)


sabnzbdSettings = SabnzbdSettings()


class NzbgetSettings(SettingsCategory):
    def __init__(self):
        self._path = "downloader.nzbget"
        super().__init__("NZBGet")
        self.host = self.addSetting(name="host", default="127.0.0.1", valuetype=str, description=None)
        self.port = self.addSetting(name="port", default=6789, valuetype=int, description=None)
        self.ssl = self.addSetting(name="ssl", default=False, valuetype=bool, description=None)
        self.username = self.addSetting(name="username", default="nzbget", valuetype=str, description=None)
        self.password = self.addSetting(name="password", default="tegbzn6789", valuetype=str, description=None, settingtype=SettingsTypes.password)


nzbgetSettings = NzbgetSettings()


class SearchIdSelection(object):
    rid = SelectOption("tvrage", "TvRage ID")
    tvdbid = SelectOption("tvdbid", "TVDB ID")
    imdbid = SelectOption("imdbid", "IMDB ID")


class GenerateQueriesSelection(object):
    internal = SelectOption("internal", "Only for internal searches")
    external = SelectOption("external", "Only for API searches")
    both = SelectOption("both", "Always")
    never = SelectOption("never", "Never")


class ProviderSettings(SettingsCategory):
    def __init__(self, title):
        if not self._path:  # This is important for any category that has settings but also subcategories because otherwise the subcategory calls this init and its path is overwritten
            self._path = "providers"
        super().__init__(title)
        self.name = self.addSetting(name="name", default=None, valuetype=str, description="Name of the provider. Used when displayed. If changed all references, history and stats get lost!")
        self.host = self.addSetting(name="host", default=None, valuetype=str, description="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.enabled = self.addSetting(name="enabled", default=True, valuetype=bool, description="")
        self.search_ids = self.addSetting(name="search_ids", default=[], valuetype=list, description=None)
        self.generate_queries = self.addSetting(name="generate_queries", default=GenerateQueriesSelection.internal.name, options=[GenerateQueriesSelection.internal, GenerateQueriesSelection.external, GenerateQueriesSelection.both], valuetype=str, description=None, settingtype=SettingsTypes.select)


# This is a superclass that does not contain any actual settings itself you we need to generate a Category_info manually
settings_infos["providers"] = CategoryInfo("Providers")


class ProviderBinsearchSettings(ProviderSettings):
    def __init__(self):
        self._path = "providers.binsearch"
        super(ProviderBinsearchSettings, self).__init__("Binsearch")
        self.host = self.addSetting(name="host", default="https://binsearch.com", valuetype=str, description="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = self.addSetting(name="name", default="binsearch", valuetype=str, description="Name of the provider. Used when displayed. If changed all references, history and stats get lost!")


providerBinsearchSettings = ProviderBinsearchSettings()


class ProviderNzbclubSettings(ProviderSettings):
    def __init__(self):
        self._path = "providers.nzbclub"
        super(ProviderNzbclubSettings, self).__init__("NZBClub")
        self.host = self.addSetting(name="host", default="http://nzbclub.com", valuetype=str, description="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = self.addSetting(name="name", default="nzbclub", valuetype=str, description="Name of the provider. Used when displayed. If changed all references, history and stats get lost!")


providerNzbclubSettings = ProviderNzbclubSettings()


class ProviderNzbindexSettings(ProviderSettings):
    def __init__(self):
        self._path = "providers.nzbindex"
        super(ProviderNzbindexSettings, self).__init__("NZBIndex")
        self.host = self.addSetting(name="host", default="https://nzbindex.com", valuetype=str, description="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = self.addSetting(name="name", default="nzbindex", valuetype=str, description="Name of the provider. Used when displayed. If changed all references, history and stats get lost!")


providerNzbindexSettings = ProviderNzbindexSettings()


class ProviderWombleSettings(ProviderSettings):
    def __init__(self):
        self._path = "providers.womble"
        super(ProviderWombleSettings, self).__init__("Womble")
        self.host = self.addSetting(name="womble", default="https://newshost.co.za", valuetype=str, description="Base host like ""https://api.someindexer.com"". In case of newznab without ""/api"".")
        self.name = self.addSetting(name="name", default="womble", valuetype=str, description="Name of the provider. Used when displayed. If changed all references, history and stats get lost!")

        # todo make settings hideable in GUI and hide generate_queries for this (and others which don't match the particular provider)


providerWombleSettings = ProviderWombleSettings()


# I would like to have solved this more generically but got stuck. This way it works and I hope nobody uses / actually needs for than 6 of these.
# As we only need the attributes to contain information on what setting to get we can create instances and pass them around and still don't need
# to worry about synchronization of settings

class ProviderNewznabSettings(ProviderSettings):
    def __init__(self, title):
        super(ProviderNewznabSettings, self).__init__(title)
        self.apikey = self.addSetting(name="apikey", default=None, valuetype=str, description=None)
        self.search_ids = self.addSetting(name="search_ids", default=[SearchIdSelection.imdbid.name, SearchIdSelection.rid.name, SearchIdSelection.tvdbid.name], valuetype=list, description=None, options=[SearchIdSelection.imdbid, SearchIdSelection.rid, SearchIdSelection.tvdbid],
                                          settingtype=SettingsTypes.multiselect)
        self.enabled = self.addSetting(name="enabled", default=False, valuetype=bool, description="")  # Disable by default because we have no meaningful initial data


class ProviderNewznab1Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab1"
        super().__init__("Newznab 1")


providerNewznab1Settings = ProviderNewznab1Settings()


class ProviderNewznab2Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab2"
        super().__init__("Newznab 2")


providerNewznab2Settings = ProviderNewznab2Settings()


class ProviderNewznab3Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab3"
        super().__init__("Newznab 3")


providerNewznab3Settings = ProviderNewznab3Settings()


class ProviderNewznab4Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab4"
        super().__init__("Newznab 4")


providerNewznab4Settings = ProviderNewznab4Settings()


class ProviderNewznab5Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab5"
        super().__init__("Newznab 5")


providerNewznab5Settings = ProviderNewznab5Settings()


class ProviderNewznab6Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab6"
        super().__init__("Newznab 6")


providerNewznab6Settings = ProviderNewznab6Settings()


class ProviderNewznab7Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab7"
        super().__init__("Newznab 7")


providerNewznab7Settings = ProviderNewznab7Settings()


class ProviderNewznab8Settings(ProviderNewznabSettings):
    def __init__(self):
        self._path = "providers.newznab8"
        super().__init__("Newznab 8")


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
