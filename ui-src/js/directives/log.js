angular
    .module('nzbhydraApp')
    .directive('hydralog', hydralog);

function hydralog() {
    return {
        //template: '<div cg-busy="{promise:logPromise,message:\'Loading log file\'}"><pre ng-bind-html="log" style="text-align: left; height: 65vh; overflow-y: scroll"></pre></div>',
        templateUrl: "static/html/directives/log.html",

        controller: controller
    };

    function controller($scope, $http, $sce, $interval, localStorageService) {

        $scope.tailInterval = null;
        $scope.doUpdateLog = localStorageService.get("doUpdateLog") != null ? localStorageService.get("doUpdateLog") : false;
        $scope.doTailLog = localStorageService.get("doTailLog") != null ? localStorageService.get("doTailLog") : false;


        function getAndShowLog() {
            return $http.get("internalapi/getlogs").success(function (data) {
                $scope.log = $sce.trustAsHtml(data.log);
            });
        }

        $scope.logPromise = getAndShowLog();

        $scope.scrollToBottom = function () {
            //$window.scrollTo(0, 1000000);
            document.getElementById("logfile").scrollTop = 10000000;
            document.getElementById("logfile").scrollTop = 10000001;
            console.log("Scrolling to bottom");
        };

        function startUpdateLogInterval() {
            $scope.tailInterval = $interval(function () {
                getAndShowLog();
                if ($scope.doTailLog) {
                    $scope.scrollToBottom();
                }
            }, 5000);
        }

        $scope.toggleUpdate = function() {
            if ($scope.doUpdateLog) {
                startUpdateLogInterval();
            } else if ($scope.tailInterval != null) {
                console.log("Cancelling");
                $interval.cancel($scope.tailInterval);
                localStorageService.set("doTailLog", false);
                $scope.doTailLog = false;
            }
            localStorageService.set("doUpdateLog", $scope.doUpdateLog);
        };

        $scope.toggleTailLog = function () {
            localStorageService.set("doTailLog", $scope.doTailLog);
        };

        if ($scope.doUpdateLog) {
          startUpdateLogInterval();
        }

    }
}

