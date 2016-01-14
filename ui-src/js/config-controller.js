angular
    .module('nzbhydraApp')
    .factory('ConfigModel', function () {
        return {};
    });

angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);

function ConfigController($scope, ConfigService, config, CategoriesService, ConfigFields, ConfigModel, $state) {
    $scope.config = config;
    $scope.submit = submit;

    function submit(form) {
        ConfigService.set($scope.config);
        ConfigService.invalidateSafe();
        form.$setPristine();
        CategoriesService.invalidate();
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
        },
        {
            name: 'System',
            model: ConfigModel.system,
            fields: $scope.fields.system
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
        },
        {
            active: false,
            state: 'config.system'
        },
        {
            active: false,
            state: 'config.log'
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

    $scope.downloadLog = function() {
        if (angular.isUndefined($scope.log)) {
            console.log("Downloading log");
            var myInjector = angular.injector(["ng"]);
            var $http = myInjector.get("$http");
            var $sce = myInjector.get("$sce");
            $http.get("internalapi/getlogs").success(function (data) {
                $scope.log = $sce.trustAsHtml(data.log);
                $scope.$digest();
            });
        }
    };

    $scope.goToConfigState = function (index) {
        $state.go($scope.allTabs[index].state);
        if (index == 5) {
            $scope.downloadLog();
        }
    }
}


