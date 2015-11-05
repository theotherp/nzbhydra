angular
    .module('nzbhydraApp')
    .controller('AboutController', AboutController);

function AboutController($scope, $http, versionsPromise) {

    $scope.currentVersion = versionsPromise.data.currentVersion;
    $scope.repVersion = versionsPromise.data.repVersion;
    $scope.updateAvailable = versionsPromise.data.updateAvailable;

}
