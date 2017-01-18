from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import arrow
from future import standard_library
from peewee import IntegrityError
from requests import RequestException

#standard_library.install_aliases()
from builtins import *
import logging
import requests
import tmdbsimple
import pytvmaze
from furl import furl
from enum import Enum
from requests.exceptions import ReadTimeout
from requests.packages.urllib3.exceptions import HTTPError, ConnectionError

from nzbhydra import webaccess
from nzbhydra.exceptions import ExternalApiInfoException
from nzbhydra.database import TvIdCache, MovieIdCache

logger = logging.getLogger('root')

tmdbsimple.API_KEY = '4df99d58875c2d01fc04936759fea56f'
tmdb_img_config = None


class TvMaze:
    
    def __init__(self, tvmazeid, rageid, tvdbid, title, poster):
        self.tvmazeid = tvmazeid
        self.rageid = rageid
        self.tvdbid = tvdbid
        self.title = title
        self.poster = poster
     

    @staticmethod
    def byId(idType, id):
        logger.info("Requesting info for %s key %s from TVMaze" % (idType, id))
        try:
            if idType == "thetvdb":
                info = pytvmaze.get_show(tvdb_id=id)
            elif idType == "tvrage":
                info = pytvmaze.get_show(tvrage_id=id)
            elif idType == "tvmaze":
                info = pytvmaze.get_show(maze_id=id)
            else:
                logger.error("Invalid call to byId() using idType %s" % idType)
                return None
            
        except pytvmaze.ShowNotFound:
            logger.error("Unable to find show on TVMaze")
            return None
        externals = info.externals
        rageid = externals["tvrage"] if "tvrage" in externals.keys() else None
        tvdbid = externals["thetvdb"] if "thetvdb" in externals.keys() else None
        title = info.name
        poster = info.image["medium"] if "medium" in info.image.keys() else None
        return TvMaze(info.id, rageid, tvdbid, title, poster)


def find_movie_ids(input):
    global tmdb_img_config
    if tmdb_img_config is None:
        tmdb_img_config = tmdbsimple.Configuration().info()["images"]
    base_url = tmdb_img_config["secure_base_url"]
    poster_size = "w92" if "w92" in tmdb_img_config["poster_sizes"] else tmdb_img_config["poster_sizes"][0]

    search = tmdbsimple.Search()
    results = search.movie(query=input)["results"]
    infos = []
    for s in results:
        title = s["title"]
        if "release_date" in s.keys() and s["release_date"] != "":
            title = "%s (%s)" % (title, arrow.get(s["release_date"]).year)
        result = {"label": title, "value": s["id"], "title": s["title"]}
        if "poster_path" in s and s["poster_path"]:
            result["poster"] = base_url + poster_size + s["poster_path"]
            infos.append(result)
    return infos


def tmdbid_to_imdbid(tmdbid):
    logger.info("Querying TMDB for IMDB id %s" % tmdbid)
    movie = tmdbsimple.Movies(tmdbid)
    response = movie.info()
    imdbid = response["imdb_id"][2:]
    title = response["title"]
    logger.info("Found TMDB id %s for IMDB id %s" % (tmdbid, imdbid))
    return imdbid, title


def imdbid_to_tmdbid(imdbid):
    logger.info("Querying TMDB for TMDB id %s" % imdbid)
    movie = tmdbsimple.Find("tt" + imdbid)
    response = movie.info(external_source="imdb_id")
    movie_results_ = response["movie_results"]
    if len(movie_results_) == 0:
        logger.error("Found no movie with IMDB id %s" % imdbid)
        return None, None
    if len(movie_results_) != 1:
        logger.error("Expected 1 result but got %d" % len(movie_results_))
    tmdbid = movie_results_[0]["id"]
    title = movie_results_[0]["title"]
    logger.info("Found IMDB id %s for TMDB id %s" % (imdbid, tmdbid))
    return str(tmdbid), title



def find_series_ids(input):
    info = webaccess.get("http://api.tvmaze.com/search/shows?q=%s" % input)
    info.raise_for_status()
    results = []
    for result in info.json():
        result = result["show"]
        if result["externals"]["thetvdb"] is None:
            logger.info("Did not find TVDB ID for %s. Will skip this result." % result["name"])
            continue
        info = {"label": result["name"], "value": str(result["externals"]["thetvdb"]), "title": result["name"]}
        try:
            info["poster"] = result["image"]["medium"]
        except:
            logger.debug("No poster found for %s" % result["name"])
            pass
        results.append(info)
    return results


def title_from_id(identifier_key, identifier_value):
    if identifier_key is None or identifier_value is None:
        raise AttributeError("Neither identifier key nor value were supplied")
    try:
        if identifier_key == "imdbid":
            if identifier_value[0:2] != "tt":
                identifier_value = "tt%s" % identifier_value
            url = furl("http://www.omdbapi.com").add({"i": identifier_value, "plot": "short", "r": "json"}).tostr()
            omdb = webaccess.get(url)
            return omdb.json()["Title"]

        if identifier_key not in ("rid", "tvdbid"):
            raise AttributeError("Unknown identifier %s" % identifier_key)

        tvmaze_key = "tvrage" if identifier_key == "rid" else "thetvdb"
        tvmaze = webaccess.get(furl("http://api.tvmaze.com/lookup/shows").add({tvmaze_key: identifier_value}).url)
        if tvmaze.status_code == 404:
            #Unfortunately TVMaze returns a 404 for unknown/invalid IDs
            raise ExternalApiInfoException("Unable to find id %s and value %s at TVMaze" % (identifier_key, identifier_value))
        tvmaze.raise_for_status()
        
        return tvmaze.json()["name"]

    except (HTTPError, ConnectionError, ReadTimeout) as e:
        logger.exception("Unable to retrieve title by id %s and value %s" % (identifier_key, identifier_value))
        raise ExternalApiInfoException(str(e))
    except Exception as e:
        logger.exception("Unable to retrieve title by id %s and value %s" % (identifier_key, identifier_value))
        raise ExternalApiInfoException(str(e))


