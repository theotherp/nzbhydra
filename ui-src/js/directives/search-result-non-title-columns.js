angular
    .module('nzbhydraApp')
    .directive('otherColumns', otherColumns);

function otherColumns($http, $templateCache, $compile, $window) {
    return {
        scope: {
            result: "="
        },
        multiElement: true,

        link: function (scope, element, attrs) {
            $http.get('static/html/directives/search-result-non-title-columns.html', {cache: $templateCache}).success(function (templateContent) {
                element.replaceWith($compile(templateContent)(scope));
            });

        },
        controller: controller
    };

    function controller($scope, $http, $uibModal, growl) {

        $scope.showNfo = showNfo;
        function showNfo(resultItem) {
            if (resultItem.has_nfo == 0) {
                return;
            }
            var uri = new URI("internalapi/getnfo");
            uri.addQuery("indexer", resultItem.indexer);
            uri.addQuery("guid", resultItem.indexerguid);
            return $http.get(uri).then(function (response) {
                if (response.data.has_nfo) {
                    $scope.openModal("lg", response.data.nfo)
                } else {
                    if (!angular.isUndefined(resultItem.message)) {
                        growl.error(resultItem.message);
                    } else {
                        growl.info("No NFO available");
                    }
                }
            });
        }

        $scope.openModal = openModal;

        function openModal(size, nfo) {
            var modalInstance = $uibModal.open({
                template: '<pre class="nfo"><span ng-bind-html="nfo"></span></pre>',
                controller: 'NfoModalInstanceCtrl',
                size: size,
                resolve: {
                    nfo: function () {
                        return nfo;
                    }
                }
            });

            modalInstance.result.then();
        }
        
        $scope.downloadNzb = downloadNzb;
        
        function downloadNzb(resultItem) {
            //href = "{{ result.link }}"
            $window.location.href = resultItem.link;
        }

    }
}

angular
    .module('nzbhydraApp')
    .controller('NfoModalInstanceCtrl', NfoModalInstanceCtrl);

function NfoModalInstanceCtrl($scope, $modalInstance, nfo) {

    $scope.nfo = nfo;

    $scope.ok = function () {
        $modalInstance.close($scope.selected.item);
    };

    $scope.cancel = function () {
        $modalInstance.dismiss();
    };
}