from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import copy
import hashlib
import random
import string
import traceback
from contextlib import contextmanager
from sets import Set

import arrow
# standard_library.install_aliases()

import validators as validators
from builtins import *
import json
import logging
import os
import collections
from furl import furl
from bunch import Bunch

from nzbhydra import categories

logger = logging.getLogger('root')

# Checklist for adding config values:
# Make sure they're anonymized if needed
# Make sure they're migrated to if needed
# Make sure they're available in safe config if needed

initialConfig = {
    "downloaders": [],
    "indexers": [
        {
            "accessType": "both",
            "categories": ["anime"],
            "downloadLimit": None,
            "enabled": False,
            "hitLimit": 0,
            "hitLimitResetTime": None,
            "host": "https://anizb.org",
            "name": "anizb",
            "password": None,
            "preselect": True,
            "score": 0,
            "search_ids": [],
            "searchTypes": [],
            "showOnSearch": True,
            "timeout": None,
            "type": "anizb",
            "username": None
        },
        {
            "accessType": "internal",
            "categories": [],
            "downloadLimit": None,
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
            "categories": [],
            "downloadLimit": None,
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
            "categories": [],
            "downloadLimit": None,
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

        }
    ],
    "main": {
        "apikey": ''.join(random.choice('0123456789ABCDEF') for i in range(32)),
        "branch": "master",
        "configVersion": 38,
        "dereferer": "http://www.dereferer.org/?$s",
        "debug": False,
        "externalUrl": None,
        "firstStart": arrow.utcnow().timestamp,
        "isFirstStart": True,
        "flaskReloader": False,
        "gitPath": None,
        "host": "0.0.0.0",
        "keepSearchResultsForDays": 7,
        "logging": {
            "consolelevel": "INFO",
            "logfilename": "nzbhydra.log",
            "logfilelevel": "INFO",
            "logIpAddresses": True,
            "logRotateAfterDays": None,
            "logMaxSize": 1000,
            "keepLogFiles": 25,
            "rolloverAtStart": False
        },
        "port": 5075,
        "repositoryBase": "https://github.com/theotherp",
        "runThreaded": True,
        "secret": None,
        "pollShown": 0,
        "shutdownForRestart": False,
        "ssl": False,
        "sslcert": None,
        "sslkey": None,
        "socksProxy": None,
        "httpProxy": None,
        "httpsProxy": None,
        "startupBrowser": True,
        "theme": "grey",
        "urlBase": None,
        "useLocalUrlForApiAccess": True,
    },
    "searching": {
        "alwaysShowDuplicates": False,
        "applyRestrictions": "both",
        "duplicateAgeThreshold": 2,
        "duplicateSizeThresholdInPercent": 1.0,
        "idFallbackToTitle": [],
        "idFallbackToTitlePerIndexer": False,
        "generate_queries": [
            "internal"
        ],
        "htmlParser": "html.parser",
        "ignorePassworded": False,
        "ignoreTemporarilyDisabled": False,
        "forbiddenWords": "",
        "maxAge": "",
        "nzbAccessType": "redirect",
        "removeLanguage": True,
        "removeObfuscated": True,
        "requiredWords": "",
        "timeout": 20,
        "userAgent": "NZBHydra",
        "requiredRegex": None,
        "forbiddenRegex": None,
        "forbiddenGroups": None,
        "forbiddenPosters": None
    },
    "categories": {
        "enableCategorySizes": True,
        "categories": {
            "tvhd": {
                "applyRestrictions": "both",
                "min": 300,
                "max": 4500,
                "newznabCategories": [
                    5040
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "xxx": {
                "applyRestrictions": "both",
                "min": 100,
                "max": 10000,
                "newznabCategories": [
                    6000
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "both",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "console": {
                "applyRestrictions": "both",
                "min": 100,
                "max": 40000,
                "newznabCategories": [
                    1000
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "tvsd": {
                "applyRestrictions": "both",
                "min": 50,
                "max": 1000,
                "newznabCategories": [
                    5030
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "anime": {
                "applyRestrictions": "both",
                "min": 50,
                "max": 15000,
                "newznabCategories": [
                    5070
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "tv": {
                "applyRestrictions": "both",
                "min": 50,
                "max": 5000,
                "newznabCategories": [
                    5000
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "movieshd": {
                "applyRestrictions": "both",
                "min": 3000,
                "max": 20000,
                "newznabCategories": [
                    2040,
                    2050,
                    2060
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "audiobook": {
                "applyRestrictions": "both",
                "min": 50,
                "max": 1000,
                "newznabCategories": [
                    3030
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "pc": {
                "applyRestrictions": "both",
                "min": 100,
                "max": 50000,
                "newznabCategories": [
                    4000
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "moviessd": {
                "applyRestrictions": "both",
                "min": 500,
                "max": 3000,
                "newznabCategories": [
                    2030
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "ebook": {
                "applyRestrictions": "both",
                "min": None,
                "max": 100,
                "newznabCategories": [
                    7020,
                    8010
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "movies": {
                "applyRestrictions": "both",
                "min": 500,
                "max": 20000,
                "newznabCategories": [
                    2000
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "mp3": {
                "applyRestrictions": "both",
                "min": 1,
                "max": 500,
                "newznabCategories": [
                    3010
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "flac": {
                "applyRestrictions": "both",
                "min": 10,
                "max": 2000,
                "newznabCategories": [
                    3040
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "comic": {
                "applyRestrictions": "both",
                "min": 1,
                "max": 250,
                "newznabCategories": [
                    7030
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            },
            "audio": {
                "applyRestrictions": "both",
                "min": 1,
                "max": 2000,
                "newznabCategories": [
                    3000
                ],
                "forbiddenWords": [],
                "requiredWords": None,
                "ignoreResults": "never",
                "requiredRegex": None,
                "forbiddenRegex": None
            }
        }
    },
    "auth": {
        "authType": "none",
        "restrictAdmin": False,
        "restrictDetailsDl": False,
        "restrictIndexerSelection": False,
        "restrictSearch": False,
        "restrictStats": False,
        "rememberUsers": True,
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
    oldLogMessages = copy.copy(logMessages)
    logMessages = []
    return oldLogMessages


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


def loadAndMigrateSettingsFile(settingsFilename):
    with codecs.open(settingsFilename, "r", "utf-8") as settingsFile:
        config = json.load(settingsFile, encoding="utf-8")
        return migrateConfig(config)


def migrateConfig(config):
    # CAUTION: Don't forget to increase the default value for configVersion
    if "configVersion" not in config["main"].keys():
        config["main"]["configVersion"] = 1
    if config["main"]["configVersion"] < initialConfig["main"]["configVersion"]:
        addLogMessage(20, "Migrating config")

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

        if config["main"]["configVersion"] == 16:
            with version_update(config, 17):
                addLogMessage(20, "Moving downloaders")
                downloaders = []
                if config["downloader"]["nzbget"]["host"]:
                    addLogMessage(20, "Found configured downloader NZBGet")
                    downloaders.append({
                        "name": "NZBGet",
                        "type": "nzbget",
                        "defaultCategory": config["downloader"]["nzbget"]["defaultCategory"],
                        "host": config["downloader"]["nzbget"]["host"],
                        "password": config["downloader"]["nzbget"]["password"],
                        "port": config["downloader"]["nzbget"]["port"],
                        "ssl": config["downloader"]["nzbget"]["ssl"],
                        "username": config["downloader"]["nzbget"]["username"],
                        "enabled": True if config["downloader"]["downloader"] == "nzbget" else False,
                        "nzbAddingType": config["downloader"]["nzbAddingType"],
                        "nzbaccesstype": config["downloader"]["nzbaccesstype"]
                    })
                if config["downloader"]["sabnzbd"]["apikey"]:
                    addLogMessage(20, "Found configured downloader SABnzbd")
                    downloaders.append({
                        "name": "SABnzbd",
                        "type": "sabnzbd",
                        "defaultCategory": config["downloader"]["sabnzbd"]["defaultCategory"],
                        "apikey": config["downloader"]["sabnzbd"]["apikey"],
                        "password": config["downloader"]["sabnzbd"]["password"],
                        "url": config["downloader"]["sabnzbd"]["url"],
                        "username": config["downloader"]["sabnzbd"]["username"],
                        "enabled": True if config["downloader"]["downloader"] == "sabnzbd" else False,
                        "nzbAddingType": config["downloader"]["nzbAddingType"],
                        "nzbaccesstype": config["downloader"]["nzbaccesstype"]
                    })
                config["downloaders"] = downloaders
        if config["main"]["configVersion"] == 17:
            with version_update(config, 18):
                addLogMessage(20, "Adding secret for auth")
                config["main"]["secret"] = createSecret()
                addLogMessage(20, "Migrating auth settings")
                if len(config["auth"]["users"]) == 0:
                    addLogMessage(20, "No users configured, setting auth type to none")
                    config["auth"]["authType"] = "none"
                    config["auth"]["restrictAdmin"] = False
                    config["auth"]["restrictStats"] = False
                    config["auth"]["restrictSearch"] = False
                else:
                    addLogMessage(20, "Found configured users, setting auth type to basic")
                    config["auth"]["authType"] = "basic"
                    for user in config["auth"]["users"]:
                        if user["username"] == "" and user["password"] == "":
                            addLogMessage(20, "Found authless user, not restricting access to search")
                            config["auth"]["restrictSearch"] = False
                            if user["maySeeAdmin"]:
                                addLogMessage(20, "Found authless user with admin rights, not restricting access to admin functions")
                                config["auth"]["restrictAdmin"] = False
                            else:
                                addLogMessage(20, "Found authless user without admin rights, restricting access to admin functions")
                                config["auth"]["restrictAdmin"] = True
                            if user["maySeeStats"]:
                                addLogMessage(20, "Found authless user with admin rights, not restricting access to stats")
                                config["auth"]["restrictStats"] = False
                            else:
                                addLogMessage(20, "Found authless user without stats rights, restricting access to stats")
                                config["auth"]["restrictStats"] = True
                        else:
                            if user["maySeeAdmin"]:
                                addLogMessage(20, "Found user with admin rights,  restricting access to admin functions")
                                config["auth"]["restrictAdmin"] = True
                            if user["maySeeStats"]:
                                addLogMessage(20, "Found user with stats rights,  restricting access to stats")
                                config["auth"]["restrictStats"] = True
                    if not any([x for x in config["auth"]["users"] if x["username"] == "" and x["password"] == ""]):
                        addLogMessage(20, "Did not find an authless user, restricting access to all functions")
                        config["auth"]["restrictAdmin"] = True
                        config["auth"]["restrictStats"] = True
                        config["auth"]["restrictSearch"] = True
                # Make sure user is not locked out
                if not any([x for x in config["auth"]["users"] if x["maySeeAdmin"]]) and config["auth"]["authType"] != "none" and config["auth"]["restrictAdmin"]:
                    addLogMessage(30, "Did not find any user with admin rights, you will need to change that manually!")

        if config["main"]["configVersion"] == 18:
            with version_update(config, 19):
                addLogMessage(20, "Moving category sizes")
                categoriesToMigrate = ["movies", "movieshd", "moviessd", "tv", "tvsd", "tvhd", "audio", "flac", "mp3", "audiobook", "console", "pc", "xxx", "ebook", "comic"]
                config["categories"] = {
                    "categories": initialConfig["categories"]["categories"],
                    "enableCategorySizes": config["searching"]["categorysizes"]["enable_category_sizes"]
                }
                for category in categoriesToMigrate:
                    if category + "min" in config["searching"]["categorysizes"]:
                        if category == "audiobook":  # was saved as "audioookmin"
                            config["categories"]["categories"][category]["min"] = config["searching"]["categorysizes"]["audioookmin"]
                        else:
                            config["categories"]["categories"][category]["min"] = config["searching"]["categorysizes"][category + "min"]

                    if category + "max" in config["searching"]["categorysizes"]:
                        if category != "moviessd":  # Movies SD Max was not set in older versions
                            config["categories"]["categories"][category]["max"] = config["searching"]["categorysizes"][category + "max"]
                        else:
                            config["categories"]["categories"][category]["max"] = 3000

                config["searching"].pop("categorysizes")
                config["searching"]["forbiddenWords"] = config["searching"]["ignoreWords"]
                config["searching"]["requiredWords"] = config["searching"]["requireWords"]

        if config["main"]["configVersion"] == 19:
            with version_update(config, 20):
                for downloader in config["downloaders"]:
                    if "iconCssClass" not in downloader.keys():
                        addLogMessage(20, "Adding icon CSS class to downloader")
                        downloader["iconCssClass"] = ""

        if config["main"]["configVersion"] == 20:
            with version_update(config, 21):
                for downloader in config["downloaders"]:
                    downloader["downloadType"] = "nzb"
                for indexer in config["indexers"]:
                    addLogMessage(20, "Enabling %s for all categories" % indexer["name"])
                    indexer["categories"] = []

        if config["main"]["configVersion"] == 21:
            with version_update(config, 22):
                addLogMessage(20, "Adding anizb indexer")
                anizb = [x for x in initialConfig["indexers"] if x["name"] == "anizb"][0]
                config["indexers"].append(anizb)

        if config["main"]["configVersion"] == 22:
            config["main"]["configVersion"] = 24  # I skipped some config numbers for some reason

        if config["main"]["configVersion"] == 24:
            with version_update(config, 25):
                if config["searching"]["duplicateAgeThreshold"] == 3600:
                    addLogMessage(20, "Setting duplicate age threshold to 8 hours")
                    config["searching"]["duplicateAgeThreshold"] = 8
                if config["searching"]["duplicateSizeThresholdInPercent"] == 0.1:
                    addLogMessage(20, "Setting duplicate size threshold to 1 percent")
                    config["searching"]["duplicateSizeThresholdInPercent"] = 1.0

        # Make super sure they're set...
        for indexer in config["indexers"]:
            if "categories" not in indexer.keys():
                addLogMessage(20, "Enabling %s for all categories" % indexer["name"])
                indexer["categories"] = []

        if config["main"]["configVersion"] == 25:
            with version_update(config, 26):
                addLogMessage(20, "Migrating API hit limit reset times to hour of day")
                for indexer in config["indexers"]:
                    # When the migration from version 22 didn't work and I didn't know I told some people to manually convert the hitLimitResetTime so I must check that it's not already a number
                    if "hitLimitResetTime" in indexer.keys() and indexer["hitLimitResetTime"] and not isinstance(indexer["hitLimitResetTime"], (int, long)):
                        t = arrow.get(indexer["hitLimitResetTime"])
                        addLogMessage(20, "Setting API hit limit reset time for indexer %s to hour of day %d" % (indexer["name"], t.hour))
                        indexer["hitLimitResetTime"] = t.hour

        if config["main"]["configVersion"] == 26:
            with version_update(config, 27):
                addLogMessage(20, "Adding empty required and forbidden regexes to categories")
                for cat in config["categories"]["categories"]:
                    config["categories"]["categories"][cat]["requiredRegex"] = None
                    config["categories"]["categories"][cat]["forbiddenRegex"] = None
                config["searching"]["requiredRegex"] = None
                config["searching"]["forbiddenRegex"] = None

        if config["main"]["configVersion"] == 27:
            with version_update(config, 28):
                addLogMessage(20, "Changing omgwtfnzbs host to .me and adding backend setting to indexers. Assuming newznab by default.")
                for indexer in config["indexers"]:
                    if indexer["name"] == "omgwtfnzbs.org":
                        indexer["host"] = "https://api.omgwtfnzbs.me"
                    if indexer["type"] == "newznab":
                        indexer["backend"] = "newznab"

        if config["main"]["configVersion"] == 28:
            with version_update(config, 29):
                addLogMessage(20, "Renaming omgwtf")
                for indexer in config["indexers"]:
                    if indexer["name"].lower() == "omgwtfnzbs.org":
                        indexer["name"] = "omgwtfnzbs"

        if config["main"]["configVersion"] == 29:
            with version_update(config, 30):
                addLogMessage(20, "Attempting to remove old omgwtfnzbs and migrate to regular newznab indexer")
                omgold = None
                omgnew = None
                for indexer in config["indexers"]:
                    if indexer["type"] == "omgwtf":
                        omgold = indexer
                    elif indexer["type"] == "newznab" and "omgwtfnzbs.me" in indexer["host"].lower():
                        omgnew = indexer
                if omgold:
                    if omgnew:
                        addLogMessage(20, "Newznab indexer for omgwtf already exists. Deleting old entry for omgwtf and giving the newznab indexer the old one's name to take over most of the history and stats")
                        omgnew["name"] = omgold["name"]
                        config["indexers"].remove(omgold)
                    else:
                        if omgold["apikey"]:
                            addLogMessage(20, "You seem to be using omgwtf. Deleting old entry for omgwtf and moving settings to new newznab indexer")
                            omgnew = {
                                "accessType": omgold["accessType"],
                                "animeCategory": None,
                                "apikey": omgold["apikey"],
                                "audiobookCategory": "3030",
                                "backend": "newznab",
                                "categories": omgold["categories"],
                                "comicCategory": None,
                                "ebookCategory": "7020",
                                "enabled": omgold["enabled"],
                                "hitLimit": omgold["hitLimit"],
                                "hitLimitResetTime": omgold["hitLimitResetTime"] if "hitLimitResetTime" in omgold.keys() else None,
                                "host": "https://api.omgwtfnzbs.me",
                                "magazineCategory": None,
                                "name": omgold["name"],
                                "password": None,
                                "preselect": omgold["preselect"],
                                "score": omgold["score"],
                                "searchTypes": [
                                    "movie",
                                    "tvsearch"
                                ],
                                "search_ids": [
                                    "imdbid",
                                    "rid",
                                    "tvdbid",
                                    "tvmazeid"
                                ],
                                "showOnSearch": True,
                                "timeout": omgold["timeout"],
                                "type": "newznab",
                                "username": None
                            }
                            config["indexers"].append(omgnew)
                            config["indexers"].remove(omgold)
                        else:
                            addLogMessage(20, "You don't seem to be using omgwtf. Deleting old entry for omgwtf.")
                            config["indexers"].remove(omgold)
                else:
                    addLogMessage(20, "omgwtf not found in your settings. That's unusual but we'll keep it that way...")
                if config["categories"]["categories"]["tvhd"]["max"] == 3000:
                    addLogMessage(20, "Increasing max size for TV HD results to 4500MB")
                    config["categories"]["categories"]["tvhd"]["max"] = 4500

        if config["main"]["configVersion"] == 30:
            with version_update(config, 31):
                addLogMessage(20, "Renaming default theme to bright theme")
                if config["main"]["theme"] == "default":
                    config["main"]["theme"] = "bright"

        if config["main"]["configVersion"] == 31:
            with version_update(config, 32):
                addLogMessage(20, "Removing womble from config")
                for indexer in config["indexers"]:
                    if indexer["type"] == "womble":
                        config["indexers"].remove(indexer)

        if config["main"]["configVersion"] == 32:
            with version_update(config, 33):
                addLogMessage(20, "Updating DrunkenSlug host")
                for indexer in config["indexers"]:
                    if "drunkenslug" in indexer["host"]:
                        indexer["host"] = "https://api.drunkenslug.com"

        if config["main"]["configVersion"] in [33, 34]:
            with version_update(config, 35):
                addLogMessage(20, "Adding empty download limit to all indexers")
                for indexer in config["indexers"]:
                    if "downloadLimit" not in indexer.keys():
                        indexer["downloadLimit"] = None

        if config["main"]["configVersion"] in [35, 36]:
            with version_update(config, 37):
                addLogMessage(20, "Adding new field to users")
                for user in config["auth"]["users"]:
                    if "maySeeDetailsDl" not in user.keys():
                        user["maySeeDetailsDl"] = True
                    if "showIndexerSelection" not in user.keys():
                        user["showIndexerSelection"] = True

        if config["main"]["configVersion"] == 37:
            with version_update(config, 38):
                addLogMessage(20, "Disabling load limiting for indexers by default")
                for indexer in config["indexers"]:
                    indexer["loadLimitOnRandom"] = None

    return config


def createSecret():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))


def load(filename):
    global config_file
    global settings
    config_file = filename
    if os.path.exists(filename):
        try:
            migratedConfig = loadAndMigrateSettingsFile(filename)
            if migratedConfig:
                settings = Bunch.fromDict(update(initialConfig, migratedConfig, level="root"))
            pass
        except Exception as e:
            addLogMessage(30, "An error occurred while migrating the settings: %s" % traceback.format_exc())
            raise e
    else:
        settings = Bunch.fromDict(initialConfig)
        settings.main.secret = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))


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
    # Only use values which would actually appear in the log
    hideThese = [
        ("main.apikey", settings.main.apikey),
        ("main.externalUrl", settings.main.externalUrl),
        ("main.host", settings.main.host),
        ("main.secret", settings.main.secret),
    ]
    for i, downloader in enumerate(settings.downloaders):
        if hasattr(downloader, "apikey"):
            hideThese.append(("downloaders[%d].apikey" % i, downloader.apikey))
        if hasattr(downloader, "username"):
            hideThese.append(("downloaders[%d].username" % i, downloader.username))
        if hasattr(downloader, "password"):
            hideThese.append(("downloaders[%d].password" % i, downloader.password))
    hideThese.extend([("auth.username", x.username) for x in settings.auth.users])
    hideThese.extend([("auth.password", x.password) for x in settings.auth.users])
    for i, indexer in enumerate(settings.indexers):
        if indexer.type in ["omgwtf", "newznab"]:
            if hasattr(indexer, "apikey"):
                hideThese.append(("indexers[%d].apikey" % i, indexer.apikey))
            if hasattr(indexer, "username"):
                hideThese.append(("indexers[%d].username" % i, indexer.username))
    return hideThese


def import_config_data(data):
    global settings
    global config_file
    settings = Bunch.fromDict(data)
    save(config_file)


def save(filename=None):
    global config_file
    if filename is None:
        filename = config_file
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


def getCategorySettingByName(name):
    for k, v in settings["categories"]["categories"].items():
        if name == k:
            return v


def getSafeConfig():
    indexers = [{"name": x["name"], "preselect": x["preselect"], "enabled": x["enabled"], "categories": x["categories"] if "categories" in x.keys() else [], "showOnSearch": x["showOnSearch"] and x["accessType"] != "external"} for x in settings["indexers"]]

    return {
        "indexers": indexers,
        "searching": {"maxAge": settings["searching"]["maxAge"], "alwaysShowDuplicates": settings["searching"]["alwaysShowDuplicates"], "enableCategorySizes": settings["categories"]["enableCategorySizes"]},
        "categories": categories.getCategories(),
        "downloaders": [{"enabled": x.enabled, "name": x.name, "type": x.type, "iconCssClass": x.iconCssClass, "defaultCategory": x.defaultCategory if hasattr(x, "defaultCategory") else None} for x in settings["downloaders"]],
        "authType": settings["auth"]["authType"],
        "dereferer": settings["main"]["dereferer"],
        "pollShown": settings["main"]["pollShown"],
        "firstStart": settings["main"]["firstStart"]
    }
