angular
    .module('nzbhydraApp')
    .factory('NzbDownloadService', NzbDownloadService);

function NzbDownloadService($http, ConfigService, CategoriesService) {

    var service = {
        download: download
    };

    return service;

    function sendNzbAddCommand(searchresultids, category) {
        console.log("Now add nzb with category " + category);
        return $http.put("internalapi/addnzbs", {searchresultids: angular.toJson(searchresultids), category: category});
    }

    function download(searchresultids) {
        var settings = ConfigService.getSafe();

        var category;
        if (settings.downloader.downloader == "nzbget") {
            category = settings.downloader.nzbget.defaultCategory
        } else {
            category = settings.downloader.sabnzbd.defaultCategory
        }

        
        if (_.isUndefined(category) || category == "" || category == null) {
            return CategoriesService.openCategorySelection().then(function (category) {
                return sendNzbAddCommand(searchresultids, category)
            }, function (error) {
                throw error;
            });
        } else {
            return sendNzbAddCommand(searchresultids, category)
        }
    }
}

