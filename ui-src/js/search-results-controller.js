angular
    .module('nzbhydraApp')
    .controller('SearchResultsController', SearchResultsController);


//SearchResultsController.$inject = ['blockUi'];
function SearchResultsController($stateParams, $scope, $q, $timeout, blockUI, SearchService, $http, $uibModal, $sce, growl) {

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
                    return $scope.sortReversed ?  -sortPredicateValue : sortPredicateValue;
                });
                //Now sort the hash group by indexer score (inverted) so that the result with the highest indexer score is shown on top (or as the only one of a hash group if it's collapsed)
                sortedHashGroup = _.sortBy(sortedHashGroup, function (item) {
                    return item.indexerscore * -1;
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
            //Remove elements of which the indexer is currently hidden    
            .filter(getItemIndexerDisplayState)
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