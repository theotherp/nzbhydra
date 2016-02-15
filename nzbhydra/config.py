from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import traceback
from contextlib import contextmanager
from sets import Set

import arrow
import shutil
from future import standard_library

#standard_library.install_aliases()
from builtins import *
import json
import logging
import os
import collections
from furl import furl
from bunch import Bunch

logger = logging.getLogger('root')


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
    "indexers": {
        "binsearch": {
            "accessType": "both",
            "enabled": True,
            "host": "https://binsearch.info",
            "name": "Binsearch",
            "preselect": True,
            "score": 0,
            "search_ids": [],
            "showOnSearch": True,
            "timeout": None
        },
        "nzbclub": {
            "accessType": "both",
            "enabled": True,
            "host": "https://www.nzbclub.com",
            "name": "NZBClub",
            "preselect": True,
            "score": 0,
            "search_ids": [],
            "showOnSearch": True,
            "timeout": None
        },
        "nzbindex": {
            "accessType": "both",
            "enabled": True,
            "generalMinSize": 1,
            "host": "https://nzbindex.com",
            "name": "NZBIndex",
            "preselect": True,
            "score": 0,
            "search_ids": [],
            "showOnSearch": True,
            "timeout": None
        },
        "womble": {
            "accessType": "external",
            "enabled": True,
            "host": "https://newshost.co.za",
            "name": "Womble",
            "preselect": True,
            "score": 0,
            "search_ids": [],
            "showOnSearch": False,
            "timeout": None
        },
        "newznab": [],
        "omgwtfnzbs": {
            "accessType": "both",
            "apikey": "",
            "enabled": False,
            "host": "https://api.omgwtfnzbs.org",
            "name": "omgwtfnzbs.org",
            "preselect": True,
            "score": 0,
            "search_ids": [
                "imdbid"
            ],
            "showOnSearch": True,
            "timeout": None,
            "username": ""
        }
    },
    "main": {
        "adminPassword": "",
        "adminUsername": "",
        "apikey": "ab00y7qye6u84lx4eqhwd0yh1wp423",
        "branch": "master",
        "configVersion": 8,
        "debug": False,
        "enableAdminAuth": False,
        "enableAdminAuthForStats": False,
        "enableAuth": False,
        "externalUrl": None,
        "flaskReloader": False,
        "host": "0.0.0.0",
        "logging": {
            "consolelevel": "INFO",
            "logfilename": "nzbhydra.log",
            "logfilelevel": "INFO"
        },
        "password": "",
        "port": 5075,
        "repositoryBase": "https://github.com/theotherp",
        "runThreaded": False,
        "ssl": False,
        "sslcert": "nzbhydra.crt",
        "sslkey": "nzbhydra.key",
        "startupBrowser": True,
        "urlBase": None,
        "useLocalUrlForApiAccess": True,
        "username": ""
    },
    "searching": {
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
        "removeDuplicatesExternal": True,
        "timeout": 20,
        "userAgent": "NZBHydra"
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
            backupFilename = "%s.%s.bak" % (settingsFilename, arrow.now().format("YYYY-MM-DD"))
            addLogMessage(20, "Copying backup of settings to %s" % backupFilename)
            shutil.copy(settingsFilename, backupFilename)
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
                            f.path = "/sabnzbd/"
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
                            if indexer_cfg["name"]:
                                config["indexers"]["newznab"].append(indexer_cfg)
                            config["indexers"].pop("newznab%d" % i)


            except Exception as e:
                addLogMessage(30, "An error occurred while migrating the config file. A backup file of the original setttings was created: %s" % backupFilename)
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
        except Exception as e:
            addLogMessage(30, "An error occurred while migrating the settings: %s" % traceback.format_exc())
            #Now what?
    else:
        settings = initialConfig


def import_config_data(data):
    global settings
    global config_file
    settings = Bunch.fromDict(data)
    save(config_file)
    # Now what?


def save(filename):
    global settings
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json.dumps(settings, ensure_ascii=False, indent=4, sort_keys=True))



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
    indexers = [{"name": x["name"], "preselect": x["preselect"], "enabled": x["enabled"], "showOnSearch": x["showOnSearch"] and x["accessType"] != "external"} for x in settings["indexers"].values() if not isinstance(x, list)]
    indexers.extend([{"name": x["name"], "preselect": x["preselect"], "enabled": x["enabled"], "showOnSearch": x["showOnSearch"] and x["accessType"] != "external"} for x in settings["indexers"]["newznab"]])
    return {
        "indexers": indexers,
        "searching": {"categorysizes": settings["searching"]["categorysizes"]},
        "downloader": {"downloader": settings["downloader"]["downloader"], "nzbget": {"defaultCategory": settings["downloader"]["nzbget"]["defaultCategory"]}, "sabnzbd": {"defaultCategory": settings["downloader"]["sabnzbd"]["defaultCategory"]}}
    }



