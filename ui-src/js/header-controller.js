angular
    .module('nzbhydraApp')
    .controller('HeaderController', HeaderController);

function HeaderController($scope, $state, HydraAuthService, ConfigService, bootstrapped) {
    
    $scope.showLogout = false;

    if (HydraAuthService.isLoggedIn()) {
        var rights = HydraAuthService.getUserRights();
        $scope.maySeeAdmin = rights.maySeeAdmin;
        $scope.maySeeStats = rights.maySeeStats;
        $scope.showLogout = ConfigService.getSafe().authType == "form";
    } else {
        $scope.maySeeAdmin = bootstrapped.showAdmin;
        $scope.maySeeStats = bootstrapped.showStats;
    }
    
    $scope.$on("user:loggedIn", function (event, data) {
        $scope.maySeeAdmin = data.maySeeAdmin;
        $scope.maySeeStats = data.maySeeStats;
        $scope.showLogout = ConfigService.getSafe().authType == "form";
    });

    $scope.$on("user:loggedOut", function (event, data) {
        if (ConfigService.getSafe().authType == "form") {
            $scope.maySeeAdmin = true;
            $scope.maySeeStats = true;
            $scope.showLogout = false;
        } else {
            $scope.maySeeAdmin = data.maySeeAdmin;
            $scope.maySeeStats = data.maySeeStats;
            $scope.showLogout = false;
        }
        
    });
    
    $scope.logout = function() {
        HydraAuthService.logout();
        $state.go("root.search");
    }
    
}
