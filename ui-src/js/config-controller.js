angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);

function ConfigController($scope, $http, ConfigService, blockUI) {

    activate();
    
    
    function activate() {
        $scope.$on('sf-render-finished', function () {
            blockUI.reset();
            console.log("Render of form finished");
        });
        blockUI.start("Loading config...");
        return ConfigService.get().then(function set(settingsAndSchemaAndForm) {
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
            ConfigService.set($scope.model);
        }
    }
}


