angular
    .module('nzbhydraApp')
    .factory('SearchService', SearchService);

function SearchService($http) {


    var lastExecutedQuery;

    var service = {search: search, loadMore: loadMore};
    return service;

    function search(category, query, tmdbid, title, tvdbid, season, episode, minsize, maxsize, minage, maxage, indexers) {
        console.log("Category: " + category);
        var uri;
        if (category.indexOf("Movies") > -1 || (category.indexOf("20") == 0)) {
            console.log("Search for movies");
            uri = new URI("internalapi/moviesearch");
            if (!_.isUndefined(tmdbid)) {
                console.log("moviesearch per tmdbid");
                uri.addQuery("tmdbid", tmdbid);
                uri.addQuery("title", title);
            } else {
                console.log("moviesearch per query");
                uri.addQuery("query", query);
            }

        } else if (category.indexOf("TV") > -1 || (category.indexOf("50") == 0)) {
            console.log("Search for shows");
            uri = new URI("internalapi/tvsearch");
            if (!_.isUndefined(tvdbid)) {
                uri.addQuery("tvdbid", tvdbid);
                uri.addQuery("title", title);
            } else {
                console.log("tvsearch per query");
                uri.addQuery("query", query);
            }

            if (!_.isUndefined(season)) {
                uri.addQuery("season", season);
            }
            if (!_.isUndefined(episode)) {
                uri.addQuery("episode", episode);
            }
        } else {
            console.log("Search for all");
            uri = new URI("internalapi/search");
            uri.addQuery("query", query);
        }

        if (_.isNumber(minsize)) {
            uri.addQuery("minsize", minsize);
        }
        if (_.isNumber(maxsize)) {
            uri.addQuery("maxsize", maxsize);
        }
        if (_.isNumber(minage)) {
            uri.addQuery("minage", minage);
        }
        if (_.isNumber(maxage)) {
            uri.addQuery("maxage", maxage);
        }
        if (!angular.isUndefined(indexers)) {
            uri.addQuery("indexers", decodeURIComponent(indexers));
        }
        

        uri.addQuery("category", category);
        uri = uri.toString();
        console.log("Calling " + uri);
        lastExecutedQuery = uri;
        return $http.get(uri).then(processData);

    }

    function loadMore(offset) {
        lastExecutedQuery.removeQuery("offset");
        lastExecutedQuery.addQuery("offset", offset);

        console.log("Calling " + lastExecutedQuery);
        return $http.get(lastExecutedQuery).then(processData);
    }

    function processData(response) {
        var results = response.data.results;
        var indexersearches = response.data.indexersearches;
        var total = response.data.total;
        var resultsCount = results.length;


        //Sum up response times of indexers from individual api accesses
        //TODO: Move this to search result controller because we need to update it every time we loaded more results
        _.each(indexersearches, function (ps) {
            if (ps.did_search) {
                ps.averageResponseTime = _.reduce(ps.api_accesses, function (memo, rp) {
                    return memo + rp.response_time;
                }, 0);
                ps.averageResponseTime = ps.averageResponseTime / ps.api_accesses.length;
            }
        });
        

        return {"results": results, "indexersearches": indexersearches, "total": total, "resultsCount": resultsCount}
    }
}