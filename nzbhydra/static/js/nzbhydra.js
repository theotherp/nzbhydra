var nzbhydraapp = angular.module('nzbhydraApp', ['angular-loading-bar', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters', 'ui.router', 'blockUI', 'schemaForm', 'mgcrea.ngStrap', 'angularUtils.directives.dirPagination', 'nvd3']);


angular.module('nzbhydraApp').config(["$stateProvider", "$urlRouterProvider", "$locationProvider", "blockUIConfig", function ($stateProvider, $urlRouterProvider, $locationProvider, blockUIConfig) {

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
                providersearches: [],
                total : 0,
                resultsCount: 0,
                mode: "results"
            }
        })
        .state("config", {
            url: "/config",
            templateUrl: "static/html/states/config.html",
            controller: "ConfigController"
        })
    .state("stats", {
            url: "/stats",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController"
        })
    ;

    $locationProvider.html5Mode(true);

}]);

nzbhydraapp.config(["paginationTemplateProvider", function(paginationTemplateProvider) {
    paginationTemplateProvider.setPath('static/html/dirPagination.tpl.html');
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

nzbhydraapp.controller('ModalInstanceCtrl', ["$scope", "$modalInstance", "nfo", function ($scope, $modalInstance, nfo) {

    $scope.nfo = nfo;


    $scope.ok = function () {
        $modalInstance.close($scope.selected.item);
    };

    $scope.cancel = function () {
        $modalInstance.dismiss();
    };
}]);


nzbhydraapp.filter('nzblink', function () {
    return function (resultItem) {
        var uri = new URI("internalapi/getnzb");
        uri.addQuery("guid", resultItem.guid);
        uri.addQuery("title", resultItem.title);
        uri.addQuery("provider", resultItem.provider);

        return uri.toString();
    }
});


nzbhydraapp.factory('focus', ["$rootScope", "$timeout", function ($rootScope, $timeout) {
    return function (name) {
        $timeout(function () {
            $rootScope.$broadcast('focusOn', name);
        });
    }
}]);


_.mixin({
    isNullOrEmpty: function (string) {
        return (_.isUndefined(string) || _.isNull(string) || string.trim().length === 0)
    }
});

angular
    .module('nzbhydraApp')
    .directive('searchResult', searchResult);

function searchResult() {
    return {
        templateUrl: 'static/html/directives/search-result.html',
        require: '^titleGroup',
        scope: {
            titleGroup: "=",
            showDuplicates: "=",
            selected: "="
        },
        controller: ['$scope', '$element', '$attrs', controller],
        multiElement: true
    };

    function controller($scope, $element, $attrs) {
        $scope.titleGroupExpanded = false;
        $scope.hashGroupExpanded = {};

        $scope.toggleTitleGroup = function () {
            $scope.titleGroupExpanded = !$scope.titleGroupExpanded;
            if (!$scope.titleGroupExpanded) {
                $scope.hashGroupExpanded[$scope.titleGroup[0][0].hash] = false; //Also collapse the first title's duplicates
            }
        };

        $scope.groupingRowDuplicatesToShow = groupingRowDuplicatesToShow;
        function groupingRowDuplicatesToShow() {
            if ($scope.showDuplicates &&  $scope.titleGroup[0].length > 1 && $scope.hashGroupExpanded[$scope.titleGroup[0][0].hash]) {
                return $scope.titleGroup[0].slice(1);
            } else {
                return [];
            }
        }

        //<div ng-repeat="hashGroup in titleGroup" ng-if="titleGroup.length > 0 && titleGroupExpanded"  class="search-results-row">
        $scope.otherTitleRowsToShow = otherTitleRowsToShow;
        function otherTitleRowsToShow() {
            if ($scope.titleGroup.length > 1 && $scope.titleGroupExpanded) {
                console.log("Other titles to show:");
                console.log($scope.titleGroup.slice(1));
                return $scope.titleGroup.slice(1);
            } else {
                return [];
            }
        }
        
        $scope.hashGroupDuplicatesToShow = hashGroupDuplicatesToShow;
        function hashGroupDuplicatesToShow(hashGroup) {
            if ($scope.showDuplicates && $scope.hashGroupExpanded[hashGroup[0].hash]) {
                return hashGroup.slice(1);
            } else {
                return [];
            }
        }
    }
}
angular
    .module('nzbhydraApp')
    .directive('otherColumns', otherColumns);

function otherColumns($http, $templateCache, $compile) {
    controller.$inject = ["$scope", "$http", "$uibModal", "$sce"];
    return {
        scope: {
            result: "="
        },
        multiElement: true,

        link: function (scope, element, attrs) {
            $http.get('static/html/directives/search-result-non-title-columns.html', {cache: $templateCache}).success(function (templateContent) {
                element.replaceWith($compile(templateContent)(scope));
            });

        },
        controller: controller
    };

    function controller($scope, $http, $uibModal, $sce) {

        $scope.showNfo = showNfo;
        function showNfo(resultItem) {
            if (!resultItem.has_nfo) {
                return;
            }
            var uri = new URI("internalapi/getnfo");
            uri.addQuery("provider", resultItem.provider);
            uri.addQuery("guid", resultItem.providerguid);
            return $http.get(uri).then(function (response) {
                if (response.data.has_nfo) {
                    $scope.openModal("lg", response.data.nfo)
                } else {
                    //todo: show error or info that no nfo is available
                    growl.info("No NFO available");
                }
            });
        }


        $scope.openModal = openModal;

        function openModal(size, nfo) {
            var modalInstance = $uibModal.open({
                template: '<pre><span ng-bind-html="nfo"></span></pre>',
                controller: 'ModalInstanceCtrl',
                size: size,
                resolve: {
                    nfo: function () {
                        return $sce.trustAsHtml(nfo);
                    }
                }
            });

            modalInstance.result.then();
        }

    }

}
otherColumns.$inject = ["$http", "$templateCache", "$compile"];
//Can be used in an ng-repeat directive to call a function when the last element was rendered
//We use it to mark the end of sorting / filtering so we can stop blocking the UI

angular
    .module('nzbhydraApp')
    .directive('onFinishRender', onFinishRender);

function onFinishRender($timeout) {
    function linkFunction(scope, element, attr) {
        
        if (scope.$last === true) {
                $timeout(function () {
                    console.log("Finished last render");
                    scope.$evalAsync(attr.onFinishRender);
                });
            }
    }

    return {
        link: linkFunction
    }
}
onFinishRender.$inject = ["$timeout"];
angular
    .module('nzbhydraApp').directive('focusOn', focusOn);

function focusOn() {
    return directive;
    function directive(scope, elem, attr) {
        scope.$on('focusOn', function (e, name) {
            if (name === attr.focusOn) {
                elem[0].focus();
            }
        });
    }
}

angular
    .module('nzbhydraApp')
    .directive('addableNzb', addableNzb);

function addableNzb() {
    return {
        templateUrl: 'static/html/directives/addable-nzb.html',
        require: '^item',
        scope: {
            item: "="
        },
        controller: ['$scope', '$http', controller]
    };

    function controller($scope, $http) {
        $scope.classname = "nzb";

        $scope.add = function () {
            $scope.classname = "nzb-spinning";
            $http.put("internalapi/addnzbs", {guids: angular.toJson([$scope.item.guid])}).success(function (response) {
                if (response.success) {
                    $scope.classname = "nzb-success";
                } else {
                    $scope.classname = "nzb-error";
                }
                
            }).error(function () {
                
            });
        }
        
    }
}
angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope, $http) {



    $http.get("internalapi/getstats").success(function (response) {
        console.log(response);
        $scope.avgResponseTimes = response.avgResponseTimes;
        $scope.avgProviderSearchResultsShares = response.avgProviderSearchResultsShares;
        $scope.avgProviderAccessSuccesses = response.avgProviderAccessSuccesses;
        console.log($scope.avgResponseTimes);
    });


}
StatsController.$inject = ["$scope", "$http"];

angular
    .module('nzbhydraApp')
    .factory('SearchService', SearchService);

function SearchService($http) {


    var lastExecutedQuery;

    var service = {search: search, loadMore: loadMore};
    return service;

    function search(category, query, imdbid, title, tvdbid, season, episode, minsize, maxsize, minage, maxage, selectedProviders) {
        console.log("Category: " + category);
        var uri;
        if (category.indexOf("Movies") > -1) {
            console.log("Search for movies");
            uri = new URI("internalapi/moviesearch");
            if (imdbid) {
                console.log("moviesearch per imdbid");
                uri.addQuery("imdbid", imdbid);
                uri.addQuery("title", title);
            } else {
                console.log("moviesearch per query");
                uri.addQuery("query", query);
            }

        } else if (category.indexOf("TV") > -1) {
            console.log("Search for shows");
            uri = new URI("internalapi/tvsearch");
            if (tvdbid) {
                uri.addQuery("tvdbid", tvdbid);
                uri.addQuery("title", title);
            }

            if (season != "") {
                uri.addQuery("season", season);
            }
            if (episode != "") {
                uri.addQuery("episode", episode);
            }
        } else {
            console.log("Search for all");
            uri = new URI("internalapi/search");
            uri.addQuery("query", query);
        }

        if (!_.isNullOrEmpty(minsize)) {
            uri.addQuery("minsize", minsize);
        }
        if (!_.isNullOrEmpty(maxsize)) {
            uri.addQuery("maxsize", maxsize);
        }
        if (!_.isNullOrEmpty(minage)) {
            uri.addQuery("minage", minage);
        }
        if (!_.isNullOrEmpty(maxage)) {
            uri.addQuery("maxage", maxage);
        }
        

        uri.addQuery("category", category);

        console.log("Calling " + uri);
        lastExecutedQuery = uri;
        return $http.get(uri).then(processData);

    }

    function loadMore(offset) {
        lastExecutedQuery.removeQuery("offset");
        lastExecutedQuery.addQuery("offset", offset);

        console.log("Calling " + lastExecutedQuery);
        return $http.get(lastExecutedQuery).then(processData);
    }

    function processData(response) {
        var results = response.data.results;
        var providersearches = response.data.providersearches;
        var total = response.data.total;
        var resultsCount = results.length;


        //Sum up response times of providers from individual api accesses
        //TODO: Move this to search result controller because we need to update it every time we loaded more results
        _.each(providersearches, function (ps) {
            ps.averageResponseTime = _.reduce(ps.api_accesses, function (memo, rp) {
                return memo + rp.response_time;
            }, 0);
            ps.averageResponseTime = ps.averageResponseTime / ps.api_accesses.length;
        });
        

        return {"results": results, "providersearches": providersearches, "total": total, "resultsCount": resultsCount}
    }
}
SearchService.$inject = ["$http"];

_.mixin({
    isNullOrEmpty: function (string) {
        return (_.isUndefined(string) || _.isNull(string) || string.trim().length === 0)
    }
});
angular
    .module('nzbhydraApp')
    .controller('SearchResultsController', SearchResultsController);


//SearchResultsController.$inject = ['blockUi'];
function SearchResultsController($stateParams, $scope, $q, $timeout, blockUI, SearchService, $http, $uibModal, $sce, growl) {

    $scope.sortPredicate = "epoch";
    $scope.sortReversed = true;

    $scope.limitTo = 101;
    $scope.offset = 0;

    //Handle incoming data
    $scope.providersearches = $stateParams.providersearches;

    $scope.providerDisplayState = []; //Stores if a provider's results should be displayed or not

    $scope.providerResultsInfo = {}; //Stores information about the provider's results like how many we already retrieved

    $scope.groupExpanded = {};

    $scope.doShowDuplicates = false;

    $scope.selected = {};

    //Initially set visibility of all found providers to true, they're needed for initial filtering / sorting
    _.forEach($scope.providersearches, function (ps) {
        $scope.providerDisplayState[ps.provider] = true;
    });

    _.forEach($scope.providersearches, function (ps) {
        $scope.providerResultsInfo[ps.provider] = {loadedResults: ps.loaded_results};
    });

    //Process results
    $scope.results = $stateParams.results;
    $scope.total = $stateParams.total;
    $scope.resultsCount = $stateParams.resultsCount;
    $scope.filteredResults = sortAndFilter($scope.results);
    stopBlocking();


    //Returns the content of the property (defined by the current sortPredicate) of the first group element 
    $scope.firstResultPredicate = firstResultPredicate;
    function firstResultPredicate(item) {
        return item[0][$scope.sortPredicate];
    }

    //Returns the unique group identifier which allows angular to keep track of the grouped search results even after filtering, making filtering by providers a lot faster (albeit still somewhat slow...)  
    $scope.groupId = groupId;
    function groupId(item) {
        return item[0][0].guid;
    }

    //Block the UI and return after timeout. This way we make sure that the blocking is done before angular starts updating the model/view. There's probably a better way to achieve that?
    function startBlocking(message) {
        var deferred = $q.defer();
        blockUI.start(message);
        $timeout(function () {
            deferred.resolve();
        }, 100);
        return deferred.promise;
    }

    //Set sorting according to the predicate. If it's the same as the old one, reverse, if not sort by the given default (so that age is descending, name ascending, etc.)
    //Sorting (and filtering) are really slow (about 2 seconds for 1000 results from 5 providers) but I haven't found any way of making it faster, apart from the tracking 
    $scope.setSorting = setSorting;
    function setSorting(predicate, reversedDefault) {
        startBlocking("Sorting / filtering...").then(function () {

            if (predicate == $scope.sortPredicate) {
                $scope.sortReversed = !$scope.sortReversed;
            } else {
                $scope.sortReversed = reversedDefault;
            }
            $scope.sortPredicate = predicate;
            $scope.filteredResults = sortAndFilter($scope.results);
            blockUI.reset();
        });
    }


    function sortAndFilter(results) {

        function getItemProviderDisplayState(item) {
            return $scope.providerDisplayState[item.provider];
        }

        function getTitleLowerCase(element) {
            return element.title.toLowerCase();
        }

        function createSortedHashgroups(titleGroup) {
            
            function createHashGroup(hashGroup) {
                //Sorting hash group's contents should not matter for size and age and title but might for category (we might remove this, it's probably mostly unnecessary)
                var sortedHashGroup = _.sortBy(hashGroup, function (item) {
                    var sortPredicateValue = item[$scope.sortPredicate];
                    return $scope.sortReversed ?  -sortPredicateValue : sortPredicateValue;
                });
                //Now sort the hash group by provider score (inverted) so that the result with the highest provider score is shown on top (or as the only one of a hash group if it's collapsed)
                sortedHashGroup = _.sortBy(sortedHashGroup, function (item) {
                    return item.providerscore * -1;
                });
                return sortedHashGroup;
            }
            
            function getHashGroupFirstElementSortPredicate(hashGroup) {
                var sortPredicateValue = hashGroup[0][$scope.sortPredicate];
                return $scope.sortReversed ?  -sortPredicateValue : sortPredicateValue;
            }
            
            return _.chain(titleGroup).groupBy("hash").map(createHashGroup).sortBy(getHashGroupFirstElementSortPredicate).value();
        }

        function getTitleGroupFirstElementsSortPredicate(titleGroup) {
            var sortPredicateValue = titleGroup[0][0][$scope.sortPredicate];
            return $scope.sortReversed ?  -sortPredicateValue : sortPredicateValue;
        }

        return _.chain(results)
            //Remove elements of which the provider is currently hidden    
            .filter(getItemProviderDisplayState)
            //Make groups of results with the same title    
            .groupBy(getTitleLowerCase)
            //For every title group make subgroups of duplicates and sort the group    
            .map(createSortedHashgroups)
            //And then sort the title group using its first hashgroup's first item (the group itself is already sorted and so are the hash groups)    
            .sortBy(getTitleGroupFirstElementsSortPredicate)
            .value();

    }

    $scope.toggleTitlegroupExpand = function toggleTitlegroupExpand(titleGroup) {
        $scope.groupExpanded[titleGroup[0][0].title] = !$scope.groupExpanded[titleGroup[0][0].title];
        $scope.groupExpanded[titleGroup[0][0].hash] = !$scope.groupExpanded[titleGroup[0][0].hash];
    };


//Clear the blocking
    $scope.stopBlocking = stopBlocking;
    function stopBlocking() {
        blockUI.reset();
    }

    $scope.loadMore = loadMore;
    function loadMore() {
        $scope.offset += 100;
        console.log("Increasing the offset to " + $scope.offset);

        startBlocking("Loading more results...").then(function () {
            SearchService.loadMore($scope.offset).then(function (data) {
                console.log("Returned more results:");
                console.log(data.results);
                console.log($scope.results);
                console.log("Total: " + data.total);
                $scope.results = $scope.results.concat(data.results);
                $scope.filteredResults = sortAndFilter($scope.results);
                $scope.total = data.total;
                $scope.resultsCount += data.resultsCount;
                console.log("Total results in $scope.results: " + $scope.results.length);

                stopBlocking();
            });
        });
    }


//Filters the results according to new visibility settings.
    $scope.toggleProviderDisplay = toggleProviderDisplay;
    function toggleProviderDisplay() {
        startBlocking("Filtering. Sorry...").then(function () {
            $scope.filteredResults = sortAndFilter($scope.results);
        }).then(function () {
            stopBlocking();
        });
    }

    $scope.countResults = countResults;
    function countResults() {
        return $scope.results.length;
    }

    $scope.downloadSelected = downloadSelected;
    function downloadSelected() {

        var guids = Object.keys($scope.selected);

        console.log(guids);
        $http.put("internalapi/addnzbs", {guids: angular.toJson(guids)}).success(function (response) {
            if (response.success) {
                console.log("success");
                growl.info("Successfully added " + response.added + " of " + response.of + " NZBs");
            } else {
                growl.error("Error while adding NZBs");
            }
        }).error(function () {
            growl.error("Error while adding NZBs");
        });
    }


}
SearchResultsController.$inject = ["$stateParams", "$scope", "$q", "$timeout", "blockUI", "SearchService", "$http", "$uibModal", "$sce", "growl"];
angular
    .module('nzbhydraApp')
    .controller('SearchController', SearchController);


SearchController.$inject = ['$scope', '$http', '$stateParams', '$uibModal', '$sce', '$state', 'SearchService', 'focus', 'ConfigService', 'blockUI', 'growl'];
function SearchController($scope, $http, $stateParams, $uibModal, $sce, $state, SearchService, focus, ConfigService, blockUI, growl) {

    console.log("Start of search controller");


    $scope.category = (typeof $stateParams.category === "undefined" || $stateParams.category == "") ? "All" : $stateParams.category;

    $scope.query = (typeof $stateParams.query === "undefined") ? "" : $stateParams.query;

    $scope.imdbid = (typeof $stateParams.imdbid === "undefined") ? "" : $stateParams.imdbid;
    $scope.tvdbid = (typeof $stateParams.tvdbid === "undefined") ? "" : $stateParams.tvdbid;
    $scope.title = (typeof $stateParams.title === "undefined") ? "" : $stateParams.title;
    $scope.season = (typeof $stateParams.season === "undefined") ? "" : $stateParams.season;
    $scope.episode = (typeof $stateParams.episode === "undefined") ? "" : $stateParams.episode;

    $scope.minsize = (typeof $stateParams.minsize === "undefined") ? "" : $stateParams.minsize;
    $scope.maxsize = (typeof $stateParams.maxsize === "undefined") ? "" : $stateParams.maxsize;
    $scope.minage = (typeof $stateParams.minage === "undefined") ? "" : $stateParams.minage;
    $scope.maxage = (typeof $stateParams.maxage === "undefined") ? "" : $stateParams.maxage;
    $scope.selectedProviders = (typeof $stateParams.providers === "undefined") ? "" : $stateParams.providers;

    $scope.showProviders = {};

    var config;


    if ($scope.title != "" && $scope.query == "") {
        $scope.query = $scope.title;
    }


    $scope.typeAheadWait = 300;
    $scope.selectedItem = "";
    $scope.autocompleteLoading = false;


    $scope.isAskById = false; //If true a check box will be shown asking the user if he wants to search by ID 
    $scope.isById = {value: true}; //If true the user wants to search by id so we enable autosearch. Was unable to achieve this using a simple boolean

    $scope.availableProviders = [];


    $scope.autocompleteClass = "autocompletePosterMovies";

    $scope.toggle = function (searchCategory) {
        $scope.category = searchCategory;

        //Show checkbox to ask if the user wants to search by ID (using autocomplete)
        $scope.isAskById = ($scope.category.indexOf("TV") > -1 || $scope.category.indexOf("Movies") > -1 );

        focus('focus-query-box');
        $scope.query = "";

        if (config.settings.searching.categorysizes.enable_category_sizes) {
            var min = config.settings.searching.categorysizes[searchCategory + " min"];
            var max = config.settings.searching.categorysizes[searchCategory + " max"];
            if (_.isNumber(min)) {
                $scope.minsize = min;
            } else {
                $scope.minsize = "";
            }
            if (_.isNumber(max)) {
                $scope.maxsize = max;
            } else {
                $scope.maxsize = "";
            }
        }
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
            return $http.get('internalapi/autocomplete?type=movie', {
                params: {
                    input: val
                }
            }).then(function (response) {
                $scope.autocompleteLoading = false;
                return response.data.results;
            });
        } else if ($scope.category.indexOf("TV") > -1) {

            return $http.get('internalapi/autocomplete?type=tv', {
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
        blockUI.start("Searching...");
        SearchService.search($scope.category, $scope.query, $scope.imdbid, $scope.title, $scope.tvdbid, $scope.season, $scope.episode, $scope.minsize, $scope.maxsize, $scope.minage, $scope.maxage, $scope.selectedProviders).then(function (searchResult) {
            $state.go("search.results", {"results": searchResult.results, "providersearches": searchResult.providersearches, total: searchResult.total, resultsCount: searchResult.resultsCount});
            $scope.imdbid = "";
            $scope.tvdbid = "";
        });
    };


    $scope.goToSearchUrl = function () {
        var state;
        var stateParams = {};
        if ($scope.imdbid != "") {
            stateParams.imdbid = $scope.imdbid;
            stateParams.title = $scope.title;


        } else if ($scope.tvdbid != "") {
            stateParams.tvdbid = $scope.tvdbid;
            stateParams.title = $scope.title;

            if ($scope.season != "") {
                stateParams.season = $scope.season;
            }
            if ($scope.episode != "") {
                stateParams.episode = $scope.episode;
            }
        } else {
            stateParams.query = $scope.query;
        }

        if ($scope.minsize != "") {
            stateParams.minsize = $scope.minsize;
        }
        if ($scope.maxsize != "") {
            stateParams.maxsize = $scope.maxsize;
        }
        if ($scope.minage != "") {
            stateParams.minage = $scope.minage;
        }
        if ($scope.maxage != "") {
            stateParams.maxage = $scope.maxage;
        }

        stateParams.category = $scope.category;

        console.log("Going to search state with params...");
        console.log(stateParams);
        $state.go("search", stateParams, {inherit: false});
    };


    $scope.selectAutocompleteItem = function ($item) {
        $scope.selectedItem = $item;
        $scope.title = $item.label;
        if ($scope.category.indexOf("Movies") > -1) {
            $scope.imdbid = $item.value;
        } else if ($scope.category.indexOf("TV") > -1) {
            $scope.tvdbid = $item.value;
        }
        $scope.query = "";
        $scope.goToSearchUrl();
    };


    $scope.autocompleteActive = function () {
        return ($scope.category.indexOf("TV") > -1) || ($scope.category.indexOf("Movies") > -1)
    };

    $scope.seriesSelected = function () {
        return ($scope.category.indexOf("TV") > -1);
    };
    
    
    ConfigService.get().then(function (cfg) {
        config = cfg;

        $scope.availableProviders = _.filter(cfg.settings.providers, function (provider) {
            return provider.enabled;
        }).map(function (provider) {
            return {name: provider.name, activated: true};
        });
        console.log($scope.availableProviders);
    });

//Resolve the search request from URL
    if ($stateParams.mode != "landing") {
        //(category, query, imdbid, title, tvdbid, season, episode, minsize, maxsize, minage, maxage)
        console.log("Came from search url, will start searching");
        $scope.startSearch();
    }


}


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
//Filters that are needed at several places. Probably possible to do tha another way but I dunno how
var filters = angular.module('filters', []);


filters.filter('bytes', function() {
	return function(bytes, precision) {
		if (isNaN(parseFloat(bytes)) || !isFinite(bytes) || bytes == 0) return '-';
		if (typeof precision === 'undefined') precision = 1;
		
		var units = ['b', 'kB', 'MB', 'GB', 'TB', 'PB'],
			number = Math.floor(Math.log(bytes) / Math.log(1024));
		//if(units[number] == "MB" || units[number] == "kB" || units[number] == "b")
		//precision = 0;
		return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +   units[number];
	}
});

filters.filter('unsafe', ['$sce', function ($sce) {
	return $sce.trustAsHtml;
}]);




angular
    .module('nzbhydraApp')
    .factory('ConfigService', ConfigService);

function ConfigService($http, $q) {

    var config;
    
    var service = {
        set: setConfig,
        get: getConfig
    };
    
    return service;
    
    

    function setConfig(settings) {
        console.log("Starting setConfig");

        $http.put('internalapi/setsettings', settings)
            .then(function (successresponse) {
                console.log("Settings saved. Updating cache");
                config.settings = settings;
            }, function (errorresponse) {
                console.log("Error saving settings: " + errorresponse);
            });

    }

    function getConfig() {

        function loadAll() {
            if (!angular.isUndefined(config)) {
                var deferred = $q.defer();
                deferred.resolve(config);
                console.log("Returning config from cache");
                return deferred.promise;
            }

            return $http.get('internalapi/getconfig')
                .then(function (configResponse) {
                    console.log("Updating config cache");
                    config = configResponse.data;
                    return configResponse.data;
                });

        }


        return loadAll().then(function (config) {
            return {schema: config.schema, settings: config.settings, form: config.form}
        });

    }
}
ConfigService.$inject = ["$http", "$q"];
angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);

function ConfigController($scope, $http, ConfigService, blockUI) {

    activate();
    
    
    function activate() {
        $scope.$on('sf-render-finished', function () {
            blockUI.reset();
            console.log("Render of form finished");
        });
        blockUI.start("Loading config...");
        return ConfigService.get().then(function set(settingsAndSchemaAndForm) {
            $scope.model = settingsAndSchemaAndForm.settings;
            $scope.schema = settingsAndSchemaAndForm.schema;
            $scope.form = settingsAndSchemaAndForm.form;
        });
    }
    

    $scope.onSubmit = function (form) {
        // First we broadcast an event so all fields validate themselves
        $scope.$broadcast('schemaFormValidate');

        // Then we check if the form is valid
        if (form.$valid) {
            ConfigService.set($scope.model);
        }
    }
}
ConfigController.$inject = ["$scope", "$http", "ConfigService", "blockUI"];



//# sourceMappingURL=nzbhydra.js.map
