from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import shutil
import traceback
from contextlib import contextmanager
from sets import Set

import arrow
# standard_library.install_aliases()
import re

import validators as validators
from builtins import *
import json
import logging
import os
import collections
from furl import furl
from bunch import Bunch

logger = logging.getLogger('root')

# Checklist for adding config values:
# Make sure they're anonymized if needed
# Make sure they're migrated to if needed
# Make sure they're available in safe config if needed

initialConfig = {
    "downloader": {
        "downloader": "none",
        "nzbAddingType": "link",
        "nzbaccesstype": "redirect",
        "nzbget": {
            "defaultCategory": None,
            "host": "127.0.0.1",
            "password": "tegbzn6789",
            "port": 6789,
            "ssl": False,
            "username": "nzbget"
        },
        "sabnzbd": {
            "apikey": None,
            "defaultCategory": None,
            "password": None,
            "url": "http://localhost:8080/sabnzbd/",
            "username": None
        }
    },
    "indexers": [
        {
            "accessType": "internal",
            "enabled": True,
            "hitLimit": 0,
            "hitLimitResetTime": None,
            "host": "https://binsearch.info",
            "name": "Binsearch",
            "password": None,
            "preselect": True,
            "score": 0,
            "search_ids": [],
            "searchTypes": [],
            "showOnSearch": True,
            "timeout": None,
            "type": "binsearch",
            "username": None
        },
        {
            "accessType": "internal",
            "enabled": True,
            "hitLimit": 0,
            "hitLimitResetTime": None,
            "host": "https://www.nzbclub.com",
            "name": "NZBClub", 
            "password": None,
            "preselect": True,
            "score": 0,
            "search_ids": [],
            "searchTypes": [],
            "showOnSearch": True,
            "timeout": None,
            "type": "nzbclub",
            "username": None

        },
        {
            "accessType": "internal",
            "enabled": True,
            "generalMinSize": 1,
            "hitLimit": 0,
            "hitLimitResetTime": None,
            "host": "https://nzbindex.com",
            "name": "NZBIndex",
            "password": None,
            "preselect": True,
            "score": 0,
            "search_ids": [],
            "searchTypes": [],
            "showOnSearch": True,
            "timeout": None,
            "type": "nzbindex",
            "username": None

        },
        {
            "accessType": "external",
            "enabled": True,
            "hitLimit": 0,
            "hitLimitResetTime": None,
            "host": "https://newshost.co.za",
            "name": "Womble",
            "password": None,
            "preselect": True,
            "score": 0,
            "search_ids": [],
            "searchTypes": [],
            "showOnSearch": False,
            "timeout": None,
            "type": "womble",
            "username": None
        },
        {
            "accessType": "both",
            "apikey": "",
            "enabled": False,
            "hitLimit": 0,
            "hitLimitResetTime": None,
            "host": "https://api.omgwtfnzbs.org",
            "name": "omgwtfnzbs.org",
            "password": None,
            "preselect": True,
            "score": 0,
            "search_ids": [
                "imdbid"
            ],
            "searchTypes": [],
            "showOnSearch": True,
            "timeout": None,
            "type": "omgwtf",
            "username": ""
        }
    ],
    "main": {
        "apikey": "ab00y7qye6u84lx4eqhwd0yh1wp423",
        "branch": "master",
        "configVersion": 16,
        "debug": False,
        "externalUrl": None,
        "flaskReloader": False,
        "gitPath": None,
        "host": "0.0.0.0",
        "keepSearchResultsForDays": 7,
        "logging": {
            "consolelevel": "INFO",
            "logfilename": "nzbhydra.log",
            "logfilelevel": "INFO"
        },
        "port": 5075,
        "repositoryBase": "https://github.com/theotherp",
        "runThreaded": True,
        "ssl": False,
        "sslcert": None,
        "sslkey": None,
        "startupBrowser": True,
        "theme": "default",
        "urlBase": None,
        "useLocalUrlForApiAccess": True,
    },
    "searching": {
        "alwaysShowDuplicates": False,
        "categorysizes": {
            "audiobookmax": 1000,
            "audiomax": 2000,
            "audiomin": 1,
            "audioookmin": 50,
            "consolemax": 40000,
            "consolemin": 100,
            "ebookmax": 100,
            "ebookmin": None,
            "enable_category_sizes": True,
            "flacmax": 2000,
            "flacmin": 10,
            "movieshdmax": 20000,
            "movieshdmin": 3000,
            "moviesmax": 20000,
            "moviesmin": 500,
            "moviessdmin": 500,
            "mp3max": 500,
            "mp3min": 1,
            "pcmax": 50000,
            "pcmin": 100,
            "tvhdmax": 3000,
            "tvhdmin": 300,
            "tvmax": 5000,
            "tvmin": 50,
            "tvsdmax": 1000,
            "tvsdmin": 50,
            "xxxmax": 10000,
            "xxxmin": 100
        },
        "duplicateAgeThreshold": 3600,
        "duplicateSizeThresholdInPercent": 0.1,
        "generate_queries": [
            "internal"
        ],
        "htmlParser": "html.parser",
        "ignorePassworded": False,
        "ignoreTemporarilyDisabled": False,
        "ignoreWords": "",
        "maxAge": "",
        "removeDuplicatesExternal": True,
        "requireWords": "",
        "timeout": 20,
        "userAgent": "NZBHydra"
    },
    "auth": {
        "users": []
    }
}

