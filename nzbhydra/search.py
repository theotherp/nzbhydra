from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
from itertools import groupby

from builtins import int
from future import standard_library

#standard_library.install_aliases()
from builtins import *
import concurrent
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
              'Audiobook': {"pretty": "Audiobook", "index": 14},
              'Console': {"pretty": "Console", "index": 10},
              'PC': {"pretty": "PC", "index": 11},
              'XXX': {"pretty": "XXX", "index": 12},
              'Ebook': {"pretty": "XXX", "index": 13}
              }

logger = logging.getLogger('root')

session = FuturesSession()


class SearchRequest(object):
    def __init__(self, type=None, query=None, identifier_key=None, identifier_value=None, season=None, episode=None, title=None, category=None, minsize=None, maxsize=None, minage=None, maxage=None, offset=0, limit=100, indexers=None):
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
        self.indexers = indexers

    @property
    def search_hash(self):
        return hash(frozenset([self.type, self.query, self.identifier_key, self.identifier_value, self.title, self.season, self.episode, self.category, self.minsize, self.maxsize, self.minage, self.maxage]))

    def __repr__(self):
        rep = "SearchRequest ["
        rep += " type \"%s\"" % self.type
        rep += (", identifier_key \"%s\" " % self.identifier_key) if self.identifier_key is not None else ""
        rep += (", identifier_value \"%s\"" % self.identifier_value) if self.identifier_value is not None else ""
        rep += (", title \"%s\"" % self.title) if self.title is not None else ""
        rep += (", season \"%s\"" % self.season) if self.season is not None else ""
        rep += (", episode \"%s\"" % self.episode) if self.episode is not None else ""
        rep += (", category \"%s\"" % self.category) if self.category is not None else ""
        rep += (", minsize \"%s\"" % self.minsize) if self.minsize is not None else ""
        rep += (", maxsize \"%s\"" % self.maxsize) if self.maxsize is not None else ""
        rep += (", minage \"%s\"" % self.minage) if self.minage is not None else ""
        rep += (", maxage \"%s\"" % self.maxage) if self.maxage is not None else ""
        rep += (", offset \"%s\"" % self.offset) if self.offset is not None else ""
        rep += (", limit \"%s\"" % self.limit) if self.limit is not None else ""
        rep += (", indexers \"%s\"" % self.indexers) if self.indexers is not None else ""
        rep += " ]"
        return rep


def canUseIdKey(indexer, key):
    if key in indexer.settings.search_ids.get():
        return True
    # We might be able to convert them using TVMaze
    if key == "tvdbid" and "rid" in indexer.settings.search_ids.get():
        return True
    if key == "rid" and "tvdbid" in indexer.settings.search_ids.get():
        return True


def pick_indexers(query_supplied=True, identifier_key=None, internal=True, selected_indexers=None):
    picked_indexers = []
    selected_indexers = selected_indexers.split("|") if selected_indexers is not None else None
    with_query_generation = False
    for p in indexers.enabled_indexers:
        if not p.settings.enabled.get():
            logger.debug("Did not pick %s because it is disabled" % p)
            continue
        if internal and p.settings.accessType.get() == "external":
            logger.debug("Did not pick %s because it is only enabled for external searches" % p)
            continue
        if not internal and p.settings.accessType.get() == "internal":
            logger.debug("Did not pick %s because it is only enabled for internal searches" % p)
            continue
        if selected_indexers and p.name not in selected_indexers:
            logger.debug("Did not pick %s because it was not selected by the user" % p)
            continue
        try:
            status = p.indexer.status.get()
            if status.disabled_until > arrow.utcnow() and not searchingSettings.ignore_disabled.get_with_default(False):
                logger.info("Did not pick %s because it is disabled temporarily due to an error: %s" % (p, status.reason))
                continue
        except IndexerStatus.DoesNotExist:
            pass

        if query_supplied and not p.supports_queries:
            logger.debug("Did not pick %s because a query was supplied but the indexer does not support queries" % p)
            continue
        if not query_supplied and p.needs_queries and identifier_key is None:
            logger.debug("Did not pick %s because no query was supplied but the indexer needs queries" % p)
            continue
        allow_query_generation = (config.InternalExternalSelection.internal.name in config.searchingSettings.generate_queries.get() and internal) or (config.InternalExternalSelection.external.name in config.searchingSettings.generate_queries.get() and not internal)
        if identifier_key is not None and not canUseIdKey(p, identifier_key):
            if not (allow_query_generation and p.generate_queries):
                logger.debug("Did not pick %s because search will be done by an identifier and the indexer or system wide settings don't allow query generation" % p)
                continue
            else:
                with_query_generation = True

        logger.debug("Picked %s" % p)
        picked_indexers.append(p)

    return picked_indexers, with_query_generation


