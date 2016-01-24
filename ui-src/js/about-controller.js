angular
    .module('nzbhydraApp')
    .controller('AboutController', AboutController);

function AboutController($scope, versionsPromise, UpdateService) {

    $scope.currentVersion = versionsPromise.data.currentVersion;
    $scope.repVersion = versionsPromise.data.repVersion;
    $scope.updateAvailable = versionsPromise.data.updateAvailable;

    $scope.update = function () {
        UpdateService.update();
    }

}
