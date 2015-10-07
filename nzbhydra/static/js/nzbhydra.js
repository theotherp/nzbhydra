var nzbhydraapp = angular.module('nzbhydraApp', ['angular-loading-bar', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters', 'ui.bootstrap-slider', 'ui.router', 'blockUI', 'schemaForm']);

angular.module('nzbhydraApp').config(function ($stateProvider, $urlRouterProvider, $locationProvider) {

    //$urlRouterProvider.otherwise("/search/");

    $stateProvider
        .state("home", {
            url: "/",
            templateUrl: "/static/html/states/search.html",
            controller: "SearchController",
            params: {
                mode: "landing"
            }
        })
        .state("search", {
            url: "/search?category&query&imdbid&tvdbid&title&season&episode&minsize&maxsize&minage&maxage",
            templateUrl: "/static/html/states/search.html",
            controller: "SearchController",
            params: {
                "category": "All",
                mode: "search"
            }
        })
        .state("search.results", {
            templateUrl: "/static/html/states/search-results.html",
            controller: "SearchResultsController",
            options: {
                inherit: false
            },
            params: {
                results: [],
                providersearches: [],
                mode: "results"
            }
        })
        .state("config", {
            url: "/config",
            templateUrl: "/static/html/states/config.html",
            controller: "ConfigController"
            
        })
        ;
        
        $locationProvider.html5Mode(true);

});

angular.module('nzbhydraApp').config(function(blockUIConfig) {
  blockUIConfig.autoBlock = false;

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
        var uri = new URI("/internalapi/getnzb");
        uri.addQuery("guid", resultItem.guid);
        uri.addQuery("title", resultItem.title);
        uri.addQuery("provider", resultItem.provider);

        return uri.toString();
    }
});


nzbhydraapp.factory('focus', function ($rootScope, $timeout) {
  return function(name) {
    $timeout(function (){
      $rootScope.$broadcast('focusOn', name);
    });
  }
});


_.mixin({
    isNullOrEmpty: function(string) {
      return (_.isUndefined(string) || _.isNull(string) || string.trim().length === 0)
    }
  });
