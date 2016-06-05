from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# standard_library.install_aliases()
import logging

from builtins import *
from peewee import fn, JOIN
from nzbhydra import database
from nzbhydra.database import Indexer, IndexerApiAccess, IndexerNzbDownload, IndexerSearch, Search, IndexerStatus, TvIdCache, MovieIdCache, SearchResult
from nzbhydra.exceptions import IndexerNotFoundException
from nzbhydra.indexers import getIndexerByName

logger = logging.getLogger('root')

def get_indexer_response_times():
    result = []
    for p in Indexer.select().order_by(Indexer.name):
        print("Limiting stats to 100 for testing only!")
        result.append({"key": p.name,
                       "values": [{"responseTime": x.response_time, "date": x.time.timestamp} for x in IndexerApiAccess().select(IndexerApiAccess.response_time, IndexerApiAccess.time).where((IndexerApiAccess.response_successful) & (IndexerApiAccess.indexer == p)).join(Indexer).limit(1)]})
    return result


def get_avg_indexer_response_times():
    result = []
    response_times = []
    for p in Indexer.select().order_by(Indexer.name):

        avg_response_time = IndexerApiAccess().select(fn.AVG(IndexerApiAccess.response_time)).where((IndexerApiAccess.response_successful) & (IndexerApiAccess.indexer == p)).tuples()[0][0]
        if avg_response_time:
            response_times.append({"name": p.name, "avgResponseTime": avg_response_time})
    avg_response_time = IndexerApiAccess().select(fn.AVG(IndexerApiAccess.response_time)).where((IndexerApiAccess.response_successful) & (IndexerApiAccess.response_time is not None)).tuples()[0][0]
    for i in response_times:
        delta = i["avgResponseTime"] - avg_response_time
        i["delta"] = delta
        result.append(i)

    return result


def get_avg_indexer_search_results_share():
    results = []
    for p in Indexer.select().order_by(Indexer.name):
        try:
            indexer = getIndexerByName(p.name)
            if not indexer.settings.enabled:
                logger.debug("Skipping download stats for %s" % p.name)
                continue
        except IndexerNotFoundException:
            logger.error("Unable to find indexer %s in configuration" % p.name)
            continue
        result = database.db.execute_sql(
                "select (100 * (select cast(sum(ps.resultsCount) as float) from indexersearch ps where ps.search_id in (select ps.search_id from indexersearch ps where ps.indexer_id == %d) and ps.indexer_id == %d)) / (select sum(ps.resultsCount) from indexersearch ps where ps.search_id in (select ps.search_id from indexersearch ps where ps.indexer_id == %d)) as sumAllResults" % (
                    p.id, p.id, p.id)).fetchone()
        results.append({"name": p.name, "avgResultsShare": result[0] if result[0] is not None else "N/A"})
    return results


def get_avg_indexer_access_success():
    results = database.db.execute_sql(
            """ 
            SELECT
              p.name,
              failed.failed
              ,success.success
            FROM indexer p left outer join (SELECT
                               count(1)     AS failed,
                               p.indexer_id AS pid1
                             FROM indexerapiaccess p
                             WHERE NOT p.response_successful
                             GROUP BY p.indexer_id) AS failed on p.id == failed.pid1
            left outer join (SELECT
                              count(1)     AS success,
                              p.indexer_id AS pid2
                            FROM indexerapiaccess p
                            WHERE p.response_successful
                            GROUP BY p.indexer_id) AS success
            on success.pid2 = p.id
            """).fetchall()
    result = []
    for i in results:
        name = i[0]
        try:
            indexer = getIndexerByName(name)
            if not indexer.settings.enabled:
                logger.debug("Skipping download stats for %s" % name)
                continue
        except IndexerNotFoundException:
            logger.error("Unable to find indexer %s in configuration" % name)
            continue
        failed = i[1] if i[1] is not None else 0
        success = i[2] if i[2] is not None else 0
        sumall = failed + success
        failed_percent = (100 * failed) / sumall if sumall > 0 else "N/A"
        success_percent = (100 * success) / sumall if sumall > 0 else "N/A"
        result.append({"name": name, "failed": failed, "success": success, "failedPercent": failed_percent, "successPercent": success_percent})

    return result


