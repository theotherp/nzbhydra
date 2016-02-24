angular
    .module('nzbhydraApp')
    .directive('hydrabackup', hydrabackup);

function hydrabackup() {
    return {
        templateUrl: 'static/html/directives/backup.html',
        controller: controller
    };

    function controller($scope, BackupService) {
        BackupService.getBackupsList().then(function(backups) {
            $scope.backups = backups;
        });
        
    }
}

