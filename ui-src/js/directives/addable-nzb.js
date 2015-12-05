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
        controller: controller
    };

    function controller($scope, ConfigService, NzbDownloadService, growl) {
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
                    growl.error("Unable to add NZB. Make sure the downloader is running and properly configured.");
                }
            }, function() {
                $scope.classname = "nzb-error";
                growl.error("An unexpected error occurred while trying to contact NZB Hydra or add the NZB.");
            })
        };

    }
}

