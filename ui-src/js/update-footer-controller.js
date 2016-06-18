angular
    .module('nzbhydraApp')
    .controller('UpdateFooterController', UpdateFooterController);

function UpdateFooterController($scope, UpdateService, HydraAuthService, bootstrapped) {

    $scope.updateAvailable = false;
    $scope.checked = false;

    $scope.mayUpdate = HydraAuthService.getUserRights().maySeeAdmin || bootstrapped.maySeeAdmin;

    $scope.$on("user:loggedIn", function (event, data) {
        if (data.maySeeAdmin && !$scope.checked) {
            retrieveUpdateInfos();
        }
    });


    if ($scope.mayUpdate) {
        retrieveUpdateInfos();
    }

    function retrieveUpdateInfos() {
        $scope.checked = true;
        UpdateService.getVersions().then(function (data) {
            $scope.currentVersion = data.data.currentVersion;
            $scope.repVersion = data.data.repVersion;
            $scope.updateAvailable = data.data.updateAvailable;
            $scope.changelog = data.data.changelog;
        });
    }


    $scope.update = function () {
        UpdateService.update();
    };

    $scope.showChangelog = function () {
        UpdateService.showChanges($scope.changelog);
    }

}
