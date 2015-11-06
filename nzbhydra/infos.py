from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
import json
import logging
from furl import furl
import requests
from nzbhydra.exceptions import ExternalApiInfoException

logger = logging.getLogger('root')


def find_movie_ids(input):
    info = requests.get("http://www.omdbapi.com/?s=%s" % input)
    info.raise_for_status()
    results = []
    if "Search" not in info.json():
        return []
    for result in info.json()["Search"]:
        if result["Type"] == "Series":
            continue
        results.append({"label": result["Title"], "year": result["Year"], "value": result["imdbID"][2:]})
    return results
        

def find_series_ids(input):
    info = requests.get("http://api.tvmaze.com/search/shows?q=%s" % input)
    info.raise_for_status()
    results = []
    for result in info.json():
        result = result["show"]
        results.append({"label": result["name"], "value": result["externals"]["thetvdb"]})
    return results
        
    
def title_from_id(identifier_key, identifier_value):
    if identifier_key is None or identifier_value is None:
        raise AttributeError("Neither identifier key nor value were supplied")
    try:
        if identifier_key == "imdbid":
            if identifier_value[0:2] != "tt":
                identifier_value = "tt%s" % identifier_value
            url = furl("http://www.omdbapi.com").add({"i": identifier_value, "plot": "short", "r": "json"}).tostr()
            omdb = requests.get(url)
            return omdb.json()["Title"]

        if identifier_key not in ("rid", "tvdbid"):
            raise AttributeError("Unknown identifier %s" % identifier_key)

        tvmaze_key = "tvrage" if identifier_key == "rid" else "thetvdb"
        tvmaze = requests.get(furl("http://api.tvmaze.com/lookup/shows").add({tvmaze_key: identifier_value}).url)
        return tvmaze.json()["name"]

    except Exception as e:
        logger.exception("Unable to retrieve title by id %s and value %s" % (identifier_key, identifier_value))
        raise ExternalApiInfoException(e)

