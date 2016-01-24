angular
    .module('nzbhydraApp')
    .controller('UpdateFooterController', UpdateFooterController);

function UpdateFooterController($scope, $http, UpdateService) {
    
    $http.get("internalapi/get_versions").then(function(data) {
        console.log(data);
        $scope.currentVersion = data.data.currentVersion;
        $scope.repVersion = data.data.repVersion;
        $scope.updateAvailable = data.data.updateAvailable;
    });

    $scope.update = function () {
        UpdateService.update();
    }

}
