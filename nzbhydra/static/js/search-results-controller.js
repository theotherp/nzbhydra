angular
    .module('nzbhydraApp')
    .controller('SearchResultsController', SearchResultsController);





//SearchResultsController.$inject = ['$stateParams'];
function SearchResultsController($stateParams, $scope) {
    
    console.log("Got state params");
    console.log($stateParams);
    
    $scope.results = $stateParams.results;
    $scope.providersearches = $stateParams.providersearches;
    
    
}
