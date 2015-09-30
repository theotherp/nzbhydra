var nzbhydraapp = angular.module('nzbhydraApp', ['ngRoute', 'angular-loading-bar', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters']);









nzbhydraapp.run(['$rootScope', '$route', function($rootScope, $route) {
    $rootScope.$on('$routeChangeSuccess', function(newVal, oldVal) {
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


nzbhydraapp.filter('sortResults', function() {
    return function(input, predicate, reversed) {
        console.log("Filter by " + predicate);
        console.log("Reversed: " + reversed);
        var sorted = _.sortBy(input, function (i) {
            return i[0][predicate];
        });
        if (reversed) {
            sorted.reverse();
        }
        return sorted;
    }
  });


nzbhydraapp.controller('MainController', ['$scope', '$http', function ($scope, $http) {
    
    $scope.results = [];
    
    $scope.isShowDuplicates = false;
    
    $scope.predicate ='age';
    
    $scope.reversed = false;
	
    $scope.searchFiles = function() {
        $http.get('/internalapi?t=search', {params: {q: $scope.query}}).then(function (data) {
            
            $scope.results = data.data.results;
			console.log($scope.results);
        });
    };
    
    $scope.setSorting = function (predicate, reversedDefault) {
		if (predicate == $scope.predicate) {
			$scope.reversed = !$scope.reversed;
		} else {
			$scope.reversed = reversedDefault;
		}
		$scope.predicate = predicate;
        console.log($scope.predicate);
	};

	
	
	$http.get('/internalapi?t=search', {params: {q: "avengers"}}).then(function (data) {
            
            $scope.results = data.data.results;
			console.log($scope.results);
        });
    
    
    
    
}]);