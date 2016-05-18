angular
    .module('nzbhydraApp')
    .controller('LoginController', LoginController);

function LoginController($scope, RequestsErrorHandler, $state, HydraAuthService, $auth, growl) {
    $scope.user = {};
    $scope.login = function() {
        RequestsErrorHandler.specificallyHandled(function() {
            $auth.login($scope.user).then(function (data) {

                console.log(data);
                HydraAuthService.setLoggedInByForm();
                growl.info("Login successful!");
                $state.go("root.search");
            }, function () {
                growl.error("Login failed!")
            });
        });
        
        
    }
    
}
