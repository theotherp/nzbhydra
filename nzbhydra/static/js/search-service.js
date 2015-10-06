angular
    .module('nzbhydraApp')
    .service('SearchService', SearchService);

function SearchService($http) {
    this.search = function (category, query, imdbid, title, tvdbid, season, episode, minsize, maxsize, minage, maxage) {


        //Search start. TODO: Move to service
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
            uri.addQuery("query", query).addQuery("category", category);
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

        console.log("Calling " + uri);
        return $http.get(uri).then(processData);


        function processData(response) {
            var results = response.data.results;
            var providersearches = response.data.providersearches;

            //Sum up response times of providers from individual api accesses
            _.each(providersearches, function (ps) {
                ps.averageResponseTime = _.reduce(ps.api_accesses, function (memo, rp) {
                    return memo + rp.response_time;
                }, 0);
                ps.averageResponseTime = ps.averageResponseTime / ps.api_accesses.length;
            });

            //_.each(providersearches, function (ps) {
            //    showProviders[ps.provider] = true;
            //});

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

            return {"results": results, "providersearches": providersearches}
        }


    };
}

