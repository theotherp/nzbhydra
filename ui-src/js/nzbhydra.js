var nzbhydraapp = angular.module('nzbhydraApp', ['angular-loading-bar', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters', 'ui.router', 'blockUI', 'mgcrea.ngStrap', 'angularUtils.directives.dirPagination', 'nvd3', 'formly', 'formlyBootstrap', 'frapontillo.bootstrap-switch']);


angular.module('nzbhydraApp').config(function ($stateProvider, $urlRouterProvider, $locationProvider, blockUIConfig) {

    blockUIConfig.autoBlock = false;
    //$urlRouterProvider.otherwise("/search/");

    $stateProvider
        .state("home", {
            url: "/",
            templateUrl: "static/html/states/search.html",
            controller: "SearchController",
            params: {
                mode: "landing"
            }
        })
        .state("search", {
            url: "/search?category&query&imdbid&tvdbid&title&season&episode&minsize&maxsize&minage&maxage&offsets",
            templateUrl: "static/html/states/search.html",
            controller: "SearchController",
            params: {
                "category": "All",
                mode: "search"
            }
        })
        .state("search.results", {
            templateUrl: "static/html/states/search-results.html",
            controller: "SearchResultsController",
            controllerAs: "srController",
            options: {
                inherit: false
            },
            params: {
                results: [],
                indexersearches: [],
                total: 0,
                resultsCount: 0,
                mode: "results"
            }
        })
        .state("config", {
            url: "/config",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                configPromise: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                    //return "";
                }]
            }
        })
        .state("stats", {
            url: "/stats",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController"
        })
    ;

    $locationProvider.html5Mode(true);

});

nzbhydraapp.config(function (paginationTemplateProvider) {
    paginationTemplateProvider.setPath('static/html/dirPagination.tpl.html');
});

nzbhydraapp.config(['$httpProvider', function ($httpProvider) {
    var interceptor = ['$location', '$q', '$injector', function ($location, $q, $injector) {
        function success(response) {
            return response;
        }

        function error(response) {
            if (response.status === 401) {
                $injector.get('$state').transitionTo('public.login');

                return $q.reject(response);
            } else {
                return $q.reject(response);
            }
        }

        return function (promise) {
            return promise.then(success, error);
        }
    }];
    $httpProvider.interceptors.push(interceptor);
}]);


nzbhydraapp.config(['cfpLoadingBarProvider', function (cfpLoadingBarProvider) {
    cfpLoadingBarProvider.latencyThreshold = 100;
}]);

nzbhydraapp.config(['growlProvider', function (growlProvider) {
    growlProvider.globalTimeToLive(5000);
    growlProvider.globalPosition('bottom-right');
}]);


nzbhydraapp.directive('ngEnter', function () {
    return function (scope, element, attr) {
        element.bind("keydown keypress", function (event) {
            if (event.which === 13) {
                scope.$apply(function () {
                    scope.$evalAsync(attr.ngEnter);
                });

                event.preventDefault();
            }
        });
    };
});

nzbhydraapp.controller('ModalInstanceCtrl', function ($scope, $modalInstance, nfo) {

    $scope.nfo = nfo;


    $scope.ok = function () {
        $modalInstance.close($scope.selected.item);
    };

    $scope.cancel = function () {
        $modalInstance.dismiss();
    };
});


nzbhydraapp.filter('nzblink', function () {
    return function (resultItem) {
        var uri = new URI("internalapi/getnzb");
        uri.addQuery("guid", resultItem.guid);
        uri.addQuery("title", resultItem.title);
        uri.addQuery("provider", resultItem.provider);

        return uri.toString();
    }
});


nzbhydraapp.factory('focus', function ($rootScope, $timeout) {
    return function (name) {
        $timeout(function () {
            $rootScope.$broadcast('focusOn', name);
        });
    }
});


_.mixin({
    isNullOrEmpty: function (string) {
        return (_.isUndefined(string) || _.isNull(string) || string.trim().length === 0)
    }
});
