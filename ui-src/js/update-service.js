angular
    .module('nzbhydraApp')
    .factory('UpdateService', UpdateService);

function UpdateService($http, growl, blockUI, RestartService) {
    
    return {
        update: update
    };

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
