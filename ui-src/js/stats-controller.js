angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope, $http, stats) {

    stats = stats.data;
    $scope.nzbDownloads = null;
    console.log(stats);
    $scope.avgResponseTimes = stats.avgResponseTimes;
    $scope.avgIndexerSearchResultsShares = stats.avgIndexerSearchResultsShares;
    $scope.avgIndexerAccessSuccesses = stats.avgIndexerAccessSuccesses;


}
