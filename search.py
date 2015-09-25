import concurrent
import json
import logging
import arrow

from furl import furl
import requests
from requests_futures.sessions import FuturesSession

from database import Provider, ProviderSearch, ProviderApiAccess, ProviderSearchApiAccess
import config
from exceptions import ProviderConnectionException, ProviderAuthException, ProviderAccessException, ExternalApiInfoException, ProviderResultParsingException
from searchmodules import newznab, womble, nzbclub



# TODO: I would like to use plugins for this but couldn't get this to work with pluginbase. Would also need a concept to work with the database
search_modules = {"newznab": newznab, "womble": womble, "nzbclub": nzbclub}
logger = logging.getLogger('root')

config.init("searching.timeout", 5, int)

session = FuturesSession()
providers = []


def pick_providers(search_type=None, query_supplied=True, identifier_key=None, allow_query_generation=False):
    picked_providers = []

    for p in providers:
        pick = True
        pick = pick and (not query_supplied or p.supports_queries)
        pick = pick and (query_supplied or not p.needs_queries)
        pick = pick and (search_type is None or search_type in p.search_types)
        pick = pick and (identifier_key is None or identifier_key in p.search_ids or (allow_query_generation and p.generate_queries))
        
        if pick:
            picked_providers.append(p)

    # todo: perhaps a provider is disabled because we reached the api limit or because it's offline and we're waiting some time or whatever
    # # If we have a query we only pick those providers that actually support queries (so no wombles)
    # picked_providers = [p for p in picked_providers if not query_supplied or p.supports_queries]
    # 
    # 
    # # If we don't have a query (either as text search or with an id or a category) we only pick those providers that dont need one, i.e. support returning a general release list (so no nzbclub)
    # picked_providers = [p for p in picked_providers if query_supplied or not p.needs_queries]
    # 
    # # If we have a certain search type only pick those providers that are to be used for it
    # picked_providers = [p for p in picked_providers if search_type is None or search_type in p.search_types]
    # 
    # # If we use id based search only pick those providers that either support it or where we're allowed to generate queries (that means we retrieve the title of the show or movie and do a text based query)    
    # picked_providers = [p for p in picked_providers if identifier_key is None or identifier_key in p.search_ids or (allow_query_generation and p.generate_queries)]
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


def pick_providers_and_search(search_type, search_function, query=None, identifier_key=None, identifier_value=None, categories=None, **kwargs):
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
                logger.error("Error while retrieving the title to the supplied identifier %s: %s" % (identifier_key, e.message))

    # Get movie search urls from those providers that support search by id
    for p in [x for x in picked_providers if x not in providers_that_allow_query_generation]:
        queries = getattr(p, search_function)(query=query, identifier_key=identifier_key, identifier_value=identifier_value, categories=categories, **kwargs)
        dbentry = ProviderSearch(provider=p.provider, query=query, identifier_key=identifier_key, identifier_value=identifier_value, categories=json.dumps(categories))
        queries_by_provider[p] = {"queries": queries, "dbsearchentry": dbentry}

    return execute_search_queries(queries_by_provider)


def search_show(query=None, identifier_key=None, identifier_value=None, season=None, episode=None, categories=None):
    logger.info("Searching for show")  # todo:extend
    return pick_providers_and_search("tv", "get_showsearch_urls", *(), query=query, identifier_key=identifier_key, identifier_value=identifier_value, categories=categories, season=season, episode=episode)


def search_movie(query=None, identifier_key=None, identifier_value=None, categories=None):
    logger.info("Searching for movie")  # todo:extend
    return pick_providers_and_search("movie", "get_moviesearch_urls", *(), query=query, identifier_key=identifier_key, identifier_value=identifier_value, categories=categories)


def title_from_id(identifier_key, identifier_value):
    if identifier_key is None or identifier_value is None:
        raise AttributeError("Neither identifier key nor value were supplied")
    try:
        if identifier_key == "imdbid":
            if identifier_value[0:2] != "tt":
                identifier_value = "tt%s" % identifier_value
            url = furl("http://www.omdbapi.com").add({"i": identifier_value, "plot": "short", "r": "json"}).tostr()
            omdb = requests.get(url) #todo weird bug here
            return omdb.json()["Title"]

        if identifier_key not in ("rid", "tvdbid"):
            raise AttributeError("Unknown identifier %s" % identifier_key)

        tvmaze_key = "tvrage" if identifier_key == "rid" else "thetvdb"
        tvmaze = requests.get(furl("http://api.tvmaze.com/lookup/shows").add({tvmaze_key: identifier_value}).url)
        return tvmaze.json()["name"]

    except Exception as e:
        raise ExternalApiInfoException("Unable to retrieve title by id %s and value %s: %s" % (identifier_key, identifier_value, e))


def execute_search_queries(queries_by_provider):
    #TODO: Probably this could be handled a lot more comprehensively with classes instead of many dicts and lists
    search_results = []
    futures = []
    providers_by_future = {}
    dbsearchentries_by_provider = {}
    
    for provider, query_and_dbentry in queries_by_provider.items():
        #For every query...
        for query in query_and_dbentry["queries"]:
            logger.debug("Requesting URL %s with timeout %d" % (query, config.cfg["searching.timeout"]))
            # ... we create a request  
            future = session.get(query, timeout=config.cfg["searching.timeout"], verify=False)
            futures.append(future)
            # ... and store its provider so we know which provider should handle the result
            providers_by_future[future] = provider
        
        dbsearchentries_by_provider[provider] = query_and_dbentry["dbsearchentry"]
    
    for f in concurrent.futures.as_completed(futures):
        provider = providers_by_future[f]
        psearch = dbsearchentries_by_provider[provider]
        psearch.save()
        papiaccess = ProviderApiAccess(provider=provider.provider, type="search")
        papiaccess.save()
        ProviderSearchApiAccess(search=psearch, api_access=papiaccess).save() #So we can later see which/how many accesses the search caused and how they went
        try:
            result = f.result()

            papiaccess.response_time = result.elapsed.microseconds / 1000
            if result.status_code != 200:
                raise ProviderConnectionException("Unable to connect to provider. Status code: %d" % result.status_code, provider)
            else:
                provider.check_auth(result.text)
                papiaccess.response_successful = True
                
                try:
                    parsed_results = provider.process_query_result(result.text)
                    psearch.results = len(parsed_results)
                    search_results.extend(parsed_results)
                    psearch.successful = True
                except Exception as e:
                    logger.exception("Error while processing search results from provider %s" % provider, e)
                    raise ProviderResultParsingException("Error while parsing the results from provider %s" % provider, e)

        except ProviderAuthException as e:
            logger.error("Unable to authorize with %s: %s" % (e.search_module, e.message))
            papiaccess.error = "Authorization error :%s" % e.message
            pass  # todo disable provider
        except ProviderConnectionException as e:
            logger.error("Unable to connect with %s: %s" % (e.search_module, e.message))
            papiaccess.error = "Connection error :%s" % e.message
            pass  # todo pause provider
        except ProviderAccessException as e:
            logger.error("Unable to access %s: %s" % (e.search_module, e.message))
            papiaccess.error = "Access error :%s" % e.message
            pass  # todo pause provider
        except Exception as e:
            logger.exception("An error error occurred while searching.", e)
            papiaccess.error = "Unknown error :%s" % e.message
        psearch.save()
        papiaccess.save()

    return search_results
