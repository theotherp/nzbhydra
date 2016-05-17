angular
    .module('nzbhydraApp')
    .controller('HeaderController', HeaderController);

function HeaderController($scope, HydraAuthService, bootstrapped) {

    if (HydraAuthService.isLoggedIn()) {
        var rights = HydraAuthService.getUserRights();
        $scope.maySeeAdmin = rights.maySeeAdmin;
        $scope.maySeeStats = rights.maySeeStats;
    } else {
        $scope.maySeeAdmin = bootstrapped.showAdmin;
        $scope.maySeeStats = bootstrapped.showStats;
    }
    
    $scope.$on("user:loggedIn", function (event, data) {
        $scope.maySeeAdmin = data.maySeeAdmin;
        $scope.maySeeStats = data.maySeeStats;
    });
    
}
