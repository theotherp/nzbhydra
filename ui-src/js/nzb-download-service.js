angular
    .module('nzbhydraApp')
    .factory('NzbDownloadService', NzbDownloadService);

function NzbDownloadService($http, ConfigService, DownloaderCategoriesService) {

    var service = {
        download: download,
        getEnabledDownloaders: getEnabledDownloaders
    };

    return service;

    function sendNzbAddCommand(downloader, searchresultids, category) {
        return $http.put("internalapi/addnzbs", {downloader: downloader.name, searchresultids: angular.toJson(searchresultids), category: category});
    }
    
    function download(downloader, searchresultids) {
        
        var category = downloader.defaultCategory;
        
        if (_.isUndefined(category) || category == "" || category == null) {
            return DownloaderCategoriesService.openCategorySelection(downloader).then(function (category) {
                return sendNzbAddCommand(downloader, searchresultids, category)
            }, function (error) {
                throw error;
            });
        } else {
            return sendNzbAddCommand(downloader, searchresultids, category)
        }
    }
    
    function getEnabledDownloaders() {
        return _.filter(ConfigService.getSafe().downloaders, "enabled");
    }
}

