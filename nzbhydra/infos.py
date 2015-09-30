import json
import logging
import requests

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
        
    