settings = Bunch()
config_file = None

logMessages = []


def addLogMessage(level, message):
    """
        Adds a log message to a list which can be logged after the logger was initialized 
    """
    global logMessages
    logMessages.append({"level": level, "message": message})


def logLogMessages():
    """
        Logs the messages that were created before the logger was initialized and then removes them from the list 
    """
    global logMessages
    for x in logMessages:
        logger.log(x["level"], x["message"])
    logMessages = []


def update(d, u, level):
    for k, v in u.items():

        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v, "%s.%s" % (level, k))
            d[k] = r
        else:
            if k in d.keys():
                d[k] = u[k]
            else:
                u.pop(k, None)
                addLogMessage(20, "Found obsolete setting %s.%s and will remove it" % (level, k))
    return d


@contextmanager
def version_update(config, version):
    addLogMessage(20, "Migrating config to version %d" % version)
    try:
        yield
        config["main"]["configVersion"] = version
        addLogMessage(20, "Migration of config to version %d finished" % version)
    except Exception as e:
        addLogMessage(30, "Exception while trying to migrate config: %s" % e)
        raise


def migrate(settingsFilename):
    with open(settingsFilename) as settingsFile:
        config = json.load(settingsFile)
        # CAUTION: Don't forget to increase the default value for configVersion
        if "configVersion" not in config["main"].keys():
            config["main"]["configVersion"] = 1
        if config["main"]["configVersion"] < initialConfig["main"]["configVersion"]:
            addLogMessage(20, "Migrating config")
            try:
                if config["main"]["configVersion"] == 1:
                    with version_update(config, 2):
                        sabnzbd = config["downloader"]["sabnzbd"]
                        if sabnzbd["host"] and sabnzbd["port"]:
                            addLogMessage(20, "Migrating sabnzbd settings")
                            f = furl()
                            f.host = sabnzbd["host"]
                            f.port = sabnzbd["port"]
                            f.scheme = "https" if sabnzbd["ssl"] else "http"
                            f.path.set("/sabnzbd/")
                            config["downloader"]["sabnzbd"]["url"] = f.url
                            addLogMessage(20, "Built sabnzbd URL: %s" % f.url)
                        elif config["downloader"]["downloader"] == "sabnzbd":
                            addLogMessage(30, "Unable to migrate from incomplete sabnzbd settings. Please set the sabnzbd URL manually")

                if config["main"]["configVersion"] == 2:
                    with version_update(config, 3):
                        addLogMessage(20, "Updating NZBClub host to https://www.nzbclub.com")
                        config["indexers"]["NZBClub"]["host"] = "https://www.nzbclub.com"

                if config["main"]["configVersion"] == 3:
                    with version_update(config, 4):
                        addLogMessage(20, "Converting Base URL to URL base and external URL")
                        baseUrl = config["main"]["baseUrl"]
                        if baseUrl is not None and baseUrl != "":
                            f = furl(config["main"]["baseUrl"])
                            if f.path != "/":
                                config["main"]["urlBase"] = str(f.path)
                                if config["main"]["urlBase"].endswith("/"):
                                    config["main"]["urlBase"] = config["main"]["urlBase"][:-1]
                            else:
                                config["main"]["urlBase"] = None
                            config["main"]["externalUrl"] = f.url
                            if config["main"]["externalUrl"].endswith("/"):
                                config["main"]["externalUrl"] = config["main"]["externalUrl"][:-1]
                            addLogMessage(20, "Setting URL base to %s and external URL to %s" % (config["main"]["urlBase"], config["main"]["externalUrl"]))
                        else:
                            config["main"]["urlBase"] = None
                            config["main"]["externalUrl"] = None
                        config["main"].pop("baseUrl")

                if config["main"]["configVersion"] == 4:
                    with version_update(config, 5):
                        addLogMessage(20, "Converting repository base URL")
                        if "repositoryBase" in config["main"].keys():
                            config["main"]["repositoryBase"] = "https://github.com/theotherp"

                if config["main"]["configVersion"] == 5:
                    with version_update(config, 6):
                        if config["downloader"]["nzbAddingType"] == "direct":
                            addLogMessage(20, 'Removing legacy setting for NZB access "direct" and setting it to redirect. Sorry.')
                            config["main"]["nzbAddingType"] = "redirect"

                if config["main"]["configVersion"] == 6:
                    with version_update(config, 7):
                        for i in range(1, 41):
                            indexer_cfg = config["indexers"]["newznab%d" % i]
                            search_ids = indexer_cfg["search_ids"]
                            indexer_cfg["search_ids"] = list(Set(search_ids))
                            if len(search_ids) != len(indexer_cfg["search_ids"]):
                                addLogMessage(20, "Removed duplicate search types from indexer %s" % indexer_cfg["name"])

                if config["main"]["configVersion"] == 7:
                    with version_update(config, 8):
                        addLogMessage(20, "Renaming keys")
                        config["indexers"]["binsearch"] = config["indexers"]["Binsearch"]
                        config["indexers"].pop("Binsearch")
                        config["indexers"]["nzbclub"] = config["indexers"]["NZBClub"]
                        config["indexers"].pop("NZBClub")
                        config["indexers"]["nzbindex"] = config["indexers"]["NZBIndex"]
                        config["indexers"].pop("NZBIndex")
                        config["indexers"]["womble"] = config["indexers"]["Womble"]
                        config["indexers"].pop("Womble")

                        config["main"]["logging"]["logfilelevel"] = config["main"]["logging"]["logfile-level"]
                        config["main"]["logging"].pop("logfile-level")
                        config["main"]["logging"]["logfilename"] = config["main"]["logging"]["logfile-filename"]
                        config["main"]["logging"].pop("logfile-filename")

                        addLogMessage(20, "Moving newznab indexers")
                        config["indexers"]["newznab"] = []
                        for i in range(1, 41):
                            indexer_cfg = config["indexers"]["newznab%d" % i]
                            if "accessType" not in indexer_cfg.keys():
                                indexer_cfg["accessType"] = "both"
                            if indexer_cfg["name"]:
                                config["indexers"]["newznab"].append(indexer_cfg)
                            config["indexers"].pop("newznab%d" % i)

                if config["main"]["configVersion"] == 8:
                    with version_update(config, 9):
                        config["auth"] = {"users": []}
                        adminNeededForStats = config["main"]["enableAdminAuthForStats"]
                        if config["main"]["enableAuth"] and config["main"]["username"]:
                            addLogMessage(20, "Will require auth for any access")
                            if config["main"]["enableAdminAuth"]:
                                if adminNeededForStats:
                                    addLogMessage(20, "Creating user %s with basic rights." % config["main"]["username"])
                                else:
                                    addLogMessage(20, "Creating user %s with basic and stats rights." % config["main"]["username"])
                                config["auth"]["users"].append({"name": config["main"]["username"], "password": config["main"]["password"], "maySeeStats": not adminNeededForStats, "maySeeAdmin": False})
                            else:
                                addLogMessage(20, "Creating simple user %s with all rights." % config["main"]["username"])
                                config["auth"]["users"].append({"name": config["main"]["username"], "password": config["main"]["password"], "maySeeStats": True, "maySeeAdmin": True})
                        else:
                            if config["main"]["enableAdminAuth"]:
                                if adminNeededForStats:
                                    addLogMessage(20, "Auth will be required for stats and admin access")
                                else:
                                    addLogMessage(20, "Auth will be required for admin access")
                                config["auth"]["users"].append({"name": None, "password": None, "maySeeStats": not adminNeededForStats, "maySeeAdmin": False})
                            else:
                                addLogMessage(20, "No auth required for any access")
                                config["auth"]["users"].append({"name": None, "password": None, "maySeeStats": True, "maySeeAdmin": True})

                        if config["main"]["enableAdminAuth"] and config["main"]["adminUsername"]:
                            addLogMessage(20, "Creating user %s with admin rights." % config["main"]["adminUsername"])
                            config["auth"]["users"].append({"name": config["main"]["adminUsername"], "password": config["main"]["adminPassword"], "maySeeStats": True, "maySeeAdmin": True})
                            if not (config["main"]["enableAuth"] and config["main"]["username"]):
                                addLogMessage(20, "Will require auth only for any admin access")

                if config["main"]["configVersion"] == 9:
                    with version_update(config, 10):
                        addLogMessage(20, "Activating threaded server")
                        config["main"]["runThreaded"] = True

                if config["main"]["configVersion"] == 10:
                    with version_update(config, 11):
                        addLogMessage(20, "Renaming keys for usernames")
                        for user in config["auth"]["users"]:
                            addLogMessage(10, "Renaming key for user")
                            user["username"] = user["name"]
                            user.pop("name")

                if config["main"]["configVersion"] == 11:
                    with version_update(config, 12):
                        addLogMessage(20, "Adding search types to indexers")
                        config["indexers"]["binsearch"]["searchTypes"] = []
                        config["indexers"]["nzbclub"]["searchTypes"] = []
                        config["indexers"]["nzbindex"]["searchTypes"] = []
                        config["indexers"]["omgwtfnzbs"]["searchTypes"] = []
                        config["indexers"]["womble"]["searchTypes"] = []
                        from nzbhydra.searchmodules import newznab
                        for n in config["indexers"]["newznab"]:
                            n["searchTypes"] = ["tvsearch", "movie"]
                            addLogMessage(20, "Checking caps of indexer %s" % n["name"])
                            try:
                                ids, types = newznab.check_caps(n["host"], n["apikey"], config["searching"]["userAgent"], config["searching"]["timeout"])
                                n["search_ids"] = ids
                                n["searchTypes"] = types
                                addLogMessage(20, "Successfully determined caps")
                            except Exception as e:
                                addLogMessage(40, "Error while trying to determine caps: %s" % e)

                if config["main"]["configVersion"] == 12:
                    with version_update(config, 13):
                        addLogMessage(20, "Adding API hit limit settings to indexers")
                        config["indexers"]["binsearch"]["hitLimit"] = None
                        config["indexers"]["nzbclub"]["hitLimit"] = None
                        config["indexers"]["nzbindex"]["hitLimit"] = None
                        config["indexers"]["omgwtfnzbs"]["hitLimit"] = None
                        config["indexers"]["womble"]["hitLimit"] = None
                        
                        config["indexers"]["binsearch"]["hitLimitResetTime"] = None
                        config["indexers"]["nzbclub"]["hitLimitResetTime"] = None
                        config["indexers"]["nzbindex"]["hitLimitResetTime"] = None
                        config["indexers"]["omgwtfnzbs"]["hitLimitResetTime"] = None
                        config["indexers"]["womble"]["hitLimitResetTime"] = None

                        from nzbhydra.searchmodules import newznab
                        for n in config["indexers"]["newznab"]:
                            n["hitLimit"] = None
                            n["hitLimitResetTime"] = arrow.get(0).isoformat()

                if config["main"]["configVersion"] == 13:
                    with version_update(config, 14):
                        addLogMessage(20, "Adding empty username and password to indexers")
                        config["indexers"]["binsearch"]["username"] = None
                        config["indexers"]["nzbclub"]["username"] = None
                        config["indexers"]["nzbindex"]["username"] = None
                        config["indexers"]["omgwtfnzbs"]["username"] = None
                        config["indexers"]["womble"]["username"] = None

                        config["indexers"]["binsearch"]["password"] = None
                        config["indexers"]["nzbclub"]["password"] = None
                        config["indexers"]["nzbindex"]["password"] = None
                        config["indexers"]["omgwtfnzbs"]["password"] = None
                        config["indexers"]["womble"]["password"] = None

                        from nzbhydra.searchmodules import newznab
                        for n in config["indexers"]["newznab"]:
                            n["username"] = None
                            n["password"] = None

                if config["main"]["configVersion"] == 14:
                    with version_update(config, 15):
                        addLogMessage(20, "Setting default theme")
                        config["main"]["theme"] = "default"

                if config["main"]["configVersion"] == 15:
                    with version_update(config, 16):
                        addLogMessage(20, "Moving indexers")
                        indexers = []
                        for indexer in ["binsearch", "nzbclub", "nzbindex", "omgwtfnzbs", "womble"]:
                            config["indexers"][indexer]["type"] = indexer if indexer != "omgwtfnzbs" else "omgwtf"
                            indexers.append(config["indexers"][indexer])
                        for indexer in config["indexers"]["newznab"]:
                            indexer["type"] = "newznab"
                            indexers.append(indexer)
                        config["indexers"] = indexers
                        

            except Exception as e:
                addLogMessage(30, "An error occurred while migrating the config file.")
                addLogMessage(30, str(traceback.format_exc()))
        return config


