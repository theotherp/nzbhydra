angular
    .module('nzbhydraApp')
    .factory('ConfigService', ConfigService);

function ConfigService($http, $q, $cacheFactory) {

    var cache = $cacheFactory('nzbhydra');
    
    return {
        set: setConfig,
        get: getConfig,
        getSafe: getSafe,
        invalidateSafe: invalidateSafe,
        maySeeAdminArea: maySeeAdminArea
    };
    
    
    function setConfig(newConfig) {
        console.log("Starting setConfig");

        $http.put('internalapi/setsettings', newConfig)
            .then(function (successresponse) {
                console.log("Settings saved. Updating cache");
                cache.put("config", newConfig);
            }, function (errorresponse) {
                console.log("Error saving settings: " + errorresponse);
            });
    }

    function getConfig() {
        function loadAll() {
            var config = cache.get("config");
            if (!angular.isUndefined(config)) {
                var deferred = $q.defer();
                deferred.resolve(config);
                return deferred.promise;
            }

            return $http.get('internalapi/getconfig')
                .then(function (configResponse) {
                    console.log("Updating config cache");
                    var config = configResponse.data;
                    cache.put("config", config);
                    return configResponse.data;
                });
        }

        return loadAll().then(function (config) {
            return config;
        });
    }

    function getSafe() {
        function loadAll() {
            var safeconfig = cache.get("safeconfig");
            if (!angular.isUndefined(safeconfig)) {
                var deferred = $q.defer();
                deferred.resolve(safeconfig);
                return deferred.promise;
            }

            return $http.get('internalapi/getsafeconfig')
                .then(function (configResponse) {
                    console.log("Updating safe config cache");
                    var config = configResponse.data;
                    cache.put("safeconfig", config);
                    return configResponse.data;
                });
        }

        return loadAll().then(function (config) {
            return config;
        });
    }
    
    function invalidateSafe() {
        cache.remove("safeconfig");
    }

    function maySeeAdminArea() {
        function loadAll() {
            var maySeeAdminArea = cache.get("maySeeAdminArea");
            if (!angular.isUndefined(maySeeAdminArea)) {
                var deferred = $q.defer();
                deferred.resolve(maySeeAdminArea);
                return deferred.promise;
            }

            return $http.get('internalapi/mayseeadminarea')
                .then(function (configResponse) {
                    console.log("Updating maySeeAdminArea cache");
                    var config = configResponse.data;
                    cache.put("maySeeAdminArea", config);
                    return configResponse.data;
                });
        }

        return loadAll().then(function (maySeeAdminArea) {
            return maySeeAdminArea;
        });
    }
}