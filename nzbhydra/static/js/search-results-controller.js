angular
    .module('nzbhydraApp')
    .controller('SearchResultsController', SearchResultsController);


//SearchResultsController.$inject = ['blockUi'];
function SearchResultsController($stateParams, $scope, $q, $timeout, blockUI, SearchService) {

    $scope.sortPredicate = "epoch";
    $scope.sortReversed = false;

    $scope.limitTo = 101;
    $scope.offset = 0;

    $scope.results = $stateParams.results;
    $scope.total = $stateParams.total;
    $scope.countLoaded = Object.keys($scope.results).length;
    setSorting($scope.sortPredicate, $scope.sortReversed);
    
    $scope.filteredResults = $stateParams.results;
    $scope.providersearches = $stateParams.providersearches;

    $scope.providerDisplayState = []; //Stores if a provider's results should be displayed or not

    $scope.providerResultsInfo = {}; //Stores information about the provider's results like how many we already retrieved

    //Initially set visibility of all found providers to true
    _.forEach($scope.providersearches, function (ps) {
        $scope.providerDisplayState[ps.provider] = true;
    });


    _.forEach($scope.providersearches, function (ps) {
        $scope.providerResultsInfo[ps.provider] = {loadedResults: ps.loaded_results};
    });


    //Returns the content of the property (defined by the current sortPredicate) of the first group element 
    $scope.firstResultPredicate = firstResultPredicate;
    function firstResultPredicate(item) {
        return item[0][$scope.sortPredicate];
    }

    //Returns the unique group identifier which allows angular to keep track of the grouped search results even after filtering, making filtering by providers a lot faster (albeit still somewhat slow...)  
    $scope.groupId = groupId;
    function groupId(item) {
        return item[0].hash;
    }

    //Block the UI and return after timeout. This way we make sure that the blocking is done before angular starts updating the model/view. There's probably a better way to achieve that?
    function startBlocking(message) {
        console.log("Blocking");
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
        
            if (predicate == $scope.sortPredicate) {
                $scope.sortReversed = !$scope.sortReversed;
            } else {
                $scope.sortReversed = reversedDefault;
            }
            $scope.sortPredicate = predicate;
            $scope.filteredResults = sortAndFilter($scope.results);
        
    }

    function addDummyRow(filteredResults) {
        var possibleDummyIndex = _.min([$scope.limitTo-1, filteredResults.length]);
        console.log("$scope.limitTo:" + $scope.limitTo + ", filteredResults.length:" +  filteredResults.length);
        filteredResults.splice(possibleDummyIndex, 0, [{age_days: 99999, title: "DUMMY", category: "", provider: "", size: 0, count: 99999}]);
        console.log("Added dummy row at location " + possibleDummyIndex);
        return filteredResults;
    }

    function sortAndFilter(results) {
        var filteredResults = _.sortBy(results, function (group) {
            return group[0][$scope.sortPredicate];
        });
        if ($scope.sortReversed) {
            filteredResults.reverse();
        }

        //Hack: We add a dummy group to the very end of the result groups. That way we make sure that the last row of ng-repeat is actually rendered and we know when to stop
        //blocking. If we don't do that when filtering out a provider to which the last group/row does not belong it will not be re-rendered. Which is usually good but not
        //when we want to know when angular is done.
        filteredResults = addDummyRow(filteredResults);
        return filteredResults;
    }

    function removeDummyRow() {
        var possibleDummyIndex = _.min([$scope.limitTo-1, $scope.filteredResults.length-1]); //If the row was added the length of filteredResults is increased by one so we subtract 1 
        console.log("$scope.limitTo:" + $scope.limitTo + ", filteredResults.length:" +  $scope.filteredResults.length-1);
        if (!_.isUndefined($scope.filteredResults[possibleDummyIndex]) && $scope.filteredResults[possibleDummyIndex][0].title == "DUMMY") {
            $scope.filteredResults.splice(possibleDummyIndex, 1);
            console.log("Removed dummy row at location " + possibleDummyIndex);
        } else {
            console.log("Did not find dummy row at position " + possibleDummyIndex);
        }
    }

    //Clear the blocking
    $scope.stopBlocking = stopBlocking;
    function stopBlocking() {        
        removeDummyRow();
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
                angular.extend($scope.results, data.results);
                $scope.filteredResults = sortAndFilter($scope.results);
                $scope.total = data.total;
                $scope.countLoaded = Object.keys($scope.results).length;
                
                stopBlocking();
            });
        });
    }


    //Filters the results according to new visibility settings.
    $scope.toggleProviderDisplay = toggleProviderDisplay;
    function toggleProviderDisplay() {
        startBlocking("Filtering. Sorry...").then(function () {
            var filteredResults = [];

            function filterByProviderVisibility(item) {
                return $scope.providerDisplayState[item.provider];
            }

            function addFilteredGroups(group) {
                var filteredGroup = _.filter(group, filterByProviderVisibility);
                if (filteredGroup.length > 0) {
                    filteredResults.push(filteredGroup);
                }
            }

            _.each($scope.results, addFilteredGroups);

            filteredResults = addDummyRow(filteredResults);
            $scope.filteredResults = filteredResults;

        })
    }
    
    $scope.countResults = countResults;
    function countResults() {
        return $scope.results.length;
    }

}