angular
    .module('nzbhydraApp')
    .factory('RestartService', RestartService);

function RestartService(blockUI, $timeout, $window, NzbHydraControlService) {

    return {
        restart: restart,
        countdownAndReload: countdownAndReload
    };

    function countdownAndReload(message, timer) {
        message = angular.isUndefined ? "" : " ";
        
        if (timer > 1) {
            blockUI.start(message + "Restarting. Will reload page in " + timer + " seconds...");
            $timeout(function () {
                countdownAndReload(message, timer -1)
            }, 1000);
        } else {
            $timeout(function () {
                blockUI.start("Reloading page...");
                $window.location.reload();
            }, 1000);
        }
        
    }
    
    

    function restart(message) {
        NzbHydraControlService.restart().then(countdownAndReload(message, 15),
            function () {
                growl.info("Unable to send restart command.");
            }
        )
    }
}
