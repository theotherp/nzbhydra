var nzbhydraapp = angular.module('nzbhydraApp', ['angular-loading-bar', 'cgBusy', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters', 'ui.router', 'blockUI', 'mgcrea.ngStrap', 'angularUtils.directives.dirPagination', 'nvd3', 'formly', 'formlyBootstrap', 'frapontillo.bootstrap-switch', 'ui.select', 'ngSanitize', 'checklist-model', 'ngAria', 'ngMessages', 'ui.router.title']);

angular.module('nzbhydraApp').config(function ($stateProvider, $urlRouterProvider, $locationProvider, blockUIConfig, $urlMatcherFactoryProvider) {

    blockUIConfig.autoBlock = false;
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
            }, resolve: {
                $title: function () {
                    return "Search results"
                }
            }
        })
        .state("config", {
            url: "/config",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            controllerAs: 'ctrl',
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function(){return "Config"}
            }
        })
        .state("config.auth", {
            url: "/auth",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "Config (Auth)"
                }
            }
        })
        .state("config.searching", {
            url: "/searching",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "Config (Searching)"
                }
            }
        })
        .state("config.downloader", {
            url: "/downloader",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "Config (Downloader)"
                }
            }
        })
        .state("config.indexers", {
            url: "/indexers",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "Config (Indexers)"
                }
            }
        })
        .state("config.system", {
            url: "/system",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "System"
                }
            }
        })
        .state("config.log", {
            url: "/log",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "System (Log)"
                }
            }
        })
        .state("stats", {
            url: "/stats",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function (StatsService) {
                    return StatsService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "Stats"
                }
            }
        })
        .state("stats.indexers", {
            url: "/indexers",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function (StatsService) {
                    return StatsService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "Stats (Indexers)"
                }
            }
        })
        .state("stats.searches", {
            url: "/searches",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function (StatsService) {
                    return StatsService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "Stats (Searches)"
                }
            }
        })
        .state("stats.downloads", {
            url: "/downloads",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function (StatsService) {
                    return StatsService.get();
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "Stats (Downloads)"
                }
            }
        })
        .state("system", {
            url: "/system",
            templateUrl: "static/html/states/system.html",
            controller: "SystemController",
            resolve: {
                foobar: ['$http', function ($http) {
                    return $http.get("internalapi/askforadmin")
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "System"
                }
            }
        })
        .state("system.updates", {
            url: "/updates",
            templateUrl: "static/html/states/system.html",
            controller: "SystemController",
            resolve: {
                foobar: ['$http', function ($http) {
                    return $http.get("internalapi/askforadmin")
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "System (Updates)"
                }
            }
        })
        .state("system.log", {
            url: "/log",
            templateUrl: "static/html/states/system.html",
            controller: "SystemController",
            resolve: {
                foobar: ['$http', function ($http) {
                    return $http.get("internalapi/askforadmin")
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "System (Log)"
                }
            }
        })
        .state("system.backup", {
            url: "/backup",
            templateUrl: "static/html/states/system.html",
            controller: "SystemController",
            resolve: {
                foobar: ['$http', function ($http) {
                    return $http.get("internalapi/askforadmin")
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "System (Backup)"
                }
            }
        })
        .state("system.about", {
            url: "/about",
            templateUrl: "static/html/states/system.html",
            controller: "SystemController",
            resolve: {
                foobar: ['$http', function ($http) {
                    return $http.get("internalapi/askforadmin")
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "System (About)"
                }
            }
        })
        .state("system.bugreport", {
            url: "/bugreport",
            templateUrl: "static/html/states/system.html",
            controller: "SystemController",
            resolve: {
                foobar: ['$http', function ($http) {
                    return $http.get("internalapi/askforadmin")
                }],
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "System (Bug report)"
                }
            }
        })
        .state("search", {
            url: "/:search?category&query&imdbid&tvdbid&title&season&episode&minsize&maxsize&minage&maxage&offsets&rid&mode&tmdbid&indexers",
            templateUrl: "static/html/states/search.html",
            controller: "SearchController",
            resolve: {
                safeConfig: ['ConfigService', function (ConfigService) {
                    return ConfigService.getSafe();
                }],
                $title: function () {
                    return "Search"
                }
            }
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

nzbhydraapp.config(function ($provide) {
    $provide.decorator("$exceptionHandler", ['$delegate', '$injector', function ($delegate, $injector) {
        return function (exception, cause) {
            $delegate(exception, cause);
            try {
                console.log(exception);
                var stack = exception.stack.split('\n').map(function (line) {
                    return line.trim();
                });
                stack = stack.join("\n");
                $injector.get("$http").put("internalapi/logerror", {error: stack, cause: angular.isDefined(cause) ? cause.toString() : "No known cause"});
                

            } catch (e) {
                console.error("Unable to log JS exception to server", e);
            }
        };
    }]);
});

_.mixin({
    isNullOrEmpty: function (string) {
        return (_.isUndefined(string) || _.isNull(string) || (_.isString(string) && string.length === 0))
    }
});
