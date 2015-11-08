angular
    .module('nzbhydraApp')
    .controller('SearchController', SearchController);


SearchController.$inject = ['$scope', '$http', '$stateParams', '$uibModal', '$sce', '$state', 'SearchService', 'focus', 'ConfigService', 'blockUI', 'growl'];
function SearchController($scope, $http, $stateParams, $uibModal, $sce, $state, SearchService, focus, ConfigService, blockUI, growl) {

    function getNumberOrUndefined(number) {
        if (_.isUndefined(number) || _.isNaN(number) || number == "") {
            return undefined;
        }
        number = parseInt(number);
        if (_.isNumber(number)) {
            return number;
        } else {
            return undefined;
        }
    }

    console.log("Start of search controller");

    //Fill the form with the search values we got from the state params (so that their values are the same as in the current url)
    $scope.mode = $stateParams.mode;
    $scope.category = (_.isUndefined($stateParams.category) || $stateParams.category == "") ? "All" : $stateParams.category;
    $scope.imdbid = $stateParams.imdbid;
    $scope.tvdbid = $stateParams.tvdbid;
    $scope.rid = $stateParams.rid;
    $scope.title = $stateParams.title;
    $scope.season = $stateParams.season;
    $scope.episode = $stateParams.episode;
    $scope.query = $stateParams.query;
    $scope.minsize = getNumberOrUndefined($stateParams.minsize);
    $scope.maxsize = getNumberOrUndefined($stateParams.maxsize);
    $scope.minage = getNumberOrUndefined($stateParams.minage);
    $scope.maxage = getNumberOrUndefined($stateParams.maxage);
    if ($scope.title != "" && $scope.query == "") {
        $scope.query = $scope.title;
    }

    $scope.showIndexers = {};

    var config;
    
    
    $scope.typeAheadWait = 300;
    $scope.selectedItem = "";
    $scope.autocompleteLoading = false;
    $scope.isAskById = false; //If true a check box will be shown asking the user if he wants to search by ID 
    $scope.isById = {value: true}; //If true the user wants to search by id so we enable autosearch. Was unable to achieve this using a simple boolean
    $scope.availableIndexers = [];
    $scope.autocompleteClass = "autocompletePosterMovies";

    $scope.toggle = function (searchCategory) {
        $scope.category = searchCategory;

        //Show checkbox to ask if the user wants to search by ID (using autocomplete)
        $scope.isAskById = ($scope.category.indexOf("TV") > -1 || $scope.category.indexOf("Movies") > -1 );

        focus('focus-query-box');
        $scope.query = "";

        if (config.searching.categorysizes.enable_category_sizes) {
            var min = config.searching.categorysizes[searchCategory + " min"];
            var max = config.searching.categorysizes[searchCategory + " max"];
            if (_.isNumber(min)) {
                $scope.minsize = min;
            } else {
                $scope.minsize = "";
            }
            if (_.isNumber(max)) {
                $scope.maxsize = max;
            } else {
                $scope.maxsize = "";
            }
        }
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
            return $http.get('internalapi/autocomplete?type=movie', {
                params: {
                    input: val
                }
            }).then(function (response) {
                $scope.autocompleteLoading = false;
                return response.data.results;
            });
        } else if ($scope.category.indexOf("TV") > -1) {

            return $http.get('internalapi/autocomplete?type=tv', {
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
        blockUI.start("Searching...");
        SearchService.search($scope.category, $scope.query, $stateParams.imdbid, $scope.title, $stateParams.rid, $scope.tvdbid, $scope.season, $scope.episode, $scope.minsize, $scope.maxsize, $scope.minage, $scope.maxage).then(function (searchResult) {
            $state.go("search.results", {
                results: searchResult.results,
                indexersearches: searchResult.indexersearches,
                total: searchResult.total,
                resultsCount: searchResult.resultsCount,
                minsize: $scope.minsize,
                maxsize: $scope.maxsize,
                minage: $scope.minage,
                maxage: $scope.maxage
            }, {
                inherit: true
            });
            $scope.imdbid = undefined;
            $scope.tvdbid = undefined;
        });
    };


    $scope.goToSearchUrl = function () {
        var stateParams = {};
        if ($scope.category.indexOf("Movies") > -1) {
            stateParams.mode = "moviesearch";
            stateParams.imdbid = $scope.imdbid;
            stateParams.title = $scope.title;
            stateParams.mode = $scope.mode;
        } else if ($scope.category.indexOf("TV") > -1) {
            stateParams.mode = "tvsearch";
            if (!_.isUndefined($scope.tvdbid)) {
                $stateParams.tvdbid = $scope.tvdbid;
            }
            else {
                stateParams.rid = $scope.rid;
            }
            stateParams.title = $scope.title;

            if (!_.isUndefined($scope.season)) {
                stateParams.season = $scope.season;
            }
            if (!_.isUndefined($scope.episode)) {
                stateParams.episode = $scope.episode;
            }
        } else {
            stateParams.mode = "search";
            stateParams.query = $scope.query;
        }

        
        stateParams.minsize = $scope.minsize;
        stateParams.maxsize = $scope.maxsize;
        stateParams.minage = $scope.minage;
        stateParams.maxage = $scope.maxage;
        stateParams.category = $scope.category;

        $state.go("search", stateParams, {inherit: false, notify: true});
    };


    $scope.selectAutocompleteItem = function ($item) {
        $scope.selectedItem = $item;
        $scope.title = $item.label;
        if ($scope.category.indexOf("Movies") > -1) {
            $scope.imdbid = $item.value;
            $scope.mode = "moviesearch";
        } else if ($scope.category.indexOf("TV") > -1) {
            $scope.tvdbid = $item.value;
            $scope.mode = "tvsearch";
        }
        $scope.query = "";
        $scope.goToSearchUrl();
    };


    $scope.autocompleteActive = function () {
        return ($scope.category.indexOf("TV") > -1) || ($scope.category.indexOf("Movies") > -1)
    };

    $scope.seriesSelected = function () {
        return ($scope.category.indexOf("TV") > -1);
    };


    ConfigService.get().then(function (cfg) {
        config = cfg;
        $scope.availableIndexers = _.filter(cfg.indexers, function (indexer) {
            return indexer.enabled;
        }).map(function (indexer) {
            return {name: indexer.name, activated: true};
        });
        console.log($scope.availableIndexers);
    });


    if ($scope.mode) {
        console.log("Starting search in newly loaded search controller");
        $scope.startSearch();
    }
    


}
