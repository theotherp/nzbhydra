angular
    .module('nzbhydraApp')
    .directive('addableNzb', addableNzb);

function addableNzb() {
    return {
        templateUrl: 'static/html/directives/addable-nzb.html',
        require: '^guid',
        scope: {
            guid: "="
        },
        controller: ['$scope', '$http', controller]
    };

    function controller($scope, $http) {
        $scope.classname = "nzb";

        $scope.add = function () {
            $scope.classname = "nzb-spinning";
            $http.put("internalapi/addnzbs", {guids: angular.toJson([$scope.guid])}).success(function (response) {
                if (response.success) {
                    $scope.classname = "nzb-success";
                } else {
                    $scope.classname = "nzb-error";
                }
                
            }).error(function () {
                
            });
        }
        
    }
}