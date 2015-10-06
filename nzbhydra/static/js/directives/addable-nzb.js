angular
    .module('nzbhydraApp')
    .directive('addableNzb', addableNzb);

function addableNzb() {
    return {
        templateUrl: '/static/html/directives/addable-nzb.html',
        require: '^item',
        scope: {
            item: "="
        },
        controller: ['$scope', '$http', controller]
    }

    function controller($scope, $http) {
        $scope.classname = "nzb";

        $scope.add = function () {
            $scope.classname = "nzb-spinning";
            var uri = new URI("/internalapi/addnzb");
            uri.addQuery("title", $scope.item.title);
            uri.addQuery("providerguid", $scope.item.providerguid);
            uri.addQuery("provider", $scope.item.provider);
            $http.get(uri).success(function () {
                $scope.classname = "nzb-success";
            }).error(function () {
                $scope.classname = "nzb-error";
            });
        }
        
    }
}