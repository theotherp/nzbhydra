angular
    .module('nzbhydraApp')
    .directive('addableNzb', addableNzb);

function addableNzb() {
    return {
        templateUrl: 'static/html/directives/addable-nzb.html',
        require: '^guid',
        scope: {
            guid: "="
        },
        controller: ['$scope', 'ConfigService', 'NzbDownloadService', controller]
    };

    function controller($scope, ConfigService, NzbDownloadService) {
        $scope.classname = "nzb";
        ConfigService.get().then(function (settings) {
            $scope.enabled = settings.downloader.downloader != "none";
        });
        
        $scope.add = function() {
            $scope.classname = "nzb-spinning";
            NzbDownloadService.download([$scope.guid]).then(function (response) {
                if (response.data.success) {
                    $scope.classname = "nzb-success";
                } else {
                    $scope.classname = "nzb-error";
                }
            }, function() {
                $scope.classname = "nzb-error";
            })
        };

    }
}

