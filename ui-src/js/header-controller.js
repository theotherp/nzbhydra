angular
    .module('nzbhydraApp')
    .controller('HeaderController', HeaderController);

function HeaderController($scope, $state, $http, growl, HydraAuthService, ConfigService, bootstrapped) {

    $scope.showLoginout = false;

    if (ConfigService.getSafe().authType == "none") {
        $scope.showAdmin = true;
        $scope.showStats = true;
        $scope.showLoginout = false;
    } else {
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
    }

    function onLogin(data) {
        $scope.showAdmin = data.maySeeAdmin;
        $scope.showStats = data.maySeeStats;
        $scope.showLoginout = true;
        $scope.loginlogoutText = "Logout";
    }

    $scope.$on("user:loggedIn", function (event, data) {
        onLogin(data);
    });

    function onLogout() {
        $scope.showAdmin = !bootstrapped.adminRestricted;
        $scope.showStats = !bootstrapped.statsRestricted;
        $scope.loginlogoutText = "Login";
        $scope.showLoginout = bootstrapped.adminRestricted || bootstrapped.statsRestricted || bootstrapped.searchRestricted;
    }

    $scope.$on("user:loggedOut", function (event, data) {
        onLogout();
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
            onLogout();
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
                    //onLogin();
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