def load(filename):
    global config_file
    global settings
    config_file = filename
    if os.path.exists(filename):
        try:
            migratedConfig = migrate(filename)
            settings = Bunch.fromDict(update(initialConfig, migratedConfig, level="root"))
            pass
        except Exception as e:
            addLogMessage(30, "An error occurred while migrating the settings: %s" % traceback.format_exc())
            # Now what?
    else:
        settings = Bunch.fromDict(initialConfig)


def getAnonymizedConfigSetting(key, value):
    if value is None:
        return None
    if value == "":
        return ""
    try:
        if key == "host":
            return getAnonymizedIpOrDomain(value)
        if key == "url" or key == "externalUrl" and value:
                f = furl(value)
                if f.host:
                    f.host = getAnonymizedIpOrDomain(f.host)
                    return f.tostr()
                return "<NOTAURL>"
        if key in ("username", "password", "apikey"):
            return "<%s:%s>" % (key.upper(), hashlib.md5(value).hexdigest())
        return value
    except Exception as e:
        logger.error('Error while anonymizing setting "%s". Obfuscating to be sure: %s' % (key, e))
        return "<%s:%s>" % (key.upper(), hashlib.md5(value).hexdigest())
        


def getAnonymizedIpOrDomain(value):
    if validators.ipv4(value) or validators.ipv6(value):
        return "<IPADDRESS:%s>" % hashlib.md5(value).hexdigest()
    elif validators.domain(value):
        return "<DOMAIN:%s>" % hashlib.md5(value).hexdigest()
    else:
        return "<NOTIPADDRESSORDOMAIN:%s>" % hashlib.md5(value).hexdigest()


