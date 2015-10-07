angular
    .module('nzbhydraApp')
    .controller('SearchResultsController', SearchResultsController);

//SearchResultsController.$inject = ['$stateParams'];
function SearchResultsController($stateParams, $scope) {

    $scope.sortPredicate = "title";
    $scope.sortReversed = true;

    $scope.results = $stateParams.results;
    $scope.filteredResults = $stateParams.results;
    $scope.providersearches = $stateParams.providersearches;

    $scope.providerDisplayState = [];

    _.forEach($scope.providersearches, function (ps) {
        $scope.providerDisplayState[ps.provider] = true;
        console.log("Set visibility of " + ps.provider + " to true");
    });


    $scope.firstResultPredicate = firstResultPredicate;
    function firstResultPredicate(item) {
        return item[0][$scope.sortPredicate];
    }


    $scope.setSorting = setSorting;
    function setSorting(predicate, reversedDefault) {
        if (predicate == $scope.sortPredicate) {
            $scope.sortReversed = !$scope.sortReversed;
        } else {
            $scope.sortReversed = reversedDefault;
        }
        $scope.sortPredicate = predicate;
    }

    $scope.shouldResultVisible = shouldResultVisible;
    function shouldResultVisible() {
        return function (item) {
            return !(item.provider in $scope.hiddenProviders);
        }
    }

    $scope.toggleProviderDisplay = toggleProviderDisplay;
    function toggleProviderDisplay() {
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

        $scope.filteredResults = filteredResults;


    }


//$scope.firstShownResult = firstShownResult;
//function firstShownResult(resultswithduplicates) {
//    var firstShownResult = _.find(resultswithduplicates, function find(item) {
//        return shouldResultVisible(item);
//    });
//    if (!_.isUndefined(firstShownResult)) {
//        console.log("First visible item in group: " + firstShownResult);
//        return [firstShownResult];
//    } else {
//        console.log("No items viisible in group");
//        return [];
//    }
//}


}


Array.prototype.remove = function (from, to) {
    var rest = this.slice((to || from) + 1 || this.length);
    this.length = from < 0 ? this.length + from : from;
    return this.push.apply(this, rest);
};