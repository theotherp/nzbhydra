angular
    .module('nzbhydraApp')
    .controller('SearchHistoryController', SearchHistoryController);


function SearchHistoryController($scope, $state, history, growl, SearchHistoryService) {
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
            cellRenderer: function (params) {
                return _formatQuery(params.data);
            },
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
        angularCompileRows: true,
        datasource: {
            getRows: function (params) {
                var page = Math.floor(params.startRow / 500) + 1;
                var limit = params.endRow - params.startRow;
                SearchHistoryService.getSearchHistory(page, limit, params.sortModel, params.filterModel).then(function (history) {
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
        SearchHistoryService.getSearchHistory(pageNumber, $scope.limit, $scope.type).then(function (history) {
            $scope.searchRequests = history.data.searchRequests;
            $scope.totalRequests = history.data.totalRequests;
            $scope.isLoaded = true;
        });
    }

    $scope.repeatSearch = function (searchRequestIndex) {
        if (searchRequestIndex == -1) {
            growl.error("Error while repeating search, sorry");
        } else {
            var stateParams = SearchHistoryService.getStateParamsForRepeatedSearch($scope.searchRequests[searchRequestIndex]);
            $state.go("root.search", stateParams, {inherit: false});
        }
    };


    $scope.formatAdditional = _formatAdditional;

    function _formatAdditional(request) {
        return SearchHistoryService.formatRequest(request, true, false, false, false);
    }

    $scope.formatQuery = _formatQuery;

    function _formatQuery(request) {
        var query = '';
        var generatedTitle = true;
        if (request.movietitle != null) {
            query = request.movietitle;
        } else if (request.tvtitle != null) {
            query = request.tvtitle;
        } else if (!request.query) {
            if (!request.identifier_key && !request.season && !request.episode) {
                query = "Update query";
            }
        } else {
            query = request.query;
            generatedTitle = false;
        }
        if (request.identifier_key && !request.tvtitle && !request.movietitle) {
            query = "Unknown title";
        }

        //The "request" object won't be available later when the function is called so we pass the index in the search requests
        var searchRequestIndex = _.findIndex($scope.searchRequests, function (other, index) {
            if (request.time == other.time) {
                return true;
            }
        });
        var html = '<a href="" ng-click="repeatSearch(' + searchRequestIndex + ')"><span class="glyphicon glyphicon-search" style="margin-right: 5px" uib-tooltip="Click to repeat search" tooltip-placement="top" tooltip-trigger="mouseenter"></span></a>';
        if (generatedTitle) {
            html += '<span class="history-title">' + query + '</span>';
        } else {
            html += query;
        }


        return html;

    }


}
