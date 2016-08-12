from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import json
import re
from itertools import groupby

from bunch import Bunch
from flask import request
# standard_library.install_aliases()
from builtins import *
import concurrent
import copy
import logging
import arrow
from playhouse.shortcuts import model_to_dict
from requests_futures.sessions import FuturesSession

from nzbhydra.database import IndexerStatus, Search, db, IndexerApiAccess, SearchResult, Indexer
from nzbhydra import config, indexers, infos, categories

logger = logging.getLogger('root')

session = FuturesSession()


class SearchRequest(object):
    def __init__(self, type=None, query=None, identifier_key=None, identifier_value=None, season=None, episode=None, title=None, category=None, minsize=None, maxsize=None, minage=None, maxage=None, offset=0, limit=100, indexers=None, forbiddenWords=None, requiredWords=None, author=None, username=None, internal=True):
        self.type = type
        self.query = query
        self.identifier_key = identifier_key
        self.identifier_value = identifier_value
        self.title = title
        self.season = season
        self.episode = episode
        self.author = author
        self.category = category
        self.minsize = minsize
        self.maxsize = maxsize
        self.minage = minage
        self.maxage = maxage
        self.offset = offset
        self.limit = limit
        self.indexers = indexers
        self.forbiddenWords = forbiddenWords if forbiddenWords else []
        self.requiredWords = requiredWords if requiredWords else []
        self.username = username
        self.internal = internal

    @property
    def search_hash(self):
        return hash(frozenset([self.type, self.query, self.identifier_key, self.identifier_value, self.title, self.season, self.episode, self.minsize, self.maxsize, self.minage, self.maxage]))

    def __repr__(self):
        rep = "SearchRequest ["
        rep += " type \"%s\"" % self.type
        rep += (", identifier_key \"%s\" " % self.identifier_key) if self.identifier_key is not None else ""
        rep += (", identifier_value \"%s\"" % self.identifier_value) if self.identifier_value is not None else ""
        rep += (", title \"%s\"" % self.title) if self.title is not None else ""
        rep += (", query \"%s\"" % self.query) if self.query is not None else ""
        rep += (", forbiddenWords \"%s\"" % self.forbiddenWords) if self.forbiddenWords is not None else ""
        rep += (", requiredWords \"%s\"" % self.requiredWords) if self.requiredWords is not None else ""
        rep += (", season \"%s\"" % self.season) if self.season is not None else ""
        rep += (", episode \"%s\"" % self.episode) if self.episode is not None else ""
        if self.category:
            if isinstance(self.category, dict) or isinstance(self.category, Bunch):
                rep += (", category \"%s\"" % self.category.pretty)
        else:
            rep += (", category \"%s\"" % self.category)
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
    if key in indexer.settings.search_ids:
        return True
    # We might be able to convert them using TVMaze
    if key == "tvdbid" and "rid" in indexer.settings.search_ids:
        return True
    if key == "rid" and "tvdbid" in indexer.settings.search_ids:
        return True


