angular
    .module('nzbhydraApp')
    .factory('UpdateService', UpdateService);

function UpdateService($http, growl, blockUI, RestartService) {
    
    return {
        update: update,
        showChanges: showChanges,
        getVersions: getVersions
    };
    
    var currentVersion;
    var repVersion;
    var updateAvailable;
    var changelog;
    
    function getVersions() {
        return $http.get("internalapi/get_versions").then(function (data) {
            
            currentVersion = data.data.currentVersion;
            repVersion = data.data.repVersion;
            updateAvailable = data.data.updateAvailable;
            changelog = data.data.changelog;
            return data;
        });
    }

    function showChanges() {

        var myInjector = angular.injector(["ng", "ui.bootstrap"]);
        var $uibModal = myInjector.get("$uibModal");
        var params = {
            size: "lg",
            templateUrl: "static/html/changelog.html",
            resolve: {
                changelog: function () {
                    return changelog;
                }
            },
            controller: function ($scope, $uibModalInstance, changelog) {
                $scope.changelog = changelog;
                $scope.ok = function () {
                    $uibModalInstance.dismiss();
                };
            }
        };

        var modalInstance = $uibModal.open(params);

        modalInstance.result.then();
    }
    
    

    function update() {
        blockUI.start("Updating. Please stand by...");
        $http.get("internalapi/update").then(function (data) {
                if (data.data.success) {
                    RestartService.restart("Update complete.");
                } else {
                    blockUI.reset();
                    growl.info("An error occurred while updating. Please check the logs.");
                }
            },
            function () {
                blockUI.reset();
                growl.info("An error occurred while updating. Please check the logs.");
            });
    }
}
