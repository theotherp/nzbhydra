angular
    .module('nzbhydraApp')
    .controller('AboutController', AboutController);

function AboutController($scope, UpdateService) {

    UpdateService.getVersions().then(function (data) {
        $scope.currentVersion = data.data.currentVersion;
        $scope.repVersion = data.data.repVersion;
        $scope.updateAvailable = data.data.updateAvailable;
        $scope.changelog = data.data.changelog;
    });

    $scope.update = function () {
        UpdateService.update();
    };
    
    $scope.showChangelog = function() {
        UpdateService.showChanges($scope.changelog);
    }

}
