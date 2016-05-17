angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope, stats, $state) {

    stats = stats.data;
    $scope.nzbDownloads = null;
    $scope.avgResponseTimes = stats.avgResponseTimes;
    $scope.avgIndexerSearchResultsShares = stats.avgIndexerSearchResultsShares;
    $scope.avgIndexerAccessSuccesses = stats.avgIndexerAccessSuccesses;
    $scope.indexerDownloadShares = stats.indexerDownloadShares;
    

    $scope.tabs = [
        {
            active: false,
            state: 'root.stats'
        },
        {
            active: false,
            state: 'root.stats.indexers'
        },
        {
            active: false,
            state: 'root.stats.searches'
        },
        {
            active: false,
            state: 'root.stats.downloads'
        }
    ];

    for (var i = 0; i < $scope.tabs.length; i++) {
        if ($state.is($scope.tabs[i].state)) {
            $scope.tabs[i].active = true;
        }
    }
    
    $scope.goToState = function (index) {
        $state.go($scope.tabs[index].state);
    }


}