def getAnonymizedConfig(config=None):
    if config is None:
        return getAnonymizedConfig(settings)
    result = {}
    if isinstance(config, str) or isinstance(config, int) or isinstance(config, float):
        return config
    for x, y in config.iteritems():
        if isinstance(y, dict):
            result[x] = getAnonymizedConfig(y)
        elif isinstance(y, list):
            result[x] = [getAnonymizedConfig(i) for i in y]
        else:
            result[x] = getAnonymizedConfigSetting(x, y)
    return result


def getSettingsToHide():
    #Only use values which would actually appear in the log
    hideThese = [
        ("main.apikey", settings.main.apikey),
        ("main.externalUrl", settings.main.externalUrl),
        ("main.host", settings.main.host),
        ("sabnzbd.apikey", settings.downloader.sabnzbd.apikey),
        ("sabnzbd.url", settings.downloader.sabnzbd.url),
        ("nzbget.host", settings.downloader.nzbget.host),
    ]
    hideThese.extend([("auth.username", x.username) for x in settings.auth.users])
    for i, indexer in enumerate(settings.indexers):
        if indexer.type in ["omgwtf", "newznab"]:
            hideThese.append(("indexers[%d].apikey" % i, indexer.apikey))
            hideThese.append(("indexers[%d].username" % i, indexer.username))
    return hideThese


