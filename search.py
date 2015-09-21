import concurrent
import logging

from requests.exceptions import RequestException
from requests_futures.sessions import FuturesSession
import config
from searchmodules import binsearch
from searchmodules import newznab




# TODO: I would like to use plugins for this but couldn't get this to work with pluginbase due to import errors, probably import loops or whatever. I hate pythons import system 
search_modules = {"binsearch": binsearch, "newznab": newznab}
logger = logging.getLogger('root')

config.init("searching.timeout", 5, int)



session = FuturesSession()
providers = []


# Load from config and initialize all configured providers using the loaded modules
def read_providers_from_config():
    global providers
    for configSection in config.cfg.section("search_providers").sections():
        if not configSection.get("search_module") in search_modules:
            raise AttributeError("Unknown search module")
        provider = search_modules[configSection.get("search_module")]
        provider = provider.get_instance(configSection)
        providers.append(provider)
    return providers


def search(query, categories=None):
    logger.info("Searching for query %s" % query)
    queries_by_provider = {}
    for p in providers:
        queries_by_provider[p] = p.get_search_urls(query, categories)
    return execute_search_queries(queries_by_provider)
    # make a general query, probably only done by the gui


def search_show(identifier=None, season=None, episode=None, quality=None):
    logger.info("Searching for tv show")
    queries_by_provider = {}
    for p in providers:
        queries_by_provider[p] = p.get_showsearch_urls(identifier, season, episode, quality)
    return execute_search_queries(queries_by_provider)


def search_movie(identifier, categories):
    logger.info("Searching for movie")
    queries_by_provider = {}
    for p in providers:
        queries_by_provider[p] = p.get_moviesearch_urls(identifier, categories)
    return execute_search_queries(queries_by_provider)


def execute_search_queries(queries_by_provider):
    search_results = []
    results_by_provider = {}
    futures = []
    providers_by_future = {}
    for provider, queries in queries_by_provider.items():
        results_by_provider[provider] = []
        for query in queries:
            logger.debug("Requesting URL %s with timeout %d" % (query, config.cfg["searching.timeout"]))
            future = session.get(query, timeout=config.cfg["searching.timeout"], verify=False)
            futures.append(future)
            providers_by_future[future] = provider

    query_results = []

    for f in concurrent.futures.as_completed(futures):
        try:
            result = f.result()
            provider = providers_by_future[f]

            if result.status_code != 200:
                # todo handle this more specific
                logger.warn("Error while calling %s" % result.url)
            else:
                query_results.append({"provider": provider, "result": result})
        except RequestException as e:
            logger.error("Error while trying to process query URL: %s" % e)
        except Exception:
            logger.exception("Error while trying to process query URL")
            pass

    for query_result in query_results:
        provider = query_result["provider"]
        result = query_result["result"]
        search_results.extend(provider.process_query_result(result.text))


    # handle errors / timeouts (log, perhaps pause usage for some time when offline)
    # then filter results, throw away passworded (if configured), etc.



    return search_results
