angular
    .module('nzbhydraApp')
    .factory('HydraAuthService', HydraAuthService);

function HydraAuthService($auth, $q, $rootScope, ConfigService, bootstrapped) {

    var loggedIn = false;
    var maySeeAdmin = bootstrapped.maySeeAdmin;
    var maySeeStats = bootstrapped.maySeeStats;
    
    return {
        isLoggedIn: isLoggedIn,
        login: login,
        logout: logout,
        setLoggedInByForm: setLoggedInByForm,
        getUserRights: getUserRights,
        setLoggedInByBasic: setLoggedInByBasic
    };
    
    function isLoggedIn() {
        return loggedIn || (ConfigService.getSafe().authType == "form" && $auth.isAuthenticated()) || ConfigService.getSafe().authType == "none";
    }
    
    function setLoggedInByForm() {
        maySeeStats = $auth.getPayload().maySeeStats;
        maySeeAdmin = $auth.getPayload().maySeeAdmin;
        loggedIn = true;
        $rootScope.$broadcast("user:loggedIn", {maySeeStats: maySeeStats, maySeeAdmin: maySeeAdmin});
    }

    function setLoggedInByBasic(_maySeeStats, _maySeeAdmin) {
        maySeeAdmin = _maySeeAdmin;
        maySeeStats = _maySeeStats;
        loggedIn = true;
        $rootScope.$broadcast("user:loggedIn", {maySeeStats: maySeeStats, maySeeAdmin: maySeeAdmin});
    }
    
    function login(user) {
        var deferred = $q.defer();
        $auth.login(user).then(function (data) {
            $rootScope.$broadcast("user:loggedIn", data);
           deferred.resolve();
        });
        return deferred;
    }
    
    function logout() {
        $auth.logout();
        $rootScope.$broadcast("user:loggedOut", {maySeeStats: bootstrapped.maySeeStats, maySeeAdmin: bootstrapped.maySeeAdmin});
    }
    
    function getUserRights() {
        return {maySeeStats: maySeeStats, maySeeAdmin: maySeeAdmin};
    }
    
    
    
   
}