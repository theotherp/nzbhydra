var nzbhydraapp = angular.module('nzbhydraApp', ['angular-loading-bar', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters', 'ui.router', 'blockUI', 'mgcrea.ngStrap', 'angularUtils.directives.dirPagination', 'nvd3', 'formly', 'formlyBootstrap', 'frapontillo.bootstrap-switch', 'ui.select', 'ngSanitize']);


angular.module('nzbhydraApp').config(["$stateProvider", "$urlRouterProvider", "$locationProvider", "blockUIConfig", function ($stateProvider, $urlRouterProvider, $locationProvider, blockUIConfig) {

    blockUIConfig.autoBlock = false;
    //$urlRouterProvider.otherwise("/search/");

    $stateProvider
        .state("home", {
            url: "/",
            templateUrl: "static/html/states/search.html",
            controller: "SearchController"
        })
        .state("search", {
            url: "/search?category&query&imdbid&tvdbid&title&season&episode&minsize&maxsize&minage&maxage&offsets&rid&mode&tmdbid",
            templateUrl: "static/html/states/search.html",
            controller: "SearchController"
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
        .state("stats", {
            url: "/stats",
            templateUrl: "static/html/states/stats.html",
            controller: "StatsController"
        })
        .state("about", {
            url: "/about",
            templateUrl: "static/html/states/about.html",
            controller: "AboutController",
            resolve: {
                versionsPromise: ['$http', function ($http) {
                    return $http.get("internalapi/get_versions");
                }]
            }
        })
    ;

    $locationProvider.html5Mode(true);

}]);

nzbhydraapp.config(["paginationTemplateProvider", function (paginationTemplateProvider) {
    paginationTemplateProvider.setPath('static/html/dirPagination.tpl.html');
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
        return (_.isUndefined(string) || _.isNull(string) || (_.isString(string) && string.length === 0))
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
    controller.$inject = ["$scope", "$http", "$uibModal", "growl"];
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

    function controller($scope, $http, $uibModal, growl) {

        $scope.showNfo = showNfo;
        function showNfo(resultItem) {
            if (!resultItem.has_nfo) {
                return;
            }
            var uri = new URI("internalapi/getnfo");
            uri.addQuery("indexer", resultItem.indexer);
            uri.addQuery("guid", resultItem.indexerguid);
            return $http.get(uri).then(function (response) {
                if (response.data.has_nfo) {
                    $scope.openModal("lg", response.data.nfo)
                } else {
                    if (!angular.isUndefined(resultItem.message)) {
                        growl.error(resultItem.message);
                    } else {
                        growl.info("No NFO available");
                    }
                }
            });
        }

        $scope.openModal = openModal;

        function openModal(size, nfo) {
            var modalInstance = $uibModal.open({
                template: '<pre style="text-align:left"><span ng-bind-html="nfo"></span></pre>',
                controller: 'ModalInstanceCtrl',
                size: size,
                resolve: {
                    nfo: function () {
                        return nfo;
                    }
                }
            });

            modalInstance.result.then();
        }

    }

}
otherColumns.$inject = ["$http", "$templateCache", "$compile"];
angular
    .module('nzbhydraApp')
    .directive('searchHistory', searchHistory);


function searchHistory() {
    return {
        templateUrl: 'static/html/directives/search-history.html',
        controller: ['$scope', '$http','$state', controller]
    };
    
    function controller($scope, $http, $state) {
        $scope.limit = 100;
        $scope.pagination = {
            current: 1
        };

        getSearchRequestsPage(1);

        $scope.pageChanged = function (newPage) {
            getSearchRequestsPage(newPage);
        };

        function getSearchRequestsPage(pageNumber) {
            $http.get("internalapi/getsearchrequests", {params: {page: pageNumber, limit: $scope.limit}}).success(function (response) {
                $scope.searchRequests = response.searchRequests;
                $scope.totalRequests = response.totalRequests;
            });
        }

        $scope.openSearch = function (request) {
            var state;
            var stateParams = {};
            if (request.identifier_key == "imdbid") {
                stateParams.imdbid = request.identifier_value;
            } else if (request.identifier_key == "tvdbid" || request.identifier_key == "rid") {
                if (request.identifier_key == "rid" ) {
                    stateParams.rid = request.identifier_value;
                } else {
                    stateParams.tvdbid = request.identifier_value;
                } 
                
                if (request.season != "") {
                    stateParams.season = request.season;
                }
                if (request.episode != "") {
                    stateParams.episode = request.episode;
                }
            }
            if (request.query != "") {
                stateParams.query = request.query;
            }
            
            stateParams.category = request.category;
            
            $state.go("search", stateParams, {inherit: false});
        };


    }
}
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
    .module('nzbhydraApp')
    .directive('indexerStatuses', indexerStatuses);

function indexerStatuses() {
    return {
        templateUrl: 'static/html/directives/indexer-statuses.html',
        controller: ['$scope', '$http', controller]
    };

    function controller($scope, $http) {
        
        getIndexerStatuses();
        
        function getIndexerStatuses() {
            $http.get("internalapi/getindexerstatuses").success(function (response) {
                $scope.indexerStatuses = response.indexerStatuses;
            });
        }
        
        $scope.isInPast = function (timestamp) {
            return timestamp * 1000 < (new Date).getTime();
        };
        
        $scope.enable = function(indexerName) {
            $http.get("internalapi/enableindexer", {params: {name: indexerName}}).then(function(response){
                $scope.indexerStatuses = response.data.indexerStatuses;
            });
        }

    }
}

angular
    .module('nzbhydraApp')
    .filter('formatDate', formatDate);

function formatDate(dateFilter) {
    return function(timestamp, hidePast) {
        if (timestamp) {
            if (timestamp * 1000 < (new Date).getTime() && hidePast) {
                return ""; //
            }
            
            var t = timestamp * 1000;
            t = dateFilter(t, 'yyyy-MM-dd HH:mm:ss Z');
            return t;
        } else {
            return "";
        }
    }
}
formatDate.$inject = ["dateFilter"];
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
    .directive('downloadHistory', downloadHistory);

function downloadHistory() {
    return {
        templateUrl: 'static/html/directives/download-history.html',
        controller: ['$scope', '$http', controller]
    };

    function controller($scope, $http) {
        $scope.limit = 100;
        $scope.pagination = {
            current: 1
        };

        getDownloadsPage(1);

        $scope.pageChanged = function (newPage) {
            getDownloadsPage(newPage);
        };
        
        function getDownloadsPage(pageNumber) {
            $http.get("internalapi/getnzbdownloads", {params:{page: pageNumber, limit: $scope.limit}}).success(function (response) {
                $scope.nzbDownloads = response.nzbDownloads;
                $scope.totalDownloads = response.totalDownloads;
                console.log($scope.nzbDownloads);
            });
        }


    }
}
angular
    .module('nzbhydraApp')
    .directive('cfgFormEntry', cfgFormEntry);

function cfgFormEntry() {
    return {
        templateUrl: 'static/html/directives/cfg-form-entry.html',
        require: ["^title", "^cfg"],
        scope: {
            title: "@",
            cfg: "=",
            help: "@",
            type: "@?",
            options: "=?"
        },
        controller: ["$scope", "$element", "$attrs", function ($scope, $element, $attrs) {
            $scope.type = angular.isDefined($scope.type) ? $scope.type : 'text';
            $scope.options = angular.isDefined($scope.type) ? $scope.$eval($attrs.options) : [];
            console.log($scope.options);

        }]
    };
}
angular
    .module('nzbhydraApp')
    .directive('addableNzb', addableNzb);

function addableNzb() {
    return {
        templateUrl: 'static/html/directives/addable-nzb.html',
        require: '^guid',
        scope: {
            guid: "="
        },
        controller: ['$scope', 'ConfigService', 'NzbDownloadService', controller]
    };

    function controller($scope, ConfigService, NzbDownloadService) {
        $scope.classname = "nzb";
        ConfigService.get().then(function (settings) {
            $scope.enabled = settings.downloader.downloader != "none";
        });
        
        $scope.add = function() {
            $scope.classname = "nzb-spinning";
            NzbDownloadService.download([$scope.guid]).then(function (response) {
                if (response.data.success) {
                    $scope.classname = "nzb-success";
                } else {
                    $scope.classname = "nzb-error";
                }
            }, function() {
                $scope.classname = "nzb-error";
            })
        };

    }
}


angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope, $http) {

    $scope.nzbDownloads = null;


    $http.get("internalapi/getstats").success(function (response) {
        $scope.avgResponseTimes = response.avgResponseTimes;
        $scope.avgIndexerSearchResultsShares = response.avgIndexerSearchResultsShares;
        $scope.avgIndexerAccessSuccesses = response.avgIndexerAccessSuccesses;
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

    function search(category, query, tmdbid, title, tvdbid, season, episode, minsize, maxsize, minage, maxage) {
        console.log("Category: " + category);
        var uri;
        if (category.indexOf("Movies") > -1 || (category.indexOf("20") == 0)) {
            console.log("Search for movies");
            uri = new URI("internalapi/moviesearch");
            if (!_.isUndefined(tmdbid)) {
                console.log("moviesearch per tmdbid");
                uri.addQuery("tmdbid", tmdbid);
                uri.addQuery("title", title);
            } else {
                console.log("moviesearch per query");
                uri.addQuery("query", query);
            }

        } else if (category.indexOf("TV") > -1 || (category.indexOf("50") == 0)) {
            console.log("Search for shows");
            uri = new URI("internalapi/tvsearch");
            if (!_.isUndefined(tvdbid)) {
                uri.addQuery("tvdbid", tvdbid);
                uri.addQuery("title", title);
            } else {
                console.log("tvsearch per query");
                uri.addQuery("query", query);
            }

            if (!_.isUndefined(season)) {
                uri.addQuery("season", season);
            }
            if (!_.isUndefined(episode)) {
                uri.addQuery("episode", episode);
            }
        } else {
            console.log("Search for all");
            uri = new URI("internalapi/search");
            uri.addQuery("query", query);
        }

        if (_.isNumber(minsize)) {
            uri.addQuery("minsize", minsize);
        }
        if (_.isNumber(maxsize)) {
            uri.addQuery("maxsize", maxsize);
        }
        if (_.isNumber(minage)) {
            uri.addQuery("minage", minage);
        }
        if (_.isNumber(maxage)) {
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
        var indexersearches = response.data.indexersearches;
        var total = response.data.total;
        var resultsCount = results.length;


        //Sum up response times of indexers from individual api accesses
        //TODO: Move this to search result controller because we need to update it every time we loaded more results
        _.each(indexersearches, function (ps) {
            ps.averageResponseTime = _.reduce(ps.api_accesses, function (memo, rp) {
                return memo + rp.response_time;
            }, 0);
            ps.averageResponseTime = ps.averageResponseTime / ps.api_accesses.length;
        });
        

        return {"results": results, "indexersearches": indexersearches, "total": total, "resultsCount": resultsCount}
    }
}
SearchService.$inject = ["$http"];
angular
    .module('nzbhydraApp')
    .controller('SearchResultsController', SearchResultsController);

//SearchResultsController.$inject = ['blockUi'];
function SearchResultsController($stateParams, $scope, $q, $timeout, blockUI, SearchService, $http, $uibModal, $sce, growl, NzbDownloadService) {

    $scope.sortPredicate = "epoch";
    $scope.sortReversed = true;
    $scope.limitTo = 100;
    $scope.offset = 0;
    //Handle incoming data
    $scope.indexersearches = $stateParams.indexersearches;
    $scope.indexerDisplayState = []; //Stores if a indexer's results should be displayed or not
    $scope.indexerResultsInfo = {}; //Stores information about the indexer's results like how many we already retrieved
    $scope.groupExpanded = {};
    $scope.doShowDuplicates = false;
    $scope.selected = {};
    
    $scope.countFilteredOut = 0;

    //Initially set visibility of all found indexers to true, they're needed for initial filtering / sorting
    _.forEach($scope.indexersearches, function (ps) {
        $scope.indexerDisplayState[ps.indexer] = true;
    });

    _.forEach($scope.indexersearches, function (ps) {
        $scope.indexerResultsInfo[ps.indexer] = {loadedResults: ps.loaded_results};
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

    //Returns the unique group identifier which allows angular to keep track of the grouped search results even after filtering, making filtering by indexers a lot faster (albeit still somewhat slow...)  
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
    //Sorting (and filtering) are really slow (about 2 seconds for 1000 results from 5 indexers) but I haven't found any way of making it faster, apart from the tracking 
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
        $scope.countFilteredOut = 0;
        function filterByAgeAndSize(item) {
            var filterOut = !(_.isNumber($stateParams.minsize) && item.size / 1024 / 1024 < $stateParams.minsize)
                && !(_.isNumber($stateParams.maxsize) && item.size / 1024 / 1024 > $stateParams.maxsize)
                && !(_.isNumber($stateParams.minage) && item.age_days < $stateParams.minage)
                && !(_.isNumber($stateParams.maxage) && item.age_days > $stateParams.maxage);
            if (!filterOut) {
                $scope.countFilteredOut++;
            }
            return filterOut;
        }
        
        
        function getItemIndexerDisplayState(item) {
            return $scope.indexerDisplayState[item.indexer];
        }

        function getTitleLowerCase(element) {
            return element.title.toLowerCase();
        }

        function createSortedHashgroups(titleGroup) {

            function createHashGroup(hashGroup) {
                //Sorting hash group's contents should not matter for size and age and title but might for category (we might remove this, it's probably mostly unnecessary)
                var sortedHashGroup = _.sortBy(hashGroup, function (item) {
                    var sortPredicateValue = item[$scope.sortPredicate];
                    return $scope.sortReversed ? -sortPredicateValue : sortPredicateValue;
                });
                //Now sort the hash group by indexer score (inverted) so that the result with the highest indexer score is shown on top (or as the only one of a hash group if it's collapsed)
                sortedHashGroup = _.sortBy(sortedHashGroup, function (item) {
                    return item.indexerscore * -1;
                });
                return sortedHashGroup;
            }

            function getHashGroupFirstElementSortPredicate(hashGroup) {
                var sortPredicateValue = hashGroup[0][$scope.sortPredicate];
                return $scope.sortReversed ? -sortPredicateValue : sortPredicateValue;
            }

            return _.chain(titleGroup).groupBy("hash").map(createHashGroup).sortBy(getHashGroupFirstElementSortPredicate).value();
        }

        function getTitleGroupFirstElementsSortPredicate(titleGroup) {
            var sortPredicateValue = titleGroup[0][0][$scope.sortPredicate];
            return $scope.sortReversed ? -sortPredicateValue : sortPredicateValue;
        }

        var filtered = _.chain(results)
            //Remove elements of which the indexer is currently hidden    
            .filter(getItemIndexerDisplayState)
            //and which were not filtered by the indexers (because they don't support queries with min/max size/age)
            .filter(filterByAgeAndSize)
            //Make groups of results with the same title    
            .groupBy(getTitleLowerCase)
            //For every title group make subgroups of duplicates and sort the group    
            .map(createSortedHashgroups)
            //And then sort the title group using its first hashgroup's first item (the group itself is already sorted and so are the hash groups)    
            .sortBy(getTitleGroupFirstElementsSortPredicate)
            .value();
        if ($scope.countFilteredOut > 0) {
            growl.info("Filtered " + $scope.countFilteredOut + " of the retrieved results");
        }
        return filtered;

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
        console.log("Loading more result withs offset " + $scope.resultsCount);

        startBlocking("Loading more results...").then(function () {
            SearchService.loadMore($scope.resultsCount).then(function (data) {
                console.log("Returned more results:");
                console.log(data.results);
                console.log($scope.results);
                console.log("Total: " + data.total);
                $scope.results = $scope.results.concat(data.results);
                $scope.filteredResults = sortAndFilter($scope.results);
                $scope.total = data.total;
                $scope.resultsCount += data.resultsCount;
                console.log("Results count: " + $scope.resultsCount);
                console.log("Total results in $scope.results: " + $scope.results.length);

                stopBlocking();
            });
        });
    }


//Filters the results according to new visibility settings.
    $scope.toggleIndexerDisplay = toggleIndexerDisplay;
    function toggleIndexerDisplay() {
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
        NzbDownloadService.download(guids).then(function (response) {
            if (response.data.success) {
                growl.info("Successfully added " + response.data.added + " of " + response.data.of + " NZBs");
            } else {
                growl.error("Error while adding NZBs");
            }
        }, function () {
            growl.error("Error while adding NZBs");
        });

    }


}
SearchResultsController.$inject = ["$stateParams", "$scope", "$q", "$timeout", "blockUI", "SearchService", "$http", "$uibModal", "$sce", "growl", "NzbDownloadService"];
angular
    .module('nzbhydraApp')
    .controller('SearchController', SearchController);


SearchController.$inject = ['$scope', '$http', '$stateParams', '$uibModal', '$sce', '$state', 'SearchService', 'focus', 'ConfigService', 'blockUI', 'growl'];
function SearchController($scope, $http, $stateParams, $uibModal, $sce, $state, SearchService, focus, ConfigService, blockUI, growl) {

    function getNumberOrUndefined(number) {
        if (_.isUndefined(number) || _.isNaN(number) || number == "") {
            return undefined;
        }
        number = parseInt(number);
        if (_.isNumber(number)) {
            return number;
        } else {
            return undefined;
        }
    }

    console.log("Start of search controller");

    //Fill the form with the search values we got from the state params (so that their values are the same as in the current url)
    $scope.mode = $stateParams.mode;
    $scope.category = (_.isUndefined($stateParams.category) || $stateParams.category == "") ? "All" : $stateParams.category;
    $scope.tmdbid = $stateParams.tmdbid;
    $scope.tvdbid = $stateParams.tvdbid;
    $scope.rid = $stateParams.rid;
    $scope.title = $stateParams.title;
    $scope.season = $stateParams.season;
    $scope.episode = $stateParams.episode;
    $scope.query = $stateParams.query;
    $scope.minsize = getNumberOrUndefined($stateParams.minsize);
    $scope.maxsize = getNumberOrUndefined($stateParams.maxsize);
    $scope.minage = getNumberOrUndefined($stateParams.minage);
    $scope.maxage = getNumberOrUndefined($stateParams.maxage);
    if (!_.isUndefined($scope.title) && _.isUndefined($scope.query)) {
        $scope.query = $scope.title;
    }

    $scope.showIndexers = {};

    var config;


    $scope.typeAheadWait = 300;
    $scope.selectedItem = "";
    $scope.autocompleteLoading = false;
    $scope.isAskById = ($scope.category.indexOf("TV") > -1 || $scope.category.indexOf("Movies") > -1 ); //If true a check box will be shown asking the user if he wants to search by ID 
    $scope.isById = {value: true}; //If true the user wants to search by id so we enable autosearch. Was unable to achieve this using a simple boolean
    $scope.availableIndexers = [];
    $scope.autocompleteClass = "autocompletePosterMovies";

    $scope.toggle = function (searchCategory) {
        $scope.category = searchCategory;

        //Show checkbox to ask if the user wants to search by ID (using autocomplete)
        $scope.isAskById = ($scope.category.indexOf("TV") > -1 || $scope.category.indexOf("Movies") > -1 );

        focus('focus-query-box');
        $scope.query = "";

        if (config.searching.categorysizes.enable_category_sizes) {
            var min = config.searching.categorysizes[searchCategory + " min"];
            var max = config.searching.categorysizes[searchCategory + " max"];
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
        SearchService.search($scope.category, $scope.query, $stateParams.tmdbid, $scope.title, $scope.tvdbid, $scope.season, $scope.episode, $scope.minsize, $scope.maxsize, $scope.minage, $scope.maxage).then(function (searchResult) {
            $state.go("search.results", {
                results: searchResult.results,
                indexersearches: searchResult.indexersearches,
                total: searchResult.total,
                resultsCount: searchResult.resultsCount,
                minsize: $scope.minsize,
                maxsize: $scope.maxsize,
                minage: $scope.minage,
                maxage: $scope.maxage
            }, {
                inherit: true
            });
            $scope.tmdbid = undefined;
            $scope.tvdbid = undefined;
        });
    };


    $scope.goToSearchUrl = function () {
        var stateParams = {};
        if ($scope.category.indexOf("Movies") > -1) {
            stateParams.mode = "moviesearch";
            stateParams.title = $scope.title;
            stateParams.mode = "moviesearch";
        } else if ($scope.category.indexOf("TV") > -1) {
            stateParams.mode = "tvsearch";
            if (!_.isUndefined($scope.tvdbid)) {
            }

            if (!_.isUndefined($scope.season)) {
            }
            if (!_.isUndefined($scope.episode)) {
            }
        } else {
            stateParams.mode = "search";
        }
        
        stateParams.tmdbid = $scope.tmdbid;
        stateParams.tvdbid = $scope.tvdbid;
        stateParams.title = $scope.title;
        stateParams.season = $scope.season;
        stateParams.episode = $scope.episode;
        stateParams.query = $scope.query;
        stateParams.minsize = $scope.minsize;
        stateParams.maxsize = $scope.maxsize;
        stateParams.minage = $scope.minage;
        stateParams.maxage = $scope.maxage;
        stateParams.category = $scope.category;

        $state.go("search", stateParams, {inherit: false, notify: true});
    };


    $scope.selectAutocompleteItem = function ($item) {
        $scope.selectedItem = $item;
        $scope.title = $item.label;
        if ($scope.category.indexOf("Movies") > -1) {
            $scope.tmdbid = $item.value;
        } else if ($scope.category.indexOf("TV") > -1) {
            $scope.tvdbid = $item.value;
        }
        $scope.query = "";
        $scope.goToSearchUrl();
    };
    
    $scope.startQuerySearch = function() {
        //Reset values because they might've been set from the last search
        $scope.title = undefined;
        $scope.tmdbid = undefined;
        $scope.tvdbid = undefined;
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
        $scope.availableIndexers = _.filter(cfg.indexers, function (indexer) {
            return indexer.enabled;
        }).map(function (indexer) {
            return {name: indexer.name, activated: true};
        });
        console.log($scope.availableIndexers);
    });


    if ($scope.mode) {
        console.log("Starting search in newly loaded search controller");
        $scope.startSearch();
    }


}

angular
    .module('nzbhydraApp')
    .factory('NzbDownloadService', NzbDownloadService);

function NzbDownloadService($http, ConfigService, CategoriesService) {
    
    var service = {
        download: download 
    };
    
    return service;
    


    function sendNzbAddCommand(guids, category) {
        console.log("Now add nzb with category " + category);        
        return $http.put("internalapi/addnzbs", {guids: angular.toJson(guids), category: category});
    }

    function download (guids) {
        return ConfigService.get().then(function (settings) {

            var category;
            if (settings.downloader.downloader == "nzbget") {
                category = settings.downloader.nzbget.defaultCategory
            } else {
                category = settings.downloader.sabnzbd.defaultCategory
            }

            if (_.isUndefined(category) || category == "" || category == null) {
                return CategoriesService.openCategorySelection().then(function (category) {
                    return sendNzbAddCommand(guids, category)
                });
            } else {
                return sendNzbAddCommand(guids, category)
            }

        });


    }

    
}
NzbDownloadService.$inject = ["$http", "ConfigService", "CategoriesService"];


angular
    .module('nzbhydraApp')
    .service('modalService', modalService);

function modalService() {
    this.open = function (msg) {
        
        //Prevent cirtcular dependency
        var myInjector = angular.injector(["ng", "ui.bootstrap"]);
        var $uibModal = myInjector.get("$uibModal");

        var modalInstance = $uibModal.open({
            template: '<pre>' + msg + '</pre>',
            size: "lg"
        });

        modalInstance.result.then();

    };
}
var HEADER_NAME = 'MyApp-Handle-Errors-Generically';
var specificallyHandleInProgress = false;

nzbhydraapp.factory('RequestsErrorHandler',  ["$q", "growl", "blockUI", "modalService", function ($q, growl, blockUI, modalService) {
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
            blockUI.reset();
            var shouldHandle = (rejection && rejection.config && rejection.config.headers && rejection.config.headers[HEADER_NAME]);
            
            if (shouldHandle) {
                var message = "An error occured :<br>" + rejection.status + ": " + rejection.statusText;

                if (rejection.data) {
                    message += "<br><br>" + rejection.data;
                }
                modalService.open(message);

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
var filters = angular.module('filters', []);

filters.filter('bytes', function() {
	return function(bytes, precision) {
		if (isNaN(parseFloat(bytes)) || !isFinite(bytes) || bytes == 0) return '-';
		if (typeof precision === 'undefined') precision = 1;
		
		var units = ['b', 'kB', 'MB', 'GB', 'TB', 'PB'],
			number = Math.floor(Math.log(bytes) / Math.log(1024));
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
    
    

    function setConfig(newConfig) {
        console.log("Starting setConfig");

        $http.put('internalapi/setsettings', newConfig)
            .then(function (successresponse) {
                console.log("Settings saved. Updating cache");
                config = newConfig;
            }, function (errorresponse) {
                console.log("Error saving settings: " + errorresponse);
            });

    }

    function getConfig() {

        function loadAll() {
            if (!angular.isUndefined(config)) {
                var deferred = $q.defer();
                deferred.resolve(config);
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
            return config;
        });

    }
}
ConfigService.$inject = ["$http", "$q"];
angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);

angular
    .module('nzbhydraApp')
    .config(["formlyConfigProvider", function config(formlyConfigProvider) {
        formlyConfigProvider.extras.removeChromeAutoComplete = true;

        // set templates here
        formlyConfigProvider.setWrapper({
            name: 'horizontalBootstrapLabel',
            template: [
                '<div class="form-group form-horizontal" ng-class="{\'row\': !options.templateOptions.noRow}">',
                '<div style="text-align:right;">',
                '<label for="{{::id}}" class="col-md-7 control-label">',
                '{{to.label}} {{to.required ? "*" : ""}}',
                '</label>',
                '</div>',
                '<div class="col-md-6">',
                '<formly-transclude></formly-transclude>',
                '</div>',
                '<span class="col-md-7 help-block">{{to.help}}</div>',
                '</div>'
            ].join(' ')
        });


        formlyConfigProvider.setWrapper({
            name: 'fieldset',
            template: [
                '<fieldset>',
                '<legend>{{options.templateOptions.label}}</legend>',
                '<formly-transclude></formly-transclude>',
                '</fieldset>'
            ].join(' ')
        });

        formlyConfigProvider.setWrapper({
            name: 'logicalGroup',
            template: [
                '<formly-transclude></formly-transclude>'
            ].join(' ')
        });

        formlyConfigProvider.setType({
            name: 'horizontalInput',
            extends: 'input',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'percentInput',
            template: [
                '<input type="number" class="form-control" placeholder="Percent" ng-model="model[options.key]" ng-pattern="/^[0-9]+(\.[0-9]{1,2})?$/" step="0.01" required />'
            ].join(' ')
        });

        formlyConfigProvider.setType({
            name: 'apiKeyInput',
            template: [
                '<div class="input-group">',
                '<input type="text" class="form-control" ng-model="model[options.key]"/>',
                '<span class="input-group-btn">',
                '<button class="btn " type="button" ng-click="generate()"><span class="glyphicon glyphicon-refresh"></span></button>',
                '</div>'
            ].join(' '),
            controller: function($scope) {
                $scope.generate = function() {
                    $scope.model[$scope.options.key] = Array(31).join((Math.random().toString(36) + '00000000000000000').slice(2, 18)).slice(0, 30);
                }
            }
        });
        

        formlyConfigProvider.setType({
            name: 'testConnection',
            templateUrl: 'button-test-connection.html',
            controller: function ($scope) {
                $scope.message = "";

                var testButton = "#button-test-connection-" + $scope.formId;
                var testMessage = "#message-test-connection-" + $scope.formId;
                function showSuccess() {
                    angular.element(testButton).removeClass("btn-default");
                    angular.element(testButton).removeClass("btn-danger");
                    angular.element(testButton).addClass("btn-success");
                }

                function showError() {
                    angular.element(testButton).removeClass("btn-default");
                    angular.element(testButton).removeClass("btn-success");
                    angular.element(testButton).addClass("btn-danger");
                }

                $scope.testConnection = function () {
                    angular.element(testButton).addClass("glyphicon-refresh-animate");
                    var myInjector = angular.injector(["ng"]);
                    var $http = myInjector.get("$http");
                    var url;
                    var params;
                    if ($scope.to.testType == "downloader") {
                        url = "internalapi/test_downloader";
                        params = {name: $scope.to.downloader, host: $scope.model.host, port: $scope.model.port, ssl: $scope.model.ssl, username: $scope.model.username, password: $scope.model.password};
                        if ($scope.to.downloader == "sabnzbd") {
                            params.apikey = $scope.model.apikey;
                        }
                    } else if ($scope.to.testType == "newznab") {
                        url = "internalapi/test_newznab";
                        params = {host: $scope.model.host, apikey: $scope.model.apikey};
                    }
                    $http.get(url, {params: params}).success(function(result){
                        //Using ng-class and a scope variable doesn't work for some reason, is only updated at second click 
                        if (result.result) {
                            angular.element(testMessage).text("");
                            showSuccess();
                        } else {
                            angular.element(testMessage).text(result.message);
                            showError();
                        }
                        
                    }).error(function() {
                        angular.element(testMessage).text(result.message);
                        showError();
                    }).finally(function() {
                        angular.element(testButton).removeClass("glyphicon-refresh-animate");
                    })
                }
            }
        });

        formlyConfigProvider.setType({
            name: 'horizontalTestConnection',
            extends: 'testConnection',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });
        

        formlyConfigProvider.setType({
            name: 'horizontalApiKeyInput',
            extends: 'apiKeyInput',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'horizontalPercentInput',
            extends: 'percentInput',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });


        formlyConfigProvider.setType({
            name: 'switch',
            template: [
                '<div style="text-align:left"><input bs-switch type="checkbox" ng-model="model[options.key]"/></div>'
            ].join(' ')

        });


        formlyConfigProvider.setType({
            name: 'duoSetting',
            extends: 'input',
            defaultOptions: {
                className: 'col-md-9',
                templateOptions: {
                    type: 'number',
                    noRow: true,
                    label: ''
                }
            }
        });

        formlyConfigProvider.setType({
            name: 'horizontalSwitch',
            extends: 'switch',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'horizontalSelect',
            extends: 'select',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });


        formlyConfigProvider.setType({
            name: 'ui-select-multiple',
            extends: 'select',
            defaultOptions: {
                templateOptions: {
                    optionsAttr: 'bs-options',
                    ngOptions: 'option[to.valueProp] as option in to.options | filter: $select.search',
                    valueProp: 'id',
                    labelProp: 'label'
                }
            },
            templateUrl: 'ui-select-multiple.html'
        });

        formlyConfigProvider.setType({
            name: 'horizontalMultiselect',
            extends: 'ui-select-multiple',
            templateUrl: 'ui-select-multiple.html',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });


        formlyConfigProvider.setType({
            name: 'label',
            template: '<label class="control-label">{{to.label}}</label>'
        });

        formlyConfigProvider.setType({
            name: 'duolabel',
            extends: 'label',
            defaultOptions: {
                className: 'col-md-2',
                templateOptions: {
                    label: '-'
                }
            }
        });


    }]);


function ConfigController($scope, ConfigService, config, CategoriesService) {
    $scope.config = config;

    $scope.submit = submit;

    function submit(form) {
        ConfigService.set($scope.config);
        form.$setPristine();
        CategoriesService.invalidate();
    }
    
    function getNewznabFieldset(index) {
        return {
            wrapper: 'fieldset',
            key: 'newznab' + index,
            templateOptions: {label: 'Newznab ' + index},
            fieldGroup: [
                {
                    key: 'enabled',
                    type: 'horizontalSwitch',
                    templateOptions: {
                        type: 'switch',
                        label: 'Enabled'
                    }
                },
                {
                    key: 'name',
                    type: 'horizontalInput',
                    templateOptions: {
                        type: 'text',
                        label: 'Name',
                        help: 'Used for identification. Changing the name will lose all history and stats!'
                    }
                },
                {
                    key: 'host',
                    type: 'horizontalInput',
                    templateOptions: {
                        type: 'text',
                        label: 'Host',
                        placeholder: 'http://www.someindexer.com'
                    }
                },
                {
                    key: 'apikey',
                    type: 'horizontalInput',
                    templateOptions: {
                        type: 'text',
                        label: 'API Key'
                    }
                },
                {
                    key: 'search_ids',
                    type: 'horizontalMultiselect',
                    templateOptions: {
                        label: 'Search types',
                        options: [
                            {label: 'TVDB', id: 'tvdbid'},
                            {label: 'TVRage', id: 'rid'},
                            {label: 'IMDB', id: 'imdbid'}
                        ]
                    }
                },
                {
                    key: 'score',
                    type: 'horizontalInput',
                    templateOptions: {
                        type: 'number',
                        label: 'Score',
                        help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                    }
                },
                {
                    type: 'horizontalTestConnection',
                    templateOptions: {
                        label: 'Test connection',
                        testType: 'newznab'
                    }
                }
            ]
        };
    }


    $scope.fields = {
        main: [
            {
                wrapper: 'fieldset',
                templateOptions: {label: 'Hosting'},
                fieldGroup: [
                    {
                        key: 'host',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Host',
                            placeholder: 'IPv4 address to bind to'
                        }
                    },
                    {
                        key: 'port',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Port',
                            placeholder: '5050'
                        }
                    },
                    {
                        key: 'ssl',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Use SSL'
                        }
                    },
                    {
                        key: 'sslcert',
                        hideExpression: '!model.ssl',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'SSL certificate file',
                            required: true
                        }
                    },
                    {
                        key: 'sslkey',
                        hideExpression: '!model.ssl',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'SSL key file',
                            required: true
                        }
                    }


                ]
            },
            {
                wrapper: 'fieldset',
                templateOptions: {label: 'Security'},
                fieldGroup: [
                    {
                        key: 'enableAuth',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enable authentication'
                        }
                    },
                    {
                        key: 'username',
                        type: 'horizontalInput',
                        hideExpression: '!model.enableAuth',
                        templateOptions: {
                            type: 'text',
                            label: 'Username',
                            required: true
                        }
                    },
                    {
                        key: 'password',
                        hideExpression: '!model.enableAuth',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'password',
                            label: 'Password',
                            required: true
                        }
                    },
                    {
                        key: 'apikey',
                        type: 'horizontalApiKeyInput',
                        templateOptions: {
                            label: 'API key'
                        }
                    }

                ]
            },
            {
                wrapper: 'fieldset',
                templateOptions: {label: 'Caching'},
                fieldGroup: [
                    {
                        key: 'enableCache',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enable caching'
                        }
                    },
                    {
                        key: 'cacheType',
                        hideExpression: '!model.enableCache',
                        type: 'horizontalSelect',
                        templateOptions: {
                            type: 'select',
                            label: 'Type',
                            options: [
                                {name: 'Memory only', value: 'memory'},
                                {name: 'File sytem', value: 'file'}
                            ]
                        }
                    },
                    {
                        key: 'cacheTimeout',
                        hideExpression: '!model.enableCache',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Cache timeout',
                            help: 'Time after which cache entries will be discarded',
                            addonRight: {
                                text: 'seconds'
                            }
                        }
                    },
                    {
                        key: 'cachethreshold',
                        hideExpression: '!model.enableCache',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Cache threshold',
                            help: 'Max amount of items held in cache',
                            addonRight: {
                                text: 'items'
                            }
                        }
                    },
                    {
                        key: 'cacheFolder',
                        hideExpression: '!model.enableCache || model.cacheType == "memory"',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Cache folder'
                        }
                    }

                ]
            },

            {
                wrapper: 'fieldset',
                key: 'logging',
                templateOptions: {label: 'Logging'},
                fieldGroup: [
                    {
                        key: 'logfile-level',
                        type: 'horizontalSelect',
                        templateOptions: {
                            type: 'select',
                            label: 'Logfile level',
                            options: [
                                {name: 'Critical', value: 'CRITICAL'},
                                {name: 'Error', value: 'ERROR'},
                                {name: 'Warning', value: 'WARNING'},
                                {name: 'Debug', value: 'DEBUG'},
                                {name: 'Info', value: 'INFO'}
                            ]
                        }
                    },
                    {
                        key: 'logfile-filename',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Log file'
                        }
                    },
                    {
                        key: 'consolelevel',
                        type: 'horizontalSelect',
                        templateOptions: {
                            type: 'select',
                            label: 'Console log level',
                            options: [
                                {name: 'Critical', value: 'CRITICAL'},
                                {name: 'Error', value: 'ERROR'},
                                {name: 'Warning', value: 'WARNING'},
                                {name: 'Info', value: 'INFO'},
                                {name: 'Debug', value: 'DEBUG'}
                            ]
                        }
                    }


                ]
            },
            {
                wrapper: 'fieldset',
                templateOptions: {label: 'Other'},
                fieldGroup: [
                    {
                        key: 'debug',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enable debugging',
                            help: "Only do this if you know what and why you're doing it"
                        }
                    },
                    {
                        key: 'startupBrowser',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Open browser on startup'
                        }
                    }
                ]
            }
        ],

        searching: [
            {
                wrapper: 'fieldset',
                templateOptions: {
                    label: 'Indexer access'
                },
                fieldGroup: [
                    {
                        key: 'timeout',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Timeout when accessing indexers',
                            addonRight: {
                                text: 'seconds'
                            }
                        }
                    },
                    {
                        key: 'ignoreTemporarilyDisabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Ignore temporarily disabled',
                            help: "If enabled access to indexers will never be paused after an error occurred"
                        }
                    },
                    {
                        key: 'generate_queries',
                        type: 'horizontalMultiselect',
                        templateOptions: {
                            label: 'Generate queries',
                            options: [
                                {label: 'Internal searches', id: 'internal'},
                                {label: 'API searches', id: 'external'}
                            ],
                            help: "Generate queries for indexers which do not support ID based searches"
                        }
                    }
                ]
            },
            {
                wrapper: 'fieldset',
                templateOptions: {
                    label: 'Result processing'
                },
                fieldGroup: [
                    {
                        key: 'htmlParser',
                        type: 'horizontalSelect',
                        templateOptions: {
                            type: 'select',
                            label: 'Type',
                            options: [
                                {name: 'Default BS (slow)', value: 'html.parser'},
                                {name: 'LXML (faster, needs to be installed separately)', value: 'lxml'}
                            ]
                        }
                    },
                    {
                        key: 'duplicateSizeThresholdInPercent',
                        type: 'horizontalPercentInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Duplicate size threshold',
                            addonRight: {
                                text: '%'
                            }

                        }
                    },
                    {
                        key: 'duplicateAgeThreshold',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Duplicate age threshold',
                            addonRight: {
                                text: 'seconds'
                            }
                        }
                    }
                ]
            },

            {
                wrapper: 'fieldset',
                key: 'categorysizes',
                templateOptions: {label: 'Category sizes'},
                fieldGroup: [

                    {
                        key: 'enable_category_sizes',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Category sizes',
                            help: "Preset min and max sizes depending on the selected category"
                        }
                    },
                    {
                        wrapper: 'logicalGroup',
                        hideExpression: '!model.enable_category_sizes',
                        fieldGroup: [
                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'Movies'
                                },
                                fieldGroup: [
                                    {
                                        key: 'moviesmin',
                                        type: 'duoSetting',
                                        templateOptions: {
                                            addonRight: {
                                                text: 'MB'
                                            }
                                        }
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'moviesmax',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },
                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'Movies HD'
                                },
                                fieldGroup: [
                                    {
                                        key: 'movieshdmin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'movieshdmax',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },
                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'Movies SD'
                                },
                                fieldGroup: [
                                    {
                                        key: 'moviessdmin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'movieshdmin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },

                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'TV'
                                },
                                fieldGroup: [
                                    {
                                        key: 'tvmin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'tvmax',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },

                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'TV HD'
                                },
                                fieldGroup: [
                                    {
                                        key: 'tvhdmin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'tvhdmax',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },

                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'TV SD'
                                },
                                fieldGroup: [
                                    {
                                        key: 'tvsdmin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'tvsdmax',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },

                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'Audio'
                                },
                                fieldGroup: [
                                    {
                                        key: 'audiomin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'audiomax',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },

                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'Audio FLAC'
                                },
                                fieldGroup: [
                                    {
                                        key: 'flacmin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'flacmax',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },

                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'Audio MP3'
                                },
                                fieldGroup: [
                                    {
                                        key: 'mp3min',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'mp3max',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },

                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'Console'
                                },
                                fieldGroup: [
                                    {
                                        key: 'consolemin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'consolemax',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },

                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'PC'
                                },
                                fieldGroup: [
                                    {
                                        key: 'pcmin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'pcmax',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            },

                            {
                                wrapper: 'horizontalBootstrapLabel',
                                templateOptions: {
                                    label: 'XXX'
                                },
                                fieldGroup: [
                                    {
                                        key: 'xxxmin',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    },
                                    {
                                        type: 'duolabel'
                                    },
                                    {
                                        key: 'xxxmax',
                                        type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                    }
                                ]
                            }
                        ]
                    }

                ]
            }

        ],

        downloader: [
            {
                key: 'downloader',
                type: 'horizontalSelect',
                templateOptions: {
                    type: 'select',
                    label: 'Downloader',
                    options: [
                        {name: 'None', value: 'none'},
                        {name: 'NZBGet', value: 'nzbget'},
                        {name: 'SABnzbd', value: 'sabnzbd'}
                    ]
                }
            },
            {
                key: 'nzbaccesstype',
                type: 'horizontalSelect',
                templateOptions: {
                    type: 'select',
                    label: 'NZB access type',
                    options: [
                        {name: 'Proxy NZBs from indexer', value: 'serve'},
                        {name: 'Redirect to the indexer', value: 'redirect'},
                        {name: 'Use direct links', value: 'direct'}
                    ],
                    help: "How external access to NZBs is provided. Proxying NZBs is recommended."
                }
            },
            {
                key: 'nzbAddingType',
                type: 'horizontalSelect',
                templateOptions: {
                    type: 'select',
                    label: 'NZB adding type',
                    options: [
                        {name: 'Send link', value: 'link'},
                        {name: 'Upload NZB', value: 'nzb'}
                    ],
                    help: "How NZBs are added to the downloader, either by sending a link to the NZB or by uploading the NZB data"
                }
            },
            {
                wrapper: 'fieldset',
                key: 'nzbget',
                hideExpression: 'model.downloader!="nzbget"',
                templateOptions: {label: 'NZBGet'},
                fieldGroup: [
                    {
                        key: 'host',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Host'
                        }
                    },
                    {
                        key: 'port',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Port',
                            placeholder: '5050'
                        }
                    },
                    {
                        key: 'ssl',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Use SSL'
                        }
                    },
                    {
                        key: 'username',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Username'
                        }
                    },
                    {
                        key: 'password',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'password',
                            label: 'Password'
                        }
                    },
                    {
                        key: 'defaultCategory',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Default category',
                            help: 'When adding NZBs this category will be used instead of asking for the category'
                        }
                    },
                    {
                        type: 'horizontalTestConnection',
                        templateOptions: {
                            label: 'Test connection',
                            testType: 'downloader',
                            downloader: 'nzbget'
                        }
                    }


                ]
            },
            {
                wrapper: 'fieldset',
                key: 'sabnzbd',
                hideExpression: 'model.downloader!="sabnzbd"',
                templateOptions: {label: 'SABnzbd'},
                fieldGroup: [
                    {
                        key: 'host',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Host'
                        }
                    },
                    {
                        key: 'port',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Port',
                            placeholder: '5050'
                        }
                    },
                    {
                        key: 'ssl',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Use SSL'
                        }
                    },
                    {
                        key: 'username',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Username',
                            help: 'Usually not needed when an API key is used'
                        }
                    },
                    {
                        key: 'password',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'password',
                            label: 'Password',
                            help: 'Usually not needed when an API key is used'
                        }
                    },
                    {
                        key: 'apikey',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'API Key'
                        }
                    },
                    {
                        key: 'defaultCategory',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Default category',
                            help: 'When adding NZBs this category will be used instead of asking for the category'
                        }
                    },
                    {
                        type: 'horizontalTestConnection',
                        templateOptions: {
                            label: 'Test connection',
                            testType: 'downloader',
                            downloader: 'sabnzbd'
                        }
                    }


                ]
            }
        ],

        indexers: [
            {
                wrapper: 'fieldset',
                key: 'Binsearch',
                templateOptions: {label: 'Binsearch'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },
            {
                wrapper: 'fieldset',
                key: 'NZBClub',
                templateOptions: {label: 'NZBClub'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }

                ]
            },
            {
                wrapper: 'fieldset',
                key: 'NZBIndex',
                templateOptions: {label: 'NZBIndex'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'generalMinSize',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Min size',
                            help: 'NZBIndex returns a lot of crap with small file sizes. Set this value and all smaller results will be filtered out no matter the category'
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },
            {
                wrapper: 'fieldset',
                key: 'Womble',
                templateOptions: {label: 'Womble'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },

            getNewznabFieldset(1),
            getNewznabFieldset(2),
            getNewznabFieldset(3),
            getNewznabFieldset(4),
            getNewznabFieldset(5),
            getNewznabFieldset(6)
            
        ]
    };

    $scope.tabs = [
        {
            name: 'Main',
            model: $scope.config.main,
            fields: $scope.fields.main,
            active: true
        },
        {
            name: 'Searching',
            model: $scope.config.searching,
            fields: $scope.fields.searching,
            active: false
        },
        {
            name: 'Downloader',
            model: $scope.config.downloader,
            fields: $scope.fields.downloader,
            active: false
        },
        {
            name: 'Indexers',
            model: $scope.config.indexers,
            fields: $scope.fields.indexers,
            active: false
        }
    ];

    
    $scope.isSavingNeeded = function(form) {
        return form.$dirty && !form.$submitted;
    }
}
ConfigController.$inject = ["$scope", "ConfigService", "config", "CategoriesService"];



