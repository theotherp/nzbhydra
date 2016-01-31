angular
    .module('nzbhydraApp')
    .factory('ConfigModel', function () {
        return {};
    });

angular
    .module('nzbhydraApp')
    .factory('ConfigWatcher', function () {
        var $scope;
        
        return {
            watch: watch
        };
        
        function watch(scope) {
            $scope = scope;
            $scope.$watchGroup(["config.main.host"], function () {
                console.log("Restart needed");
            }, true);
        }
    });


angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);

function ConfigController($scope, ConfigService, config, CategoriesService, ConfigFields, ConfigModel, ModalService, RestartService, $state) {
    $scope.config = config;
    $scope.submit = submit;
    
    $scope.restartRequired = false;
    
    ConfigFields.setRestartWatcher(function() {
        $scope.restartRequired = true;
    });

    function submit(form) {
        ConfigService.set($scope.config);
        ConfigService.invalidateSafe();
        form.$setPristine();
        CategoriesService.invalidate();
        if ($scope.restartRequired) {
            ModalService.open("Restart required", "The changes you have made may require a restart to be effective.<br>Do you want to restart now?", function () {
                RestartService.restart();
            }, function() {
                $scope.restartRequired = false;
            });
        }
    }

    ConfigModel = config;

    $scope.fields = ConfigFields.getFields();

    $scope.formTabs = [
        {
            name: 'Main',
            model: ConfigModel.main,
            fields: $scope.fields.main
        },
        {
            name: 'Searching',
            model: ConfigModel.searching,
            fields: $scope.fields.searching
        },
        {
            name: 'Downloader',
            model: ConfigModel.downloader,
            fields: $scope.fields.downloader
        },
        {
            name: 'Indexers',
            model: ConfigModel.indexers,
            fields: $scope.fields.indexers
        }
    ];

    $scope.allTabs = [
        {
            active: false,
            state: 'config'
        },
        {
            active: false,
            state: 'config.searching'
        },
        {
            active: false,
            state: 'config.downloader'
        },
        {
            active: false,
            state: 'config.indexers'
        }
    ];


    for (var i = 0; i < $scope.allTabs.length; i++) {
        if ($state.is($scope.allTabs[i].state)) {
            $scope.allTabs[i].active = true;
        }
    }

    $scope.isSavingNeeded = function (form) {
        return form.$dirty && !form.$submitted;
    };

    $scope.goToConfigState = function (index) {
        $state.go($scope.allTabs[index].state);
        if (index == 5) {
            $scope.downloadLog();
        }
    };
    
}


