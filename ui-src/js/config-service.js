angular
    .module('nzbhydraApp')
    .factory('ConfigService', ConfigService);

function ConfigService($http, $q) {

    var config;
    
    var service = {
        set: setConfig,
        get: getConfig
    };
    
    return service;
    
    

    function setConfig(settings) {
        console.log("Starting setConfig");

        $http.put('internalapi/setsettings', settings)
            .then(function (successresponse) {
                console.log("Settings saved. Updating cache");
                config.settings = settings;
            }, function (errorresponse) {
                console.log("Error saving settings: " + errorresponse);
            });

    }

    function getConfig() {

        function loadAll() {
            if (!angular.isUndefined(config)) {
                var deferred = $q.defer();
                deferred.resolve(config);
                console.log("Returning config from cache");
                return deferred.promise;
            }

            return $http.get('internalapi/getconfig')
                .then(function (configResponse) {
                    console.log("Updating config cache");
                    config = configResponse.data;
                    return configResponse.data;
                });

        }


        return loadAll().then(function (config) {
            return {settings: config}
        });

    }
}