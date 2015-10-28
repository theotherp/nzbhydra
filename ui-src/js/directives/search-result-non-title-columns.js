angular
    .module('nzbhydraApp')
    .directive('otherColumns', otherColumns);

function otherColumns($http, $templateCache, $compile) {
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

    function controller($scope, $http, $uibModal, $sce) {

        $scope.showNfo = showNfo;
        function showNfo(resultItem) {
            if (!resultItem.has_nfo) {
                return;
            }
            var uri = new URI("internalapi/getnfo");
            uri.addQuery("provider", resultItem.provider);
            uri.addQuery("guid", resultItem.providerguid);
            return $http.get(uri).then(function (response) {
                if (response.data.has_nfo) {
                    $scope.openModal("lg", response.data.nfo)
                } else {
                    //todo: show error or info that no nfo is available
                    growl.info("No NFO available");
                }
            });
        }


        $scope.openModal = openModal;

        function openModal(size, nfo) {
            var modalInstance = $uibModal.open({
                template: '<pre><span ng-bind-html="nfo"></span></pre>',
                controller: 'ModalInstanceCtrl',
                size: size,
                resolve: {
                    nfo: function () {
                        return $sce.trustAsHtml(nfo);
                    }
                }
            });

            modalInstance.result.then();
        }

    }

}