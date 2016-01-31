angular
    .module('nzbhydraApp')
    .directive('hydralog', hydralog);

function hydralog() {
    return {
        template: '<div cg-busy="{promise:logPromise,message:\'Loading log file\'}"><pre ng-bind-html="log" style="text-align: left"></pre></div>',
        controller: controller
    };

    function controller($scope, $http, $sce) {
        $scope.logPromise = $http.get("internalapi/getlogs").success(function (data) {
            $scope.log = $sce.trustAsHtml(data.log);
        });

    }
}

