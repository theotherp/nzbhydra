import concurrent
from concurrent.futures import ThreadPoolExecutor
import json
import logging

import arrow
from furl import furl
import requests
from requests_futures.sessions import FuturesSession

from database import Provider, ProviderSearch, ProviderApiAccess, ProviderSearchApiAccess, ProviderStatus
import config
from exceptions import ProviderConnectionException, ProviderAuthException, ProviderAccessException, ExternalApiInfoException, ProviderResultParsingException
from searchmodules import newznab, womble, nzbclub, nzbindex




# TODO: I would like to use plugins for this but couldn't get this to work with pluginbase. Would also need a concept to work with the database
search_modules = {"newznab": newznab, "womble": womble, "nzbclub": nzbclub, "nzbindex": nzbindex}
logger = logging.getLogger('root')

config.init("searching.timeout", 5, int)

session = FuturesSession()
providers = []


def pick_providers(search_type=None, query_supplied=True, identifier_key=None, allow_query_generation=False):
    picked_providers = []

    for p in providers:
        if not p.provider.enabled:
            logger.debug("Did not pick %s because it is disabled" % p)
            continue
        try:
            status = p.provider.status.get()
            if status.disabled_until > arrow.utcnow():
                logger.debug("Did not pick %s because it is disabled temporarily due to an error: %s" % (p, status.reason))
                continue
        except ProviderStatus.DoesNotExist:
            pass

        if query_supplied and not p.supports_queries:
            logger.debug("Did not pick %s because a query was supplied but the provider does not support queries" % p)
            continue
        if not query_supplied and p.needs_queries:
            logger.debug("Did not pick %s because no query was supplied but the provider needs queries" % p)
            continue
        if search_type is not None and search_type not in p.search_types:
            logger.debug("Did not pick %s because it does not support supplied search type %s" % (p, search_type))
            continue
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


def search(query, categories=None):
    logger.info("Searching for query '%s'" % query)
    queries_by_provider = {}
    for p in pick_providers(search_type="general", query_supplied=True):
        queries = p.get_search_urls(query, categories)
        dbentry = ProviderSearch(provider=p.provider, query=query)
        queries_by_provider[p] = {"queries": queries, "dbsearchentry": dbentry}
    return execute_search_queries(queries_by_provider)
    # make a general query, probably only done by the gui


def pick_providers_and_generate_queries(search_type, search_function, query=None, identifier_key=None, identifier_value=None, categories=None, **kwargs):
    # The search_type is used to determine the providers, the search function is the function that is called using the supplied parameters, for every provider we found 
    queries_by_provider = {}
    picked_providers = pick_providers(search_type=search_type, query_supplied=query is not None or identifier_key is not None, identifier_key=identifier_key, allow_query_generation=True)

    # If we have no query, we can still try to generate one for the providers which don't support query based searches, but only if we have an identifier.
    providers_that_allow_query_generation = []
    if query is None and identifier_key is not None:
        providers_that_allow_query_generation = [x for x in picked_providers if x.generate_queries and identifier_key not in x.search_ids]
        if any(providers_that_allow_query_generation) and config.cfg.get("searching.allow_query_generation", True):  # todo init
            try:
                generated_query = title_from_id(identifier_key, identifier_value)

                if categories is not None:
                    pass  # todo if so configured attempt to map categories to strings?

                logger.info("Generated query for movie search from identifier %s=%s: %s" % (identifier_key, identifier_value, generated_query))

                # and then finally use the generated query
                for p in providers_that_allow_query_generation:
                    queries = getattr(p, search_function)(query=generated_query, identifier_key=identifier_key, identifier_value=identifier_value, categories=categories, **kwargs)

                    dbentry = ProviderSearch(provider=p.provider, query=generated_query, query_generated=True, identifier_key=identifier_key, identifier_value=identifier_value, categories=json.dumps(categories))
                    queries_by_provider[p] = {"queries": queries, "dbsearchentry": dbentry}
            except ExternalApiInfoException as e:
                logger.error("Error while retrieving the title to the supplied identifier %s: %s" % (identifier_key, e))

    # Get movie search urls from those providers that support search by id
    for p in [x for x in picked_providers if x not in providers_that_allow_query_generation]:
        queries = getattr(p, search_function)(query=query, identifier_key=identifier_key, identifier_value=identifier_value, categories=categories, **kwargs)
        dbentry = ProviderSearch(provider=p.provider, query=query, identifier_key=identifier_key, identifier_value=identifier_value, categories=json.dumps(categories))
        queries_by_provider[p] = {"queries": queries, "dbsearchentry": dbentry}

    return queries_by_provider


def search_show(query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
    logger.info("Searching for show")  # todo:extend
    queries_by_provider = pick_providers_and_generate_queries("tv", "get_showsearch_urls", *(), query=query, identifier_key=identifier_key, identifier_value=identifier_value, categories=categories, season=season, episode=episode)
    return execute_search_queries(queries_by_provider)


def search_movie(query=None, identifier_key=None, identifier_value=None, categories=None):
    logger.info("Searching for movie")  # todo:extend
    queries_by_provider = pick_providers_and_generate_queries("movie", "get_moviesearch_urls", *(), query=query, identifier_key=identifier_key, identifier_value=identifier_value, categories=categories)
    return execute_search_queries(queries_by_provider)


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






def execute(provider, queries):
    return provider.execute_queries(queries)

def execute_search_queries(queries_by_provider):
    # TODO: Probably this could be handled a lot more comprehensively with classes instead of many dicts and lists
    search_results = []


    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for provider, query_and_dbentry in queries_by_provider.items():
            futures.append(executor.submit(execute, provider, query_and_dbentry["queries"]))
        for f in concurrent.futures.as_completed(futures):
            results = f.result()
            search_results.extend(results)

    return search_results
