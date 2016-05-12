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
            t = dateFilter(t, 'yyyy-MM-dd HH:mm');
            return t;
        } else {
            return "";
        }
    }
}

angular
    .module('nzbhydraApp')
    .filter('reformatDate', reformatDate);

function reformatDate() {
    return function (date) {
        //Date in database is saved as UTC without timezone information
        return moment(date, "ddd, D MMM YYYY HH:mm:ss z").utcOffset(240).format("YYYY-MM-DD HH:mm");
        
    }
}