angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope, $http) {



    $http.get("internalapi/getstats").success(function (response) {
        console.log(response);
        $scope.avgResponseTimes = response.avgResponseTimes;
        $scope.avgProviderSearchResultsShares = response.avgProviderSearchResultsShares;
        $scope.avgProviderAccessSuccesses = response.avgProviderAccessSuccesses;
        console.log($scope.avgResponseTimes);
    });


}
