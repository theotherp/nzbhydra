from peewee import fn

from nzbhydra.database import Provider, ProviderApiAccess
from nzbhydra import database

count = 0


def get_count():
    global count
    count += 1
    return count


def get_provider_response_times():
    result = []

    # //$scope.data = [{
    # //    key: "v", values: [{x: 1, y: 102}
    # //    ]
    for p in Provider.select():
        print("Limiting stats to 100 for testing only!")
        result.append({"key": p.name,
                       "values": [{"responseTime": x.response_time, "date": x.time.timestamp} for x in ProviderApiAccess().select(ProviderApiAccess.response_time, ProviderApiAccess.time).where((ProviderApiAccess.response_successful) & (ProviderApiAccess.provider == p)).join(Provider).limit(1)]})
    return result


def get_avg_provider_response_times():
    result = []

    # //$scope.data = [{
    # //    key: "v", values: [{x: 1, y: 102}
    # //    ]
    response_times = []
    for p in Provider.select().order_by(Provider.name):

        avg_response_time = ProviderApiAccess().select(fn.AVG(ProviderApiAccess.response_time)).where((ProviderApiAccess.response_successful) & (ProviderApiAccess.provider == p)).tuples()[0][0]
        if avg_response_time:
            response_times.append({"name": p.name, "avgResponseTime": avg_response_time})
    avg_response_time = ProviderApiAccess().select(fn.AVG(ProviderApiAccess.response_time)).where((ProviderApiAccess.response_successful) & (ProviderApiAccess.response_time is not None)).tuples()[0][0]
    for i in response_times:
        delta = i["avgResponseTime"] - avg_response_time
        i["delta"] = delta
        result.append(i)

    return result


def get_avg_provider_search_results_share():
    results = []
    for p in Provider.select().order_by(Provider.name):
        result = database.db.execute_sql(
            "select (100 * (select cast(sum(ps.results) as float) from providersearch ps where ps.search_id in (select ps.search_id from providersearch ps where ps.provider_id == %d) and ps.provider_id == %d)) / (select sum(ps.results) from providersearch ps where ps.search_id in (select ps.search_id from providersearch ps where ps.provider_id == %d)) as sumAllResults" % (
            p.id, p.id, p.id)).fetchone()
        results.append({"name": p.name, "avgResultsShare": result[0]})
    return results


# ProviderSearch().select(fn.SUM(ProviderSearch.results)).where(ProviderSearch.successful).group_by(ProviderSearch.search).order_by(ProviderSearch.time)


def get_avg_provider_access_success():
    # select p.name, failed.failed, success.success from provider p, (select count(1) as failed, p.provider_id as pid1 from providerapiaccess p where not p.response_successful group by p.provider_id) as failed, (select count(1) as success, p.provider_id as pid2 from providerapiaccess p where p.response_successful group by p.provider_id) as success  where p.id = pid1 and p.id = pid2 group by pid1
    results = database.db.execute_sql(
        "SELECT p.name, failed.failed, success.success FROM provider p, (SELECT count(1) AS failed, p.provider_id AS pid1 FROM providerapiaccess p WHERE NOT p.response_successful GROUP BY p.provider_id) AS failed, (SELECT count(1) AS success, p.provider_id AS pid2 FROM providerapiaccess p WHERE p.response_successful GROUP BY p.provider_id) AS success  WHERE p.id = pid1 AND p.id = pid2 GROUP BY pid1").fetchall()
    result = []
    for i in results:
        name = i[0]
        failed = i[1]
        success = i[2]
        sumall = failed + success
        failed_percent = (100 * failed) / sumall
        success_percent = (100 * success) / sumall
        result.append({"name": name, "failed": failed, "success": success, "failedPercent": failed_percent, "successPercent": success_percent})

    return result
