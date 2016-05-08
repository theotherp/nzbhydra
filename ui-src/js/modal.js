angular
    .module('nzbhydraApp')
    .factory('ModalService', ModalService);

function ModalService($uibModal, $q) {
    
    return {
        open: open
    };
    
    function open(headline, message, params) {
        //params example:
        /*
        var p =
        {
            yes: {
                text: "Yes",    //default: Ok
                onYes: function() {}
            },
            no: {               //default: Empty
                text: "No",
                onNo: function () {
                }
            },
            cancel: {           
                text: "Cancel", //default: Cancel
                onCancel: function () {
                }
            }
        };
        */
        var modalInstance = $uibModal.open({
            templateUrl: 'static/html/modal.html',
            controller: 'ModalInstanceCtrl',
            size: 'md',
            resolve: {
                headline: function () {
                    return headline;
                },
                message: function(){ 
                    return message;
                },
                params: function() {
                    return params;
                }
            }
        });

        modalInstance.result.then(function() {
            
        }, function() {
            
        });
    }
    
}

angular
    .module('nzbhydraApp')
    .controller('ModalInstanceCtrl', ModalInstanceCtrl);

function ModalInstanceCtrl($scope, $uibModalInstance, headline, message, params) {

    $scope.message = message;
    $scope.headline = headline;
    $scope.params = params;
    $scope.showCancel = angular.isDefined(params.cancel);
    $scope.showNo = angular.isDefined(params.no);

    if (angular.isDefined(params.yes) && angular.isUndefined(params.yes.text)) {
        params.yes.text = "Yes";
    }
    
    if (angular.isDefined(params.no) && angular.isUndefined(params.no.text)) {
        params.no.text = "No";
    }
    
    if (angular.isDefined(params.cancel) && angular.isUndefined(params.cancel.text)) {
        params.cancel.text = "Cancel";
    }

    $scope.yes = function () {
        $uibModalInstance.close();
        if(angular.isDefined(params.yes) && angular.isDefined(params.yes.onYes)) {
            params.yes.onYes();
        }
    };

    $scope.no = function () {
        $uibModalInstance.close();
        if (angular.isDefined(params.no) && angular.isDefined(params.no.onNo)) {
            params.no.onNo();
        }
    };

    $scope.cancel = function () {
        $uibModalInstance.dismiss();
        if (angular.isDefined(params.cancel) && angular.isDefined(params.cancel.onCancel)) {
            params.cancel.onCancel();
        }
    };

    $scope.$on("modal.closing", function (targetScope, reason, c) {
        if (reason == "backdrop click") {
            $scope.cancel();
        }
    });
}