def pick_indexers(search_request):
    # type: (nzbhydra.search.SearchRequest, bool) -> List[nzbhydra.search_modules.SearchModule]
    query_supplied = True if search_request.query else False
    queryCanBeGenerated = None  # Store if we can generate a query from IDs. Initiall true but when we need this the first time and query generation fails we set it to false
    picked_indexers = []
    selected_indexers = search_request.indexers.split("|") if search_request.indexers is not None else None
    for p in indexers.enabled_indexers:
        if not p.settings.enabled:
            logger.debug("Did not pick %s because it is disabled" % p)
            continue
        if search_request.internal and p.settings.accessType == "external":
            logger.debug("Did not pick %s because it is only enabled for external searches" % p)
            continue
        if not search_request.internal and p.settings.accessType == "internal":
            logger.debug("Did not pick %s because it is only enabled for internal searches" % p)
            continue
        if selected_indexers and p.name not in selected_indexers:
            logger.debug("Did not pick %s because it was not selected by the user" % p)
            continue
        try:
            status = p.indexer.status.get()
            if status.disabled_until > arrow.utcnow() and not config.settings.searching.ignoreTemporarilyDisabled:
                logger.info("Did not pick %s because it is disabled temporarily due to an error: %s" % (p, status.reason))
                continue
        except IndexerStatus.DoesNotExist:
            pass
        if hasattr(p.settings, "categories") and len(p.settings.categories) > 0:
            if search_request.category.category.name != "all" and search_request.category.category.name not in p.settings.categories:
                logger.debug("Did not pick %s because it is not enabled for category %s" % (p, search_request.category.category.pretty))
                continue
        if p.settings.hitLimit > 0:
            if p.settings.hitLimitResetTime:
                comparisonTime = arrow.utcnow().replace(hour=p.settings.hitLimitResetTime, minute=0, second=0)
                if comparisonTime > arrow.utcnow():
                    comparisonTime = arrow.get(comparisonTime.datetime - datetime.timedelta(days=1))  # Arrow is too dumb to properly subtract 1 day (throws an error on every first of the month)
            else:
                # Use rolling time window
                comparisonTime = arrow.get(arrow.utcnow().datetime - datetime.timedelta(days=1))

            apiHits = IndexerApiAccess().select().where((IndexerApiAccess.indexer == p.indexer) & (IndexerApiAccess.time > comparisonTime) & IndexerApiAccess.response_successful).count()
            if apiHits >= p.settings.hitLimit:
                if p.settings.hitLimitResetTime:
                    logger.info("Did not pick %s because its API hit limit of %d was reached. Will pick again after %02d:00" % (p, p.settings.hitLimit, p.settings.hitLimitResetTime))
                else:
                    try:
                        firstHitTimeInWindow = IndexerApiAccess().select().where(IndexerApiAccess.indexer == p.indexer & IndexerApiAccess.response_successful).order_by(IndexerApiAccess.time.desc()).offset(p.settings.hitLimit).limit(1).get().time.datetime
                        nextHitAfter = arrow.get(firstHitTimeInWindow + datetime.timedelta(days=1))
                        logger.info("Did not pick %s because its API hit limit of %d was reached. Next possible hit at %s" % (p, p.settings.hitLimit, nextHitAfter.format('YYYY-MM-DD HH:mm')))
                    except IndexerApiAccess.DoesNotExist:
                        logger.info("Did not pick %s because its API hit limit of %d was reached" % (p, p.settings.hitLimit))
                continue
            else:
                logger.debug("%s has had %d of a maximum of %d API hits since %02d:%02d" % (p, apiHits, p.settings.hitLimit, comparisonTime.hour, comparisonTime.minute))

        if (query_supplied or search_request.identifier_key is not None) and not p.supports_queries:
            logger.debug("Did not pick %s because a query was supplied but the indexer does not support queries" % p)
            continue

        # Here on we check if we could supply the indexer with generated/retrieved data like the title of a series
        if not query_supplied and p.needs_queries and search_request.identifier_key is None:
            logger.debug("Did not pick %s because no query was supplied but the indexer needs queries" % p)
            continue

        # If we can theoretically do that we must try to actually get the title, otherwise the indexer won't be able to search 
        allow_query_generation = (config.InternalExternalSelection.internal in config.settings.searching.generate_queries and search_request.internal) or (config.InternalExternalSelection.external in config.settings.searching.generate_queries and not search_request.internal)
        if search_request.identifier_key is not None and not canUseIdKey(p, search_request.identifier_key):
            if not (allow_query_generation and p.generate_queries):
                logger.debug("Did not pick %s because search will be done by an identifier and the indexer or system wide settings don't allow query generation" % p)
                continue
            else:
                if queryCanBeGenerated is None:
                    try:
                        title = infos.convertId(search_request.identifier_key, "title", search_request.identifier_value)
                        if title:
                            search_request.title = title
                            queryCanBeGenerated = True
                        else:
                            queryCanBeGenerated = False
                    except:
                        queryCanBeGenerated = False
                        logger.debug("Unable to get title for supplied ID. Indexers that don't support the ID will be skipped")
                if not queryCanBeGenerated:
                    logger.debug("Did not pick %s because search will be done by an identifier and retrieval of the title for query generation failed" % p)
                    continue

        logger.debug("Picked %s" % p)
        picked_indexers.append(p)

    return picked_indexers


