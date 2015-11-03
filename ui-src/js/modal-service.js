angular
    .module('nzbhydraApp')
    .service('modalService', modalService);

function modalService() {
    this.open = function (msg) {
        
        //Prevent cirtcular dependency
        var myInjector = angular.injector(["ng", "ui.bootstrap"]);
        var $uibModal = myInjector.get("$uibModal");

        var modalInstance = $uibModal.open({
            template: '<pre>' + msg + '</pre>',
            size: "lg"
        });

        modalInstance.result.then();

    };
}