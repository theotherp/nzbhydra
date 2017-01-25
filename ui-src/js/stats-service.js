angular
    .module('nzbhydraApp')
    .factory('StatsService', StatsService);

function StatsService($http) {

    return {
        get: getStats,
        getDownloadHistory: getDownloadHistory
    };

    function getStats(after, before) {
        return $http.get("internalapi/getstats", {params: {after:after, before:before}}).success(function (response) {
            return response.data;
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
        return $http.get("internalapi/getnzbdownloads", {params: {page: pageNumber, limit: limit, type: type}}).success(function (response) {
            return {
                nzbDownloads: response.nzbDownloads,
                totalDownloads: response.totalDownloads
            };
            
        });
    }

}