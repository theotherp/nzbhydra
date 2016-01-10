angular
    .module('nzbhydraApp')
    .factory('RestartService', RestartService);

function RestartService(blockUI, $timeout, $window) {

    return {
        restart: restart
    };

    function restart(message) {
        message = angular.isUndefined ? "" : " ";
        
        blockUI.start(message  + "Restarting. Will reload page in 5 seconds...");
        $timeout(function () {
            blockUI.start(message  + "Restarting. Will reload page in 4 seconds...");
            $timeout(function () {
                blockUI.start(message  +  "Restarting. Will reload page in 3 seconds...");
                $timeout(function () {
                    blockUI.start(message  + "Restarting. Will reload page in 2 seconds...");
                    $timeout(function () {
                        blockUI.start(message + "Restarting. Will reload page in 1 second...");
                        $timeout(function () {
                            blockUI.start("Reloading page...");
                            $window.location.reload();
                        }, 1000);
                    }, 1000);
                }, 1000);
            }, 1000);
        }, 1000);
    }
}
