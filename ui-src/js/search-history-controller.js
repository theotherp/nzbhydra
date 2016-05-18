angular
    .module('nzbhydraApp')
    .controller('SearchHistoryController', SearchHistoryController);


function SearchHistoryController($scope, $state, StatsService, history) {
    $scope.type = "All";
    $scope.limit = 100;
    $scope.pagination = {
        current: 1
    };
    $scope.isLoaded = true;
    $scope.searchRequests = history.data.searchRequests;
    $scope.totalRequests = history.data.totalRequests;


    $scope.pageChanged = function (newPage) {
        getSearchRequestsPage(newPage);
    };

    $scope.changeType = function (type) {
        $scope.type = type;
        getSearchRequestsPage($scope.pagination.current);
    };

    function getSearchRequestsPage(pageNumber) {
        StatsService.getSearchHistory(pageNumber, $scope.limit, $scope.type).then(function (history) {
            $scope.searchRequests = history.data.searchRequests;
            $scope.totalRequests = history.data.totalRequests;
            $scope.isLoaded = true;
        });
    }

    $scope.openSearch = function (request) {
        var stateParams = {};
        if (request.identifier_key == "imdbid") {
            stateParams.imdbid = request.identifier_value;
        } else if (request.identifier_key == "tvdbid" || request.identifier_key == "rid") {
            if (request.identifier_key == "rid") {
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
        if (request.type == "tv") {
            stateParams.mode = "tvsearch"
        } else if (request.type == "tv") {
            stateParams.mode = "moviesearch"
        } else {
            stateParams.mode = "search"
        }

        if (request.category != "") {
            stateParams.category = request.category;
        }

        stateParams.category = request.category;

        $state.go("root.search", stateParams, {inherit: false});
    };

    $scope.formatQuery = function (request) {
        if (request.movietitle != null) {
            return request.movietitle;
        }
        if (request.tvtitle != null) {
            return request.tvtitle;
        }
        return request.query;
    }


}