pseudo_cache = {}


def search(search_request):
    if search_request.maxage is None and config.settings.searching.maxAge:
        search_request.maxage = config.settings.searching.maxAge
        logger.info("Will ignore results older than %d days" % search_request.maxage)

    # Clean up cache
    for k in list(pseudo_cache.keys()):
        if pseudo_cache[k]["last_access"].replace(minutes=+5) < arrow.utcnow():
            pseudo_cache.pop(k)

    # Clean up old search results. We do this here because we don't have any background jobs and this is the function most regularly called
    keepFor = config.settings.main.keepSearchResultsForDays
    oldSearchResultsCount = SearchResult.select().where(SearchResult.firstFound < (datetime.date.today() - datetime.timedelta(days=keepFor))).count()
    if oldSearchResultsCount > 0:
        logger.info("Deleting %d search results from database that are older than %d days" % (oldSearchResultsCount, keepFor))
        SearchResult.delete().where(SearchResult.firstFound < (datetime.date.today() - datetime.timedelta(days=keepFor))).execute()

    limit = search_request.limit
    external_offset = int(search_request.offset)
    search_hash = search_request.search_hash
    categoryResult = categories.getCategoryByAnyInput(search_request.category)
    search_request.category = categoryResult
    if search_hash not in pseudo_cache.keys() or search_request.offset == 0:  # If it's a new search (which starts with offset 0) do it again instead of using the cached results
        logger.debug("Didn't find this query in cache or want to do a new search")
        cache_entry = {"results": [], "indexer_infos": {}, "total": 0, "last_access": arrow.utcnow(), "offset": 0}
        category = categoryResult.category
        indexers_to_call = pick_indexers(search_request)
        for p in indexers_to_call:
            cache_entry["indexer_infos"][p] = {"has_more": True, "search_request": search_request, "total_included": False}
        
        dbsearch = Search(internal=search_request.internal, query=search_request.query, category=categoryResult.category.pretty, identifier_key=search_request.identifier_key, identifier_value=search_request.identifier_value, season=search_request.season, episode=search_request.episode, type=search_request.type,
                          username=search_request.username)
        # dbsearch.save()
        cache_entry["dbsearch"] = dbsearch

        # Find ignored words and parse query for ignored words
        search_request.forbiddenWords = []
        search_request.requiredWords = []
        applyRestrictionsGlobal = config.settings.searching.applyRestrictions == "both" or (config.settings.searching.applyRestrictions == "internal" and search_request.internal) or (config.settings.searching.applyRestrictions == "external" and not search_request.internal)
        applyRestrictionsCategory = category.applyRestrictions == "both" or (category.applyRestrictions == "internal" and search_request.internal) or (search_request.category.category.applyRestrictions == "external" and not search_request.internal)
        if config.settings.searching.forbiddenWords and applyRestrictionsGlobal:
            logger.debug("Using configured global forbidden words: %s" % config.settings.searching.forbiddenWords)
            search_request.forbiddenWords.extend([x.lower().strip() for x in list(filter(bool, config.settings.searching.forbiddenWords.split(",")))])
        if config.settings.searching.requiredWords and applyRestrictionsGlobal:
            logger.debug("Using configured global required words: %s" % config.settings.searching.requiredWords)
            search_request.requiredWords.extend([x.lower().strip() for x in list(filter(bool, config.settings.searching.requiredWords.split(",")))])
        
        if category.forbiddenWords and applyRestrictionsCategory:
            logger.debug("Using configured forbidden words for category %s: %s" % (category.pretty, category.forbiddenWords))
            search_request.forbiddenWords.extend([x.lower().strip() for x in list(filter(bool, category.forbiddenWords.split(",")))])
        if category.requiredWords and applyRestrictionsCategory:
            logger.debug("Using configured required words for category %s: %s" % (category.pretty, category.requiredWords))
            search_request.requiredWords.extend([x.lower().strip() for x in list(filter(bool, category.requiredWords.split(",")))])
        
        
        if search_request.query:
            forbiddenWords = [str(x[1]) for x in re.findall(r"[\s|\b](\-\-|!)(?P<term>\w+)", search_request.query)]
            if len(forbiddenWords) > 0:
                logger.debug("Query before removing NOT terms: %s" % search_request.query)
                search_request.query = re.sub(r"[\s|\b](\-\-|!)(?P<term>\w+)", "", search_request.query)
                logger.debug("Query after removing NOT terms: %s" % search_request.query)
                logger.debug("Found NOT terms: %s" % ",".join(forbiddenWords))

                search_request.forbiddenWords.extend(forbiddenWords)

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
            #Drastically improves db access time but means that if one database write fails all fail. That's a risk we need to take 
            with db.atomic():
                for result in queries_execution_result.results:
                    if result.title is None or result.link is None or result.indexerguid is None:
                        logger.info("Skipping result with missing data: %s" % result)
                        continue
                    searchResult = SearchResult().get_or_create(indexer=indexer.indexer, guid=result.indexerguid, defaults={"title": result.title, "link": result.link, "details": result.details_link})
                    searchResult = searchResult[0]  # Second is a boolean determining if the search result was created
                    result.searchResultId = searchResult.id
                    search_results.append(result)
        
                logger.debug("%s returned %d results" % (indexer, len(queries_execution_result.results)))
                cache_entry["indexer_infos"][indexer].update(
                    {"did_search": queries_execution_result.didsearch, "indexer": indexer.name, "search_request": search_request, "has_more": queries_execution_result.has_more, "total": queries_execution_result.total, "total_known": queries_execution_result.total_known,
                     "indexer_search": queries_execution_result.indexerSearchEntry})
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

        if search_request.internal or config.settings.searching.removeDuplicatesExternal:
            countBefore = len(search_results)
            grouped_by_sameness = find_duplicates(search_results)
            allresults = []
            for group in grouped_by_sameness:
                if search_request.internal:
                    for i in group:
                        # We give each group of results a unique value by which they can be identified later
                        i.hash = hash(group[0].details_link)
                        allresults.append(i)

                else:
                    # We sort by age first and then by indexerscore so the newest result with the highest indexer score is chosen
                    group = sorted(group, key=lambda x: x.epoch, reverse=True)
                    group = sorted(group, key=lambda x: x.indexerscore, reverse=True)
                    allresults.append(group[0])
            search_results = allresults
            if not search_request.internal:
                countAfter = len(search_results)
                countRemoved = countBefore - countAfter
                logger.info("Removed %d duplicates from %d results" % (countRemoved, countBefore))
        search_results = sorted(search_results, key=lambda x: x.epoch, reverse=True)

        cache_entry["results"].extend(search_results)
        cache_entry["offset"] += limit

    if search_request.internal:
        logger.debug("We have %d cached results and return them all because we search internally" % len(cache_entry["results"]))
        nzb_search_results = copy.deepcopy(cache_entry["results"][external_offset:])
    else:
        logger.debug("We have %d cached results and return %d-%d of %d total available accounting for the limit set for the API search" % (len(cache_entry["results"]), external_offset, external_offset + limit, cache_entry["total"]))
        nzb_search_results = copy.deepcopy(cache_entry["results"][external_offset:(external_offset + limit)])
    cache_entry["last_access"] = arrow.utcnow()

    return {"results": nzb_search_results, "indexer_infos": cache_entry["indexer_infos"], "dbsearchid": cache_entry["dbsearch"].id, "total": cache_entry["total"], "offset": external_offset}


