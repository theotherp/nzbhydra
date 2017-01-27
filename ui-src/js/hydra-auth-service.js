angular
    .module('nzbhydraApp')
    .factory('HydraAuthService', HydraAuthService);

function HydraAuthService($q, $rootScope, $http, $cookies, bootstrapped) {

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
        getUserName: getUserName,
        getUserInfos: getUserInfos
    };


    function decode_flask_cookie(val) {
        if (val.indexOf('\\') === -1) {
            return val;  // not encoded
        }
        val = val.slice(1, -1).replace(/\\"/g, '"');
        val = val.replace(/\\(\d{3})/g, function (match, octal) {
            return String.fromCharCode(parseInt(octal, 8));
        });
        return val.replace(/\\\\/g, '\\');
    }


    function getUserInfos() {
        var cookie = decode_flask_cookie($cookies.get("userinfos"));
        return JSON.parse(cookie);
    }

    
    function isLoggedIn() {
        return JSON.parse(decode_flask_cookie($cookies.get("userinfos"))).username;
    }
    
    function setLoggedInByForm() {
        $rootScope.$broadcast("user:loggedIn");
    }

    function setLoggedInByBasic(_maySeeStats, _maySeeAdmin, _username) {
        maySeeAdmin = _maySeeAdmin;
        maySeeStats = _maySeeStats;
        username = _username;
        loggedIn = true;
    }
    
    function login(username, password) {
        var deferred = $q.defer();
        return $http.post("/auth/login", data = {username: username, password: password}).then(function () {
            $rootScope.$broadcast("user:loggedIn");
           deferred.resolve();
        });
        return deferred;
    }
    
    function logout() {
        var deferred = $q.defer();
        return $http.post("/auth/logout").then(function() {
            $rootScope.$broadcast("user:loggedOut");
            deferred.resolve();
        });
        return deferred;
    }
    
    function getUserRights() {
        var userInfos = getUserInfos();
        return {maySeeStats: userInfos.maySeeStats, maySeeAdmin: userInfos.maySeeAdmin, maySeeSearch: userInfos.maySeeSearch};
    }
    
    function getUserName() {
        return username;
    }


    
    
    
   
}