pseudo_cache = {}


def search(internal, search_request):
    for k in list(pseudo_cache.keys()):
        if pseudo_cache[k]["last_access"].replace(minutes=+5) < arrow.utcnow():
            pseudo_cache.pop(k)
    limit = search_request.limit
    external_offset = int(search_request.offset)
    search_hash = search_request.search_hash
    if search_hash not in pseudo_cache.keys() or search_request.offset == 0:  # If it's a new search (which starts with offset 0) do it again instead of using the cached results
        logger.debug("Didn't find this query in cache or want to do a new search")
        cache_entry = {"results": [], "indexer_infos": {}, "total": 0, "last_access": arrow.utcnow(), "offset": 0}
        indexers_to_call, with_query_generation = pick_indexers(query_supplied=True if search_request.query is not None and search_request.query != "" else False, identifier_key=search_request.identifier_key, internal=internal, selected_indexers=search_request.indexers)
        for p in indexers_to_call:
            cache_entry["indexer_infos"][p] = {"has_more": True, "search_request": search_request, "total_included": False}
        dbsearch = Search(internal=internal, query=search_request.query, category=search_request.category, identifier_key=search_request.identifier_key, identifier_value=search_request.identifier_value, season=search_request.season, episode=search_request.episode, type=search_request.type)
        #dbsearch.save()
        cache_entry["dbsearch"] = dbsearch

        if with_query_generation and search_request.identifier_key and search_request.title is None:
            try: 
                search_request.title = infos.title_from_id(search_request.identifier_key, search_request.identifier_value)
            except:
                pass
        pseudo_cache[search_hash] = cache_entry
    else:
        cache_entry = pseudo_cache[search_hash]
        indexers_to_call = [indexer for indexer, info in cache_entry["indexer_infos"].items() if info["has_more"]]
        dbsearch = cache_entry["dbsearch"]
        logger.debug("Found search in cache")

        logger.debug("Will search at indexers as long as we don't have enough results for the current offset+limit and any indexer has more results.")
    while len(cache_entry["results"]) < external_offset + limit and len(indexers_to_call) > 0:
        logger.debug("We want %d results but have only %d so far" % ((external_offset + limit), len(cache_entry["results"])))
        logger.debug("%d indexers still have results" % len(indexers_to_call))
        search_request.offset = cache_entry["offset"]
        logger.debug("Searching indexers with offset %d" % search_request.offset)
        result = search_and_handle_db(dbsearch, {x: search_request for x in indexers_to_call})
        search_results = []
        indexers_to_call = []
        
        for indexer, queries_execution_result in result["results"].items():
            search_results.extend(queries_execution_result.results)
            logger.debug("%s returned %d results" % (indexer, len(queries_execution_result.results)))
            cache_entry["indexer_infos"][indexer].update({"search_request": search_request, "has_more": queries_execution_result.has_more, "total": queries_execution_result.total, "total_known": queries_execution_result.total_known, "indexer_search": queries_execution_result.indexerSearchEntry})
            if queries_execution_result.has_more:
                indexers_to_call.append(indexer)
                logger.debug("%s still has more results so we could use it the next round" % indexer)

            if queries_execution_result.total_known:
                if not cache_entry["indexer_infos"][indexer]["total_included"]:
                    cache_entry["total"] += queries_execution_result.total
                    logger.debug("%s reports %d total results. We'll include in the total this time only" % (indexer, queries_execution_result.total))
                    cache_entry["indexer_infos"][indexer]["total_included"] = True
            elif queries_execution_result.has_more:
                logger.debug("%s doesn't report an exact number of results so let's just add another 100 to the total" % indexer)
                cache_entry["total"] += 100


        if internal or config.searchingSettings.removeDuplicatesExternal.get():
            countBefore = len(search_results)
            grouped_by_sameness = find_duplicates(search_results)
            allresults = []
            for group in grouped_by_sameness:
                if internal:
                    for i in group:
                        # We give each group of results a unique value by which they can be identified later
                        i.hash = hash(group[0].guid)
                        allresults.append(i)
                    
                else:
                    # We sort by age first and then by indexerscore so the newest result with the highest indexer score is chosen
                    group = sorted(group, key=lambda x: x.epoch, reverse=True)
                    group = sorted(group, key=lambda x: x.indexerscore, reverse=True)
                    allresults.append(group[0])
            search_results = allresults
            if not internal:
                countAfter = len(search_results)
                countRemoved = countBefore - countAfter
                logger.info("Removed %d duplicates from %d results" % (countRemoved, countBefore))
        search_results = sorted(search_results, key=lambda x: x.epoch, reverse=True)

        cache_entry["results"].extend(search_results)
        cache_entry["offset"] += limit

    if internal:
        logger.debug("We have %d cached results and return them all because we search internally" % len(cache_entry["results"]))
        nzb_search_results = copy.deepcopy(cache_entry["results"][external_offset:])
    else:
        logger.debug("We have %d cached results and return %d-%d of %d total available accounting for the limit set for the API search" % (len(cache_entry["results"]), external_offset, external_offset + limit, cache_entry["total"]))
        nzb_search_results = copy.deepcopy(cache_entry["results"][external_offset:(external_offset + limit)])
    cache_entry["last_access"] = arrow.utcnow()
    
    return {"results": nzb_search_results, "indexer_infos": cache_entry["indexer_infos"], "dbsearchid": cache_entry["dbsearch"].id, "total": cache_entry["total"], "offset": external_offset}


