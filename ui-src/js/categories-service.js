angular
    .module('nzbhydraApp')
    .factory('CategoriesService', CategoriesService);

function CategoriesService($http, $q, $uibModal) {

    var categories;
    var selectedCategory;
    
    var service = {
        get: getCategories,
        invalidate: invalidate,
        select : select,
        openCategorySelection: openCategorySelection 
    };
    
    return service;
    

    function getCategories() {

        function loadAll() {
            if (!angular.isUndefined(categories)) {
                var deferred = $q.defer();
                deferred.resolve(categories);
                return deferred.promise;
            }

            return $http.get('internalapi/getcategories')
                .then(function (categoriesResponse) {
                    
                        console.log("Updating downloader categories cache");
                        categories = categoriesResponse.data;
                        return categoriesResponse.data;
                    
                }, function(error) {
                    throw error;
                });
        }

        return loadAll().then(function (categories) {
            return categories.categories;
        }, function (error) {
            throw error;
        });
    }

    
    var deferred;
    
    function openCategorySelection() {
        $uibModal.open({
            templateUrl: 'static/html/directives/addable-nzb-modal.html',
            controller: 'CategorySelectionController',
            size: "sm",
            resolve: {
                categories: getCategories
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