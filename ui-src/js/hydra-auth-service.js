angular
    .module('nzbhydraApp')
    .factory('HydraAuthService', HydraAuthService);

function HydraAuthService($auth, $q, $rootScope, ConfigService, bootstrapped) {

    var loggedIn = false;
    var username;
    var maySeeAdmin = bootstrapped.maySeeAdmin;
    var maySeeStats = bootstrapped.maySeeStats;
    
    return {
        isLoggedIn: isLoggedIn,
        login: login,
        logout: logout,
        setLoggedInByForm: setLoggedInByForm,
        getUserRights: getUserRights,
        setLoggedInByBasic: setLoggedInByBasic,
        getUserName: getUserName
    };
    
    function isLoggedIn() {
        return loggedIn || (ConfigService.getSafe().authType == "form" && $auth.isAuthenticated()) || ConfigService.getSafe().authType == "none";
    }
    
    function setLoggedInByForm() {
        maySeeStats = $auth.getPayload().maySeeStats;
        maySeeAdmin = $auth.getPayload().maySeeAdmin;
        username = $auth.getPayload().username;
        loggedIn = true;
        $rootScope.$broadcast("user:loggedIn", {maySeeStats: maySeeStats, maySeeAdmin: maySeeAdmin});
    }

    function setLoggedInByBasic(_maySeeStats, _maySeeAdmin, _username) {
        maySeeAdmin = _maySeeAdmin;
        maySeeStats = _maySeeStats;
        username = _username;
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
        loggedIn = false;
        $rootScope.$broadcast("user:loggedOut");
    }
    
    function getUserRights() {
        return {maySeeStats: maySeeStats, maySeeAdmin: maySeeAdmin};
    }
    
    function getUserName() {
        return username;
    }
    
    
    
   
}