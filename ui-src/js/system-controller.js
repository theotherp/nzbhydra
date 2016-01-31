angular
    .module('nzbhydraApp')
    .controller('SystemController', SystemController);

function SystemController($scope, $state, growl, RestartService, NzbHydraControlService) {


    $scope.shutdown = function () {
        NzbHydraControlService.shutdown().then(function () {
                growl.info("Shutdown initiated. Cya!");
            },
            function () {
                growl.info("Unable to send shutdown command.");
            })
    };

    $scope.restart = function () {
        RestartService.restart();
    };
    

    $scope.tabs = [
        {
            active: false,
            state: 'system'
        },
        {
            active: false,
            state: 'system.control'
        },
        {
            active: false,
            state: 'system.log'
        },
        {
            active: false,
            state: 'system.about'
        }
    ];


    for (var i = 0; i < $scope.tabs.length; i++) {
        if ($state.is($scope.tabs[i].state)) {
            $scope.tabs[i].active = true;
        }
    }


    $scope.goToState = function (index) {
        $state.go($scope.tabs[index].state);
    }
    
    
}
