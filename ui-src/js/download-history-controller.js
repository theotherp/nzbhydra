angular
    .module('nzbhydraApp')
    .controller('DownloadHistoryController', DownloadHistoryController);


function DownloadHistoryController($scope, StatsService, downloads) {
    $scope.type = "All";
    $scope.limit = 100;
    $scope.pagination = {
        current: 1
    };

    $scope.nzbDownloads = downloads.data.nzbDownloads;
    $scope.totalDownloads = downloads.data.totalDownloads;

    $scope.changeType = function (type) {
        $scope.type = type;
        getDownloadsPage($scope.pagination.current);
    };


    $scope.pageChanged = function (newPage) {
        getDownloadsPage(newPage);
    };

    function getDownloadsPage(pageNumber) {
        StatsService.getDownloadHistory(pageNumber, $scope.limit, $scope.type).then(function(downloads) {
            $scope.nzbDownloads = downloads.data.nzbDownloads;
            $scope.totalDownloads = downloads.data.totalDownloads;
        });
        
    }


}