def search_and_handle_db(dbsearch, indexers_and_search_requests):
    results_by_indexer = start_search_futures(indexers_and_search_requests)
    dbsearch.username = request.authorization.username if request.authorization is not None else None
    dbsearch.save()
    for indexer, result in results_by_indexer.items():
        if result.didsearch:
            indexersearchentry = result.indexerSearchEntry
            indexersearchentry.search = dbsearch
            indexersearchentry.save()
            result.indexerApiAccessEntry.username = request.authorization.username if request.authorization is not None else None
            try:
                result.indexerApiAccessEntry.indexer = Indexer.get(Indexer.name == indexer)
                result.indexerApiAccessEntry.save()
                result.indexerStatus.save()
            except Indexer.DoesNotExist:
                logger.error("Tried to save indexer API access but no indexer with name %s was found in the database. Adding it now. This shouldn't've happened. If possible send a bug report with a full log." % indexer)
                Indexer().create(name=indexer)
            except Exception as e:
                logger.error("Error saving IndexerApiAccessEntry", e)

    logger.debug("Returning search results now")
    return {"results": results_by_indexer, "dbsearch": dbsearch}


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
            try:
                results = f.result()
                indexer_to_searchresults[futures_to_indexers[f]] = results
                logger.debug("Retrieved %d of %d calls from executor" % (count, len(futures_to_indexers)))
                count += 1
            except Exception as e:
                logger.exception("Error while calling search module")

    return indexer_to_searchresults


