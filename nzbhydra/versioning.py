from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# standard_library.install_aliases()
from builtins import *
import logging
from distutils.version import StrictVersion
from nzbhydra import config
import requests

version_txt_url = "https://raw.githubusercontent.com/theotherp/nzbhydra/" + config.mainSettings.branch.get() + "/version.txt"
repository_url = "https://github.com/theotherp/nzbhydra"

logger = logging.getLogger('root')


def check_for_new_version():
    new_version_available, new_version = is_new_version_available()
    if new_version_available:
        logger.info(("New version %s available at %s" % (new_version, repository_url)))


def get_rep_version():
    try:
        r = requests.get(version_txt_url, verify=False)
        r.raise_for_status()
        return StrictVersion(r.text)
    except requests.RequestException as e:
        logger.error("Error downloading version.txt from %s to check new updates: %s" % (version_txt_url, e))
        return None


def get_current_version():
    try: 
        with open("version.txt", "r") as f:
            version = f.read()
        return StrictVersion(version)
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
        
