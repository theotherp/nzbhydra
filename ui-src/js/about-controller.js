angular
    .module('nzbhydraApp')
    .controller('AboutController', AboutController);

function AboutController($scope, $http, versionsPromise, growl, blockUI) {

    $scope.currentVersion = versionsPromise.data.currentVersion;
    $scope.repVersion = versionsPromise.data.repVersion;
    $scope.updateAvailable = versionsPromise.data.updateAvailable;

    $scope.update = function () {
        blockUI.start("Updating. Please stand by...");
        $http.get("internalapi/update").then(function (data) {
                if (data.data.success) {
                    growl.info("Update complete. Restarting. Give it a couple of seconds...");
                } else {
                    growl.info("An error occurred while updating. Please check the logs.");
                }
            },
            function () {
                growl.info("An error occurred while updating. Please check the logs.");
            }).finally(function () {
            blockUI.reset();
        })
    }

}
