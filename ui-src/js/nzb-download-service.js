angular
    .module('nzbhydraApp')
    .factory('NzbDownloadService', NzbDownloadService);

function NzbDownloadService($http, ConfigService, CategoriesService) {
    
    var service = {
        download: download 
    };
    
    return service;
    


    function sendNzbAddCommand(items, category) {
        console.log("Now add nzb with category " + category);        
        return $http.put("internalapi/addnzbs", {items: angular.toJson(items), category: category});
    }

    function download (items) {
        return ConfigService.getSafe().then(function (settings) {

            var category;
            if (settings.downloader.downloader == "nzbget") {
                category = settings.downloader.nzbget.defaultCategory
            } else {
                category = settings.downloader.sabnzbd.defaultCategory
            }

            if (_.isUndefined(category) || category == "" || category == null) {
                return CategoriesService.openCategorySelection().then(function (category) {
                    return sendNzbAddCommand(items, category)
                }, function(error) {
                    throw error;
                });
            } else {
                return sendNzbAddCommand(items, category)
            }

        });


    }

    
}

