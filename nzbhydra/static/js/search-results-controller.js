angular
    .module('nzbhydraApp')
    .controller('SearchResultsController', SearchResultsController);


//SearchResultsController.$inject = ['blockUi'];
function SearchResultsController($stateParams, $scope, $q, $timeout, blockUI, blockUIConfig) {

    $scope.sortPredicate = "age_days";
    $scope.sortReversed = false;

    $scope.results = $stateParams.results;
    $scope.filteredResults = $stateParams.results;
    $scope.providersearches = $stateParams.providersearches;

    $scope.providerDisplayState = [];

    //Initially set visibility of all found providers to true
    _.forEach($scope.providersearches, function (ps) {
        $scope.providerDisplayState[ps.provider] = true;
    });


    //Returns the content of the property (defined by the current sortPredicate) of the first group element 
    $scope.firstResultPredicate = firstResultPredicate;
    function firstResultPredicate(item) {
        return item[0][$scope.sortPredicate];
    }

    //Returns the unique group identifier which allows angular to keep track of the grouped search results even after filtering, making filtering by providers a lot faster (albeit still somewhat slow...)  
    $scope.groupId = groupId;
    function groupId(item) {
        return item[0].count;
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
        startBlocking("Sorting. Sorry...").then(function () {
            if (predicate == $scope.sortPredicate) {
                $scope.sortReversed = !$scope.sortReversed;
            } else {
                $scope.sortReversed = reversedDefault;
            }
            $scope.sortPredicate = predicate;

            var filteredResults = _.sortBy($scope.filteredResults, function(group) {
                return group[0][$scope.sortPredicate];
            });
            if ($scope.sortReversed) {
                filteredResults.reverse();
            }
            
            //Hack: We add a dummy group to the very end of the result groups. That way we make sure that the last row of ng-repeat is actually rendered and we know when to stop
            //blocking. If we don't do that when filtering out a provider to which the last group/row does not belong it will not be re-rendered. Which is usually good but not
            //when we want to know when angular is done.
            filteredResults.push([{age_days: 99999, title: "DUMMY", category: "", provider: "", size: 0}]);
            $scope.filteredResults = filteredResults; 
            
        });
    

    }

    //Clear the blocking
    $scope.stopBlocking = stopBlocking;
    function stopBlocking() {
        //Remove the dummy row that was added when filtering/sorting but only if we actually added it
        if ($scope.filteredResults[$scope.filteredResults.length-1][0].title == "DUMMY") {
            $scope.filteredResults.splice($scope.filteredResults.length - 1, 1);
            console.log("Removed dummy row");
        }
        blockUI.reset();
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


        console.log("Adding dummy");
        filteredResults.push([{age_days: 0, title: "DUMMY", category: "", provider: "", size: 0}]);
        $scope.filteredResults = filteredResults;
        
        })
    }

}


Array.prototype.remove = function (from, to) {
    var rest = this.slice((to || from) + 1 || this.length);
    this.length = from < 0 ? this.length + from : from;
    return this.push.apply(this, rest);
};
