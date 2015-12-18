angular
    .module('nzbhydraApp')
    .factory('StatsService', StatsService);

function StatsService($http) {
    
    return {
        get: getStats
    };

    function getStats() {
            return $http.get("internalapi/getstats").success(function (response) {
               return response.data;
            });

    }

}