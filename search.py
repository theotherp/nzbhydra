import concurrent
import logging

from requests.exceptions import RequestException
from requests_futures.sessions import FuturesSession
from werkzeug.exceptions import HTTPException

import config
from exceptions import ProviderConnectionException, ProviderAuthException, NzbHydraException, ProviderAccessException
from searchmodules import binsearch, newznab, womble, nzbclub



# TODO: I would like to use plugins for this but couldn't get this to work with pluginbase due to import errors, probably import loops or whatever. I hate pythons import system 
search_modules = {"binsearch": binsearch, "newznab": newznab, "womble": womble, "nzbclub": nzbclub}
logger = logging.getLogger('root')

config.init("searching.timeout", 5, int)

session = FuturesSession()
providers = []


def pick_providers(search_type=None, query_needed=True, identifier_key=None):
    picked_providers = providers
    # todo: perhaps a provider is disabled because we reached the api limit or because it's offline and we're waiting some time or whatever

    picked_providers = [p for p in picked_providers if not search_type or search_type in p.search_types]
    picked_providers = [p for p in picked_providers if not query_needed or p.supports_queries]
    picked_providers = [p for p in picked_providers if not identifier_key or identifier_key in p.search_ids]
    return picked_providers


# Load from config and initialize all configured providers using the loaded modules
def read_providers_from_config():
    global providers
    providers = []

    for configSection in config.cfg.section("search_providers").sections():
        if not configSection.get("module"):
            raise AttributeError("Provider section without module %s" % configSection)
        if not configSection.get("module") in search_modules:
            raise AttributeError("Unknown search module %s" % configSection.get("module"))
        if configSection.get("enabled", True):
            provider = search_modules[configSection.get("module")]
            provider = provider.get_instance(configSection)
            providers.append(provider)
    return providers


def search(query, categories=None):
    logger.info("Searching for query '%s'" % query)
    queries_by_provider = {}
    for p in pick_providers(search_type="general", query_needed=True):
        queries_by_provider[p] = p.get_search_urls(query, categories)
    return execute_search_queries(queries_by_provider)
    # make a general query, probably only done by the gui


def search_show(query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
    logger.info("Searching for tv show") #todo: extend
    queries_by_provider = {}
    for p in pick_providers(search_type="tv", query_needed=query is not None, identifier_key=identifier_key):
        queries_by_provider[p] = p.get_showsearch_urls(query, identifier_key, identifier_value, season, episode, categories)
    return execute_search_queries(queries_by_provider)


def search_movie(query=None, identifier_key=None, identifier_value=None, categories=None):
    logger.info("Searching for movie") #todo:extend
    queries_by_provider = {}
    for p in pick_providers(search_type="movie", query_needed=query is not None, identifier_key=identifier_key):
        queries_by_provider[p] = p.get_moviesearch_urls(query, identifier_key, identifier_value, categories)
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
                raise ProviderConnectionException("Unable to connect to provider. Status code: %d" % result.status_code, provider)
            else:
                provider.check_auth(result.text)
                query_results.append({"provider": provider, "result": result})
            
        except ProviderAuthException as e:
            logger.error("Unable to authorize with %s: %s" % (e.search_module, e.message))
            pass #todo disable provider
        except ProviderConnectionException as e:
            logger.error("Unable to connect with %s: %s" % (e.search_module, e.message))
            pass #todo pause provider
        except ProviderAccessException as e:
            logger.error("Unable to access %s: %s" % (e.search_module, e.message))
            pass #todo pause provider
        except Exception as e:
            logger.exception("An error error occurred while searching.", e)
        

    for query_result in query_results:
        provider = query_result["provider"]
        result = query_result["result"]
        try:
            processed_results = provider.process_query_result(result.text)
        except Exception as e:
            logger.exception("Error while processing search results from provider %s" % provider, e)
        search_results.extend(processed_results)

    #todo: add information about the providers / search results / etc. so we can show them in the gui later
    #for example how long the provider took for responses, if the search was successful, how many items per provider, etc. to a degree those calculations can also be done by the gui later


    return search_results
