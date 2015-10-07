angular
    .module('nzbhydraApp')
    .controller('SearchController', SearchController);


SearchController.$inject = ['$scope', '$http', '$stateParams','$modal', '$sce', '$state', 'SearchService', 'focus'];
function SearchController($scope, $http, $stateParams,$modal, $sce, $state, SearchService, focus) {

    console.log("STart of search controller");


    $scope.category = (typeof $stateParams.category === "undefined" || $stateParams.category == "") ? "All" : $stateParams.category;

    $scope.query = (typeof $stateParams.query === "undefined") ? "" : $stateParams.query;

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


    if ($scope.title != "" && $scope.query == "") {
        $scope.query = $scope.title;
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
        
        focus('focus-query-box');
        $scope.query = "";
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
        SearchService.search($scope.category, $scope.query, $scope.imdbid, $scope.title, $scope.tvdbid, $scope.season, $scope.episode, $scope.minsize, $scope.maxsize, $scope.minage, $scope.maxage).then(function (searchResult) {
            $state.go("search.results", {"results": searchResult.results, "providersearches": searchResult.providersearches});
            $scope.imdbid = "";
            $scope.tvdbid = "";
        });
    };
    
    
    $scope.goToSearchUrl = function () {
        var state;
        var stateParams = {};
        if ($scope.imdbid != "") {
            stateParams.imdbid = $scope.imdbid;
            stateParams.title = $scope. title;
            

        } else if ($scope.tvdbid != "") {
            stateParams.tvdbid = $scope.tvdbid;
            stateParams.title = $scope. title;

            if ($scope.season != "") {
                stateParams.season = $scope.season;
            }
            if ($scope.episode != "") {
                stateParams.episode = $scope.episode;
            }
        } else {
            stateParams.query = $scope.query;
        }

        if ($scope.minsize != "") {
            stateParams.minsize = $scope.minsize;
        }
        if ($scope.maxsize != "") {
            stateParams.maxsize = $scope.maxsize;
        }
        if ($scope.minage != "") {
        stateParams.minage = $scope.minage;
        }
        if ($scope.maxage != "") {
            stateParams.maxage = $scope.maxage;
        }

        stateParams.category = $scope.category;

        console.log("Going to search state with params...");
        console.log(stateParams);
        $state.go("search", stateParams, {inherit: false});
    };


    $scope.selectAutocompleteItem = function ($item) {
        $scope.selectedItem = $item;
        $scope.title = $item.label;
        if ($scope.category.indexOf("Movies") > -1) {
            $scope.imdbid = $item.value;
        } else if ($scope.category.indexOf("TV") > -1) {
            $scope.tvdbid = $item.value;
        }
        $scope.query = "";
        $scope.goToSearchUrl();
    };


    $scope.autocompleteActive = function () {
        return false;
        return ($scope.category.indexOf("TV") > -1) || ($scope.category.indexOf("Movies") > -1)
    };

    $scope.seriesSelected = function () {
        return false;
        return ($scope.category.indexOf("TV") > -1);
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


    if ($stateParams.mode != "landing") {
        //(category, query, imdbid, title, tvdbid, season, episode, minsize, maxsize, minage, maxage)
        console.log("Came from search url, will start searching");
        $scope.startSearch();
    }


}