angular
    .module('nzbhydraApp')
    .factory('CategoriesService', CategoriesService);

function CategoriesService($http, $q, $uibModal) {

    var categories;
    var selectedCategory;
    
    var service = {
        get: getCategories,
        invalidate: invalidate,
        select : select,
        openCategorySelection: openCategorySelection 
    };
    
    return service;
    

    function getCategories() {

        function loadAll() {
            if (!angular.isUndefined(categories)) {
                var deferred = $q.defer();
                deferred.resolve(categories);
                return deferred.promise;
            }

            return $http.get('internalapi/getcategories')
                .then(function (categoriesResponse) {
                    console.log("Updating downloader categories cache");
                    categories = categoriesResponse.data;
                    return categoriesResponse.data;
                });
        }

        return loadAll().then(function (categories) {
            return categories.categories;
        });
    }

    var deferred;
    
    function openCategorySelection() {
        $uibModal.open({
            templateUrl: 'static/html/directives/addable-nzb-modal.html',
            controller: 'CategorySelectionController',
            size: "sm",
            resolve: {
                categories: getCategories
            }
        });
        deferred = $q.defer();
        return deferred.promise;
    }
    
    function select(category) {
        selectedCategory = category;
        console.log("Selected category " + category);
        deferred.resolve(category);
    }
    
    function invalidate() {
        console.log("Invalidating categories");
        categories = undefined;
    }
}
CategoriesService.$inject = ["$http", "$q", "$uibModal"];

angular
    .module('nzbhydraApp').controller('CategorySelectionController', ["$scope", "$uibModalInstance", "CategoriesService", "categories", function ($scope, $uibModalInstance, CategoriesService, categories) {
    console.log(categories);
    $scope.categories = categories;
    $scope.select = function (category) {
        CategoriesService.select(category);
        $uibModalInstance.close($scope);
    }
}]);
angular
    .module('nzbhydraApp')
    .controller('AboutController', AboutController);

function AboutController($scope, $http, versionsPromise) {

    $scope.currentVersion = versionsPromise.data.currentVersion;
    $scope.repVersion = versionsPromise.data.repVersion;
    $scope.updateAvailable = versionsPromise.data.updateAvailable;

}
AboutController.$inject = ["$scope", "$http", "versionsPromise"];

//# sourceMappingURL=nzbhydra.js.map