def getIndexerDownloadStats():
    results = []
    allDownloadsCount = IndexerNzbDownload.select().count()
    for p in Indexer.select().order_by(Indexer.name):
        try:
            indexer = getIndexerByName(p.name)
            if not indexer.settings.enabled:
                logger.debug("Skipping download stats for %s" % p.name)
                continue
        except IndexerNotFoundException:
            logger.error("Unable to find indexer %s in configuration" % p.name)
            continue
        dlCount = IndexerNzbDownload().\
            select(Indexer.name, IndexerApiAccess.response_successful). \
            join(IndexerApiAccess, JOIN.LEFT_OUTER). \
            join(Indexer, JOIN.LEFT_OUTER).\
            where(Indexer.id == p).\
            count()
        results.append({"name": p.name,
                        "total": dlCount,
                        "share": 100 / (allDownloadsCount / dlCount) if allDownloadsCount > 0 and dlCount > 0 else 0})
    return results


def get_nzb_downloads(page=0, limit=100, type=None):
    query = IndexerNzbDownload() \
        .select(Indexer.name.alias("indexerName"), IndexerNzbDownload.title, IndexerNzbDownload.time, SearchResult.id.alias('searchResultId'), SearchResult.details.alias('detailsLink'), Search.internal, IndexerApiAccess.response_successful, IndexerApiAccess.username) \
        .join(SearchResult, JOIN.LEFT_OUTER) \
        .switch(IndexerNzbDownload) \
        .join(IndexerApiAccess, JOIN.LEFT_OUTER) \
        .join(Indexer, JOIN.LEFT_OUTER) \
        .switch(IndexerApiAccess) \
        .join(IndexerSearch, JOIN.LEFT_OUTER) \
        .join(Search, JOIN.LEFT_OUTER)
        
    if type == "Internal":
        query = query.where(Search.internal)
    elif type == "API":
        query = query.where(~Search.internal)

    total_downloads = query.count()
    nzb_downloads = list(query.order_by(IndexerNzbDownload.time.desc()).paginate(page, limit).dicts())
    downloads = {"totalDownloads": total_downloads, "nzbDownloads": nzb_downloads}
    return downloads


#((Search.identifier_value == MovieIdCache.imdb) & (Search.identifier_key == "imdbid"))
def get_search_requests(page=0, limit=100, type=None):
    query = Search().select(Search.time, Search.internal, Search.query, Search.identifier_key, Search.identifier_value, Search.category, Search.season, Search.episode, Search.type, Search.username, TvIdCache.title.alias("tvtitle"), MovieIdCache.title.alias("movietitle")).join(TvIdCache, JOIN.LEFT_OUTER, on=(
        ((Search.identifier_value == TvIdCache.tvdb) & (Search.identifier_key == "tvdbid")) | 
        ((Search.identifier_value == TvIdCache.tvrage) & (Search.identifier_key == "rid"))
    )).join(MovieIdCache, JOIN.LEFT_OUTER, on=(
        ((Search.identifier_value == MovieIdCache.imdb) & (Search.identifier_key == "imdbid")) |
        ((Search.identifier_value == MovieIdCache.tmdb) & (Search.identifier_key == "tmdbid"))))

    if type is not None and type != "All":
        query = query.where(Search.internal) if type == "Internal" else query.where(~Search.internal)
    total_requests = query.count()
    requests = list(query.order_by(Search.time.desc()).paginate(page, limit).dicts())

    search_requests = {"totalRequests": total_requests, "searchRequests": requests}
    return search_requests


def get_indexer_statuses():
    return list(IndexerStatus().select(Indexer.name, IndexerStatus.first_failure, IndexerStatus.latest_failure, IndexerStatus.disabled_until, IndexerStatus.level, IndexerStatus.reason).join(Indexer).dicts())