def import_config_data(data):
    global settings
    global config_file
    settings = Bunch.fromDict(data)
    save(config_file)
    # Now what?


def save(filename):
    global settings
    try:
        s = json.dumps(settings.toDict(), ensure_ascii=False, indent=4, sort_keys=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(s)
    except Exception as e:
        logger.exception("Error while saving settings")
        


class CacheTypeSelection(object):
    file = "file"
    memory = "memory"


class DatabaseDriverSelection(object):
    sqlite = "sqlite"
    apsw = "apsw"


class HtmlParserSelection(object):
    html = "html.parser"
    lxml = "lxml"

    options = [html, lxml]


class InternalExternalSelection(object):
    internal = "internal"
    external = "external"
    options = [internal, external]


class NzbAccessTypeSelection(object):
    serve = "serve"
    redirect = "redirect"


class NzbAddingTypeSelection(object):
    link = "link"
    nzb = "nzb"


class DownloaderSelection(object):
    none = "none"
    sabnzbd = "sabnzbd"
    nzbget = "nzbget"


class SearchIdSelection(object):
    rid = "rid"
    tvdbid = "tvdbid"
    imdbid = "imdbid"
    tmdbid = "tmdbid"
    tvmazeid = "tvmazeid"


class InternalExternalSingleSelection(object):
    internal = "internal"
    external = "external"
    both = "both"
    options = [internal, external, both]


def getSafeConfig():
    indexers = [{"name": x["name"], "preselect": x["preselect"], "enabled": x["enabled"], "showOnSearch": x["showOnSearch"] and x["accessType"] != "external"} for x in settings["indexers"]]
    return {
        "indexers": indexers,
        "searching": {"categorysizes": settings["searching"]["categorysizes"], "maxAge": settings["searching"]["maxAge"], "alwaysShowDuplicates": settings["searching"]["alwaysShowDuplicates"]},
        "downloader": {"downloader": settings["downloader"]["downloader"], "nzbget": {"defaultCategory": settings["downloader"]["nzbget"]["defaultCategory"]}, "sabnzbd": {"defaultCategory": settings["downloader"]["sabnzbd"]["defaultCategory"]}}
    }
