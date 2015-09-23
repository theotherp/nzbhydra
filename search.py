import concurrent
import logging

from requests_futures.sessions import FuturesSession

import config
from exceptions import ProviderConnectionException, ProviderAuthException, ProviderAccessException
from searchmodules import binsearch, newznab, womble, nzbclub




# TODO: I would like to use plugins for this but couldn't get this to work with pluginbase due to import errors, probably import loops or whatever. I hate pythons import system 
search_modules = {"binsearch": binsearch, "newznab": newznab, "womble": womble, "nzbclub": nzbclub}
logger = logging.getLogger('root')

config.init("searching.timeout", 5, int)

session = FuturesSession()
providers = []


def pick_providers(search_type=None, query_supplied=True, identifier_key=None, allow_query_generation=False):
    picked_providers = providers
    # todo: perhaps a provider is disabled because we reached the api limit or because it's offline and we're waiting some time or whatever
    # If we have a query we only pick those providers that actually support queries (so no wombles)
    picked_providers = [p for p in picked_providers if not query_supplied or p.supports_queries]
    
    # If we don't have a query (either as text search or with an id or a category) we only pick those providers that dont need one, i.e. support returning a general release list (so no nzbclub)
    picked_providers = [p for p in picked_providers if query_supplied or not p.needs_queries]
    
    # If we have a certain search type only pick those providers that are to be used for it
    picked_providers = [p for p in picked_providers if search_type is None or search_type in p.search_types]
    
    # If we use id based search only pick those providers that either support it or where we're allowed to generate queries (that means we retrieve the title of the show or movie and do a text based query)    
    picked_providers = [p for p in picked_providers if identifier_key is None or identifier_key in p.search_ids or (allow_query_generation and p.generate_queries)]
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
    for p in pick_providers(search_type="general", query_supplied=True):
        queries_by_provider[p] = p.get_search_urls(query, categories)
    return execute_search_queries(queries_by_provider)
    # make a general query, probably only done by the gui


def search_show(query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
    logger.info("Searching for tv show")  # todo: extend
    queries_by_provider = {}
    for p in pick_providers(search_type="tv", query_supplied=query is not None, identifier_key=identifier_key):
        queries_by_provider[p] = p.get_showsearch_urls(query, identifier_key, identifier_value, season, episode, categories)
    return execute_search_queries(queries_by_provider)


def search_movie(query=None, identifier_key=None, identifier_value=None, categories=None):
    logger.info("Searching for movie")  # todo:extend
    queries_by_provider = {}
    picked_providers = pick_providers(search_type="movie", query_supplied=query is not None or identifier_key is not None, identifier_key=identifier_key, allow_query_generation=True)

    providers_that_allow_query_generation = []
    if query is None and identifier_key is not None:
        #If we have no query, we can still try to generate one for the providers which don't support query based searches, but only if we have an identifier.
        providers_that_allow_query_generation = [x for x in picked_providers if x.generate_queries and identifier_key not in x.search_ids]
        if any(providers_that_allow_query_generation):
            #todo actually retrieve title
            generated_query = "movie.title"
            if categories is not None:
                pass #todo if so configured attempt to map categories to strings?
    
    #Get movie search urls from those providers that support search by id
    for p in [x for x in picked_providers if x not in providers_that_allow_query_generation]:
        queries_by_provider[p] = p.get_moviesearch_urls(query, identifier_key, identifier_value, categories)
        
    #and then from all providers for which we generated the query
    for p in providers_that_allow_query_generation:
        queries_by_provider[p] = p.get_moviesearch_urls(generated_query, identifier_key, identifier_value, categories)
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
            pass  # todo disable provider
        except ProviderConnectionException as e:
            logger.error("Unable to connect with %s: %s" % (e.search_module, e.message))
            pass  # todo pause provider
        except ProviderAccessException as e:
            logger.error("Unable to access %s: %s" % (e.search_module, e.message))
            pass  # todo pause provider
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

    # todo: add information about the providers / search results / etc. so we can show them in the gui later
    # for example how long the provider took for responses, if the search was successful, how many items per provider, etc. to a degree those calculations can also be done by the gui later


    return search_results
