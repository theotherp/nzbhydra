import concurrent
from concurrent.futures import ThreadPoolExecutor
import copy
import logging

import arrow
from requests_futures.sessions import FuturesSession

from nzbhydra.config import searchingSettings
from nzbhydra.database import IndexerStatus, Search
from nzbhydra import config, indexers, infos

categories = {'All': {"pretty": "All", "index": 0},
              'Movies': {"pretty": "Movie", "index": 1},
              'Movies HD': {"pretty": "HD", "index": 2},
              'Movies SD': {"pretty": "SD", "index": 3},
              'TV': {"pretty": "TV", "index": 4},
              'TV SD': {"pretty": "SD", "index": 5},
              'TV HD': {"pretty": "HD", "index": 6},
              'Audio': {"pretty": "Audio", "index": 7},
              'Audio FLAC': {"pretty": "Audio FLAC", "index": 8},
              'Audio MP3': {"pretty": "Audio MP3", "index": 9},
              'Console': {"pretty": "Console", "index": 10},
              'PC': {"pretty": "PC", "index": 11},
              'XXX': {"pretty": "XXX", "index": 12}
              }

logger = logging.getLogger('root')

session = FuturesSession()


class SearchRequest(object):
    def __init__(self, type=None, query=None, identifier_key=None, identifier_value=None, season=None, episode=None, title=None, category=None, minsize=None, maxsize=None, minage=None, maxage=None, offset=0, limit=100):
        self.type = type
        self.query = query
        self.identifier_key = identifier_key
        self.identifier_value = identifier_value
        self.title = title
        self.season = season
        self.episode = episode
        self.category = category
        self.minsize = minsize
        self.maxsize = maxsize
        self.minage = minage
        self.maxage = maxage
        self.offset = offset
        self.limit = limit

    @property
    def search_hash(self):
        return hash(frozenset([self.type, self.query, self.identifier_key, self.identifier_value, self.title, self.season, self.episode, self.category, self.minsize, self.maxsize, self.minage, self.maxage]))


def pick_indexers(query_supplied=True, identifier_key=None, internal=True, selected_indexers=None):
    picked_indexers = []
    selected_indexers = selected_indexers.split(",") if selected_indexers is not None else None
    with_query_generation = False
    for p in indexers.configured_indexers:
        if not p.settings.enabled.get():
            logger.debug("Did not pick %s because it is disabled" % p)
            continue
        if selected_indexers and p.name not in selected_indexers:
            logger.debug("Did not pick %s because it was not selected by the user" % p)
            continue
        try:
            status = p.indexer.status.get()
            if status.disabled_until > arrow.utcnow() and searchingSettings.temporarilyDisableProblemIndexers.get_with_default(True):
                logger.info("Did not pick %s because it is disabled temporarily due to an error: %s" % (p, status.reason))
                continue
        except IndexerStatus.DoesNotExist:
            pass

        # if category is not None and p.indexer.settings.get("categories") is not None and category not in p.indexer.settings.get("categories", []):
        #     logger.debug("Did not pick %s because it is not enabled for category %s" % (p, category))
        #     continue
        if query_supplied and not p.supports_queries:
            logger.debug("Did not pick %s because a query was supplied but the indexer does not support queries" % p)
            continue
        if not query_supplied and p.needs_queries and identifier_key is None:
            logger.debug("Did not pick %s because no query was supplied but the indexer needs queries" % p)
            continue
        allow_query_generation = (config.InternalExternalSelection.internal.name in config.searchingSettings.generate_queries.get() and internal) or (config.InternalExternalSelection.external.name in config.searchingSettings.generate_queries.get() and not internal)
        if (identifier_key is not None and identifier_key not in p.settings.search_ids.get()) and not (allow_query_generation and p.generate_queries):
            logger.debug("Did not pick %s because search will be done by an identifier and the indexer or system wide settings don't allow query generation" % p)
            continue
        else:
            with_query_generation = True

        picked_indexers.append(p)

    return picked_indexers, with_query_generation


pseudo_cache = {}


