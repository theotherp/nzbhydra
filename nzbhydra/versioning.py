from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library

standard_library.install_aliases()
from builtins import *
import logging


from nzbhydra import config
import requests

 
repository_url = "https://github.com/theotherp/nzbhydra"

logger = logging.getLogger('root')


def check_for_new_version():
    new_version_available, new_version = is_new_version_available()
    if new_version_available:
        logger.info(("New version %s available at %s" % (new_version, repository_url)))


def get_rep_version():
    try:
        from distutils.version import StrictVersion
        url = "https://raw.githubusercontent.com/theotherp/nzbhydra/" + config.mainSettings.branch.get() + "/version.txt"
        r = requests.get(url, verify=False)
        r.raise_for_status()
        return StrictVersion(r.text)
    except (ImportError, AttributeError):
        logger.error("Error while getting repository version: Unable to import StrictVersion. Are you running this in virtualenv?")
        return None
    except requests.RequestException as e:
        logger.error("Error downloading version.txt from %s to check new updates: %s" % (url, e))
        return None


def get_current_version():
    try:
        from distutils.version import StrictVersion
        with open("version.txt", "r") as f:
            version = f.read()
        return StrictVersion(version)
    except (ImportError, AttributeError):
        logger.error("Error while getting current version: Unable to import StrictVersion. Are you running this in virtualenv?")
        return None
    except Exception as e:
        logger.error("Unable to open version.txt: %s" % e)
        return None


def is_new_version_available():
    rep_version = get_rep_version()
    current_version = get_current_version()
    try:
        if rep_version is not None and current_version is not None:
            return rep_version > current_version, rep_version
    except Exception as e:
        logger.error("Error while comparion versions: %s" % e)
        return False, None
    return False, None
        
