angular
    .module('nzbhydraApp')
    .directive('hydrabackup', hydrabackup);

function hydrabackup() {
    return {
        templateUrl: 'static/html/directives/backup.html',
        controller: controller
    };

    function controller($scope, BackupService, Upload, RequestsErrorHandler, growl, RestartService, $http) {
        $scope.refreshBackupList = function () {
            BackupService.getBackupsList().then(function (backups) {
                $scope.backups = backups;
            });
        };

        $scope.refreshBackupList();

        $scope.uploadActive = false;


        $scope.createAndDownloadBackupFile = function() {

                $http({method: 'GET', url: 'internalapi/getbackup', responseType: 'arraybuffer'}).success(function (data, status, headers, config) {
                    var a = document.createElement('a');
                    var blob = new Blob([data], {'type': "application/octet-stream"});
                    a.href = URL.createObjectURL(blob);
                    a.download = "nzbhydra-backup-" + moment().format("YYYY-MM-DD-HH-mm") + ".zip";

                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    $scope.refreshBackupList();
                }).error(function (data, status, headers, config) {
                    console.log("Error:" + status);
                });

        };

        $scope.uploadBackupFile = function (file, errFiles) {
            RequestsErrorHandler.specificallyHandled(function () {
                console.log("Hallo");
                $scope.file = file;
                $scope.errFile = errFiles && errFiles[0];
                if (file) {
                    $scope.uploadActive = true;
                    file.upload = Upload.upload({
                        url: 'internalapi/restorebackup',
                        data: {content: file}
                    });

                    file.upload.then(function (response) {
                        $scope.uploadActive = false;
                        file.result = response.data;
                        RestartService.restart("Restore successful.");

                    }, function (response) {
                        $scope.uploadActive = false;
                        growl.error(response.data)
                    }, function (evt) {
                        file.progress = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
                        file.loaded = Math.floor(evt.loaded / 1024);
                        file.total = Math.floor(evt.total / 1024);
                    });
                }
            });
        };

        $scope.restoreFromFile = function(filename) {
            BackupService.restoreFromFile(filename).then(function() {
                RestartService.restart("Restore successful.");
            },
            function(response) {
                growl.error(response.data);
            })
        }

    }
}