def search(internal, search_request: SearchRequest):
    for k in list(pseudo_cache.keys()):
        if pseudo_cache[k]["last_access"].replace(minutes=+5) < arrow.utcnow():
            pseudo_cache.pop(k)
    limit = search_request.limit  # todo use actual configured limit
    external_offset = int(search_request.offset)
    search_hash = search_request.search_hash
    if search_hash not in pseudo_cache.keys():
        print("Didn't find this query in cache")
        cache_entry = {"results": [], "indexer_infos": {}, "total": 0, "last_access": arrow.utcnow(), "offset": 0}
        indexers_to_call, with_query_generation = pick_indexers(query_supplied=True if search_request.query is not None else False, identifier_key=search_request.identifier_key, internal=internal)
        for p in indexers_to_call:
            cache_entry["indexer_infos"][p] = {"has_more": True, "search_request": search_request, "total_included": False}
        dbsearch = Search(internal=internal, query=search_request.query, category=search_request.category, identifier_key=search_request.identifier_key, identifier_value=search_request.identifier_value, season=search_request.season, episode=search_request.episode)
        dbsearch.save()
        cache_entry["dbsearch"] = dbsearch

        if with_query_generation and search_request.identifier_key and search_request.title is None:
            search_request.title = infos.title_from_id(search_request.identifier_key, search_request.identifier_value)
        pseudo_cache[search_hash] = cache_entry
    else:
        cache_entry = pseudo_cache[search_hash]
        indexers_to_call = [indexer for indexer, info in cache_entry["indexer_infos"].items() if info["has_more"]]
        dbsearch = cache_entry["dbsearch"]
        print("Found search in cache")

    print("Will search at indexers as long as we don't have enough results for the current offset+limit and any indexer has more results.")
    while len(cache_entry["results"]) < external_offset + limit and len(indexers_to_call) > 0:
        print("We want %d results but have only %d so far" % ((external_offset + limit), len(cache_entry["results"])))
        print("%d indexers still have results" % len(indexers_to_call))
        search_request.offset = cache_entry["offset"]
        print("Searching indexers with offset %d" % search_request.offset)
        result = search_and_handle_db(dbsearch, {x: search_request for x in indexers_to_call})
        search_results = []
        indexers_to_call = []
        for indexer, queries_execution_result in result["results"].items():
            search_results.extend(queries_execution_result.results)
            print("%s returned %d results" % (indexer, len(queries_execution_result.results)))
            cache_entry["indexer_infos"][indexer].update({"search_request": search_request, "has_more": queries_execution_result.has_more, "total": queries_execution_result.total, "total_known": queries_execution_result.total_known, "indexer_search": queries_execution_result.dbentry})
            if queries_execution_result.has_more:
                indexers_to_call.append(indexer)
                print("%s still has more results so we could use it the next round" % indexer)

            if queries_execution_result.total_known:
                if not cache_entry["indexer_infos"][indexer]["total_included"]:
                    cache_entry["total"] += queries_execution_result.total
                    print("%s reports %d total results. We'll include in the total this time only" % (indexer, queries_execution_result.total))
                    cache_entry["indexer_infos"][indexer]["total_included"] = True
            elif queries_execution_result.has_more:
                print("%s doesn't report an exact number of results so let's just add another 100 to the total" % indexer)
                cache_entry["total"] += 100

        search_results = sorted(search_results, key=lambda x: x.epoch, reverse=True)
        cache_entry["results"].extend(search_results)
        cache_entry["offset"] += limit
        #todo: perhaps move duplicate handling here. WOuld allow to recognize duplicates that were added, for example 100 were already loaded and then we get 101-200 und 100 and 101 are duplicates
        #todo: then make configurable if we want to delete duplicates for api, internal, both, none. would also mean that we return 100 actually different results, otherwise in the worst case we could for example return 50 originals and 50 duplicates
    
    
    if internal:
        print("We have %d cached results and them all because we search internally" % len(cache_entry["results"]))
        nzb_search_results = copy.deepcopy(cache_entry["results"][external_offset:])
    else:
        print("We have %d cached results and return %d-%d of %d total available accounting for the limit set for the API search" % (len(cache_entry["results"]), external_offset, external_offset + limit, cache_entry["total"]))
        nzb_search_results = copy.deepcopy(cache_entry["results"][external_offset:(external_offset + limit)])
    cache_entry["last_access"] = arrow.utcnow()
    
    
    return {"results": nzb_search_results, "indexer_infos": cache_entry["indexer_infos"], "dbsearch": cache_entry["dbsearch"].id, "total": cache_entry["total"], "offset": external_offset}


def search_and_handle_db(dbsearch, indexers_and_search_requests):
    results_by_indexer = start_search_futures(indexers_and_search_requests)
    for i in results_by_indexer.values():
        indexersearchentry = i.dbentry
        indexersearchentry.search = dbsearch
        indexersearchentry.save()
    logger.debug("Returning search results now")
    return {"results": results_by_indexer, "dbsearchid": dbsearch.id}


def execute(indexer, search_function, args):
    return getattr(indexer, search_function)(args)


def start_search_futures(indexers_and_search_requests):
    indexer_to_searchresults = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(indexers_and_search_requests)) as executor:
        futures_to_indexers = {}
        count = 1
        for indexer, search_request in indexers_and_search_requests.items():
            future = executor.submit(indexer.search, search_request)
            futures_to_indexers[future] = indexer
            logger.debug("Added %d of %d calls to executor" % (count, len(indexers_and_search_requests)))
            count += 1
        count = 1
        for f in concurrent.futures.as_completed(futures_to_indexers.keys()):
            results = f.result()
            indexer_to_searchresults[futures_to_indexers[f]] = results
            logger.debug("Retrieved %d of %d calls from executor" % (count, len(futures_to_indexers)))
            count += 1

    return indexer_to_searchresults
