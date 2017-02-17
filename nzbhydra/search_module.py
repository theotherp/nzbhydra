from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import logging
import re
from sqlite3 import OperationalError

import arrow
from builtins import *
from flask import request
from peewee import fn, OperationalError
from requests import RequestException
from requests.auth import HTTPBasicAuth
from retry import retry

from nzbhydra import config, databaseLock
from nzbhydra import webaccess
from nzbhydra.database import IndexerSearch, IndexerApiAccess, IndexerStatus, Indexer
from nzbhydra.database import InterfaceError
from nzbhydra.exceptions import IndexerResultParsingException, IndexerAuthException, IndexerAccessException
from nzbhydra.log import removeSensitiveData
from nzbhydra.nzb_search_result import NzbSearchResult

QueriesExecutionResult = collections.namedtuple("QueriesExecutionResult", "didsearch results indexerSearchEntry indexerApiAccessEntry indexerStatus total loaded_results total_known has_more rejected")
IndexerProcessingResult = collections.namedtuple("IndexerProcessingResult", "entries queries total total_known has_more rejected")
titleRegex = re.compile("(\w[\w']*\w|\w)")


class SearchModule(object):
    logger = logging.getLogger('root')

    # regarding quality:
    # possibly use newznab qualities as base, map for other indexers (nzbclub etc)


    def __init__(self, settings):
        self.settings = settings
        self.module = "Abstract search module"
        self.supports_queries = True
        self.needs_queries = False
        self.category_search = True  # If true the indexer supports searching in a given category (possibly without any query or id)
        self.limit = 100
        self.supportedFilters = []
        self.supportsNot = None
        self.indexerDb = None

    def __repr__(self):
        return self.name

    @property
    def indexer(self):
        if self.indexerDb is None:
            self.indexerDb = Indexer.get(fn.lower(Indexer.name) == self.settings.name.lower())
        return self.indexerDb

    @property
    def host(self):
        return self.settings.host

    @property
    def name(self):
        return self.settings.name

    @property
    def score(self):
        return self.settings.score

    @property
    def search_ids(self):
        if "search_ids" not in self.settings.keys():
            self.error('Search IDs property not set. Please open the config for this indexer and click "Check capabilities"')
            return []
        return self.settings.search_ids

    @property
    def searchTypes(self):
        if "searchTypes" not in self.settings.keys():
            self.error('Search types property not set. Please open the config for this indexer and click "Check capabilities"')
            return []
        return self.settings.searchTypes

    @property
    def generate_queries(self):
        return True  # TODO pass when used check for internal vs external
        # return self.indexer.settings.get("generate_queries", True)  # If true and a search by movieid or tvdbid or rid is done then we attempt to find the title and generate queries for indexers which don't support id-based searches

    def search(self, search_request):
        self.info("Starting search")
        if search_request.type == "tv":
            if search_request.query is None and search_request.identifier_key is None and self.needs_queries:
                self.error("TV search without query or id or title is not possible with this indexer")
                return []
            if search_request.query is None and not self.generate_queries:
                self.error("TV search is not possible with this provideer because query generation is disabled")
            if search_request.identifier_key in self.search_ids:
                # Best case, we can search using the ID
                urls = self.get_showsearch_urls(search_request)
            elif search_request.title is not None:
                # If we cannot search using the ID we generate a query using the title provided by the GUI
                search_request.query = search_request.title
                urls = self.get_showsearch_urls(search_request)
            elif search_request.query is not None:
                # Simple case, just a regular raw search but in movie category
                urls = self.get_showsearch_urls(search_request)
            else:
                # Just show all the latest tv releases
                urls = self.get_showsearch_urls(search_request)
        elif search_request.type == "movie":
            if search_request.query is None and search_request.title is None and search_request.identifier_key is None and self.needs_queries:
                self.error("Movie search without query or IMDB id or title is not possible with this indexer")
                return []
            if search_request.query is None and not self.generate_queries:
                self.error("Movie search is not possible with this provideer because query generation is disabled")
            if search_request.identifier_key is not None and "imdbid" in self.search_ids:
                # Best case, we can search using IMDB id
                urls = self.get_moviesearch_urls(search_request)
            elif search_request.title is not None:
                # If we cannot search using the ID we generate a query using the title provided by the GUI
                search_request.query = search_request.title
                urls = self.get_moviesearch_urls(search_request)
            elif search_request.query is not None:
                # Simple case, just a regular raw search but in movie category
                urls = self.get_moviesearch_urls(search_request)
            else:
                # Just show all the latest movie releases
                urls = self.get_moviesearch_urls(search_request)
        elif search_request.type == "ebook":
            urls = self.get_ebook_urls(search_request)
        elif search_request.type == "audiobook":
            urls = self.get_audiobook_urls(search_request)
        elif search_request.type == "comic":
            urls = self.get_comic_urls(search_request)
        elif search_request.type == "anime":
            urls = self.get_anime_urls(search_request)
        else:
            urls = self.get_search_urls(search_request)
        queries_execution_result = self.execute_queries(urls, search_request)
        return queries_execution_result

    # Access to most basic functions
    def get_search_urls(self, search_request):
        # return url(s) to search. Url is then retrieved and result is returned if OK
        # we can return multiple urls in case a module needs to make multiple requests (e.g. when searching for a show
        # using general queries
        return []

    def get_showsearch_urls(self, search_request):
        # to extend
        # if module supports it, search specifically for show, otherwise make sure we create a query that searches
        # for for s01e01, 1x1 etc
        return []

    def get_moviesearch_urls(self, search_request):
        # to extend
        # if module doesnt support it possibly use (configurable) size restrictions when searching
        return []

    def get_ebook_urls(self, search_request):
        # to extend
        # if module doesnt support it possibly use (configurable) size restrictions when searching
        return []

    def get_audiobook_urls(self, search_request):
        # to extend
        # if module doesnt support it possibly use (configurable) size restrictions when searching
        return []

    def get_comic_urls(self, search_request):
        # to extend
        # if module doesnt support it possibly use (configurable) size restrictions when searching
        return []

    def get_anime_urls(self, search_request):
        # to extend
        # if module doesnt support it possibly use (configurable) size restrictions when searching
        return []

    def get_details_link(self, guid):
        return ""

    def get_entry_by_id(self, guid, title):
        # to extend
        # Returns an NzbSearchResult for the given GUID 
        return None

    def create_nzb_search_result(self):
        result = NzbSearchResult(indexer=self.name, indexerscore=self.score, attributes=[{"name": "hydraIndexerName", "value": self.settings.name},
                                                                                         {"name": "hydraIndexerHost", "value": self.settings.host},
                                                                                         {"name": "hydraIndexerScore", "value": self.settings.score}])
        return result

    @staticmethod
    def getRejectedCountDict():
        return {
            "the results were passworded": 0,
            "the title contained a forbidden word": 0,
            "a required word was missing in the title": 0,
            "the required regex was not found in the title": 0,
            "the forbidden regex was found in the title": 0,
            "they were posted in a forbidden group": 0,
            "they were posted by a forbidden poster": 0,
            "they had the wrong size": 0,
            "they had the wrong age": 0,
            "they were missing necessary attributes": 0,
            "their category is to be ignored": 0
        }

    def accept_result(self, nzbSearchResult, searchRequest, supportedFilters):
        global titleRegex
        # Allows the implementations to check against one general rule if the search result is ok or shall be discarded
        if config.settings.searching.ignorePassworded and nzbSearchResult.passworded:
            return False, "passworded results shall be ignored", "the results were passworded"
        # Forbidden and required words are handled differently depending on if they contain a dash or dot. If yes we do a simple search, otherwise a word based comparison
        for word in searchRequest.forbiddenWords:
            if "-" in word or "." in word or "nzbgeek" in self.settings.host:  # NZBGeek must be handled here because it only allows 12 words at all so it's possible that not all words were ignored
                if word.strip().lower() in nzbSearchResult.title.lower():
                    return False, '"%s" is in the list of ignored words or excluded by the query' % word, "the title contained a forbidden word"
            elif word.strip().lower() in titleRegex.findall(nzbSearchResult.title.lower()):
                return False, '"%s" is in the list of ignored words or excluded by the query' % word, "the title contained a forbidden word"
        if searchRequest.requiredWords and len(searchRequest.requiredWords) > 0:
            foundRequiredWord = False
            titleWords = titleRegex.findall(nzbSearchResult.title.lower())
            for word in searchRequest.requiredWords:
                if "-" in word or "." in word:
                    if word.strip().lower() in nzbSearchResult.title.lower():
                        foundRequiredWord = True
                        break
                elif word.strip().lower() in titleWords:
                    foundRequiredWord = True
                    break
            if not foundRequiredWord:
                return False, 'None of the required words is contained in the title "%s"' % nzbSearchResult.title, "a required word was missing in the title"

        applyRestrictionsGlobal = config.settings.searching.applyRestrictions == "both" or (config.settings.searching.applyRestrictions == "internal" and searchRequest.internal) or (config.settings.searching.applyRestrictions == "external" and not searchRequest.internal)
        applyRestrictionsCategory = searchRequest.category.category.applyRestrictions == "both" or (searchRequest.category.category.applyRestrictions == "internal" and searchRequest.internal) or (searchRequest.category.category.applyRestrictions == "external" and not searchRequest.internal)
        if (searchRequest.category.category.requiredRegex and applyRestrictionsCategory and not re.search(searchRequest.category.category.requiredRegex.lower(), nzbSearchResult.title.lower())) \
                or (config.settings.searching.requiredRegex and applyRestrictionsGlobal and not re.search(config.settings.searching.requiredRegex.lower(), nzbSearchResult.title.lower())):
            return False, "Required regex not found in title", "the required regex was not found in the title"
        if (searchRequest.category.category.forbiddenRegex and applyRestrictionsCategory and re.search(searchRequest.category.category.forbiddenRegex.lower(), nzbSearchResult.title.lower())) \
                or (config.settings.searching.forbiddenRegex and applyRestrictionsGlobal and re.search(config.settings.searching.forbiddenRegex.lower(), nzbSearchResult.title.lower())):
            return False, "Forbidden regex found in title", "the forbidden regex was found in the title"
        if config.settings.searching.forbiddenGroups and nzbSearchResult.group:
            for forbiddenPoster in config.settings.searching.forbiddenGroups.split(","):
                if forbiddenPoster in nzbSearchResult.group:
                    return False, "Posted in forbidden group '%s'" % forbiddenPoster, "they were posted in a forbidden group"
        if config.settings.searching.forbiddenPosters and nzbSearchResult.poster:
            for forbiddenPoster in config.settings.searching.forbiddenPosters.split(","):
                if forbiddenPoster in nzbSearchResult.poster:
                    return False, "Posted by forbidden poster '%s'" % forbiddenPoster, "they were posted by a forbidden poster"
        if searchRequest.minsize and nzbSearchResult.size / (1024 * 1024) < searchRequest.minsize:
            return False, "Smaller than requested minimum size: %dMB < %dMB" % (nzbSearchResult.size / (1024 * 1024), searchRequest.minsize), "they had the wrong size"
        if searchRequest.maxsize and nzbSearchResult.size / (1024 * 1024) > searchRequest.maxsize:
            return False, "Bigger than requested maximum size: %dMB > %dMB" % (nzbSearchResult.size / (1024 * 1024), searchRequest.maxsize), "they had the wrong size"
        if searchRequest.minage and nzbSearchResult.age_days < searchRequest.minage:
            return False, "Younger than requested minimum age: %dd < %dd" % (nzbSearchResult.age_days, searchRequest.minage), "they had the wrong age"
        if searchRequest.maxage and nzbSearchResult.age_days > searchRequest.maxage:
            return False, "Older than requested maximum age: %dd > %dd" % (nzbSearchResult.age_days, searchRequest.maxage), "they had the wrong age"
        if nzbSearchResult.pubdate_utc is None:
            return False, "Unknown age", "they were missing necessary attributes"
        if nzbSearchResult.category:
            ignore = False
            reason = ""
            if nzbSearchResult.category.ignoreResults == "always":
                reason = "always"
                ignore = True
            elif nzbSearchResult.category.ignoreResults == "internal" and searchRequest.internal:
                reason = "for internal searches"
                ignore = True
            elif nzbSearchResult.category.ignoreResults == "external" and not searchRequest.internal:
                reason = "for API searches"
                ignore = True
            elif self.settings.categories and nzbSearchResult.category.name not in self.settings.categories:
                reason = "by this indexer"
                ignore = True
            if ignore:
                return False, "Results from category %s are configured to be ignored %s" % (nzbSearchResult.category.pretty, reason), "their category is to be ignored"

        return True, None, ""

    def process_query_result(self, result, searchRequest, maxResults=None):
        return []

    def check_auth(self, body):
        # check the response body to see if request was authenticated. If yes, do nothing, if no, raise exception 
        return []

    disable_periods = [0, 15, 30, 60, 3 * 60, 6 * 60, 12 * 60, 24 * 60]

    def handle_indexer_success(self, doSaveIndexerStatus=True):
        # Deescalate level by 1 (or stay at 0) and reset reason and disable-time
        try:
            indexer_status = self.indexer.status.get()
        except IndexerStatus.DoesNotExist:
            indexer_status = IndexerStatus(indexer=self.indexer)
        if indexer_status.level > 0:
            indexer_status.level -= 1
        indexer_status.reason = None
        indexer_status.disabled_permanently = False
        indexer_status.disabled_until = arrow.get(0)  # Because I'm too dumb to set it to None/null

        if doSaveIndexerStatus:
            self.saveIndexerStatus(indexer_status)
        return indexer_status

    @retry((InterfaceError, OperationalError), delay=1, tries=5, logger=logger)
    def saveIndexerStatus(self, indexer_status):
        with databaseLock:
            indexer_status.save()

    def handle_indexer_failure(self, reason=None, disable_permanently=False, saveIndexerStatus=True):
        # Escalate level by 1. Set disabled-time according to level so that with increased level the time is further in the future
        try:
            indexer_status = self.indexer.status.get()
        except IndexerStatus.DoesNotExist:
            indexer_status = IndexerStatus(indexer=self.indexer)

        if indexer_status.level == 0:
            indexer_status.first_failure = arrow.utcnow()

        indexer_status.latest_failure = arrow.utcnow()
        indexer_status.reason = reason  # Overwrite the last reason if one is set, should've been logged anyway
        if disable_permanently:
            indexer_status.disabled_permanently = True
            self.info("Disabling indexer permanently until reenabled by user because the authentication failed")
        else:
            indexer_status.level = min(len(self.disable_periods) - 1, indexer_status.level + 1)
            indexer_status.disabled_until = arrow.utcnow().replace(minutes=+self.disable_periods[indexer_status.level])
            self.info("Disabling indexer temporarily due to access problems. Will be reenabled %s" % indexer_status.disabled_until.humanize())

        if saveIndexerStatus:
            self.saveIndexerStatus(indexer_status)

        return indexer_status

    def get(self, url, timeout=None, cookies=None):
        # overwrite for special handling, e.g. cookies
        headers = {'User-Agent': "NZBHydra"}
        if hasattr(self.settings, "userAgent") and self.settings.userAgent:
            headers['User-Agent'] = self.settings.userAgent
        elif config.settings.searching.userAgent:
            headers['User-Agent'] = config.settings.searching.userAgent
        if timeout is None:
            timeout = self.settings.timeout
        if timeout is None:
            timeout = config.settings.searching.timeout
        if hasattr(self.settings, "username") and self.settings.username and self.settings.password:
            auth = HTTPBasicAuth(self.settings.username, self.settings.password)
            self.debug("Using HTTP auth")
        else:
            auth = None
        self.debug("Requesting %s with timeout %d" % (url, timeout))
        return webaccess.get(url, timeout=timeout, cookies=cookies, headers=headers, auth=auth)

    def get_url_with_papi_access(self, url, type, cookies=None, timeout=None, saveToDb=True):
        papiaccess = IndexerApiAccess(indexer=self.indexer, type=type, url=url, time=arrow.utcnow().datetime)
        try:
            papiaccess.username = request.authorization.username if request.authorization is not None else None
        except RuntimeError:
            # Is thrown when we're searching which is run in a thread. When downloading NFOs or whatever this will work
            pass
        indexerStatus = None
        try:
            time_before = arrow.utcnow()
            response = self.get(url, cookies=cookies, timeout=timeout)
            response.raise_for_status()

            time_after = arrow.utcnow()
            papiaccess.response_time = (time_after - time_before).seconds * 1000 + ((time_after - time_before).microseconds / 1000)
            papiaccess.response_successful = True
            self.debug("HTTP request to indexer completed in %dms" % papiaccess.response_time)
            indexerStatus = self.handle_indexer_success(doSaveIndexerStatus=saveToDb)
        except RequestException as e:
            self.error("Error while connecting to URL %s: %s" % (url, str(e)))
            papiaccess.error = "Connection failed: %s" % removeSensitiveData(str(e))
            response = None
            indexerStatus = self.handle_indexer_failure("Connection failed: %s" % removeSensitiveData(str(e)), saveIndexerStatus=saveToDb)
        finally:
            if saveToDb:
                self.saveIndexerStatus(papiaccess)
        return response, papiaccess, indexerStatus

    def get_nfo(self, guid):
        return None

    def get_nzb_link(self, guid, title):
        return None

    def get_search_ids_from_indexer(self):
        return []

    def execute_queries(self, queries, searchRequest):
        if len(queries) == 0:
            return QueriesExecutionResult(didsearch=False, results=[], indexerSearchEntry=None, indexerApiAccessEntry=None, indexerStatus=None, total=0, loaded_results=0, total_known=True, has_more=False, rejected=self.getRejectedCountDict())
        results = []
        executed_queries = set()
        psearch = IndexerSearch(indexer=self.indexer)
        papiaccess = IndexerApiAccess()
        indexerStatus = None
        total_results = 0
        total_known = False
        has_more = False
        rejected = self.getRejectedCountDict()
        while len(queries) > 0:
            query = queries.pop()
            if query in executed_queries:
                # To make sure that in case an offset is reported wrong or we have a bug we don't get stuck in an endless loop 
                continue

            try:
                request, papiaccess, indexerStatus = self.get_url_with_papi_access(query, "search", saveToDb=False)
                papiaccess.indexer_search = psearch

                executed_queries.add(query)

                if request is not None:
                    if request.text == "":
                        raise IndexerResultParsingException("Indexer returned an empty page", self)
                    self.check_auth(request.text)
                    self.debug("Successfully loaded URL %s" % request.url)
                    try:

                        parsed_results = self.process_query_result(request.content, searchRequest)
                        results.extend(parsed_results.entries)  # Retrieve the processed results
                        queries.extend(parsed_results.queries)  # Add queries that were added as a result of the parsing, e.g. when the next result page should also be loaded
                        total_results += parsed_results.total
                        total_known = parsed_results.total_known
                        has_more = parsed_results.has_more
                        rejected = parsed_results.rejected

                        papiaccess.response_successful = True
                        indexerStatus = self.handle_indexer_success(False)
                    except Exception:
                        self.exception("Error while processing search results from indexer %s" % self)
                        raise IndexerResultParsingException("Error while parsing the results from indexer", self)
            except IndexerAuthException as e:
                papiaccess.error = "Authorization error :%s" % e.message
                self.error(papiaccess.error)
                indexerStatus = self.handle_indexer_failure(reason="Authentication failed", disable_permanently=True)
                papiaccess.response_successful = False
            except IndexerAccessException as e:
                papiaccess.error = "Access error: %s" % e.message
                self.error(papiaccess.error)
                indexerStatus = self.handle_indexer_failure(reason="Access failed")
                papiaccess.response_successful = False
            except IndexerResultParsingException as e:
                papiaccess.error = "Access error: %s" % e.message
                self.error(papiaccess.error)
                indexerStatus = self.handle_indexer_failure(reason="Parsing results failed")
                papiaccess.response_successful = False
            except Exception as e:
                self.exception("An error error occurred while searching: %s", e)
                if papiaccess is not None:
                    papiaccess.error = "Unknown error :%s" % e
                    papiaccess.response_successful = False
            finally:
                if papiaccess is not None:
                    psearch.successful = papiaccess.response_successful
                else:
                    self.error("Unable to save API response to database")
                psearch.resultsCount = total_results
        return QueriesExecutionResult(didsearch=True, results=results, indexerSearchEntry=psearch, indexerApiAccessEntry=papiaccess, indexerStatus=indexerStatus, total=total_results, loaded_results=len(results), total_known=total_known, has_more=has_more, rejected=rejected)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug("%s: %s" % (self.name, msg), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info("%s: %s" % (self.name, msg), *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self.logger.warn("%s: %s" % (self.name, msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error("%s: %s" % (self.name, msg), *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.logger.exception("%s: %s" % (self.name, msg), *args, **kwargs)

    def isNumber(self, string):
        if string is None:
            return False
        try:
            int(string)
            return True
        except (TypeError, ValueError):
            return False

    def getDates(self, entry, usenetdate, preciseDate=True):
        entry.epoch = usenetdate.timestamp
        entry.age = usenetdate.humanize()
        entry.pubdate_utc = str(usenetdate)
        age = (arrow.utcnow() - usenetdate)
        if age.days == 0 and preciseDate:
            if age.seconds < 3600:
                entry.age = "%dm" % ((arrow.utcnow() - usenetdate).seconds / 60)
            else:
                entry.age = "%dh" % ((arrow.utcnow() - usenetdate).seconds / 3600)
        else:
            entry.age = str(age.days) + "d"
        entry.age_days = age.days
        entry.precise_date = preciseDate
        entry.pubDate = usenetdate.format("ddd, DD MMM YYYY HH:mm:ss Z")


def get_instance(indexer):
    return SearchModule(indexer)
