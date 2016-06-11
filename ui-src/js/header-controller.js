angular
    .module('nzbhydraApp')
    .controller('HeaderController', HeaderController);

function HeaderController($scope, $state, $http, growl, HydraAuthService, ConfigService, bootstrapped) {

    $scope.showLoginout = false;

    if (HydraAuthService.isLoggedIn()) {
        var rights = HydraAuthService.getUserRights();
        $scope.showAdmin = rights.maySeeAdmin;
        $scope.showStats = rights.maySeeStats;
        $scope.loginlogoutText = "Logout";
        $scope.showLoginout = true;
    } else {
        $scope.showAdmin = !bootstrapped.adminRestricted;
        $scope.showStats = !bootstrapped.statsRestricted;
        $scope.loginlogoutText = "Login";
        $scope.showLoginout = bootstrapped.adminRestricted || bootstrapped.statsRestricted || bootstrapped.searchRestricted;
    }

    $scope.$on("user:loggedIn", function (event, data) {
        $scope.showAdmin = data.maySeeAdmin;
        $scope.showStats = data.maySeeStats;
        $scope.showLoginout = true;
        $scope.loginlogoutText = "Logout";
    });

    $scope.$on("user:loggedOut", function (event, data) {
        $scope.showAdmin = !bootstrapped.adminRestricted;
        $scope.showStats = !bootstrapped.statsRestricted;
        $scope.loginlogoutText = "Login";
        $scope.showLoginout = bootstrapped.adminRestricted || bootstrapped.statsRestricted || bootstrapped.searchRestricted;
    });

    $scope.loginout = function () {
        if (HydraAuthService.isLoggedIn()) {
            HydraAuthService.logout();

            if (ConfigService.getSafe().authType == "basic") {
                growl.info("Logged out. Close your browser to make sure session is closed.");
            }
            else if (ConfigService.getSafe().authType == "form") {
                growl.info("Logged out");
            } 
            $state.go("root.search");
        } else {
            if (ConfigService.getSafe().authType == "basic") {
                var params = {};
                if (HydraAuthService.getUserName()) {
                    params = {
                        old_username: HydraAuthService.getUserName()
                    }
                } 
                $http.get("internalapi/askforpassword", {params: params}).then(function () {
                    growl.info("Login successful!");
                    $state.go("root.search");
                })
            } else if (ConfigService.getSafe().authType == "form") {
                $state.go("root.login");
            } else {
                growl.info("You shouldn't need to login but here you go!");
            }

        }

    }

}
