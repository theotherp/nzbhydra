import concurrent
from concurrent.futures import ThreadPoolExecutor
import logging

import arrow
from requests_futures.sessions import FuturesSession

from nzbhydra.database import Provider, ProviderStatus, Search
from nzbhydra import config
from nzbhydra.searchmodules import newznab, womble, nzbclub, nzbindex, binsearch

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

# TODO: I would like to use plugins for this but couldn't get this to work with pluginbase. Would also need a concept to work with the database
search_modules = {"newznab": newznab, "womble": womble, "nzbclub": nzbclub, "nzbindex": nzbindex, "binsearch": binsearch}
logger = logging.getLogger('root')

config.init("searching.timeout", 5, int)
config.init("searching.ignore_temporarily_disabled", False, bool)  # If true we try providers even if they are temporarily disabled
config.init("searching.allow_query_generation", "both", str)  # "internal", "external", "both", anything else

session = FuturesSession()
providers = []


def pick_providers(query_supplied=True, identifier_key=None, category=None, internal=True):
    picked_providers = []

    for p in providers:
        if not p.provider.enabled:
            logger.debug("Did not pick %s because it is disabled" % p)
            continue
        try:
            status = p.provider.status.get()
            if status.disabled_until > arrow.utcnow() and not config.cfg.get("searching.ignore_temporarily_disabled", False):
                logger.info("Did not pick %s because it is disabled temporarily due to an error: %s" % (p, status.reason))
                continue
        except ProviderStatus.DoesNotExist:
            pass

        if category is not None and p.provider.settings.get("categories") is not None and category not in p.provider.settings.get("categories", []):
            logger.debug("Did not pick %s because it is not enabled for category %s" % (p, category))
            continue
        if query_supplied and not p.supports_queries:
            logger.debug("Did not pick %s because a query was supplied but the provider does not support queries" % p)
            continue
        if not query_supplied and p.needs_queries and identifier_key is None:
            logger.debug("Did not pick %s because no query was supplied but the provider needs queries" % p)
            continue
        allow_query_generation = (config.cfg.get("searching.allow_query_generation") == "both") or (config.cfg.get("searching.allow_query_generation") == "internal" and internal) or (config.cfg.get("searching.allow_query_generation") == "external" and not internal)
        if not (identifier_key is None or identifier_key in p.search_ids or (allow_query_generation and p.generate_queries)):
            logger.debug("Did not pick %s because search will be done by an identifier and the provider or system wide settings don't allow query generation" % p)
            continue

        picked_providers.append(p)

    return picked_providers


# Load from config and initialize all configured providers using the loaded modules
def read_providers_from_config():
    global providers
    providers = []

    for provider in Provider().select():
        if provider.module not in search_modules.keys():
            pass  # todo raise exception

        module = search_modules[provider.module]
        provider_instance = module.get_instance(provider)
        providers.append(provider_instance)

    return providers


def search(internal, args):
    logger.info("Searching for query '%s'" % args["query"])
    dbsearch = Search(internal=internal, query=args["query"], category=args["category"])
    dbsearch.save()
    providers_to_call = pick_providers(query_supplied=True, internal=internal)

    results_by_provider = start_search_futures(providers_to_call, "search", args)
    for i in results_by_provider.values():
        providersearchentry = i["providersearchdbentry"]
        providersearchentry.search = dbsearch
        providersearchentry.save()
    return results_by_provider


def search_show(internal, args):
    logger.info("Searching for show")  # todo:extend
    identifier_key = "rid" if args["rid"] else "tvdbid" if args["tvdbid"] else None
    identifier_value = args[identifier_key] if identifier_key else None
    dbsearch = Search(internal=internal, query=args["query"], identifier_key=identifier_key, identifier_value=identifier_value, season=args["season"], category=args["category"])
    dbsearch.save()
    providers_to_call = pick_providers(query_supplied=True if args["query"] is not None else False, identifier_key=identifier_key, category=args["category"], internal=internal)

    results_by_provider = start_search_futures(providers_to_call, "search_show", args)
    for i in results_by_provider.values():
        providersearchentry = i["providersearchdbentry"]
        providersearchentry.search = dbsearch
        providersearchentry.save()
    return results_by_provider
    

def search_movie(internal, args):
    logger.info("Searching for movie")  # todo:extend
    dbsearch = Search(internal=internal, query=args["query"], category=args["category"], identifier_key="imdbid" if args["imdbid"] is not None else None, identifier_value=args["imdbid"] if args["imdbid"] is not None else None)
    dbsearch.save()
    providers_to_call = pick_providers(query_supplied=True if args["query"] is not None else False, identifier_key="imdbid" if args["imdbid"] is not None else None, category=args["category"], internal=internal)

    results_by_provider = start_search_futures(providers_to_call, "search_movie", args)
    for i in results_by_provider.values():
        providersearchentry = i["providersearchdbentry"]
        providersearchentry.search = dbsearch
        providersearchentry.save()
    return results_by_provider


def execute(provider, search_function, args):
    return getattr(provider, search_function)(args)


def start_search_futures(providers_to_call, search_function, args):
    search_results_by_provider = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(providers_to_call)) as executor:
        futures = []
        providers_by_future = {}
        count = 1
        for provider in providers_to_call:
            future = executor.submit(execute, provider, search_function, args)
            futures.append(future)
            providers_by_future[future] = provider
            logger.debug("Added %d of %d calls to executor" % (count, len(providers_to_call)))
            count += 1
        count = 1
        for f in concurrent.futures.as_completed(futures):
            results = f.result()
            search_results_by_provider[providers_by_future[f]] = results
            logger.debug("Retrieved %d of %d calls from executor" % (count, len(futures)))
            count += 1

    return search_results_by_provider
