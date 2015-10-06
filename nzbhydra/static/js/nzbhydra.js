var nzbhydraapp = angular.module('nzbhydraApp', ['angular-loading-bar', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters', 'ui.bootstrap-slider', 'ui.router']);

nzbhydraapp.config(function ($stateProvider, $urlRouterProvider, $locationProvider) {

    //$urlRouterProvider.otherwise("/search/");

    $stateProvider
        .state("home", {
            url: "/",
            templateUrl: "/static/html/states/search.html",
            controller: "SearchController",
            params: {
                "mode": "landing"
            }
        })
        .state("search", {
            url: "/search?category&query",
            templateUrl: "/static/html/states/search.html",
            controller: "SearchController",
            params: {
                "category": "All"
            }
        }).
        state("search.results", {
            templateUrl: "/static/html/states/search-results.html",
            controller: "SearchResultsController",
            params: {
                results: [],
                providersearches: []
            }
        });
        
        $locationProvider.html5Mode(true);

});


/*
 ['$routeProvider', '$locationProvider', function ($routeProvider, $locationProvider) {
 $routeProvider.when('/search/:category/:query', {
 templateUrl: '/static/html/searchtemplate.html',
 controller: 'SearchController',
 title: 'NZB Hydra - Search',
 resolve: {
 ignored: function ($route) {
 $route.current.params.mode = "all";
 }
 }

 }).when('/searchmovies/:category/:imdbid/:title/', {
 templateUrl: '/static/html/searchtemplate.html',
 controller: 'SearchController',
 title: 'NZB Hydra - Movie search',
 resolve: {
 ignored: function ($route) {
 $route.current.params.mode = "movie";
 }
 }

 }).when('/searchtv/:category/:tvdbid/:title/:season?/:episode?', {
 templateUrl: '/static/html/searchtemplate.html',
 controller: 'SearchController',
 title: 'NZB Hydra - TV search',
 resolve: {
 ignored: function ($route) {
 $route.current.params.mode = "tv";
 }
 }

 }).when('/config', {
 templateUrl: '/js/views/news/news.html',
 controller: 'ConfigController',
 title: 'NZB Hydra - Configuration'

 }).otherwise({
 templateUrl: '/static/html/searchtemplate.html',
 controller: 'SearchController',
 title: 'NZB Hydra',
 resolve: {
 ignored: function ($route) {
 $route.current.params.mode = "landing";
 }
 }
 });

 $locationProvider.html5Mode(true);
 }]
 */

/*
nzbhydraapp.run(['$rootScope', '$route', function ($rootScope, $route) {
    $rootScope.$on('$routeChangeSuccess', function (newVal, oldVal) {
        if (oldVal !== newVal) {
            document.title = $route.current.title;
        }
    });
}]);
*/

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
}]);


//Generic error handling

var HEADER_NAME = 'MyApp-Handle-Errors-Generically';
var specificallyHandleInProgress = false;

nzbhydraapp.factory('RequestsErrorHandler', ['$q', 'growl', function ($q, growl) {
    return {
        // --- The user's API for claiming responsiblity for requests ---
        specificallyHandled: function (specificallyHandledBlock) {
            specificallyHandleInProgress = true;
            try {
                return specificallyHandledBlock();
            } finally {
                specificallyHandleInProgress = false;
            }
        },

        // --- Response interceptor for handling errors generically ---
        responseError: function (rejection) {
            var shouldHandle = (rejection && rejection.config && rejection.config.headers && rejection.config.headers[HEADER_NAME]);

            if (shouldHandle) {
                var message = "An error occured:<br>" + rejection.status + ": " + rejection.statusText;

                if (rejection.data) {
                    message += "<br><br>" + rejection.data;
                }
                //growl.error(message);
                alert(message);
            }

            return $q.reject(rejection);
        }
    };
}]);


nzbhydraapp.config(['$provide', '$httpProvider', function ($provide, $httpProvider) {
    $httpProvider.interceptors.push('RequestsErrorHandler');

    // --- Decorate $http to add a special header by default ---

    function addHeaderToConfig(config) {
        config = config || {};
        config.headers = config.headers || {};

        // Add the header unless user asked to handle errors himself
        if (!specificallyHandleInProgress) {
            config.headers[HEADER_NAME] = true;
        }

        return config;
    }

    // The rest here is mostly boilerplate needed to decorate $http safely
    $provide.decorator('$http', ['$delegate', function ($delegate) {
        function decorateRegularCall(method) {
            return function (url, config) {
                return $delegate[method](url, addHeaderToConfig(config));
            };
        }

        function decorateDataCall(method) {
            return function (url, data, config) {
                return $delegate[method](url, data, addHeaderToConfig(config));
            };
        }

        function copyNotOverriddenAttributes(newHttp) {
            for (var attr in $delegate) {
                if (!newHttp.hasOwnProperty(attr)) {
                    if (typeof($delegate[attr]) === 'function') {
                        newHttp[attr] = function () {
                            return $delegate.apply($delegate, arguments);
                        };
                    } else {
                        newHttp[attr] = $delegate[attr];
                    }
                }
            }
        }

        var newHttp = function (config) {
            return $delegate(addHeaderToConfig(config));
        };

        newHttp.get = decorateRegularCall('get');
        newHttp.delete = decorateRegularCall('delete');
        newHttp.head = decorateRegularCall('head');
        newHttp.jsonp = decorateRegularCall('jsonp');
        newHttp.post = decorateDataCall('post');
        newHttp.put = decorateDataCall('put');

        copyNotOverriddenAttributes(newHttp);

        return newHttp;
    }]);
}]);


function sortResults(input, predicate, reversed) {
    var sorted = _.sortBy(input, function (i) {
        return i[0][predicate];
    });
    if (reversed) {
        sorted.reverse();
    }
    return sorted;
}

nzbhydraapp.filter('sortResults', function () {
    return function (input, predicate, reversed) {
        var sorted = _.sortBy(input, function (i) {
            return i[0][predicate];
        });
        if (reversed) {
            sorted.reverse();
        }
        return sorted;
    }
});


nzbhydraapp.directive('ngEnter', function () {
    return function (scope, element, attrs) {
        element.bind("keydown keypress", function (event) {
            if (event.which === 13) {
                scope.$apply(function () {
                    scope.startSearch();
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
        var uri = new URI("/internalapi/getnzb");
        uri.addQuery("guid", resultItem.guid);
        uri.addQuery("title", resultItem.title);
        uri.addQuery("provider", resultItem.provider);

        return uri.toString();
    }
});


nzbhydraapp.filter('firstShownResult', function () {
    return function (resultswithduplicates, isShowFunction) {
        var firstShownResult = _.find(resultswithduplicates, function find(item) {
            return isShowFunction(item);
        });
        if (!_.isUndefined(firstShownResult)) {
            return [firstShownResult];
        } else {
            return [];
        }
    };
});

nzbhydraapp.filter('shownDuplicates', function () {
    return function (resultswithduplicates, isShowFunction) {
        var shownResults = _.filter(resultswithduplicates, function find(item) {
            return isShowFunction(item);
        });
        if (shownResults.length > 1) {
            return shownResults.slice(1);
        } else {
            return [];
        }
    };
});



_.mixin({
    isNullOrEmpty: function(string) {
      return (_.isUndefined(string) || _.isNull(string) || string.trim().length === 0)
    }
  });
