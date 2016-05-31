var nzbhydraapp = angular.module('nzbhydraApp', ['angular-loading-bar', 'cgBusy', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters', 'ui.router', 'blockUI', 'mgcrea.ngStrap', 'angularUtils.directives.dirPagination', 'nvd3', 'formly', 'formlyBootstrap', 'frapontillo.bootstrap-switch', 'ui.select', 'ngSanitize', 'checklist-model', 'ngAria', 'ngMessages', 'ui.router.title', 'satellizer', 'LocalStorageModule']);

angular.module('nzbhydraApp').config(function ($stateProvider, $urlRouterProvider, $locationProvider, blockUIConfig, $urlMatcherFactoryProvider, $authProvider, localStorageServiceProvider, bootstrapped) {

    blockUIConfig.autoBlock = false;
    $urlMatcherFactoryProvider.strictMode(false);

    $urlRouterProvider.otherwise("/");


    $stateProvider
        .state('root', {
            url: '',
            abstract: true,
            resolve: {
                //loginRequired: loginRequired
            },
            views: {
                'header': {
                    templateUrl: 'static/html/states/header.html',
                    controller: 'HeaderController'
                },
                'footer': {
                    templateUrl: 'footer.html'
                }
            }
        })
        .state("root.config", {
            url: "/config",
            views: {
                'container@': {
                    templateUrl: "static/html/states/config.html",
                    controller: "ConfigController",
                    controllerAs: 'ctrl',
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        config: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.get();
                        }],
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "Config"
                        }
                    }
                }
            }
        })
        .state("root.config.auth", {
            url: "/auth",
            views: {
                'container@': {
                    templateUrl: "static/html/states/config.html",
                    controller: "ConfigController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        config: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.get();
                        }],
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "Config (Auth)"
                        }
                    }
                }
            }
        })
        .state("root.config.searching", {
            url: "/searching",
            views: {
                'container@': {
                    templateUrl: "static/html/states/config.html",
                    controller: "ConfigController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        config: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.get();
                        }],
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "Config (Searching)"
                        }
                    }
                }
            }
        })
        .state("root.config.downloader", {
            url: "/downloader",
            views: {
                'container@': {
                    templateUrl: "static/html/states/config.html",
                    controller: "ConfigController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        config: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.get();
                        }],
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "Config (Downloader)"
                        }
                    }
                }
            }
        })
        .state("root.config.indexers", {
            url: "/indexers",
            views: {
                'container@': {
                    templateUrl: "static/html/states/config.html",
                    controller: "ConfigController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        config: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.get();
                        }],
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "Config (Indexers)"
                        }
                    }
                }
            }
        })
        .state("root.config.system", {
            url: "/system",
            templateUrl: "static/html/states/config.html",
            views: {
                'container@': {
                    controller: "ConfigController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        config: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.get();
                        }],
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "System"
                        }
                    }
                }
            }
        })
        .state("root.config.log", {
            url: "/log",
            views: {
                'container@': {
                    templateUrl: "static/html/states/config.html",
                    controller: "ConfigController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        config: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.get();
                        }],
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "System (Log)"
                        }
                    }
                }
            }
        })
        .state("root.stats", {
            url: "/stats",
            abstract: true,
            views: {
                'container@': {
                    templateUrl: "static/html/states/stats.html",
                    controller: function($scope, $state) {
                        $scope.$state = $state;
                    },
                    resolve: {
                        loginRequired: loginRequiredStats,
                        $title: function () {
                            return "Stats"
                        }
                    }
                    
                }
            }            
        })
        .state("root.stats.main", {
            url: "/stats",
            views: {
                'stats@root.stats': {
                    templateUrl: "static/html/states/main-stats.html",
                    controller: "StatsController",
                    resolve: {
                        loginRequired: loginRequiredStats,
                        stats: ['loginRequired', 'StatsService', function (loginRequired, StatsService) {
                            return StatsService.get();
                        }],
                        $title: function () {
                            return "Stats"
                        }
                    }
                }
            }
        })
        .state("root.stats.indexers", {
            url: "/indexers",
            views: {
                'stats@root.stats': {
                    templateUrl: "static/html/states/indexer-statuses.html",
                    controller: IndexerStatusesController,
                    resolve: {
                        loginRequired: loginRequiredStats,
                        statuses: function($http) {
                            return $http.get("internalapi/getindexerstatuses").success(function (response) {
                                return response.indexerStatuses;
                            });
                        },
                        $title: function () {
                            return "Stats (Indexers)"
                        }
                    }
                }
            }
        })
        .state("root.stats.searches", {
            url: "/searches",
            views: {
                'stats@root.stats': {
                    templateUrl: "static/html/states/search-history.html",
                    controller: SearchHistoryController,
                    resolve: {
                        loginRequired: loginRequiredStats,
                        history: function(StatsService) {
                            return StatsService.getSearchHistory();
                        },
                        $title: function () {
                            return "Stats (Searches)"
                        }
                    }
                }
            }
        })
        .state("root.stats.downloads", {
            url: "/downloads",
            views: {
                'stats@root.stats': {
                    templateUrl: 'static/html/states/download-history.html',
                    controller: DownloadHistoryController,
                    resolve: {
                        loginRequired: loginRequiredStats,
                        downloads: function (StatsService) {
                            return StatsService.getDownloadHistory();
                        },
                        $title: function () {
                            return "Stats (Downloads)"
                        }
                    }
                }
            }
        })
        .state("root.system", {
            url: "/system",
            views: {
                'container@': {
                    templateUrl: "static/html/states/system.html",
                    controller: "SystemController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        askAdmin: ['loginRequired', '$http', function (loginRequired, $http) {
                            return $http.get("internalapi/askadmin");
                        }],
                        $title: function () {
                            return "System"
                        }
                    }
                }
            }
        })
        .state("root.system.updates", {
            url: "/updates",
            views: {
                'container@': {
                    templateUrl: "static/html/states/system.html",
                    controller: "SystemController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "System (Updates)"
                        }
                    }
                }
            }
        })
        .state("root.system.log", {
            url: "/log",
            views: {
                'container@': {
                    templateUrl: "static/html/states/system.html",
                    controller: "SystemController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "System (Log)"
                        }
                    }
                }
            }
        })
        .state("root.system.backup", {
            url: "/backup",
            views: {
                'container@': {
                    templateUrl: "static/html/states/system.html",
                    controller: "SystemController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "System (Backup)"
                        }
                    }
                }
            }
        })
        .state("root.system.about", {
            url: "/about",
            views: {
                'container@': {
                    templateUrl: "static/html/states/system.html",
                    controller: "SystemController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "System (About)"
                        }
                    }
                }
            }
        })
        .state("root.system.bugreport", {
            url: "/bugreport",
            views: {
                'container@': {
                    templateUrl: "static/html/states/system.html",
                    controller: "SystemController",
                    resolve: {
                        loginRequired: loginRequiredAdmin,
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "System (Bug report)"
                        }
                    }
                }
            }
        })
        .state("root.search", {
            url: "/?category&query&imdbid&tvdbid&title&season&episode&minsize&maxsize&minage&maxage&offsets&rid&mode&tmdbid&indexers",
            views: {
                'container@': {
                    templateUrl: "static/html/states/search.html",
                    controller: "SearchController",
                    resolve: {
                        loginRequired: loginRequiredSearch,
                        safeConfig: ['loginRequired', 'ConfigService', function (loginRequired, ConfigService) {
                            return ConfigService.getSafe();
                        }],
                        $title: function () {
                            return "Search"
                        }
                    }
                }
            }
        })
        .state("root.search.results", {
            views: {
                'results@root.search': {
                    templateUrl: "static/html/states/search-results.html",
                    controller: "SearchResultsController",
                    controllerAs: "srController",
                    options: {
                        inherit: true
                    },
                    resolve: {
                        loginRequired: loginRequiredSearch,
                        $title: function () {
                            return "Search results"
                        }
                    }
                }
            }
        })
        .state("root.login", {
            url: "/login",
            views: {
                'container@': {
                    templateUrl: "static/html/states/login.html",
                    controller: "LoginController",
                    resolve: {
                        loginRequired: function () {
                            return null;
                        },
                        $title: function () {
                            return "Login"
                        }
                    }
                }
            }
        })
    ;


    $locationProvider.html5Mode(true);

    $authProvider.httpInterceptor = function () {
        return true;
    };
    $authProvider.withCredentials = true;
    $authProvider.tokenRoot = null;
    $authProvider.baseUrl = bootstrapped.baseUrl;
    $authProvider.loginUrl = '/auth/login';
    $authProvider.signupUrl = '/auth/signup';
    $authProvider.unlinkUrl = '/unlink/';
    $authProvider.tokenName = 'token';
    $authProvider.tokenPrefix = 'satellizer';
    $authProvider.authHeader = 'TokenAuthorization';
    $authProvider.authToken = 'Bearer';
    $authProvider.storageType = 'localStorage';


    //Because I don't know for what state the login is required / asked I have a function for each 

    function loginRequiredSearch($q, $timeout, $auth, $state, bootstrapped) {
        
        var deferred = $q.defer();

        if (bootstrapped.authType != "form" || $auth.isAuthenticated() || bootstrapped.maySeeSearch) {
            deferred.resolve();
        } else {
            $timeout(function () {
                // This code runs after the authentication promise has been rejected.
                // Go to the log-in page
                $state.go("root.login");
            })
        }
        return deferred.promise;
    }

    function loginRequiredStats($q, $timeout, $auth, $state, bootstrapped) {
        var deferred = $q.defer();

        if (bootstrapped.authType != "form" || $auth.isAuthenticated() || bootstrapped.maySeeStats) {
            deferred.resolve();
        } else {
            $timeout(function () {
                // This code runs after the authentication promise has been rejected.
                // Go to the log-in page
                $state.go("root.login");
            })
        }
        return deferred.promise;
    }

    function loginRequiredAdmin($q, $timeout, $auth, $state, bootstrapped) {
        var deferred = $q.defer();

        if (bootstrapped.authType != "form" || $auth.isAuthenticated() || bootstrapped.maySeeAdmin) {
            deferred.resolve();
        } else {
            $timeout(function () {
                // This code runs after the authentication promise has been rejected.
                // Go to the log-in page
                $state.go("root.login");
            })
        }
        return deferred.promise;
    }

    localStorageServiceProvider
        .setPrefix('nzbhydra');
    localStorageServiceProvider
        .setNotify(true, false);
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
        uri.addQuery("searchResultId", resultItem.searchResultId);
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

nzbhydraapp.run(function ($rootScope) {
    $rootScope.$on('$stateChangeSuccess',
        function (event, toState, toParams, fromState, fromParams) {
            try {
                $rootScope.title = toState.views[Object.keys(toState.views)[0]].resolve.$title();
            } catch(e) {
                
            }
                
        });
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

nzbhydraapp.factory('sessionInjector', function ($injector) {
    var sessionInjector = {
        response: function (response) {
            if (response.headers("Hydra-MaySeeAdmin") != null) {
                $injector.get("HydraAuthService").setLoggedInByBasic(response.headers("Hydra-MaySeeStats") == "True", response.headers("Hydra-MaySeeAdmin") == "True")
            }
            
            return response;
        }
    };
    return sessionInjector;
});

nzbhydraapp.config(['$httpProvider', function ($httpProvider) {
    $httpProvider.interceptors.push('sessionInjector');
}]);

nzbhydraapp.directive('autoFocus', function ($timeout) {
    return {
        restrict: 'AC',
        link: function (_scope, _element) {
            $timeout(function () {
                _element[0].focus();
            }, 0);
        }
    };
});