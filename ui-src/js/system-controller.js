angular
    .module('nzbhydraApp')
    .controller('SystemController', SystemController);

function SystemController($scope, $state, $http, growl, RestartService, NzbHydraControlService) {


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
            state: 'root.system'
        },
        {
            active: false,
            state: 'root.system.updates'
        },
        {
            active: false,
            state: 'root.system.log'
        },
        {
            active: false,
            state: 'root.system.backup'
        },
        {
            active: false,
            state: 'root.system.bugreport'
        },
        {
            active: false,
            state: 'root.system.about'
        }
    ];


    for (var i = 0; i < $scope.tabs.length; i++) {
        if ($state.is($scope.tabs[i].state)) {
            $scope.tabs[i].active = true;
        }
    }


    $scope.goToState = function (index) {
        $state.go($scope.tabs[index].state);
    
    };

    $scope.downloadDebuggingInfos = function() {
        $http({method: 'GET', url: '/internalapi/getdebugginginfos', responseType: 'arraybuffer'}).success(function (data, status, headers, config) {
            var a = document.createElement('a');
            console.log(data);
            var blob = new Blob([data], {'type': "application/octet-stream"});
            a.href = URL.createObjectURL(blob);
            var filename = "nzbhydra-debuginfo-" + moment().format("YYYY-MM-DD-HH-mm") + ".zip";
            a.download = filename;
            a.click();
        }).error(function (data, status, headers, config) {
            // handle error
        });
    }
    
}
