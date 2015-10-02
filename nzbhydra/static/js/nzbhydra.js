var nzbhydraapp = angular.module('nzbhydraApp', ['ngRoute', 'angular-loading-bar', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters']);


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


nzbhydraapp.controller('ModalInstanceCtrl', ['$scope', '$modalInstance', 'content', 'title', function ($scope, $modalInstance, content, title) {

    $scope.content = content;
    $scope.title = title;

    $scope.ok = function () {
        $modalInstance.close();
    };

    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
    };
}]);


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


nzbhydraapp.controller('SearchController', ['$scope', '$http', function ($scope, $http) {

    $scope.category = "All";
    $scope.searchTerm = "";
    $scope.extraInfo = "";
    $scope.searchSeason = "";
    $scope.searchEpisode = "";
    $scope.typeAheadWait = 300;
    $scope.selectedItem = "";
    $scope.selectedQuality = "All qualities";
    $scope.autocompleteLoading = false;

    
    $scope.isAskById = false; //If true a check box will be shown asking the user if he wants to search by ID 
    $scope.isById = {value: false}; //If true the user wants to search by id so we enable autosearch. Was unable to achieve this using a simple boolean
    

    $scope.autocompleteClass = "autocompletePosterMovies";

    $scope.toggle = function (searchCategory) {
        $scope.category = searchCategory;
        $scope.selectedItem = "";
        $scope.searchTerm = "";

        //Show checkbox to ask if the user wants to search by ID (using autocomplete)
        $scope.isAskById = ($scope.category.indexOf("TV") > -1 || $scope.category.indexOf("Movies") > -1 );


        //Wait longer for series because it takes so long to query and is more expensive
        if ($scope.category.indexOf("TV") > -1) {
            console.log("Setting type ahead wait to 600ms");
            $scope.typeAheadWait = 600;
        } else {
            $scope.typeAheadWait = 300;
        }
    };


    // Any function returning a promise object can be used to load values asynchronously
    $scope.getAutocomplete = function (val) {
        $scope.autocompleteLoading = true;
        $scope.seriesSelected = false;
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
            console.log("ha");
            return {};
        }
    };


    $scope.selectAutocompleteItem = function ($item) {
        $scope.selectedItem = $item;


        $scope.startSearch($item);

    };
    
    

    $scope.startSearch = function () {
        var uri = new URI("/internalapi");
        if ($scope.category.indexOf("Movies") > -1) {
                uri.addQuery("t", "moviesearch");
            if ($scope.selectedItem.value != undefined) {
                console.log("moviesearch per imdbid");
                uri.addQuery("imdbid", $scope.selectedItem.value);
            } else {
                console.log("moviesearch per query");
                uri.addQuery("q", $scope.searchTerm);
            }
            
        } else if ($scope.category.indexOf("TV") > -1) {
            uri.addQuery("t", "tvsearch");
            uri.addQuery("tvdbid", $scope.selectedItem.value);
            if ($scope.searchSeason != "") {
                uri.addQuery("season", $scope.searchSeason);
            }
            if ($scope.searchEpisode != "") {
                uri.addQuery("episode", $scope.searchEpisode);
            }
        } else {
            uri.addQuery("t", "search").addQuery("q", $scope.searchTerm);
        }

        console.log(uri);
        $http.get(uri).then(function (data) {

            $scope.results = data.data.results;
            console.log($scope.results);
        });


    };

    $scope.autocompleteActive = function () {
        return ($scope.category.indexOf("TV") > -1) || ($scope.category.indexOf("Movies") > -1)
    };


    $scope.results = [];
    $scope.isShowDuplicates = false;
    $scope.predicate = 'age';
    $scope.reversed = false;

    $scope.setSorting = function (predicate, reversedDefault) {
        if (predicate == $scope.predicate) {
            $scope.reversed = !$scope.reversed;
        } else {
            $scope.reversed = reversedDefault;
        }
        $scope.predicate = predicate;
        console.log($scope.predicate);
    };


}]);