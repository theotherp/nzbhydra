angular
    .module('nzbhydraApp')
    .service('ConfigService', ConfigService);

function ConfigService($http) {
    
this.getSettingsAndSchemaAndForm = function() {
        
        function loadAll() {
        return $http.get('/internalapi/getconfig')
            .then(function (config) {
               return config.data;
            });
            
        }

        
        return loadAll().then(function(config) {
            return {schema: config.schema, settings: config.settings, form: config.form}
        });
        
    }
}