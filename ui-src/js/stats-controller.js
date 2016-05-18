angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope, stats) {

    stats = stats.data;
    $scope.nzbDownloads = null;
    $scope.avgResponseTimes = stats.avgResponseTimes;
    $scope.avgIndexerSearchResultsShares = stats.avgIndexerSearchResultsShares;
    $scope.avgIndexerAccessSuccesses = stats.avgIndexerAccessSuccesses;
    $scope.indexerDownloadShares = stats.indexerDownloadShares;
    
}
