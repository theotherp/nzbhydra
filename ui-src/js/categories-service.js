angular
    .module('nzbhydraApp')
    .factory('CategoriesService', CategoriesService);

function CategoriesService($http, $q, $uibModal) {

    var categories = {};
    var selectedCategory = {};

    var service = {
        get: getCategories,
        invalidate: invalidate,
        select: select,
        openCategorySelection: openCategorySelection
    };

    var deferred;

    return service;


    function getCategories(downloader) {

        function loadAll() {
            if (angular.isDefined(categories) && angular.isDefined(categories.downloader)) {
                var deferred = $q.defer();
                deferred.resolve(categories.downloader);
                return deferred.promise;
            }

            return $http.get('internalapi/getcategories', {params: {downloader: downloader.name}})
                .then(function (categoriesResponse) {
                    
                    console.log("Updating downloader categories cache");
                    categories[downloader] = categoriesResponse.data.categories;
                    return categoriesResponse.data.categories;

                }, function (error) {
                    throw error;
                });
        }

        return loadAll().then(function (categories) {
            return categories;
        }, function (error) {
            throw error;
        });
    }


    function openCategorySelection(downloader) {
        $uibModal.open({
            templateUrl: 'static/html/directives/addable-nzb-modal.html',
            controller: 'CategorySelectionController',
            size: "sm",
            resolve: {
                categories: function () {
                    return getCategories(downloader)
                }
            }
        });
        deferred = $q.defer();
        return deferred.promise;
    }

    function select(category) {
        selectedCategory = category;
        console.log("Selected category " + category);
        deferred.resolve(category);
    }

    function invalidate() {
        console.log("Invalidating categories");
        categories = undefined;
    }
}

angular
    .module('nzbhydraApp').controller('CategorySelectionController', function ($scope, $uibModalInstance, CategoriesService, categories) {
    console.log(categories);
    $scope.categories = categories;
    $scope.select = function (category) {
        CategoriesService.select(category);
        $uibModalInstance.close($scope);
    }
});