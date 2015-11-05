import logging
from distutils.version import StrictVersion

import requests

version_txt_url = "https://raw.githubusercontent.com/theotherp/nzbhydra/master/version.txt"
repository_url = "https://github.com/theotherp/nzbhydra"

logger = logging.getLogger('root')


def check_for_new_version():
    if is_new_version_available():
        logger.info(("New version %s available at %s" % (get_current_version(), repository_url)))


def get_rep_version():
    try:
        r = requests.get(version_txt_url)
        r.raise_for_status()
        return StrictVersion(r.text)
    except requests.exceptions.ConnectionError:
        logger.error("Error download repository version.txt for version check")
        return None


def get_current_version():
    with open("version.txt", "r") as f:
        version = f.read()
    return version


def is_new_version_available():
    return get_rep_version() > get_current_version()
