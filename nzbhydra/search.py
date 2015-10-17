import concurrent
from concurrent.futures import ThreadPoolExecutor
import logging

import arrow
from requests_futures.sessions import FuturesSession

from nzbhydra.config import searchingSettings
from nzbhydra.database import ProviderStatus, Search
from nzbhydra import config
from nzbhydra import providers

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
        allow_query_generation = (config.cfg.get("searching.allow_query_generation") == "both") or (config.cfg.get("searching.allow_query_generation") == "internal" and internal) or (config.cfg.get("searching.allow_query_generation") == "external" and not internal)
        if not (identifier_key is None or identifier_key not in p.settings.search_ids.get() or (allow_query_generation and p.generate_queries)):
            logger.debug("Did not pick %s because search will be done by an identifier and the provider or system wide settings don't allow query generation" % p)
            continue

        picked_providers.append(p)

    return picked_providers


pseudo_cache = {}


def search(internal, search_request: SearchRequest):
    search_hash = search_request.search_hash
    if search_hash in pseudo_cache.keys():
        cache_entry = pseudo_cache[search_hash]
        print("Found this query in cache. Would try to return from already loaded results")
        # Load the next <limit> results with offset <offset>
        # If we need more results than are cached we need to call the providers again. We check which providers actually have more results to offer
        # and increase their offset by their limit
        if search_request.offset + search_request.limit > len(cache_entry["results"]):
            print("We want %d + %d results but only have %d cached" % (search_request.offset, search_request.limit, len(cache_entry["results"])))
            providers_to_call = {}
            for provider, info in cache_entry["provider_infos"].items():
                if info["has_more"]:
                    provider_search_request = info["search_request"]
                    provider_search_request.offset += 100
                    print("Increased the offset for %s to %d" % (provider, provider_search_request.offset))
                    providers_to_call[provider] = provider_search_request
                else:
                    print("%s has no more results to offer" % provider)
            result = search_and_handle_db(Search().get(Search.id == cache_entry["dbsearchid"]), providers_to_call)
            nzb_search_results = []
            for provider, queries_execution_result in result["results"].items():
                nzb_search_results.extend(queries_execution_result.results)
                cache_entry["provider_search_entries"][provider] = queries_execution_result.dbentry
                cache_entry[provider] = {"has_more": queries_execution_result.has_more}
            cache_entry["results"].extend(nzb_search_results)
        else:
            print("We want %d + %d results and still have %d cached" % (search_request.offset, search_request.limit, len(cache_entry["results"])))
    else:
        print("Didn't find this query in cache")

        cache_entry = {"results": [], "provider_search_entries": {}}

        # logger.info("Searching for query '%s'" % args["query"])
        dbsearch = Search(internal=internal, query=search_request.query, category=search_request.category, identifier_key=search_request.identifier_key, identifier_value=search_request.identifier_value, season=search_request.season, episode=search_request.episode)
        dbsearch.save()
        providers_to_call = pick_providers(query_supplied=True if search_request.query is not None else False, identifier_key=search_request.identifier_key, internal=internal)
        

        providers_and_search_requests = {}
        for p in providers_to_call:
            providers_and_search_requests[p] = search_request
        result = search_and_handle_db(dbsearch, providers_and_search_requests)
        nzb_search_results = []
        cache_entry["provider_infos"] = {}
        for provider, queries_execution_result in result["results"].items():
            nzb_search_results.extend(queries_execution_result.results)
            cache_entry["provider_search_entries"][provider] = queries_execution_result.dbentry
            cache_entry["provider_infos"][provider] = {"search_request": search_request, "has_more": queries_execution_result.has_more, "total": queries_execution_result.total, "total_known": queries_execution_result.total_known}
        cache_entry["results"].extend(nzb_search_results)
        cache_entry["dbsearchid"] = result["dbsearchid"]

        pseudo_cache[search_hash] = cache_entry
    # Try to find an approximately realistic total count. If a provider returns its total precisely use it, otherwise just pretend it has 100 more if it has any more at all
    total = 0
    for info in cache_entry["provider_infos"].values():
        if info["total_known"]:
            total += info["total"]
        elif info["has_more"]:
            total += 100

    return {"results": cache_entry["results"][search_request.offset:(search_request.offset + search_request.limit)], "provider_searches": cache_entry["provider_search_entries"], "dbsearchid": cache_entry["dbsearchid"], "total": total, "offset": search_request.offset}


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
