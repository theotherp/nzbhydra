angular
    .module('nzbhydraApp')
    .factory('SearchService', SearchService);

function SearchService($http) {
    

    var lastExecutedQuery;
    
    var service = {search: search, loadMore: loadMore};
    return service;

    function search(category, query, imdbid, title, tvdbid, season, episode, minsize, maxsize, minage, maxage, selectedProviders) {
        console.log("Category: " + category);
        var uri;
        if (category.indexOf("Movies") > -1) {
            console.log("Search for movies");
            uri = new URI("/internalapi/moviesearch");
            if (imdbid != "undefined") {
                console.log("moviesearch per imdbid");
                uri.addQuery("imdbid", imdbid);
                uri.addQuery("title", title);
            } else {
                console.log("moviesearch per query");
                uri.addQuery("query", query);
            }

        } else if (category.indexOf("TV") > -1) {
            console.log("Search for shows");
            uri = new URI("/internalapi/tvsearch");
            if (tvdbid) {
                uri.addQuery("tvdbid", tvdbid);
                uri.addQuery("title", title);
            }

            if (season != "") {
                uri.addQuery("season", season);
            }
            if (episode != "") {
                uri.addQuery("episode", episode);
            }
        } else {
            console.log("Search for all");
            uri = new URI("/internalapi/search");
            uri.addQuery("query", query);
        }

        if (!_.isNullOrEmpty(minsize)) {
            uri.addQuery("minsize", minsize);
        }
        if (!_.isNullOrEmpty(maxsize)) {
            uri.addQuery("maxsize", maxsize);
        }
        if (!_.isNullOrEmpty(minage)) {
            uri.addQuery("minage", minage);
        }
        if (!_.isNullOrEmpty(maxage)) {
            uri.addQuery("maxage", maxage);
        }
        if (!_.isNullOrEmpty(selectedProviders)) {
            uri.addQuery("providers", selectedProviders);
        }

        uri.addQuery("category", category);

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
            var providersearches = response.data.providersearches;
            var total = response.data.total;
        
            results = _.groupBy(results, function(element) {
                return element.hash; 
            });

            //Sum up response times of providers from individual api accesses
            //TODO: Move this to search result controller because we need to update it every time we loaded more results
            _.each(providersearches, function (ps) {
                ps.averageResponseTime = _.reduce(ps.api_accesses, function (memo, rp) {
                    return memo + rp.response_time;
                }, 0);
                ps.averageResponseTime = ps.averageResponseTime / ps.api_accesses.length;
            });


            //Filter the events once. Not all providers follow or allow all the restrictions, so we enfore them here
            filteredResults = _.filter(results, function (item) {
                var doShow = true;
                item = item[0]; //We take the first element of the bunch because their size and age should be nearly identical
                if (doShow && minsize) {
                    doShow &= item.size > minsize * 1024 * 1024;
                }
                if (doShow && maxsize) {
                    doShow &= item.size < maxsize * 1024 * 1024;
                }
                if (doShow && minage) {
                    doShow &= item.age_days > minage;
                }
                if (doShow && maxage) {
                    doShow &= item.age_days < maxage;
                }
                return doShow;
            });

            return {"results": results, "providersearches": providersearches, "total": total}
        }
}

_.mixin({
    isNullOrEmpty: function (string) {
        return (_.isUndefined(string) || _.isNull(string) || string.trim().length === 0)
    }
});