angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope, $http) {

    $scope.nzbDownloads = null;


    $http.get("internalapi/getstats").success(function (response) {
        $scope.avgResponseTimes = response.avgResponseTimes;
        $scope.avgIndexerSearchResultsShares = response.avgIndexerSearchResultsShares;
        $scope.avgIndexerAccessSuccesses = response.avgIndexerAccessSuccesses;
    });



}
