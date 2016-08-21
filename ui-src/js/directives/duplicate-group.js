angular
    .module('nzbhydraApp')
    .directive('duplicateGroup', duplicateGroup);

function duplicateGroup() {
    return {
        templateUrl: 'static/html/directives/duplicate-group.html',
        scope: {
            duplicates: "<",
            selected: "=",
            isFirstRow: "<",
            rowIndex: "<",
            displayTitleToggle: "<"
        },
        controller: ['$scope', '$element', '$attrs','localStorageService', titleRowController]
    };

    function titleRowController($scope, localStorageService) {
        $scope.titlesExpanded = false;
        $scope.duplicatesExpanded = false;
        $scope.foo = {
            duplicatesDisplayed: localStorageService.get("duplicatesDisplayed") != null ? localStorageService.get("duplicatesDisplayed") : false
        };
        $scope.duplicatesToShow = duplicatesToShow;
        function duplicatesToShow() {
            return $scope.duplicates.slice(1);
        }

        $scope.toggleTitleExpansion = function() {
            $scope.titlesExpanded = !$scope.titlesExpanded;
            $scope.$emit("toggleTitleExpansion", $scope.titlesExpanded);
        };
        
        $scope.toggleDuplicateExpansion = function() {
            $scope.duplicatesExpanded = !$scope.duplicatesExpanded;
        };

        $scope.$on("invertSelection", function() {
            for (var i = 0; i < $scope.duplicates.length; i++) {
                if ($scope.duplicatesExpanded ) {
                    invertSelection($scope.selected, $scope.duplicates[i]);
                } else {
                    if (i > 0) {
                        //Always remove duplicates that aren't displayed
                        invertSelection($scope.selected, $scope.duplicates[i], true);
                    } else {
                        invertSelection($scope.selected, $scope.duplicates[i]);
                    }
                }
            }
        });

        $scope.$on("duplicatesDisplayed", function(event, args) {
            $scope.foo.duplicatesDisplayed = args;
        });

        function invertSelection(a, b, dontPush) {
            var index = _.indexOf(a,b);
            if (index > -1) {
                a.splice(index,1);
            } else {
                if (!dontPush)
                a.push(b);
            }
        }
    }


}