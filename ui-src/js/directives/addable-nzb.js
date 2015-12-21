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
        $scope.classname = "";
        
        ConfigService.getSafe().then(function (settings) {
            $scope.downloader = settings.downloader.downloader;
            if ($scope.downloader != "none") {
                $scope.enabled = true;
                $scope.classname = $scope.downloader == "sabnzbd" ? "sabnzbd" : "nzbget";
            } else {
                $scope.enabled = false;
            }
            
        });
        
        $scope.add = function() {
            $scope.classname = "nzb-spinning";
            NzbDownloadService.download([$scope.guid]).then(function (response) {
                if (response.data.success) {
                    $scope.classname = $scope.downloader == "sabnzbd" ? "sabnzbd-success" : "nzbget-success";
                } else {
                    $scope.classname = $scope.downloader == "sabnzbd" ? "sabnzbd-error" : "nzbget-error";
                    growl.error("Unable to add NZB. Make sure the downloader is running and properly configured.");
                }
            }, function() {
                $scope.classname = $scope.downloader == "sabnzbd" ? "sabnzbd-error" : "nzbget-error";
                growl.error("An unexpected error occurred while trying to contact NZB Hydra or add the NZB.");
            })
        };

    }
}

