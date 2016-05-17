angular
    .module('nzbhydraApp')
    .factory('HydraAuthService', HydraAuthService);

function HydraAuthService(localStorageService, $auth, $q, $rootScope) {

    return {
        isLoggedIn: isLoggedIn,

        login: login,
        setLoggedIn: setLoggedIn,
        getUserRights: getUserRights 
        
    };
    
    function isLoggedIn() {
        return $auth.isAuthenticated();
    }
    
    function setLoggedIn() {
        var maySeeStats = $auth.getPayload().maySeeStats;
        var maySeeAdmin = $auth.getPayload().maySeeAdmin;
        $rootScope.$broadcast("user:loggedIn", {maySeeStats: maySeeStats, maySeeAdmin: maySeeAdmin});
    }
    
    function login(user) {
        var deferred = $q.defer();
        $auth.login(user).then(function (data) {
            console.log("logged in");
            $rootScope.$broadcast("user:loggedIn", data);
           deferred.resolve();
        });
        return deferred;
    }
    
    function getUserRights() {
        if (!isLoggedIn()) {
            return {maySeeStats: false, maySeeAdmin: false}
        } else {
            var maySeeStats = $auth.getPayload().maySeeStats;
            var maySeeAdmin = $auth.getPayload().maySeeAdmin;
            return {maySeeStats: maySeeStats, maySeeAdmin: maySeeAdmin};
        }
    }
    
   
}