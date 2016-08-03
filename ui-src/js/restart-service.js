angular
    .module('nzbhydraApp')
    .factory('RestartService', RestartService);

function RestartService(blockUI, $timeout, $window, NzbHydraControlService) {

    return {
        restart: restart,
        countdownAndReload: countdownAndReload
    };

    function countdownAndReload(message) {
        message = angular.isUndefined ? "" : " ";
        //THere has to be a better way for this
        blockUI.start(message + "Restarting. Will reload page in 9 seconds...");
        $timeout(function () {
            blockUI.start(message + "Restarting. Will reload page in 8 seconds...");
            $timeout(function () {
                blockUI.start(message + "Restarting. Will reload page in 7 seconds...");
                $timeout(function () {
                    blockUI.start(message + "Restarting. Will reload page in 6 seconds...");
                    $timeout(function () {
                        blockUI.start(message + "Restarting. Will reload page in 5 seconds...");
                        $timeout(function () {
                            blockUI.start(message + "Restarting. Will reload page in 4 seconds...");
                            $timeout(function () {
                                blockUI.start(message + "Restarting. Will reload page in 3 seconds...");
                                $timeout(function () {
                                    blockUI.start(message + "Restarting. Will reload page in 2 seconds...");
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
                    }, 1000);
                }, 1000);
            }, 1000);
        }, 1000);
    }

    function restart(message) {
        NzbHydraControlService.restart().then(countdownAndReload(message),
            function () {
                growl.info("Unable to send restart command.");
            }
        )
    }
}