def canConvertId(fromType, toType):
    fromType = fromType.replace("rid", "tvrage").replace("id", "")
    toType = toType.replace("rid", "tvrage").replace("id", "")
    conversionMap = {"imdb": ["tmdb"],
                     "tmdb": ["imdb"],
                     "tvrage": ["tvdb", "tvmaze"],
                     "tvdb": ["tvrage", "tvmaze"],
                     "tvmaze": ["tvdb", "tvrage"]
                     }
    return toType == "title" or (fromType in conversionMap.keys() and toType in conversionMap[fromType])


def canConvertList(fromId, toIdList):
    return any([canConvertId(fromId, x) for x in toIdList])


def _tryFromCache(fromType, toType, id):
    #Return a tuple of a boolean which indicates if a cache entry was found and the cache entry or None
    #This way we will know if a cache entry exists or the cached value is None 
    try:
        if fromType == "tvrage":
            cacheEntry = TvIdCache.get(TvIdCache.tvrage == id)
        elif fromType == "tvdb":
            cacheEntry = TvIdCache.get(TvIdCache.tvdb == id)
        elif fromType == "tvmaze":
            cacheEntry = TvIdCache.get(TvIdCache.tvmaze == id)
        elif fromType == "imdb":
            cacheEntry = MovieIdCache.get(MovieIdCache.imdb == id)
        elif fromType == "tmdb":
            cacheEntry = MovieIdCache.get(MovieIdCache.tmdb == id)
        else:
            return False, None
    except (TvIdCache.DoesNotExist, MovieIdCache.DoesNotExist):
        return False, None
    return True, cacheEntry
        


def _cacheTvMazeIds(tvMaze):
    try:
        cacheEntry = TvIdCache(tvmaze=tvMaze.tvmazeid, tvrage=tvMaze.rageid, tvdb=tvMaze.tvdbid, title=tvMaze.title)
        cacheEntry.save()
        return cacheEntry
    except IntegrityError as e:
        logger.debug("Unable to save cached TvMaze entry to database. Probably already exists")
        pass
    except Exception:
        logger.exception("Unable to save cached TvMaze entry to database")
        pass


def convertId(fromType, toType, id):
    logger.info("Converting from %s value %s to %s " % (fromType, id, toType))
    #Clean up names
    fromType = fromType.replace("rid", "tvrage").replace("id", "")
    toType = toType.replace("rid", "tvrage").replace("id", "")
    if fromType.replace("rid", "tvrage").replace("id", "") == toType.replace("rid", "tvrage").replace("id", ""):
        return id
    
    if toType != "title" and not canConvertId(fromType, toType):
        logger.error("Unable to convert from %s to %s" % (fromType, toType))
        return None
    
    hasCacheEntry, result = _tryFromCache(fromType, toType, id)
    if hasCacheEntry:
        logger.debug("Found conversion from %s value %s to %s in cache" % (fromType, id, toType))
    
    elif fromType == "imdb":
        convertedId, title = imdbid_to_tmdbid(id)
        if convertedId is None:
            return None
        result = MovieIdCache(tmdb=convertedId, imdb=id, title=title) 
        result.save()
        
    elif fromType == "tmdb":
        convertedId, title = tmdbid_to_imdbid(id)
        if convertedId is None:
            return None
        result = MovieIdCache(imdb=convertedId, tmdb=id, title=title)
        result.save()
    
    elif fromType in ("tvrage", "tvdb", "tvmaze"):
        fromType = fromType.replace("tvdb", "thetvdb") #TVMaze uses "thetvdb"...
        result = TvMaze.byId(fromType, id)
        if result is None:
            return None
        result = _cacheTvMazeIds(result)

    if result is None:
        return None
    wantedType = getattr(result, toType)
    if wantedType is None:
        return None
    
    logger.info("Successfully converted from %s value %s to %s " % (fromType, id, toType))
    if isinstance(wantedType, int):
        return str(wantedType)
    return wantedType
    

def convertIdToAny(fromType, possibleToTypes, id):
    """
    Attempts to convert from a given ID to any of the possible IDs
    :param fromType: The ID which we know
    :param possibleToTypes: A list of IDs we would want
    :param id: The ID
    :return: Tuple: True or False for result, type of the converted id, the converted id
    """
    if not isinstance(possibleToTypes, list):
        possibleToTypes = [possibleToTypes]
    fromType = fromType.replace("rid", "tvrage").replace("id", "")
    possibleToTypes = [x.replace("rid", "tvrage").replace("id", "") for x in possibleToTypes]
    if fromType in possibleToTypes:
        return True, fromType, id
    for possibleToType in possibleToTypes:
        if canConvertId(fromType, possibleToType):
            result = convertId(fromType, possibleToType, id)
            return True if result is not None else False, possibleToType, result 
    else:
        logger.info("Unable to convert from ID type %s to any of %s" % (fromType, ",".join(possibleToTypes)))
        return False, None, None
    
    
    
    