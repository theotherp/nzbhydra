angular
    .module('nzbhydraApp')
    .controller('SearchHistoryController', SearchHistoryController);


function SearchHistoryController($scope, $state, StatsService, history, $filter) {
    $scope.type = "All";
    $scope.limit = 100;
    $scope.pagination = {
        current: 1
    };
    $scope.isLoaded = true;
    $scope.searchRequests = history.data.searchRequests;
    $scope.totalRequests = history.data.totalRequests;

    var columnDefs = [
        {
            headerName: "Date",
            field: "time",
            sort: "desc",
            cellRenderer: function (date) {
                return moment.utc(date.value, "ddd, D MMM YYYY HH:mm:ss z").local().format("YYYY-MM-DD HH:mm")
            },
            filterParams: {apply: true},
            width: 150,
            suppressSizeToFit: true
        },
        {
            headerName: "Query",
            field: "query",
            filterParams: {apply: true, newRowsAction: "keep"}
        },
        {
            headerName: "Category",
            field: "category",
            filterParams: {apply: true, newRowsAction: "keep"},
            width: 110,
            suppressSizeToFit: true
        },
        {
            headerName: "Additional parameters",
            field: "additional",
            filterParams: {apply: true, newRowsAction: "keep"},
            cellRenderer: function (params) {
                return _formatAdditional(params.data);
            },
            suppressSorting: true
        },
        {
            headerName: "Access",
            field: "internal",
            filterParams: {apply: true, newRowsAction: "keep"},
            cellRenderer: function (data) {
                return data.value ? "Internal" : "API";
            },
            width: 100,
            suppressSizeToFit: true
        },
        {
            headerName: "Username",
            field: "username",
            filterParams: {apply: true, newRowsAction: "keep"},
        }
    ];


    $scope.gridOptions = {
        columnDefs: columnDefs,
        rowModelType: "pagination",
        debug: false,
        enableColResize: true,
        enableServerSideSorting: true,
        enableServerSideFilter: true,
        paginationPageSize: 500,
        suppressRowClickSelection: true,
        datasource: {
            getRows: function (params) {
                var page = Math.floor(params.startRow / 500) + 1;
                var limit = params.endRow - params.startRow;
                console.log(params);
                StatsService.getSearchHistory(page, limit, params.sortModel, params.filterModel).then(function (history) {
                    // $scope.searchRequests = history.data.searchRequests;
                    // $scope.totalRequests = history.data.totalRequests;
                    // $scope.isLoaded = true;
                    params.successCallback(history.data.searchRequests, history.data.totalRequests);
                    $scope.gridOptions.api.sizeColumnsToFit();
                    $scope.gridOptions.api.sizeColumnsToFit();
                });

            }
        }
    };


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
            stateParams.mode = "movie"
        } else {
            stateParams.mode = "search"
        }

        if (request.movietitle != null) {
            stateParams.title = request.movietitle;
        }
        if (request.tvtitle != null) {
            stateParams.title = request.tvtitle;
        }

        if (request.category) {
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

        if (!request.query && !request.identifier_key && !request.season && !request.episode) {
            return "Update query";
        }
        return request.query;
    };

    $scope.formatAdditional = _formatAdditional;

    function _formatAdditional(request) {
        var result = [];
        //ID key: ID value
        //season
        //episode
        //author
        //title
        if (request.identifier_key) {
            var href;
            var key;
            if (request.identifier_key == "imdbid") {
                key = "IMDB ID";
                href = "https://www.imdb.com/title/tt"
            } else if (request.identifier_key == "tvdbid") {
                key = "TVDB ID";
                href = "https://thetvdb.com/?tab=series&id="
            } else if (request.identifier_key == "rid") {
                key = "TVRage ID";
                href = "internalapi/redirect_rid?rid="
            } else if (request.identifier_key == "tmdb") {
                key = "TMDV ID";
                href = "https://www.themoviedb.org/movie/"
            }
            href = href + request.identifier_value;
            href = $filter("dereferer")(href);
            result.push(key + ": " + '<a target="_blank" href="' + href + '">' + request.identifier_value + "</a>");
        }
        if (request.season) {
            result.push("Season: " + request.season);
        }
        if (request.episode) {
            result.push("Episode: " + request.episode);
        }
        if (request.author) {
            result.push("Author: " + request.author);
        }
        if (request.title) {
            result.push("Title: " + request.title);
        }
        return result.join(", ");
    }


}
