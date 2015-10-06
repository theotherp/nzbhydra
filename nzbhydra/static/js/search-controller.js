angular
    .module('nzbhydraApp')
    .controller('SearchController', SearchController);





SearchController.$inject = ['$scope', '$http', '$stateParams', '$location', '$modal', '$sce', '$state', 'SearchService'];
function SearchController($scope, $http, $stateParams, $location, $modal, $sce, $state, SearchService) {
    
    console.log("SearchController");
    console.log($stateParams.category);
    console.log($stateParams);
    
    
    
    
    
    
    $scope.category = (typeof $stateParams.category === "undefined" || $stateParams.category == "") ? "All" : $stateParams.category;

    $scope.searchTerm = (typeof $stateParams.query === "undefined") ? "" : $stateParams.query;

    $scope.imdbid = (typeof $stateParams.imdbid === "undefined") ? "" : $stateParams.imdbid;
    $scope.tvdbid = (typeof $stateParams.tvdbid === "undefined") ? "" : $stateParams.tvdbid;
    $scope.title = (typeof $stateParams.title === "undefined") ? "" : $stateParams.title;
    $scope.season = (typeof $stateParams.season === "undefined") ? "" : $stateParams.season;
    $scope.episode = (typeof $stateParams.episode === "undefined") ? "" : $stateParams.episode;

    $scope.minsize = (typeof $stateParams.minsize === "undefined") ? "" : $stateParams.minsize;
    $scope.maxsize = (typeof $stateParams.maxsize === "undefined") ? "" : $stateParams.maxsize;
    $scope.minage = (typeof $stateParams.minage === "undefined") ? "" : $stateParams.minage;
    $scope.maxage = (typeof $stateParams.maxage === "undefined") ? "" : $stateParams.maxage;

    $scope.showProviders = {};
    
    
    
    SearchService.search("All", "avengers").then(function(searchResult) {
        //$scope.results = searchResult.results;
        //$scope.providersearches = searchResult.providersearches;
        ///console.log(searchResult.results);
        $state.go("search.results", {"results": searchResult.results, "providersearches": searchResult.providersearches});
    });


    if ($scope.title != "" && $scope.query == "") {
        $scope.searchTerm = $scope.title;
    }

//Only start search if we're in search mode, landing mode just shows the search box
    
    
    
    
    console.log($stateParams.mode);
    if ($stateParams.mode != "landing") {

        
    }
    

    $scope.typeAheadWait = 300;
    $scope.selectedItem = "";
    $scope.autocompleteLoading = false;


    $scope.isAskById = false; //If true a check box will be shown asking the user if he wants to search by ID 
    $scope.isById = {value: true}; //If true the user wants to search by id so we enable autosearch. Was unable to achieve this using a simple boolean


    $scope.autocompleteClass = "autocompletePosterMovies";

    $scope.toggle = function (searchCategory) {
        $scope.category = searchCategory;

        //Show checkbox to ask if the user wants to search by ID (using autocomplete)
        $scope.isAskById = ($scope.category.indexOf("TV") > -1 || $scope.category.indexOf("Movies") > -1 );
    };


// Any function returning a promise object can be used to load values asynchronously
    $scope.getAutocomplete = function (val) {
        $scope.autocompleteLoading = true;
        //Expected model returned from API:
        //label: What to show in the results
        //title: Will be used for file search
        //value: Will be used as extraInfo (ttid oder tvdb id)
        //poster: url of poster to show

        //Don't use autocomplete if checkbox is disabled
        if (!$scope.isById.value) {
            return {};
        }

        if ($scope.category.indexOf("Movies") > -1) {
            return $http.get('/internalapi/autocomplete?type=movie', {
                params: {
                    input: val
                }
            }).then(function (response) {
                $scope.autocompleteLoading = false;
                return response.data.results;
            });
        } else if ($scope.category.indexOf("TV") > -1) {

            return $http.get('/internalapi/autocomplete?type=tv', {
                params: {
                    input: val
                }
            }).then(function (response) {
                $scope.autocompleteLoading = false;
                return response.data.results;
            });
        } else {
            return {};
        }
    };

    $scope.startSearch = function () {
        var uri;
        if ($scope.imdbid != "") {
            uri = new URI("/searchmovies");
            uri.segment($scope.category);
            uri.segment($scope.imdbid);
            uri.segment($scope.title);
        } else if ($scope.tvdbid != "") {
            uri = new URI("/searchtv");
            uri.segment($scope.category);
            uri.segment($scope.tvdbid);
            uri.segment($scope.title);
            if ($scope.season != "") {
                uri.segment($scope.season);
            }
            if ($scope.episode != "") {
                uri.segment($scope.episode);
            }
        } else {
            uri = new URI("/search");
            uri.segment($scope.category);
            uri.segment($scope.searchTerm);
        }

        if ($scope.minsize != "") {
            uri.addQuery("minsize", $scope.minsize);
        }
        if ($scope.maxsize != "") {
            uri.addQuery("maxsize", $scope.maxsize);
        }
        if ($scope.minage != "") {
            uri.addQuery("minage", $scope.minage);
        }
        if ($scope.maxage != "") {
            uri.addQuery("maxage", $scope.maxage);
        }

        $location.url(uri);
        $scope.imdbid = "";
        $scope.tvdbid = "";
    };


    $scope.selectAutocompleteItem = function ($item) {
        $scope.selectedItem = $item;
        $scope.title = $item.label;
        if ($scope.category.indexOf("Movies") > -1) {
            $scope.imdbid = $item.value;
        } else if ($scope.category.indexOf("TV") > -1) {
            $scope.tvdbid = $item.value;
        }
        $scope.startSearch();
    };


    $scope.autocompleteActive = function () {
        return ($scope.category.indexOf("TV") > -1) || ($scope.category.indexOf("Movies") > -1)
    };

    $scope.seriesSelected = function () {
        return ($scope.category.indexOf("TV") > -1);
    };


    $scope.results = [];
    $scope.isShowDuplicates = true;
    $scope.predicate = 'age_days';
    $scope.reversed = false;


    $scope.setSorting = function (predicate, reversedDefault) {
        if (predicate == $scope.predicate) {
            $scope.reversed = !$scope.reversed;
        } else {
            $scope.reversed = reversedDefault;
        }
        $scope.predicate = predicate;
    };


//True if the provider is selected in the table filter, false else 
    $scope.isShow = function (item) {
        return $scope.showProviders[item.provider];
    };


    $scope.showNfo = function (resultItem) {
        var uri = new URI("/internalapi/getnfo");
        uri.addQuery("provider", resultItem.provider);
        uri.addQuery("guid", resultItem.guid);
        return $http.get(uri).then(function (response) {
            if (response.data.has_nfo) {
                $scope.open("lg", response.data.nfo)
            } else {
                //todo: show error or info that no nfo is available
            }
        });
    };


    $scope.nzbgetclass = {};
    $scope.nzbgetEnabled = true;

    $scope.addNzb = function (resultItem) {
        var uri = new URI("/internalapi/addnzb");
        uri.addQuery("title", resultItem.title);
        uri.addQuery("providerguid", resultItem.providerguid);
        uri.addQuery("provider", resultItem.provider);
        $scope.nzbgetclass[resultItem.guid] = "nzb-spinning";
        return $http.get(uri).success(function () {
            $scope.nzbgetclass[resultItem.guid] = "nzb-success";
        }).error(function () {
            $scope.nzbgetclass[resultItem.guid] = "nzb-error";
        })
            ;
    };

    $scope.nzbclass = function (resultItem) {
        if ($scope.nzbgetclass[resultItem.guid]) {
            return $scope.nzbgetclass[resultItem.guid];
        } else {
            return "nzb";
        }
    }


    $scope.open = function (size, nfo) {

        var modalInstance = $modal.open({
            animation: $scope.animationsEnabled,
            template: '<pre><span ng-bind-html="nfo"></span></pre>',
            controller: 'ModalInstanceCtrl',
            size: size,
            resolve: {
                nfo: function () {
                    return $sce.trustAsHtml(nfo);
                }
            }
        });
    };

}
