var nzbhydraapp = angular.module('nzbhydraApp', ['ngRoute', 'angular-loading-bar', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters', 'ui.bootstrap-slider']);

nzbhydraapp.config(['$routeProvider', '$locationProvider', function ($routeProvider, $locationProvider) {
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
}]);


nzbhydraapp.run(['$rootScope', '$route', function ($rootScope, $route) {
    $rootScope.$on('$routeChangeSuccess', function (newVal, oldVal) {
        if (oldVal !== newVal) {
            document.title = $route.current.title;
        }
    });
}]);

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
                growl.error(message);
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

nzbhydraapp.controller('SearchController', ['$scope', '$http', '$routeParams', '$location', '$modal', '$sce', function ($scope, $http, $routeParams, $location, $modal, $sce) {

    $scope.category = (typeof $routeParams.category === "undefined") ? "All" : $routeParams.category;

    $scope.searchTerm = (typeof $routeParams.query === "undefined") ? "" : $routeParams.query;

    $scope.imdbid = (typeof $routeParams.imdbid === "undefined") ? "" : $routeParams.imdbid;
    $scope.tvdbid = (typeof $routeParams.tvdbid === "undefined") ? "" : $routeParams.tvdbid;
    $scope.title = (typeof $routeParams.title === "undefined") ? "" : $routeParams.title;
    $scope.season = (typeof $routeParams.season === "undefined") ? "" : $routeParams.season;
    $scope.episode = (typeof $routeParams.episode === "undefined") ? "" : $routeParams.episode;

    $scope.minsize = (typeof $routeParams.minsize === "undefined") ? "" : $routeParams.minsize;
    $scope.maxsize = (typeof $routeParams.maxsize === "undefined") ? "" : $routeParams.maxsize;
    $scope.minage = (typeof $routeParams.minage === "undefined") ? "" : $routeParams.minage;
    $scope.maxage = (typeof $routeParams.maxage === "undefined") ? "" : $routeParams.maxage;

    $scope.showProviders = {};


    if ($scope.title != "" && $scope.query == "") {
        $scope.searchTerm = $scope.title;
    }

//Only start search if we're in search mode, landing mode just shows the search box
    console.log($routeParams.mode);
    if ($routeParams.mode != "landing") {

        //Search start. TODO: Move to service

        var uri = new URI("/internalapi");
        if ($scope.category.indexOf("Movies") > -1) {
            uri.addQuery("t", "moviesearch");
            if ($scope.imdbid != "undefined") {
                console.log("moviesearch per imdbid");
                uri.addQuery("imdbid", $scope.imdbid);
                uri.addQuery("title", $scope.title);
            } else {
                console.log("moviesearch per query");
                uri.addQuery("query", $scope.searchTerm);
            }

        } else if ($scope.category.indexOf("TV") > -1) {
            uri.addQuery("t", "tvsearch");
            if ($scope.tvdbid) {
                uri.addQuery("tvdbid", $scope.tvdbid);
                uri.addQuery("title", $scope.title);
            }

            if ($scope.season != "") {
                uri.addQuery("season", $scope.season);
            }
            if ($scope.episode != "") {
                uri.addQuery("episode", $scope.episode);
            }
        } else {
            uri.addQuery("t", "search").addQuery("query", $scope.searchTerm).addQuery("category", $scope.category);
        }

        if ($scope.minsize != "") {
            uri.addQuery("minsize", $scope.minsize);
        }
        if ($scope.maxsize != "") {
            uri.addQuery("maxsize", $scope.maxsize);
        }
        if ($scope.minage != "") {
            uri.addQuery("minage", $scope.minage);
        }
        if ($scope.maxage != "") {
            uri.addQuery("maxage", $scope.maxage);
        }


        $http.get(uri).then(function (data) {

            $scope.results = data.data.results;
            $scope.providersearches = data.data.providersearches;

            //Sum up response times of providers from individual api accesses
            _.each($scope.providersearches, function (ps) {
                ps.averageResponseTime = _.reduce(ps.api_accesses, function (memo, rp) {
                    return memo + rp.response_time;
                }, 0);
                ps.averageResponseTime = ps.averageResponseTime / ps.api_accesses.length;
            });

            _.each($scope.providersearches, function (ps) {
                $scope.showProviders[ps.provider] = true;
            });

            //Filter the events once. Not all providers follow or allow all the restrictions, so we enfore them here
            $scope.filteredResults = _.filter($scope.results, function (item) {
                var doShow = true;
                item = item[0]; //We take the first element of the bunch because their size and age should be nearly identical
                if (doShow && $scope.minsize) {
                    doShow &= item.size > $scope.minsize * 1024 * 1024;
                }
                if (doShow && $scope.maxsize) {
                    doShow &= item.size < $scope.maxsize * 1024 * 1024;
                }
                if (doShow && $scope.minage) {
                    doShow &= item.age_days > $scope.minage;
                }
                if (doShow && $scope.maxage) {
                    doShow &= item.age_days < $scope.maxage;
                }
                return doShow;
            });

        });


        //Search end
    }

    $scope.typeAheadWait = 300;
    $scope.selectedItem = "";
    $scope.autocompleteLoading = false;


    $scope.isAskById = false; //If true a check box will be shown asking the user if he wants to search by ID 
    $scope.isById = {value: true}; //If true the user wants to search by id so we enable autosearch. Was unable to achieve this using a simple boolean


    $scope.autocompleteClass = "autocompletePosterMovies";

    $scope.toggle = function (searchCategory) {
        $scope.category = searchCategory;

        //Show checkbox to ask if the user wants to search by ID (using autocomplete)
        $scope.isAskById = ($scope.category.indexOf("TV") > -1 || $scope.category.indexOf("Movies") > -1 );
    };


// Any function returning a promise object can be used to load values asynchronously
    $scope.getAutocomplete = function (val) {
        $scope.autocompleteLoading = true;
        //Expected model returned from API:
        //label: What to show in the results
        //title: Will be used for file search
        //value: Will be used as extraInfo (ttid oder tvdb id)
        //poster: url of poster to show

        //Don't use autocomplete if checkbox is disabled
        if (!$scope.isById.value) {
            return {};
        }

        if ($scope.category.indexOf("Movies") > -1) {
            return $http.get('internalapi?t=autocompletemovie', {
                params: {
                    input: val
                }
            }).then(function (response) {
                $scope.autocompleteLoading = false;
                return response.data.results;
            });
        } else if ($scope.category.indexOf("TV") > -1) {

            return $http.get('internalapi?t=autocompleteseries', {
                params: {
                    input: val
                }
            }).then(function (response) {
                $scope.autocompleteLoading = false;
                return response.data.results;
            });
        } else {
            return {};
        }
    };

    $scope.startSearch = function () {
        var uri;
        if ($scope.imdbid != "") {
            uri = new URI("/searchmovies");
            uri.segment($scope.category);
            uri.segment($scope.imdbid);
            uri.segment($scope.title);
        } else if ($scope.tvdbid != "") {
            uri = new URI("/searchtv");
            uri.segment($scope.category);
            uri.segment($scope.tvdbid);
            uri.segment($scope.title);
            if ($scope.season != "") {
                uri.segment($scope.season);
            }
            if ($scope.episode != "") {
                uri.segment($scope.episode);
            }
        } else {
            uri = new URI("/search");
            uri.segment($scope.category);
            uri.segment($scope.searchTerm);
        }

        if ($scope.minsize != "") {
            uri.addQuery("minsize", $scope.minsize);
        }
        if ($scope.maxsize != "") {
            uri.addQuery("maxsize", $scope.maxsize);
        }
        if ($scope.minage != "") {
            uri.addQuery("minage", $scope.minage);
        }
        if ($scope.maxage != "") {
            uri.addQuery("maxage", $scope.maxage);
        }

        $location.url(uri)

    };


    $scope.selectAutocompleteItem = function ($item) {
        $scope.selectedItem = $item;
        $scope.title = $item.label;
        if ($scope.category.indexOf("Movies") > -1) {
            $scope.imdbid = $item.value;
        } else if ($scope.category.indexOf("TV") > -1) {
            $scope.tvdbid = $item.value;
        }
        $scope.startSearch();
    };


    $scope.autocompleteActive = function () {
        return ($scope.category.indexOf("TV") > -1) || ($scope.category.indexOf("Movies") > -1)
    };

    $scope.seriesSelected = function () {
        return ($scope.category.indexOf("TV") > -1);
    };


    $scope.results = [];
    $scope.isShowDuplicates = true;
    $scope.predicate = 'age_days';
    $scope.reversed = false;


    $scope.setSorting = function (predicate, reversedDefault) {
        if (predicate == $scope.predicate) {
            $scope.reversed = !$scope.reversed;
        } else {
            $scope.reversed = reversedDefault;
        }
        $scope.predicate = predicate;
    };


//True if the provider is selected in the table filter, false else 
    $scope.isShow = function (item) {
        return $scope.showProviders[item.provider];
    };


    $scope.showNfo = function (resultItem) {
        var uri = new URI("/internalapi");
        uri.addQuery("t", "getnfo");
        uri.addQuery("provider", resultItem.provider);
        uri.addQuery("guid", resultItem.guid);
        return $http.get(uri).then(function (response) {
            if (response.data.has_nfo) {
                $scope.open("lg", response.data.nfo)
            } else {
                //todo: show error or info that no nfo is available
            }
        });
    };


    $scope.nzbgetclass = {};
    $scope.nzbgetEnabled = true;

    $scope.addNzb = function (resultItem) {
        var uri = new URI("/internalapi");
        uri.addQuery("t", "addnzb");
        uri.addQuery("title", resultItem.title);
        uri.addQuery("guid", resultItem.guid);
        uri.addQuery("provider", resultItem.provider);
        $scope.nzbgetclass[resultItem.guid] = "nzb-spinning";
        return $http.get(uri).success(function () {
            $scope.nzbgetclass[resultItem.guid] = "nzbget-success";
        }).error(function () {
            $scope.nzbgetclass[resultItem.guid] = "nzbget-error";
        })
            ;
    };

    $scope.nzbclass = function (resultItem) {
        if ($scope.nzbgetclass[resultItem.guid]) {
            return $scope.nzbgetclass[resultItem.guid];
        } else {
            return "nzbget";
        }
    }


    $scope.open = function (size, nfo) {

        var modalInstance = $modal.open({
            animation: $scope.animationsEnabled,
            template: '<pre><span ng-bind-html="nfo"></span></pre>',
            controller: 'ModalInstanceCtrl',
            size: size,
            resolve: {
                nfo: function () {
                    return $sce.trustAsHtml(nfo);
                }
            }
        });
    };

}])
;

nzbhydraapp.filter('nzblink', function () {
    return function (resultItem) {
        var uri = new URI("/internalapi");
        uri.addQuery("t", "getnzb");
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