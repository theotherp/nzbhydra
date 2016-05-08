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
            }, true);
        }
    });


angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);

function ConfigController($scope, ConfigService, config, CategoriesService, ConfigFields, ConfigModel, ModalService, RestartService, $state, growl) {
    $scope.config = config;
    $scope.submit = submit;

    $scope.restartRequired = false;
    $scope.ignoreSaveNeeded = false;

    ConfigFields.setRestartWatcher(function () {
        $scope.restartRequired = true;
    });
    

    function submit() {
        if ($scope.form.$valid) {
            
            ConfigService.set($scope.config);
            ConfigService.invalidateSafe();
            $scope.form.$setPristine();
            CategoriesService.invalidate();
            if ($scope.restartRequired) {
                ModalService.open("Restart required", "The changes you have made may require a restart to be effective.<br>Do you want to restart now?", {
                    yes: {
                        onYes: function () {
                            RestartService.restart();
                        }
                    },
                    no: {
                        onNo: function () {
                            $scope.restartRequired = false;
                        }
                    }
                });
            }
        } else {
            growl.error("Config invalid. Please check your settings.");
            
            //Ridiculously hacky way to make the error messages appear
            try {
                if (angular.isDefined(form.$error.required)) {
                    _.each(form.$error.required, function (item) {
                        if (angular.isDefined(item.$error.required)) {
                            _.each(item.$error.required, function (item2) {
                                item2.$setTouched();
                            });
                        } 
                    });
                }
                angular.forEach($scope.form.$error.required, function (field) {
                    field.$setTouched();
                });
            } catch(err) {
                //
            }
            
        }
    }

    ConfigModel = config;

    $scope.fields = ConfigFields.getFields($scope.config);

    $scope.formTabs = [
        {
            name: 'Main',
            model: ConfigModel.main,
            fields: $scope.fields.main
        },
        {
            name: 'Authorization',
            model: ConfigModel.auth,
            fields: $scope.fields.auth
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
            state: 'config.auth'
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

    $scope.isSavingNeeded = function () {
        return $scope.form.$dirty && $scope.form.$valid && !$scope.ignoreSaveNeeded;
    };

    $scope.goToConfigState = function (index) {
        $state.go($scope.allTabs[index].state);
        if (index == 5) {
            $scope.downloadLog();
        }
    };

    $scope.$on('$stateChangeStart',
        function (event, toState, toParams, fromState, fromParams) {
            if ($scope.isSavingNeeded()) {
                event.preventDefault();
                ModalService.open("Unsaved changed", "Do you want to save before leaving?", {
                    yes: {
                        onYes: function() {
                            $scope.submit();
                            $state.go(toState);
                        },
                        text: "Yes"
                    },
                    no: {
                        onNo: function () {
                            $scope.ignoreSaveNeeded = true;
                            $scope.ctrl.options.resetModel();
                            $state.go(toState);
                        },
                        text: "No"
                    },
                    cancel: {
                        onCancel: function () {
                            event.preventDefault();
                        },
                        text: "Cancel"
                    }
                });
            }            
        })
}


