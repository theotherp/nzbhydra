from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library

from requests import RequestException

standard_library.install_aliases()
from builtins import *
import logging
import requests
import tmdbsimple
from furl import furl
from enum import Enum
from nzbhydra.exceptions import ExternalApiInfoException
from nzbhydra.database import TvIdCache, MovieIdCache

logger = logging.getLogger('root')

tmdbsimple.API_KEY = '4df99d58875c2d01fc04936759fea56f'
tmdb_img_config = None


class TvMaze:
    
    class IdType(Enum):
        tvmaze = "tvmaze"
        tvrage = "tvrage"
        tvdb = "thetvdb"      
    
    def __init__(self, tvmazeid, rageid, tvdbid, title, poster, all):
        self.tvmazeid = tvmazeid
        self.rageid = rageid
        self.tvdbid = tvdbid
        self.title = title
        self.poster = poster
        self.all = all
     

    @staticmethod
    def byId(idType, id):
        try:
            if idType == TvMaze.IdType.tvdb.value or idType == TvMaze.IdType.tvrage.value:
                info = requests.get(furl("http://api.tvmaze.com/lookup/shows").add({idType: id}).url)
            elif idType == TvMaze.IdType.tvmaze.value:
                info = requests.get(furl("http://api.tvmaze.com/shows/").add(path=id).url)
            else:
                logger.error("Invalid call to byId() using idType %s" % idType)
                return None
            info.raise_for_status()
        except RequestException as e:
            logger.exception("Unable to contact TVMaze")
            return None
        json = info.json()
        externals = json["externals"]
        rageid = externals["tvrage"] if "tvrage" in externals.keys() else None
        tvdbid = externals["thetvdb"] if "thetvdb" in externals.keys() else None
        title = json["name"]
        poster = json["image"]["medium"] if "medium" in json["image"].keys() else None
        return TvMaze(json["id"], rageid, tvdbid, title, poster, json)


def find_movie_ids(input):
    global tmdb_img_config
    if tmdb_img_config is None:
        tmdb_img_config = tmdbsimple.Configuration().info()["images"]
    base_url = tmdb_img_config["secure_base_url"]
    poster_size = "w92" if "w92" in tmdb_img_config["poster_sizes"] else tmdb_img_config["poster_sizes"][0]

    search = tmdbsimple.Search()
    results = search.movie(query=input)
    infos = []
    for s in results:
        result = {"label": s["title"], "value": s["id"]}
        if "poster_path" in s and s["poster_path"]:
            result["poster"] = base_url + poster_size + s["poster_path"]
            infos.append(result)
    return infos


def tmdbid_to_imdbid(tmdbid):
    logger.info("Querying IMDB for TMDB id %s" % tmdbid)
    movie = tmdbsimple.Movies(tmdbid)
    response = movie.info()
    imdbid = response["imdb_id"][2:]
    logger.info("Found TMDB id %s for IMDB id %s" % (tmdbid, imdbid))
    return imdbid


def imdbid_to_tmdbid(imdbid):
    logger.info("Querying TMDB for IMDB id %s" % imdbid)
    movie = tmdbsimple.Find(imdbid)
    response = movie.info(external_source="imdb_id")
    movie_results_ = response["movie_results"]
    if len(movie_results_) != 1:
        logger.error("Expected 1 result but got %d" % len(movie_results_))
    tmdbid = movie_results_[0]["id"]
    logger.info("Found IMDB id %s for TMDB id %s" % (imdbid, tmdbid))
    return str(tmdbid)



def find_series_ids(input):
    info = requests.get("http://api.tvmaze.com/search/shows?q=%s" % input)
    info.raise_for_status()
    results = []
    for result in info.json():
        result = result["show"]
        if result["externals"]["thetvdb"] is None:
            logger.info("Did not find TVDB ID for %s. Will skip this result." % result["name"])
            continue
        info = {"label": result["name"], "value": str(result["externals"]["thetvdb"])}
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
            omdb = requests.get(url)
            return omdb.json()["Title"]

        if identifier_key not in ("rid", "tvdbid"):
            raise AttributeError("Unknown identifier %s" % identifier_key)

        tvmaze_key = "tvrage" if identifier_key == "rid" else "thetvdb"
        tvmaze = requests.get(furl("http://api.tvmaze.com/lookup/shows").add({tvmaze_key: identifier_value}).url)
        return tvmaze.json()["name"]

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
    return fromType in conversionMap.keys() and toType in conversionMap[fromType]


def canConvertList(fromId, toIdList):
    return any([canConvertId(fromId, x) for x in toIdList])


def _tryFromCache(fromType, toType, id):
    #Return a tuple of a boolean which indicates if a cache entry was found and the cache entry or None
    #This way we will know if a cache entry exists or the cached value is None 
    try:
        if fromType == "tvrage":
            id = TvIdCache.get(TvIdCache.tvrage == id)
        elif fromType == "tvdb":
            id = TvIdCache.get(TvIdCache.tvdb == id)
        elif fromType == "tvmaze":
            id = TvIdCache.get(TvIdCache.tvmaze == id)
        elif fromType == "imdb":
            id = MovieIdCache.get(MovieIdCache.imdb == id)
        elif fromType == "tmdb":
            id = MovieIdCache.get(MovieIdCache.tmdb == id)
        else:
            return False, None
    except (TvIdCache.DoesNotExist, MovieIdCache.DoesNotExist):
        return False, None
    if toType == "tvdb":
        return True, id.tvdb
    elif toType == "tvrage":
        return True, id.tvrage
    elif toType == "tvmaze":
        return True, id.tvmaze
    elif toType == "imdb":
        return True, id.imdb
    elif toType == "tmdb":
        return True, id.tmdb
    else:
        return False, None


def _cacheTvMazeIds(tvMaze):
    try:
        TvIdCache(tvmaze=tvMaze.tvmazeid, tvrage=tvMaze.rageid, tvdb=tvMaze.tvdbid).save()
    except Exception:
        logger.exception("Unable to save cached TvMaze entry to database")
        pass


def convertId(fromType, toType, id):
    logger.info("Converting %s value %s from %s " % (toType, id, fromType))
    #Clean up names
    fromType = fromType.replace("rid", "tvrage").replace("id", "")
    toType = toType.replace("rid", "tvrage").replace("id", "")
    
    if fromType == toType:
        return id
    
    if not canConvertId(fromType, toType):
        logger.error("Unable to convert from %s to %s" % (fromType, toType))
        return None
    
    hasCacheEntry, fromCache = _tryFromCache(fromType, toType, id)
    if hasCacheEntry:
        logger.debug("Returning %s value %s from %s from cache" % (toType, id, fromType))
        return fromCache
    
    if fromType == "imdb":
        result = imdbid_to_tmdbid(id)
        MovieIdCache(tmdb=result, imdb=id).save()
        return result
        
    
    if fromType == "tmdb":
        result = tmdbid_to_imdbid(id)
        MovieIdCache(imdb=result, tmdb=id).save()
        return result
    
    if fromType in ("tvrage", "tvdb", "tvmaze"):
        fromType = fromType.replace("tvdb", "thetvdb") #TVMaze uses "thetvdb"...
        result = TvMaze.byId(fromType, id)
        if result is None:
            return None
        _cacheTvMazeIds(result)
        if toType == "tvdb":
            return str(result.tvdbid)
        if toType == "tvmaze":
            return str(result.tvmazeid)
        if toType == "tvrage":
            return str(result.rageid)
    
    return None


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
    
    
    
    