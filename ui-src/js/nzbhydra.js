var nzbhydraapp = angular.module('nzbhydraApp', ['angular-loading-bar', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters', 'ui.router', 'blockUI', 'mgcrea.ngStrap', 'angularUtils.directives.dirPagination', 'nvd3', 'formly', 'formlyBootstrap', 'frapontillo.bootstrap-switch', 'ui.select', 'ngSanitize', 'checklist-model']);


angular.module('nzbhydraApp').config(function ($stateProvider, $urlRouterProvider, $locationProvider, blockUIConfig, $urlMatcherFactoryProvider) {

    blockUIConfig.autoBlock = false;
    //$urlRouterProvider.otherwise("/search/");
    $urlMatcherFactoryProvider.strictMode(false);
    
    $stateProvider
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
                minsize: undefined,
                maxsize: undefined,
                minage: undefined,
                maxage: undefined
            }
        })
        .state("config", {
            url: "/config",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("config.searching", {
            url: "/searching",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("config.downloader", {
            url: "/downloader",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("config.indexers", {
            url: "/indexers",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("config.system", {
            url: "/system",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("config.log", {
            url: "/log",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("stats", {
            url: "/stats",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function(StatsService) {
                    return StatsService.get();
                }]
            }
        })
        .state("stats.indexers", {
            url: "/indexers",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function (StatsService) {
                    return StatsService.get();
                }]
            }
        })
        .state("stats.searches", {
            url: "/searches",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function (StatsService) {
                    return StatsService.get();
                }]
            }
        })
        .state("stats.downloads", {
            url: "/downloads",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function (StatsService) {
                    return StatsService.get();
                }]
            }
        })
        .state("about", {
            url: "/about",
            templateUrl: "static/html/states/about.html",
            controller: "AboutController"
        })
        .state("search", {
            url: "/:search?category&query&imdbid&tvdbid&title&season&episode&minsize&maxsize&minage&maxage&offsets&rid&mode&tmdbid&indexers",
            templateUrl: "static/html/states/search.html",
            controller: "SearchController"
        })
    ;

    $locationProvider.html5Mode(true);

});

nzbhydraapp.config(function (paginationTemplateProvider) {
    paginationTemplateProvider.setPath('static/html/dirPagination.tpl.html');
});


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

nzbhydraapp.filter('unsafe', function ($sce) {
    return $sce.trustAsHtml;
});


_.mixin({
    isNullOrEmpty: function (string) {
        return (_.isUndefined(string) || _.isNull(string) || (_.isString(string) && string.length === 0))
    }
});
