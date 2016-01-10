angular
    .module('nzbhydraApp')
    .factory('UpdateService', UpdateService);

function UpdateService($http, growl, blockUI, $timeout, $window) {
    
    return {
        update: update
    };

    function update() {
        blockUI.start("Updating. Please stand by...");
        $http.get("internalapi/update").then(function (data) {
                if (data.data.success) {
                    //Hell yeah...
                    blockUI.start("Update complete. Restarting. Will reload page in 5 seconds...");
                    $timeout(function () {
                        blockUI.start("Update complete. Restarting. Will reload page in 4 seconds...");
                        $timeout(function () {
                            blockUI.start("Update complete. Restarting. Will reload page in 3 seconds...");
                            $timeout(function () {
                                blockUI.start("Update complete. Restarting. Will reload page in 2 seconds...");
                                $timeout(function () {
                                    blockUI.start("Update complete. Restarting. Will reload page in 1 second...");
                                    $timeout(function () {
                                        blockUI.start("Reloading page...");
                                        $window.location.reload();
                                    }, 1000);
                                }, 1000);
                            }, 1000);
                        }, 1000);
                    }, 1000);
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
