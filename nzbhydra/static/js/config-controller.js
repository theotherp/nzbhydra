angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);


ConfigController.$inject = ['$scope', '$http', 'ConfigService', 'blockUI'];
function ConfigController($scope, $http, ConfigService, blockUI) {
    
    activate().then(function() {
        blockUI.reset();
    });
    
    

    


    function activate() {
        blockUI.start("Loading config...");
            return ConfigService.getSettingsAndSchemaAndForm().then(function set(settingsAndSchemaAndForm) {
       $scope.model = settingsAndSchemaAndForm.settings;
        $scope.schema = settingsAndSchemaAndForm.schema;
        $scope.form = settingsAndSchemaAndForm.form;
    });
    }
    

    $scope.onSubmit = function (form) {
        // First we broadcast an event so all fields validate themselves
        $scope.$broadcast('schemaFormValidate');

        // Then we check if the form is valid
        if (form.$valid) {
            console.log($scope.model);
            $http.put('/internalapi/setsettings', $scope.model)
                .then(function (successresponse) {
                    console.log("Settings saved")
                }, function (errorresponse) {
                    console.log("Error saving settings: " + errorresponse);
                });
        }
    }
}


