angular
    .module('nzbhydraApp')
    .directive('downloadHistory', downloadHistory);

function downloadHistory() {
    return {
        templateUrl: 'static/html/directives/download-history.html',
        controller: ['$scope', '$http', controller],
        scope: {}
    };

    function controller($scope, $http) {
        $scope.limit = 100;
        $scope.pagination = {
            current: 1
        };

        getDownloadsPage(1);

        $scope.pageChanged = function (newPage) {
            getDownloadsPage(newPage);
        };
        
        function getDownloadsPage(pageNumber) {
            $http.get("internalapi/getnzbdownloads", {params:{page: pageNumber, limit: $scope.limit}}).success(function (response) {
                $scope.nzbDownloads = response.nzbDownloads;
                $scope.totalDownloads = response.totalDownloads;
                console.log($scope.nzbDownloads);
            });
        }


    }
}