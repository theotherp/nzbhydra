angular
    .module('nzbhydraApp')
    .factory('ModalService', ModalService);

function ModalService($uibModal) {
    
    return {
        open: openModal
    };
    
    function openModal(headline, message, ok, cancel) {
        var modalInstance = $uibModal.open({
            templateUrl: 'static/html/modal.html',
            controller: 'ModalInstanceCtrl',
            size: 'md',
            resolve: {
                headline: function () {
                    return headline
                },
                message: function(){ return message},
                ok: function() {
                    return ok;
                },
                cancel: function() {
                    return cancel;
                }
            }
        });

        modalInstance.result.then(function() {
            
        }, function() {
            cancel();
        });
    }
    
}

angular
    .module('nzbhydraApp')
    .controller('ModalInstanceCtrl', ModalInstanceCtrl);

function ModalInstanceCtrl($scope, $uibModalInstance, headline, message, ok, cancel) {

    $scope.message = message;
    $scope.headline = headline;

    $scope.ok = function () {
        $uibModalInstance.close();
        if(!angular.isUndefined(ok)) {
            ok();
        }
    };

    $scope.cancel = function () {
        $uibModalInstance.dismiss();
        if (!angular.isUndefined(cancel)) {
            cancel();
        }
    };
}
