angular
    .module('nzbhydraApp')
    .controller('LoginController', LoginController);

function LoginController($scope, $stateParams, $state, HydraAuthService, $auth) {
    $scope.user = {};
    $scope.login = function() {
        $auth.login($scope.user).then(function(data) {
            
            console.log("Logged in from LoginController");
            HydraAuthService.setLoggedIn();
            $state.go("root.search");
        });
        
    }
    
}