def search_and_handle_db(dbsearch, indexers_and_search_requests):
    results_by_indexer = start_search_futures(indexers_and_search_requests)
    dbsearch.save()
    for i in results_by_indexer.values():
        indexersearchentry = i.indexerSearchEntry
        indexersearchentry.search = dbsearch
        indexersearchentry.save()
        i.indexerApiAccessEntry.save()
        i.indexerStatus.save()
        
    logger.debug("Returning search results now")
    return {"results": results_by_indexer, "dbsearch": dbsearch}


def execute(indexer, search_function, args):
    return getattr(indexer, search_function)(args)


def start_search_futures(indexers_and_search_requests):
    indexer_to_searchresults = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(indexers_and_search_requests)) as executor:
        futures_to_indexers = {}
        count = 1
        for indexer, search_request in indexers_and_search_requests.items():
            future = executor.submit(indexer.search, copy.copy(search_request))
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


def find_duplicates(results):
    #We need to sort by age first, then by title and then group by title
    sorted_results = sorted(results, key=lambda x: x.pubdate_utc, reverse=True)
    sorted_results = sorted(sorted_results, key=lambda x: re.sub(r"[ \.\-_]", "", x.title.lower()))
    grouped_by_title = groupby(sorted_results, key=lambda x: re.sub(r"[ \.\-_]", "", x.title.lower()))
    grouped_by_sameness = []
    for title, titleGroup in grouped_by_title:
        titleGroup = list(titleGroup)
        grouped = [titleGroup[:1]]
        for i in titleGroup[1:]:
            foundGroup = False
            for group in grouped:
                for other in group:
                    same = i.indexer != other.indexer
                    same = same and test_for_duplicate_age(i, other)
                    same = same and test_for_duplicate_size(i, other)
                    if same:
                        foundGroup = True
                        group.append(i)
                        break
                if foundGroup:
                    break
            if not foundGroup:
                grouped.append([i])
        grouped_by_sameness.extend(grouped)    

    return grouped_by_sameness


def test_for_duplicate_age(search_result_1, search_result_2):
    if search_result_1.epoch is None or search_result_2.epoch is None:
        return False
    age_threshold = config.searchingSettings.duplicateAgeThreshold.get()

    group_known = search_result_1.group is not None and search_result_2.group is not None
    same_group = search_result_1.group == search_result_2.group
    poster_known = search_result_1.poster is not None and search_result_2.poster is not None
    same_poster = search_result_1.poster == search_result_2.poster
    if (group_known and not same_group) or (poster_known and not same_poster):
        return False
    if (same_group and not poster_known) or (same_poster and not group_known):
        age_threshold = 3
    if same_group and same_poster:
        age_threshold = 8

    same_age = abs(search_result_1.epoch - search_result_2.epoch) / (60 * 60) <= age_threshold  # epoch difference (seconds) to minutes    
    return same_age


def test_for_duplicate_size(search_result_1, search_result_2):
    if not search_result_1.size or not search_result_2.size:
        return False
    size_threshold = config.searchingSettings.duplicateSizeThresholdInPercent.get()
    size_difference = search_result_1.size - search_result_2.size
    size_average = (search_result_1.size + search_result_2.size) / 2
    size_difference_percent = abs(size_difference / size_average) * 100
    same_size = size_difference_percent <= size_threshold

    return same_size
