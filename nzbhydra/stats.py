from peewee import fn

from nzbhydra.database import Indexer, IndexerApiAccess, IndexerNzbDownload, IndexerSearch, Search
from nzbhydra import database


def get_indexer_response_times():
    result = []

    # //$scope.data = [{
    # //    key: "v", values: [{x: 1, y: 102}
    # //    ]
    for p in Indexer.select():
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
        result = database.db.execute_sql(
            "select (100 * (select cast(sum(ps.results) as float) from indexersearch ps where ps.search_id in (select ps.search_id from indexersearch ps where ps.indexer_id == %d) and ps.indexer_id == %d)) / (select sum(ps.results) from indexersearch ps where ps.search_id in (select ps.search_id from indexersearch ps where ps.indexer_id == %d)) as sumAllResults" % (
                p.id, p.id, p.id)).fetchone()
        results.append({"name": p.name, "avgResultsShare": result[0]})
    return results


# IndexerSearch().select(fn.SUM(IndexerSearch.results)).where(IndexerSearch.successful).group_by(IndexerSearch.search).order_by(IndexerSearch.time)


def get_avg_indexer_access_success():
    # select p.name, failed.failed, success.success from indexer p, (select count(1) as failed, p.indexer_id as pid1 from indexerapiaccess p where not p.response_successful group by p.indexer_id) as failed, (select count(1) as success, p.indexer_id as pid2 from indexerapiaccess p where p.response_successful group by p.indexer_id) as success  where p.id = pid1 and p.id = pid2 group by pid1
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
        failed = i[1] if i[1] is not None else 0
        success = i[2] if i[2] is not None else 0
        sumall = failed + success
        failed_percent = (100 * failed) / sumall if sumall > 0 else "N/A"
        success_percent = (100 * success) / sumall if sumall > 0 else "N/A"
        result.append({"name": name, "failed": failed, "success": success, "failedPercent": failed_percent, "successPercent": success_percent})

    return result


def get_nzb_downloads(page=0, limit=100):
    total_downloads = IndexerNzbDownload().select().count()
    return {"totalDownloads": total_downloads, "nzbDownloads": list(
        IndexerNzbDownload().select(Indexer.name, IndexerNzbDownload.title, IndexerNzbDownload.time, Search.internal).join(Indexer).join(IndexerSearch).join(Search).where(IndexerNzbDownload.indexer == Indexer.id).order_by(IndexerNzbDownload.time.desc()).group_by(IndexerNzbDownload.id).paginate(page,
                                                                                                                                                                                                                                                                                                       limit).dicts())}
