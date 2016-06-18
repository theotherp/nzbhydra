angular
    .module('nzbhydraApp')
    .factory('StatsService', StatsService);

function StatsService($http) {

    return {
        get: getStats,
        getSearchHistory: getSearchHistory,
        getDownloadHistory: getDownloadHistory
    };

    function getStats() {
        return $http.get("internalapi/getstats").success(function (response) {
            return response.data;
        });
    }

    function getSearchHistory(pageNumber, limit, type) {
        if (angular.isUndefined(pageNumber)) {
            pageNumber = 1;
        }
        if (angular.isUndefined(limit)) {
            limit = 100;
        }
        if (angular.isUndefined(type)) {
            type = "All";
        }
        return $http.get("internalapi/getsearchrequests", {params: {page: pageNumber, limit: limit, type: type}}).success(function (response) {
            return {
                searchRequests: response.searchRequests,
                totalRequests: response.totalRequests
            }
        });
    }
    
    function getDownloadHistory(pageNumber, limit, type) {
        if (angular.isUndefined(pageNumber)) {
            pageNumber = 1;
        }
        if (angular.isUndefined(limit)) {
            limit = 100;
        }
        if (angular.isUndefined(type)) {
            type = "All";
        }
        console.log(1);
        return $http.get("internalapi/getnzbdownloads", {params: {page: pageNumber, limit: limit, type: type}}).success(function (response) {
            console.log(2);
            return {
                nzbDownloads: response.nzbDownloads,
                totalDownloads: response.totalDownloads
            };
            
        });
    }

}