def find_duplicates(results):
    # We group all results with the same title together (only those can be duplicates of each other)
    sorted_results = sorted(results, key=lambda x: re.sub(r"[ \.\-_]", "", x.title.lower()))
    grouped_by_title = groupby(sorted_results, key=lambda x: re.sub(r"[ \.\-_]", "", x.title.lower()))
    grouped_by_sameness = []
    for title, titleGroup in grouped_by_title:
        # As we compare the results' size first we want to have the results sorted by that
        titleGroup = sorted(list(titleGroup), key=lambda x: x.pubdate_utc, reverse=True)
        grouped = [titleGroup[:1]]
        for i in titleGroup[1:]:
            foundGroup = False
            for group in grouped:
                for other in group:
                    same = testForSameness(i, other)
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


def testForSameness(result1, result2):
    group_known = result1.group is not None and result2.group is not None
    same_group = result1.group == result2.group
    poster_known = result1.poster is not None and result2.poster is not None
    same_poster = result1.poster == result2.poster

    age_threshold = config.settings["searching"]["duplicateAgeThreshold"]
    size_threshold = config.settings["searching"]["duplicateSizeThresholdInPercent"]
    if (group_known and not same_group) or (poster_known and not same_poster):
        return False
    if (same_group and not poster_known) or (same_poster and not group_known):
        age_threshold = 4
        size_threshold = 2
    if same_group and same_poster:
        age_threshold = 2
        size_threshold = 1
    
    same = result1.indexer != result2.indexer
    same = same and test_for_duplicate_age(result1, result2, age_threshold)
    same = same and test_for_duplicate_size(result1, result2, size_threshold)
    return same


def test_for_duplicate_age(result1, result2, age_threshold):
    if result1.epoch is None or result2.epoch is None:
        return False
    
    group_known = result1.group is not None and result2.group is not None
    same_group = result1.group == result2.group
    poster_known = result1.poster is not None and result2.poster is not None
    same_poster = result1.poster == result2.poster
    if (group_known and not same_group) or (poster_known and not same_poster):
        return False
    
    same_age = abs(result1.epoch - result2.epoch) / (60 * 60) <= age_threshold  # epoch difference (seconds) to minutes    
    return same_age


def test_for_duplicate_size(result1, result2, size_threshold):
    if not result1.size or not result2.size:
        return False
    size_difference = result1.size - result2.size
    size_average = (result1.size + result2.size) / 2
    size_difference_percent = abs(size_difference / size_average) * 100
    same_size = size_difference_percent <= size_threshold

    return same_size
