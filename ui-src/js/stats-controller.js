angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope, $http) {

    $scope.nzbDownloads = null;


    $http.get("internalapi/getstats").success(function (response) {
        $scope.avgResponseTimes = response.avgResponseTimes;
        $scope.avgProviderSearchResultsShares = response.avgProviderSearchResultsShares;
        $scope.avgProviderAccessSuccesses = response.avgProviderAccessSuccesses;
    });

    $scope.nzbDownloadsSelected = function () {
        if (!$scope.nzbDownloads) {
            $http.get("internalapi/getnzbdownloads").success(function (response) {
                $scope.nzbDownloads = response.nzbDownloads;
                console.log($scope.nzbDownloads);
            });
        }
    }


}
