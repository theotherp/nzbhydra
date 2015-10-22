import concurrent
from concurrent.futures import ThreadPoolExecutor
import copy
import logging

import arrow
from requests_futures.sessions import FuturesSession

from nzbhydra.config import searchingSettings
from nzbhydra.database import ProviderStatus, Search
from nzbhydra import config, providers, infos

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


def pick_providers(query_supplied=True, identifier_key=None, internal=True, selected_providers=None):
    picked_providers = []
    selected_providers = selected_providers.split(",") if selected_providers is not None else None
    with_query_generation = False
    for p in providers.configured_providers:
        if not p.settings.enabled.get():
            logger.debug("Did not pick %s because it is disabled" % p)
            continue
        if selected_providers and p.name not in selected_providers:
            logger.debug("Did not pick %s because it was not selected by the user" % p)
            continue
        try:
            status = p.provider.status.get()
            if status.disabled_until > arrow.utcnow() and searchingSettings.temporarilyDisableProblemIndexers.get_with_default(True):
                logger.info("Did not pick %s because it is disabled temporarily due to an error: %s" % (p, status.reason))
                continue
        except ProviderStatus.DoesNotExist:
            pass

        # if category is not None and p.provider.settings.get("categories") is not None and category not in p.provider.settings.get("categories", []):
        #     logger.debug("Did not pick %s because it is not enabled for category %s" % (p, category))
        #     continue
        if query_supplied and not p.supports_queries:
            logger.debug("Did not pick %s because a query was supplied but the provider does not support queries" % p)
            continue
        if not query_supplied and p.needs_queries and identifier_key is None:
            logger.debug("Did not pick %s because no query was supplied but the provider needs queries" % p)
            continue
        allow_query_generation = (config.InternalExternalSelection.internal.name in config.searchingSettings.generate_queries.get() and internal) or (config.InternalExternalSelection.external.name in config.searchingSettings.generate_queries.get() and not internal)
        if (identifier_key is not None and identifier_key not in p.settings.search_ids.get()) and not (allow_query_generation and p.generate_queries):
            logger.debug("Did not pick %s because search will be done by an identifier and the provider or system wide settings don't allow query generation" % p)
            continue
        else:
            with_query_generation = True

        picked_providers.append(p)

    return picked_providers, with_query_generation


pseudo_cache = {}


def search(internal, search_request: SearchRequest):
    for k, v in pseudo_cache.items():
        if v["last_access"].replace(minutes=+5) < arrow.utcnow():
            pseudo_cache.pop(k)
    limit = search_request.limit  # todo use actual configured limit
    external_offset = int(search_request.offset)
    search_hash = search_request.search_hash
    if search_hash not in pseudo_cache.keys():
        print("Didn't find this query in cache")
        cache_entry = {"results": [], "provider_infos": {}, "total": 0, "last_access": arrow.utcnow(), "offset": 0}
        providers_to_call, with_query_generation = pick_providers(query_supplied=True if search_request.query is not None else False, identifier_key=search_request.identifier_key, internal=internal)
        for p in providers_to_call:
            cache_entry["provider_infos"][p] = {"has_more": True, "search_request": search_request, "total_included": False}
        dbsearch = Search(internal=internal, query=search_request.query, category=search_request.category, identifier_key=search_request.identifier_key, identifier_value=search_request.identifier_value, season=search_request.season, episode=search_request.episode)
        dbsearch.save()
        cache_entry["dbsearch"] = dbsearch

        if with_query_generation and search_request.identifier_key and search_request.title is None:
            search_request.title = infos.title_from_id(search_request.identifier_key, search_request.identifier_value)
        pseudo_cache[search_hash] = cache_entry
    else:
        cache_entry = pseudo_cache[search_hash]
        providers_to_call = [provider for provider, info in cache_entry["provider_infos"].items() if info["has_more"]]
        dbsearch = cache_entry["dbsearch"]
        print("Found search in cache")

    print("Will search at providers as long as we don't have enough results for the current offset+limit and any provider has more results.")
    while len(cache_entry["results"]) < external_offset + limit and len(providers_to_call) > 0:
        print("We want %d results but have only %d so far" % ((external_offset + limit), len(cache_entry["results"])))
        print("%d providers still have results" % len(providers_to_call))
        search_request.offset = cache_entry["offset"]
        print("Searching providers with offset %d" % search_request.offset)
        result = search_and_handle_db(dbsearch, {x: search_request for x in providers_to_call})
        search_results = []
        providers_to_call = []
        for provider, queries_execution_result in result["results"].items():
            search_results.extend(queries_execution_result.results)
            print("%s returned %d results" % (provider, len(queries_execution_result.results)))
            cache_entry["provider_infos"][provider].update({"search_request": search_request, "has_more": queries_execution_result.has_more, "total": queries_execution_result.total, "total_known": queries_execution_result.total_known, "provider_search": queries_execution_result.dbentry})
            if queries_execution_result.has_more:
                providers_to_call.append(provider)
                print("%s still has more results so we could use it the next round" % provider)

            if queries_execution_result.total_known:
                if not cache_entry["provider_infos"][provider]["total_included"]:
                    cache_entry["total"] += queries_execution_result.total
                    print("%s reports %d total results. We'll include in the total this time only" % (provider, queries_execution_result.total))
                    cache_entry["provider_infos"][provider]["total_included"] = True
            elif queries_execution_result.has_more:
                print("%s doesn't report an exact number of results so let's just add another 100 to the total" % provider)
                cache_entry["total"] += 100

        search_results = sorted(search_results, key=lambda x: x.epoch, reverse=True)
        cache_entry["results"].extend(search_results)
        cache_entry["offset"] += limit

    nzb_search_results = copy.deepcopy(cache_entry["results"][external_offset:(external_offset + limit)])
    cache_entry["last_access"] = arrow.utcnow()
    print("We have %d cached results and return %d-%d of %d total available" % (len(cache_entry["results"]), external_offset, external_offset + limit, cache_entry["total"]))
    return {"results": nzb_search_results, "provider_infos": cache_entry["provider_infos"], "dbsearch": cache_entry["dbsearch"].id, "total": cache_entry["total"], "offset": external_offset}


def search_and_handle_db(dbsearch, providers_and_search_requests):
    results_by_provider = start_search_futures(providers_and_search_requests)
    for i in results_by_provider.values():
        providersearchentry = i.dbentry
        providersearchentry.search = dbsearch
        providersearchentry.save()
    logger.debug("Returning search results now")
    return {"results": results_by_provider, "dbsearchid": dbsearch.id}


def execute(provider, search_function, args):
    return getattr(provider, search_function)(args)


def start_search_futures(providers_and_search_requests):
    provider_to_searchresults = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(providers_and_search_requests)) as executor:
        futures_to_providers = {}
        count = 1
        for provider, search_request in providers_and_search_requests.items():
            future = executor.submit(provider.search, search_request)
            futures_to_providers[future] = provider
            logger.debug("Added %d of %d calls to executor" % (count, len(providers_and_search_requests)))
            count += 1
        count = 1
        for f in concurrent.futures.as_completed(futures_to_providers.keys()):
            results = f.result()
            provider_to_searchresults[futures_to_providers[f]] = results
            logger.debug("Retrieved %d of %d calls from executor" % (count, len(futures_to_providers)))
            count += 1

    return provider_to_searchresults
