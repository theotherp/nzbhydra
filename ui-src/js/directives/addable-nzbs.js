angular
    .module('nzbhydraApp')
    .directive('addableNzbs', addableNzbs);

function addableNzbs() {
    return {
        templateUrl: 'static/html/directives/addable-nzbs.html',
        require: ['^searchResultId'],
        scope: {
            searchResultId: "="
        },
        controller: controller
    };

    function controller($scope, NzbDownloadService) {
        $scope.downloaders = NzbDownloadService.getEnabledDownloaders();
    }
}
