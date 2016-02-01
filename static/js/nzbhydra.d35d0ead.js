var nzbhydraapp = angular.module('nzbhydraApp', ['angular-loading-bar', 'cgBusy', 'ngAnimate', 'ui.bootstrap', 'ipCookie', 'angular-growl', 'angular.filter', 'filters', 'ui.router', 'blockUI', 'mgcrea.ngStrap', 'angularUtils.directives.dirPagination', 'nvd3', 'formly', 'formlyBootstrap', 'frapontillo.bootstrap-switch', 'ui.select', 'ngSanitize', 'checklist-model']);


angular.module('nzbhydraApp').config(["$stateProvider", "$urlRouterProvider", "$locationProvider", "blockUIConfig", "$urlMatcherFactoryProvider", function ($stateProvider, $urlRouterProvider, $locationProvider, blockUIConfig, $urlMatcherFactoryProvider) {

    blockUIConfig.autoBlock = false;
    //$urlRouterProvider.otherwise("/search/");
    $urlMatcherFactoryProvider.strictMode(false);
    
    $stateProvider
        .state("search.results", {
            templateUrl: "static/html/states/search-results.6791b6ca.html",
            controller: "SearchResultsController",
            controllerAs: "srController",
            options: {
                inherit: false
            },
            params: {
                results: [],
                indexersearches: [],
                total: 0,
                resultsCount: 0,
                minsize: undefined,
                maxsize: undefined,
                minage: undefined,
                maxage: undefined
            }
        })
        .state("config", {
            url: "/config",
            templateUrl: "static/html/states/config.6833b821.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("config.searching", {
            url: "/searching",
            templateUrl: "static/html/states/config.6833b821.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("config.downloader", {
            url: "/downloader",
            templateUrl: "static/html/states/config.6833b821.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("config.indexers", {
            url: "/indexers",
            templateUrl: "static/html/states/config.6833b821.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("config.system", {
            url: "/system",
            templateUrl: "static/html/states/config.6833b821.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("config.log", {
            url: "/log",
            templateUrl: "static/html/states/config.6833b821.html",
            controller: "ConfigController",
            resolve: {
                config: ['ConfigService', function (ConfigService) {
                    return ConfigService.get();
                }]
            }
        })
        .state("stats", {
            url: "/stats",
            templateUrl: "static/html/states/stats.1ea63a87.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function(StatsService) {
                    return StatsService.get();
                }]
            }
        })
        .state("stats.indexers", {
            url: "/indexers",
            templateUrl: "static/html/states/stats.1ea63a87.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function (StatsService) {
                    return StatsService.get();
                }]
            }
        })
        .state("stats.searches", {
            url: "/searches",
            templateUrl: "static/html/states/stats.1ea63a87.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function (StatsService) {
                    return StatsService.get();
                }]
            }
        })
        .state("stats.downloads", {
            url: "/downloads",
            templateUrl: "static/html/states/stats.1ea63a87.html",
            controller: "StatsController",
            resolve: {
                stats: ['StatsService', function (StatsService) {
                    return StatsService.get();
                }]
            }
        })
        .state("system", {
            url: "/system",
            templateUrl: "static/html/states/system.438d2e23.html",
            controller: "SystemController",
            resolve: {
                foobar: ['$http', function ($http) {
                    return $http.get("internalapi/askforadmin")
                }]
            }
        })
        .state("system.updates", {
            url: "/updates",
            templateUrl: "static/html/states/system.438d2e23.html",
            controller: "SystemController",
            resolve: {
                foobar: ['$http', function ($http) {
                    return $http.get("internalapi/askforadmin")
                }]
            }
        })
        .state("system.log", {
            url: "/log",
            templateUrl: "static/html/states/system.438d2e23.html",
            controller: "SystemController",
            resolve: {
                foobar: ['$http', function ($http) {
                    return $http.get("internalapi/askforadmin")
                }]
            }
        })
        .state("system.about", {
            url: "/about",
            templateUrl: "static/html/states/system.438d2e23.html",
            controller: "SystemController",
            resolve: {
                foobar: ['$http', function ($http) {
                    return $http.get("internalapi/askforadmin")
                }]
            }
        })
        .state("search", {
            url: "/:search?category&query&imdbid&tvdbid&title&season&episode&minsize&maxsize&minage&maxage&offsets&rid&mode&tmdbid&indexers",
            templateUrl: "static/html/states/search.39761786.html",
            controller: "SearchController"
        })
    ;

    $locationProvider.html5Mode(true);
}]);

nzbhydraapp.config(["paginationTemplateProvider", function (paginationTemplateProvider) {
    paginationTemplateProvider.setPath('static/html/dirPagination.tpl.1ba1b587.html');
}]);

nzbhydraapp.config(['cfpLoadingBarProvider', function (cfpLoadingBarProvider) {
    cfpLoadingBarProvider.latencyThreshold = 100;
}]);

nzbhydraapp.config(['growlProvider', function (growlProvider) {
    growlProvider.globalTimeToLive(5000);
    growlProvider.globalPosition('bottom-right');
}]);


nzbhydraapp.directive('ngEnter', function () {
    return function (scope, element, attr) {
        element.bind("keydown keypress", function (event) {
            if (event.which === 13) {
                scope.$apply(function () {
                    scope.$evalAsync(attr.ngEnter);
                });

                event.preventDefault();
            }
        });
    };
});

nzbhydraapp.filter('nzblink', function () {
    return function (resultItem) {
        var uri = new URI("internalapi/getnzb");
        uri.addQuery("guid", resultItem.guid);
        uri.addQuery("title", resultItem.title);
        uri.addQuery("provider", resultItem.provider);

        return uri.toString();
    }
});

nzbhydraapp.factory('focus', ["$rootScope", "$timeout", function ($rootScope, $timeout) {
    return function (name) {
        $timeout(function () {
            $rootScope.$broadcast('focusOn', name);
        });
    }
}]);

nzbhydraapp.filter('unsafe', ["$sce", function ($sce) {
    return $sce.trustAsHtml;
}]);


_.mixin({
    isNullOrEmpty: function (string) {
        return (_.isUndefined(string) || _.isNull(string) || (_.isString(string) && string.length === 0))
    }
});

angular
    .module('nzbhydraApp')
    .directive('hydraupdates', hydraupdates);

function hydraupdates() {
    controller.$inject = ["$scope", "UpdateService", "$sce"];
    return {
        templateUrl: 'static/html/directives/updates.ac872ba2.html',
        controller: controller
    };

    function controller($scope, UpdateService, $sce) {

        $scope.loadingPromise = UpdateService.getVersions().then(function (data) {
            $scope.currentVersion = data.data.currentVersion;
            $scope.repVersion = data.data.repVersion;
            $scope.updateAvailable = data.data.updateAvailable;
            if ($scope.repVersion > $scope.currentVersion) {
                UpdateService.getChangelog().then(function(data) {
                    $scope.changelog = data.data.changelog;
                })
            }
        });
        
        UpdateService.getVersionHistory().then(function(data) {
            $scope.versionHistory = $sce.trustAsHtml(data.data.versionHistory);
        });

        $scope.update = function () {
            UpdateService.update();
        };

        $scope.showChangelog = function () {
            UpdateService.showChanges($scope.changelog);
        };
        
        

    }
}


angular
    .module('nzbhydraApp')
    .directive('searchResult', searchResult);

function searchResult() {
    return {
        templateUrl: 'static/html/directives/search-result.6810540b.html',
        require: '^titleGroup',
        scope: {
            titleGroup: "=",
            showDuplicates: "=",
            selected: "=",
            rowIndex: "="
        },
        controller: ['$scope', '$element', '$attrs', controller],
        multiElement: true
    };

    function controller($scope, $element, $attrs) {
        $scope.titleGroupExpanded = false;
        $scope.hashGroupExpanded = {};

        $scope.toggleTitleGroup = function () {
            $scope.titleGroupExpanded = !$scope.titleGroupExpanded;
            if (!$scope.titleGroupExpanded) {
                $scope.hashGroupExpanded[$scope.titleGroup[0][0].hash] = false; //Also collapse the first title's duplicates
            }
        };

        $scope.groupingRowDuplicatesToShow = groupingRowDuplicatesToShow;
        function groupingRowDuplicatesToShow() {
            if ($scope.showDuplicates &&  $scope.titleGroup[0].length > 1 && $scope.hashGroupExpanded[$scope.titleGroup[0][0].hash]) {
                return $scope.titleGroup[0].slice(1);
            } else {
                return [];
            }
        }

        //<div ng-repeat="hashGroup in titleGroup" ng-if="titleGroup.length > 0 && titleGroupExpanded"  class="search-results-row">
        $scope.otherTitleRowsToShow = otherTitleRowsToShow;
        function otherTitleRowsToShow() {
            if ($scope.titleGroup.length > 1 && $scope.titleGroupExpanded) {
                return $scope.titleGroup.slice(1);
            } else {
                return [];
            }
        }
        
        $scope.hashGroupDuplicatesToShow = hashGroupDuplicatesToShow;
        function hashGroupDuplicatesToShow(hashGroup) {
            if ($scope.showDuplicates && $scope.hashGroupExpanded[hashGroup[0].hash]) {
                return hashGroup.slice(1);
            } else {
                return [];
            }
        }
    }
}
angular
    .module('nzbhydraApp')
    .directive('otherColumns', otherColumns);

function otherColumns($http, $templateCache, $compile) {
    controller.$inject = ["$scope", "$http", "$uibModal", "growl"];
    return {
        scope: {
            result: "="
        },
        multiElement: true,

        link: function (scope, element, attrs) {
            $http.get('static/html/directives/search-result-non-title-columns.d41c710e.html', {cache: $templateCache}).success(function (templateContent) {
                element.replaceWith($compile(templateContent)(scope));
            });

        },
        controller: controller
    };

    function controller($scope, $http, $uibModal, growl) {

        $scope.showNfo = showNfo;
        function showNfo(resultItem) {
            if (resultItem.has_nfo == 0) {
                return;
            }
            var uri = new URI("internalapi/getnfo");
            uri.addQuery("indexer", resultItem.indexer);
            uri.addQuery("guid", resultItem.indexerguid);
            return $http.get(uri).then(function (response) {
                if (response.data.has_nfo) {
                    $scope.openModal("lg", response.data.nfo)
                } else {
                    if (!angular.isUndefined(resultItem.message)) {
                        growl.error(resultItem.message);
                    } else {
                        growl.info("No NFO available");
                    }
                }
            });
        }

        $scope.openModal = openModal;

        function openModal(size, nfo) {
            var modalInstance = $uibModal.open({
                template: '<pre class="nfo"><span ng-bind-html="nfo"></span></pre>',
                controller: 'NfoModalInstanceCtrl',
                size: size,
                resolve: {
                    nfo: function () {
                        return nfo;
                    }
                }
            });

            modalInstance.result.then();
        }

    }
}
otherColumns.$inject = ["$http", "$templateCache", "$compile"];

angular
    .module('nzbhydraApp')
    .controller('NfoModalInstanceCtrl', NfoModalInstanceCtrl);

function NfoModalInstanceCtrl($scope, $modalInstance, nfo) {

    $scope.nfo = nfo;

    $scope.ok = function () {
        $modalInstance.close($scope.selected.item);
    };

    $scope.cancel = function () {
        $modalInstance.dismiss();
    };
}
NfoModalInstanceCtrl.$inject = ["$scope", "$modalInstance", "nfo"];
angular
    .module('nzbhydraApp')
    .directive('searchHistory', searchHistory);


function searchHistory() {
    return {
        templateUrl: 'static/html/directives/search-history.7373552f.html',
        controller: ['$scope', '$http','$state', controller],
        scope: {}
    };
    
    function controller($scope, $http, $state) {
        $scope.type = "All";
        $scope.limit = 100;
        $scope.pagination = {
            current: 1
        };

        getSearchRequestsPage(1);

        $scope.pageChanged = function (newPage) {
            getSearchRequestsPage(newPage);
        };
        
        $scope.changeType = function(type) {
            $scope.type = type;
            getSearchRequestsPage($scope.pagination.current);
        };

        function getSearchRequestsPage(pageNumber) {
            $http.get("internalapi/getsearchrequests", {params: {page: pageNumber, limit: $scope.limit, type: $scope.type}}).success(function (response) {
                $scope.searchRequests = response.searchRequests;
                $scope.totalRequests = response.totalRequests;
            });
        }
        
        $scope.openSearch = function (request) {
            var stateParams = {};
            if (request.identifier_key == "imdbid") {
                stateParams.imdbid = request.identifier_value;
            } else if (request.identifier_key == "tvdbid" || request.identifier_key == "rid") {
                if (request.identifier_key == "rid" ) {
                    stateParams.rid = request.identifier_value;
                } else {
                    stateParams.tvdbid = request.identifier_value;
                } 
                
                if (request.season != "") {
                    stateParams.season = request.season;
                }
                if (request.episode != "") {
                    stateParams.episode = request.episode;
                }
            }
            if (request.query != "") {
                stateParams.query = request.query;
            }
            if (request.type == "tv") {
                stateParams.mode = "tvsearch"
            } else if (request.type == "tv") {
                stateParams.mode = "moviesearch"
            } else {
                stateParams.mode = "search"
            }
            
            if (request.category != "") {
                stateParams.category = request.category;
            }

            stateParams.category = request.category;
            
            $state.go("search", stateParams, {inherit: false});
        };


    }
}
//Can be used in an ng-repeat directive to call a function when the last element was rendered
//We use it to mark the end of sorting / filtering so we can stop blocking the UI

angular
    .module('nzbhydraApp')
    .directive('onFinishRender', onFinishRender);

function onFinishRender($timeout) {
    function linkFunction(scope, element, attr) {
        
        if (scope.$last === true) {
                $timeout(function () {
                    scope.$evalAsync(attr.onFinishRender);
                });
            }
    }

    return {
        link: linkFunction
    }
}
onFinishRender.$inject = ["$timeout"];
angular
    .module('nzbhydraApp')
    .directive('hydralog', hydralog);

function hydralog() {
    controller.$inject = ["$scope", "$http", "$sce"];
    return {
        template: '<div cg-busy="{promise:logPromise,message:\'Loading log file\'}"><pre ng-bind-html="log" style="text-align: left"></pre></div>',
        controller: controller
    };

    function controller($scope, $http, $sce) {
        $scope.logPromise = $http.get("internalapi/getlogs").success(function (data) {
            $scope.log = $sce.trustAsHtml(data.log);
        });

    }
}


angular
    .module('nzbhydraApp')
    .directive('indexerStatuses', indexerStatuses);

function indexerStatuses() {
    return {
        templateUrl: 'static/html/directives/indexer-statuses.5805f631.html',
        controller: ['$scope', '$http', controller]
    };

    function controller($scope, $http) {
        
        getIndexerStatuses();
        
        function getIndexerStatuses() {
            $http.get("internalapi/getindexerstatuses").success(function (response) {
                $scope.indexerStatuses = response.indexerStatuses;
            });
        }
        
        $scope.isInPast = function (timestamp) {
            return timestamp * 1000 < (new Date).getTime();
        };
        
        $scope.enable = function(indexerName) {
            $http.get("internalapi/enableindexer", {params: {name: indexerName}}).then(function(response){
                $scope.indexerStatuses = response.data.indexerStatuses;
            });
        }

    }
}

angular
    .module('nzbhydraApp')
    .filter('formatDate', formatDate);

function formatDate(dateFilter) {
    return function(timestamp, hidePast) {
        if (timestamp) {
            if (timestamp * 1000 < (new Date).getTime() && hidePast) {
                return ""; //
            }
            
            var t = timestamp * 1000;
            t = dateFilter(t, 'yyyy-MM-dd HH:mm:ss Z');
            return t;
        } else {
            return "";
        }
    }
}
formatDate.$inject = ["dateFilter"];
angular
    .module('nzbhydraApp').directive('focusOn', focusOn);

function focusOn() {
    return directive;
    function directive(scope, elem, attr) {
        scope.$on('focusOn', function (e, name) {
            if (name === attr.focusOn) {
                elem[0].focus();
            }
        });
    }
}

angular
    .module('nzbhydraApp')
    .directive('downloadHistory', downloadHistory);

function downloadHistory() {
    return {
        templateUrl: 'static/html/directives/download-history.f487c230.html',
        controller: ['$scope', '$http', controller],
        scope: {}
    };

    function controller($scope, $http) {
        $scope.type = "All";
        $scope.limit = 100;
        $scope.pagination = {
            current: 1
        };

        $scope.changeType = function (type) {
            $scope.type = type;
            getDownloadsPage($scope.pagination.current);
        };

        getDownloadsPage(1);

        $scope.pageChanged = function (newPage) {
            getDownloadsPage(newPage);
        };
        
        function getDownloadsPage(pageNumber) {
            $http.get("internalapi/getnzbdownloads", {params:{page: pageNumber, limit: $scope.limit, type: $scope.type}}).success(function (response) {
                $scope.nzbDownloads = response.nzbDownloads;
                $scope.totalDownloads = response.totalDownloads;
            });
        }


    }
}
angular
    .module('nzbhydraApp')
    .directive('cfgFormEntry', cfgFormEntry);

function cfgFormEntry() {
    return {
        templateUrl: 'static/html/directives/cfg-form-entry.a54d5a07.html',
        require: ["^title", "^cfg"],
        scope: {
            title: "@",
            cfg: "=",
            help: "@",
            type: "@?",
            options: "=?"
        },
        controller: ["$scope", "$element", "$attrs", function ($scope, $element, $attrs) {
            $scope.type = angular.isDefined($scope.type) ? $scope.type : 'text';
            $scope.options = angular.isDefined($scope.type) ? $scope.$eval($attrs.options) : [];
        }]
    };
}
angular
    .module('nzbhydraApp')
    .directive('addableNzb', addableNzb);

function addableNzb() {
    controller.$inject = ["$scope", "ConfigService", "NzbDownloadService", "growl"];
    return {
        templateUrl: 'static/html/directives/addable-nzb.23bf7a2d.html',
        require: ['^indexerguid', '^title', '^indexer', '^dbsearchid'],
        scope: {
            indexerguid: "=",
            title: "=",
            indexer: "=",
            dbsearchid: "="
        },
        controller: controller
    };

    function controller($scope, ConfigService, NzbDownloadService, growl) {
        $scope.classname = "";
        
        ConfigService.getSafe().then(function (settings) {
            $scope.downloader = settings.downloader.downloader;
            if ($scope.downloader != "none") {
                $scope.enabled = true;
                $scope.classname = $scope.downloader == "sabnzbd" ? "sabnzbd" : "nzbget";
            } else {
                $scope.enabled = false;
            }
            
        });
        
        $scope.add = function() {
            $scope.classname = "nzb-spinning";
            NzbDownloadService.download([{"indexerguid": $scope.indexerguid, "title": $scope.title, "indexer": $scope.indexer, "dbsearchid": $scope.dbsearchid}]).then(function (response) {
                if (response.data.success) {
                    $scope.classname = $scope.downloader == "sabnzbd" ? "sabnzbd-success" : "nzbget-success";
                } else {
                    $scope.classname = $scope.downloader == "sabnzbd" ? "sabnzbd-error" : "nzbget-error";
                    growl.error("Unable to add NZB. Make sure the downloader is running and properly configured.");
                }
            }, function() {
                $scope.classname = $scope.downloader == "sabnzbd" ? "sabnzbd-error" : "nzbget-error";
                growl.error("An unexpected error occurred while trying to contact NZB Hydra or add the NZB.");
            })
        };

    }
}


angular
    .module('nzbhydraApp')
    .factory('UpdateService', UpdateService);

function UpdateService($http, growl, blockUI, RestartService) {

    var currentVersion;
    var repVersion;
    var updateAvailable;
    var changelog;
    var versionHistory;
    
    return {
        update: update,
        showChanges: showChanges,
        getVersions: getVersions,
        getChangelog: getChangelog,
        getVersionHistory: getVersionHistory
    };
    
    
    
    function getVersions() {
        return $http.get("internalapi/get_versions").then(function (data) {
            currentVersion = data.data.currentVersion;
            repVersion = data.data.repVersion;
            updateAvailable = data.data.updateAvailable;
            return data;
        });
    }

    function getChangelog() {
        return $http.get("internalapi/get_changelog").then(function (data) {
            changelog = data.data.changelog;
            return data;
        });
    }
    
    function getVersionHistory() {
        return $http.get("internalapi/get_version_history").then(function (data) {
            versionHistory = data.data.versionHistory;
            return data;
        });
    }

    function showChanges() {

        var myInjector = angular.injector(["ng", "ui.bootstrap"]);
        var $uibModal = myInjector.get("$uibModal");
        var params = {
            size: "lg",
            templateUrl: "static/html/changelog.dbc51f8b.html",
            resolve: {
                changelog: function () {
                    return changelog;
                }
            },
            controller: function ($scope, $sce, $uibModalInstance, changelog) {
                //I fucking hate that untrusted HTML shit
                changelog = $sce.trustAsHtml(changelog);
                $scope.changelog = changelog;
                console.log(changelog);
                $scope.ok = function () {
                    $uibModalInstance.dismiss();
                };
            }
        };

        var modalInstance = $uibModal.open(params);

        modalInstance.result.then();
    }
    

    function update() {
        blockUI.start("Updating. Please stand by...");
        $http.get("internalapi/update").then(function (data) {
                if (data.data.success) {
                    RestartService.countdownAndReload("Update complete.");
                } else {
                    blockUI.reset();
                    growl.info("An error occurred while updating. Please check the logs.");
                }
            },
            function () {
                blockUI.reset();
                growl.info("An error occurred while updating. Please check the logs.");
            });
    }
}
UpdateService.$inject = ["$http", "growl", "blockUI", "RestartService"];


angular
    .module('nzbhydraApp')
    .controller('UpdateFooterController', UpdateFooterController);

function UpdateFooterController($scope, UpdateService) {

    $scope.updateAvailable = false;
    
    UpdateService.getVersions().then(function(data) {
        $scope.currentVersion = data.data.currentVersion;
        $scope.repVersion = data.data.repVersion;
        $scope.updateAvailable = data.data.updateAvailable;
        if ($scope.repVersion > $scope.currentVersion) {
            UpdateService.getChangelog().then(function (data) {
                $scope.changelog = data.data.changelog;
            })
        } 
    });
    

    $scope.update = function () {
        UpdateService.update();
    };

    $scope.showChangelog = function () {
        UpdateService.showChanges($scope.changelog);
    }

}
UpdateFooterController.$inject = ["$scope", "UpdateService"];

angular
    .module('nzbhydraApp')
    .controller('SystemController', SystemController);

function SystemController($scope, $state, growl, RestartService, NzbHydraControlService) {


    $scope.shutdown = function () {
        NzbHydraControlService.shutdown().then(function () {
                growl.info("Shutdown initiated. Cya!");
            },
            function () {
                growl.info("Unable to send shutdown command.");
            })
    };

    $scope.restart = function () {
        RestartService.restart();
    };
    

    $scope.tabs = [
        {
            active: false,
            state: 'system'
        },
        {
            active: false,
            state: 'system.updates'
        },
        {
            active: false,
            state: 'system.log'
        },
        {
            active: false,
            state: 'system.about'
        }
    ];


    for (var i = 0; i < $scope.tabs.length; i++) {
        if ($state.is($scope.tabs[i].state)) {
            $scope.tabs[i].active = true;
        }
    }


    $scope.goToState = function (index) {
        $state.go($scope.tabs[index].state);
    }
    
    
}
SystemController.$inject = ["$scope", "$state", "growl", "RestartService", "NzbHydraControlService"];

angular
    .module('nzbhydraApp')
    .factory('StatsService', StatsService);

function StatsService($http) {
    
    return {
        get: getStats
    };

    function getStats() {
            return $http.get("internalapi/getstats").success(function (response) {
               return response.data;
            });

    }

}
StatsService.$inject = ["$http"];
angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope, stats, $state) {

    stats = stats.data;
    $scope.nzbDownloads = null;
    $scope.avgResponseTimes = stats.avgResponseTimes;
    $scope.avgIndexerSearchResultsShares = stats.avgIndexerSearchResultsShares;
    $scope.avgIndexerAccessSuccesses = stats.avgIndexerAccessSuccesses;


    $scope.tabs = [
        {
            active: false,
            state: 'stats'
        },
        {
            active: false,
            state: 'stats.indexers'
        },
        {
            active: false,
            state: 'stats.searches'
        },
        {
            active: false,
            state: 'stats.downloads'
        }
    ];


    for (var i = 0; i < $scope.tabs.length; i++) {
        if ($state.is($scope.tabs[i].state)) {
            $scope.tabs[i].active = true;
        }
    }
    

    $scope.goToState = function (index) {
        $state.go($scope.tabs[index].state);
    }


}
StatsController.$inject = ["$scope", "stats", "$state"];

angular
    .module('nzbhydraApp')
    .factory('SearchService', SearchService);

function SearchService($http) {


    var lastExecutedQuery;

    var service = {search: search, loadMore: loadMore};
    return service;

    function search(category, query, tmdbid, title, tvdbid, season, episode, minsize, maxsize, minage, maxage, indexers) {
        console.log("Category: " + category);
        var uri;
        if (category.indexOf("Movies") > -1 || (category.indexOf("20") == 0)) {
            console.log("Search for movies");
            uri = new URI("internalapi/moviesearch");
            if (!_.isUndefined(tmdbid)) {
                console.log("moviesearch per tmdbid");
                uri.addQuery("tmdbid", tmdbid);
                uri.addQuery("title", title);
            } else {
                console.log("moviesearch per query");
                uri.addQuery("query", query);
            }

        } else if (category.indexOf("TV") > -1 || (category.indexOf("50") == 0)) {
            console.log("Search for shows");
            uri = new URI("internalapi/tvsearch");
            if (!_.isUndefined(tvdbid)) {
                uri.addQuery("tvdbid", tvdbid);
                uri.addQuery("title", title);
            } else {
                console.log("tvsearch per query");
                uri.addQuery("query", query);
            }

            if (!_.isUndefined(season)) {
                uri.addQuery("season", season);
            }
            if (!_.isUndefined(episode)) {
                uri.addQuery("episode", episode);
            }
        } else {
            console.log("Search for all");
            uri = new URI("internalapi/search");
            uri.addQuery("query", query);
        }

        if (_.isNumber(minsize)) {
            uri.addQuery("minsize", minsize);
        }
        if (_.isNumber(maxsize)) {
            uri.addQuery("maxsize", maxsize);
        }
        if (_.isNumber(minage)) {
            uri.addQuery("minage", minage);
        }
        if (_.isNumber(maxage)) {
            uri.addQuery("maxage", maxage);
        }
        if (!angular.isUndefined(indexers)) {
            uri.addQuery("indexers", decodeURIComponent(indexers));
        }
        

        uri.addQuery("category", category);

        console.log("Calling " + uri);
        lastExecutedQuery = uri;
        return $http.get(uri).then(processData);

    }

    function loadMore(offset) {
        lastExecutedQuery.removeQuery("offset");
        lastExecutedQuery.addQuery("offset", offset);

        console.log("Calling " + lastExecutedQuery);
        return $http.get(lastExecutedQuery).then(processData);
    }

    function processData(response) {
        var results = response.data.results;
        var indexersearches = response.data.indexersearches;
        var total = response.data.total;
        var resultsCount = results.length;


        //Sum up response times of indexers from individual api accesses
        //TODO: Move this to search result controller because we need to update it every time we loaded more results
        _.each(indexersearches, function (ps) {
            if (ps.did_search) {
                ps.averageResponseTime = _.reduce(ps.api_accesses, function (memo, rp) {
                    return memo + rp.response_time;
                }, 0);
                ps.averageResponseTime = ps.averageResponseTime / ps.api_accesses.length;
            }
        });
        

        return {"results": results, "indexersearches": indexersearches, "total": total, "resultsCount": resultsCount}
    }
}
SearchService.$inject = ["$http"];
angular
    .module('nzbhydraApp')
    .controller('SearchResultsController', SearchResultsController);

//SearchResultsController.$inject = ['blockUi'];
function SearchResultsController($stateParams, $scope, $q, $timeout, blockUI, SearchService,growl, NzbDownloadService) {

    $scope.sortPredicate = "epoch";
    $scope.sortReversed = true;
    $scope.limitTo = 100;
    $scope.offset = 0;
    //Handle incoming data
    $scope.indexersearches = $stateParams.indexersearches;
    $scope.indexerDisplayState = []; //Stores if a indexer's results should be displayed or not
    $scope.indexerResultsInfo = {}; //Stores information about the indexer's results like how many we already retrieved
    $scope.groupExpanded = {};
    $scope.doShowDuplicates = false;
    $scope.selected = [];
    
    $scope.countFilteredOut = 0;

    //Initially set visibility of all found indexers to true, they're needed for initial filtering / sorting
    _.forEach($scope.indexersearches, function (ps) {
        $scope.indexerDisplayState[ps.indexer.toLowerCase()] = true;
    });

    _.forEach($scope.indexersearches, function (ps) {
        $scope.indexerResultsInfo[ps.indexer.toLowerCase()] = {loadedResults: ps.loaded_results};
    });
    

    //Process results
    $scope.results = $stateParams.results;
    $scope.total = $stateParams.total;
    $scope.resultsCount = $stateParams.resultsCount;
    $scope.filteredResults = sortAndFilter($scope.results);
    stopBlocking();


    //Returns the content of the property (defined by the current sortPredicate) of the first group element 
    $scope.firstResultPredicate = firstResultPredicate;
    function firstResultPredicate(item) {
        return item[0][$scope.sortPredicate];
    }

    //Returns the unique group identifier which allows angular to keep track of the grouped search results even after filtering, making filtering by indexers a lot faster (albeit still somewhat slow...)  
    $scope.groupId = groupId;
    function groupId(item) {
        return item[0][0].guid;
    }

    //Block the UI and return after timeout. This way we make sure that the blocking is done before angular starts updating the model/view. There's probably a better way to achieve that?
    function startBlocking(message) {
        var deferred = $q.defer();
        blockUI.start(message);
        $timeout(function () {
            deferred.resolve();
        }, 100);
        return deferred.promise;
    }

    //Set sorting according to the predicate. If it's the same as the old one, reverse, if not sort by the given default (so that age is descending, name ascending, etc.)
    //Sorting (and filtering) are really slow (about 2 seconds for 1000 results from 5 indexers) but I haven't found any way of making it faster, apart from the tracking 
    $scope.setSorting = setSorting;
    function setSorting(predicate, reversedDefault) {
        startBlocking("Sorting / filtering...").then(function () {

            if (predicate == $scope.sortPredicate) {
                $scope.sortReversed = !$scope.sortReversed;
            } else {
                $scope.sortReversed = reversedDefault;
            }
            $scope.sortPredicate = predicate;
            $scope.filteredResults = sortAndFilter($scope.results);
            blockUI.reset();
        });
    }


    
    function sortAndFilter(results) {
        $scope.countFilteredOut = 0;
        function filterByAgeAndSize(item) {
            var filterOut = !(_.isNumber($stateParams.minsize) && item.size / 1024 / 1024 < $stateParams.minsize)
                && !(_.isNumber($stateParams.maxsize) && item.size / 1024 / 1024 > $stateParams.maxsize)
                && !(_.isNumber($stateParams.minage) && item.age_days < $stateParams.minage)
                && !(_.isNumber($stateParams.maxage) && item.age_days > $stateParams.maxage);
            if (!filterOut) {
                $scope.countFilteredOut++;
            }
            return filterOut;
        }
        
        
        function getItemIndexerDisplayState(item) {
            return $scope.indexerDisplayState[item.indexer.toLowerCase()];
        }

        function getCleanedTitle(element) {
            return element.title.toLowerCase().replace(/[\s\-\._]/ig, "");
        }

        function createSortedHashgroups(titleGroup) {

            function createHashGroup(hashGroup) {
                //Sorting hash group's contents should not matter for size and age and title but might for category (we might remove this, it's probably mostly unnecessary)
                var sortedHashGroup = _.sortBy(hashGroup, function (item) {
                    var sortPredicateValue = item[$scope.sortPredicate];
                    return $scope.sortReversed ? -sortPredicateValue : sortPredicateValue;
                });
                //Now sort the hash group by indexer score (inverted) so that the result with the highest indexer score is shown on top (or as the only one of a hash group if it's collapsed)
                sortedHashGroup = _.sortBy(sortedHashGroup, function (item) {
                    return item.indexerscore * -1;
                });
                return sortedHashGroup;
            }

            function getHashGroupFirstElementSortPredicate(hashGroup) {
                var sortPredicateValue = hashGroup[0][$scope.sortPredicate];
                return $scope.sortReversed ? -sortPredicateValue : sortPredicateValue;
            }

            return _.chain(titleGroup).groupBy("hash").map(createHashGroup).sortBy(getHashGroupFirstElementSortPredicate).value();
        }

        function getTitleGroupFirstElementsSortPredicate(titleGroup) {
            var sortPredicateValue = titleGroup[0][0][$scope.sortPredicate];
            return $scope.sortReversed ? -sortPredicateValue : sortPredicateValue;
        }

        var filtered = _.chain(results)
            //Remove elements of which the indexer is currently hidden    
            .filter(getItemIndexerDisplayState)
            //and which were not filtered by the indexers (because they don't support queries with min/max size/age)
            .filter(filterByAgeAndSize)
            //Make groups of results with the same title    
            .groupBy(getCleanedTitle)
            //For every title group make subgroups of duplicates and sort the group    
            .map(createSortedHashgroups)
            //And then sort the title group using its first hashgroup's first item (the group itself is already sorted and so are the hash groups)    
            .sortBy(getTitleGroupFirstElementsSortPredicate)
            .value();
        if ($scope.countFilteredOut > 0) {
            growl.info("Filtered " + $scope.countFilteredOut + " of the retrieved results");
        }
        return filtered;

    }

    $scope.toggleTitlegroupExpand = function toggleTitlegroupExpand(titleGroup) {
        $scope.groupExpanded[titleGroup[0][0].title] = !$scope.groupExpanded[titleGroup[0][0].title];
        $scope.groupExpanded[titleGroup[0][0].hash] = !$scope.groupExpanded[titleGroup[0][0].hash];
    };


//Clear the blocking
    $scope.stopBlocking = stopBlocking;
    function stopBlocking() {
        blockUI.reset();
    }

    $scope.loadMore = loadMore;
    function loadMore() {
        console.log("Loading more result withs offset " + $scope.resultsCount);

        startBlocking("Loading more results...").then(function () {
            SearchService.loadMore($scope.resultsCount).then(function (data) {
                console.log("Returned more results:");
                console.log(data.results);
                console.log($scope.results);
                console.log("Total: " + data.total);
                $scope.results = $scope.results.concat(data.results);
                $scope.filteredResults = sortAndFilter($scope.results);
                $scope.total = data.total;
                $scope.resultsCount += data.resultsCount;
                console.log("Results count: " + $scope.resultsCount);
                console.log("Total results in $scope.results: " + $scope.results.length);

                stopBlocking();
            });
        });
    }


//Filters the results according to new visibility settings.
    $scope.toggleIndexerDisplay = toggleIndexerDisplay;
    function toggleIndexerDisplay(indexer) {
        $scope.indexerDisplayState[indexer.toLowerCase()] = $scope.indexerDisplayState[indexer.toLowerCase()]; 
        startBlocking("Filtering. Sorry...").then(function () {
            $scope.filteredResults = sortAndFilter($scope.results);
        }).then(function () {
            stopBlocking();
        });
    }

    $scope.countResults = countResults;
    function countResults() {
        return $scope.results.length;
    }

    $scope.downloadSelected = downloadSelected;
    function downloadSelected() {

        if (angular.isUndefined($scope.selected) || $scope.selected.length == 0) {
            growl.info("You should select at least one result...");
        } else {

            var values = _.map($scope.selected, function (value) {
                return {"indexerguid": value.indexerguid, "title": value.title, "indexer": value.indexer, "dbsearchid": value.dbsearchid}
            });

            console.log(values);
            NzbDownloadService.download(values).then(function (response) {
                if (response.data.success) {
                    growl.info("Successfully added " + response.data.added + " of " + response.data.of + " NZBs");
                } else {
                    growl.error("Error while adding NZBs");
                }
            }, function () {
                growl.error("Error while adding NZBs");
            });
        }
    }
    
    $scope.invertSelection = function invertSelection() {
        $scope.selected = _.difference($scope.results, $scope.selected);
    }

}
SearchResultsController.$inject = ["$stateParams", "$scope", "$q", "$timeout", "blockUI", "SearchService", "growl", "NzbDownloadService"];
angular
    .module('nzbhydraApp')
    .controller('SearchController', SearchController);

function SearchController($scope, $http, $stateParams, $state, SearchService, focus, ConfigService, blockUI) {
    
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

    //Fill the form with the search values we got from the state params (so that their values are the same as in the current url)
    $scope.mode = $stateParams.mode;
    
    $scope.category = (_.isUndefined($stateParams.category) || $stateParams.category == "") ? "All" : $stateParams.category;
    $scope.tmdbid = $stateParams.tmdbid;
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
    if (!_.isUndefined($scope.title) && _.isUndefined($scope.query)) {
        $scope.query = $scope.title;
    }
    if (!angular.isUndefined($stateParams.indexers)) {
        $scope.indexers = decodeURIComponent($stateParams.indexers).split("|");
    }

    $scope.showIndexers = {};

    var safeConfig;


    $scope.typeAheadWait = 300;
    $scope.selectedItem = "";
    $scope.autocompleteLoading = false;
    $scope.isAskById = ($scope.category.indexOf("TV") > -1 || $scope.category.indexOf("Movies") > -1 ); //If true a check box will be shown asking the user if he wants to search by ID 
    $scope.isById = {value: true}; //If true the user wants to search by id so we enable autosearch. Was unable to achieve this using a simple boolean
    $scope.availableIndexers = [];
    $scope.autocompleteClass = "autocompletePosterMovies";

    $scope.toggle = function (searchCategory) {
        $scope.category = searchCategory;

        //Show checkbox to ask if the user wants to search by ID (using autocomplete)
        $scope.isAskById = ($scope.category.indexOf("TV") > -1 || $scope.category.indexOf("Movies") > -1 );

        focus('focus-query-box');
        $scope.query = "";

        if (safeConfig.searching.categorysizes.enable_category_sizes) {
            var min = safeConfig.searching.categorysizes[(searchCategory + " min").toLowerCase().replace(" ", "")];
            var max = safeConfig.searching.categorysizes[(searchCategory + " max").toLowerCase().replace(" ", "")];
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
        var indexers = angular.isUndefined($scope.indexers) ? undefined : $scope.indexers.join("|");
        SearchService.search($scope.category, $scope.query, $stateParams.tmdbid, $scope.title, $scope.tvdbid, $scope.season, $scope.episode, $scope.minsize, $scope.maxsize, $scope.minage, $scope.maxage, indexers).then(function (searchResult) {
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
            $scope.tmdbid = undefined;
            $scope.tvdbid = undefined;
        });
    };
    
    function getSelectedIndexers() {
        var activatedIndexers = _.filter($scope.availableIndexers).filter(function (indexer) {
            return indexer.activated ;
        });
            return _.pluck(activatedIndexers, "name").join("|");
    }


    $scope.goToSearchUrl = function () {
        var stateParams = {};
        if ($scope.category.indexOf("Movies") > -1) {
            stateParams.mode = "moviesearch";
            stateParams.title = $scope.title;
            stateParams.mode = "moviesearch";
        } else if ($scope.category.indexOf("TV") > -1) {
            stateParams.mode = "tvsearch";
            stateParams.title = $scope.title;
        } else if ($scope.category == "Ebook") {
            stateParams.mode = "ebook";
        } else {
            stateParams.mode = "search";
        }
        
        stateParams.tmdbid = $scope.tmdbid;
        stateParams.tvdbid = $scope.tvdbid;
        stateParams.title = $scope.title;
        stateParams.season = $scope.season;
        stateParams.episode = $scope.episode;
        stateParams.query = $scope.query;
        stateParams.minsize = $scope.minsize;
        stateParams.maxsize = $scope.maxsize;
        stateParams.minage = $scope.minage;
        stateParams.maxage = $scope.maxage;
        stateParams.category = $scope.category;
        stateParams.indexers = encodeURIComponent(getSelectedIndexers());
        
        $state.go("search", stateParams, {inherit: false, notify: true, reload: true});
    };


    $scope.selectAutocompleteItem = function ($item) {
        $scope.selectedItem = $item;
        $scope.title = $item.title;
        if ($scope.category.indexOf("Movies") > -1) {
            $scope.tmdbid = $item.value;
        } else if ($scope.category.indexOf("TV") > -1) {
            $scope.tvdbid = $item.value;
        }
        $scope.query = "";
        $scope.goToSearchUrl();
    };
    
    $scope.startQuerySearch = function() {
        //Reset values because they might've been set from the last search
        $scope.title = undefined;
        $scope.tmdbid = undefined;
        $scope.tvdbid = undefined;
        $scope.goToSearchUrl();
    };


    $scope.autocompleteActive = function () {
        return ($scope.category.indexOf("TV") > -1) || ($scope.category.indexOf("Movies") > -1)
    };

    $scope.seriesSelected = function () {
        return ($scope.category.indexOf("TV") > -1);
    };
    
    $scope.toggleIndexer = function(indexer) {
        $scope.indexers[indexer] = !$scope.indexers[indexer]
    };
    

    function isIndexerPreselected(indexer) {
        if (angular.isUndefined($scope.indexers)) {
            return indexer.preselect;
        } else {
            return _.contains($scope.indexers, indexer.name);
        }
        
    }

    ConfigService.getSafe().then(function (cfg) {
        safeConfig = cfg;
        $scope.availableIndexers = _.chain(cfg.indexers).filter(function (indexer) {
            return indexer.enabled && indexer.showOnSearch;
        }).sortBy("name")
            .map(function (indexer) {
            return {name: indexer.name, activated: isIndexerPreselected(indexer)};
        }).value();
        
    });

    if ($scope.mode) {
        console.log("Starting search in newly loaded search controller");
        $scope.startSearch();
    }


    


}
SearchController.$inject = ["$scope", "$http", "$stateParams", "$state", "SearchService", "focus", "ConfigService", "blockUI"];

angular
    .module('nzbhydraApp')
    .factory('RestartService', RestartService);

function RestartService(blockUI, $timeout, $window, NzbHydraControlService) {

    return {
        restart: restart,
        countdownAndReload: countdownAndReload
    };

    function countdownAndReload(message) {
        message = angular.isUndefined ? "" : " ";

        blockUI.start(message + "Restarting. Will reload page in 5 seconds...");
        $timeout(function () {
            blockUI.start(message + "Restarting. Will reload page in 4 seconds...");
            $timeout(function () {
                blockUI.start(message + "Restarting. Will reload page in 3 seconds...");
                $timeout(function () {
                    blockUI.start(message + "Restarting. Will reload page in 2 seconds...");
                    $timeout(function () {
                        blockUI.start(message + "Restarting. Will reload page in 1 second...");
                        $timeout(function () {
                            blockUI.start("Reloading page...");
                            $window.location.reload();
                        }, 1000);
                    }, 1000);
                }, 1000);
            }, 1000);
        }, 1000);
    }

    function restart(message) {
        NzbHydraControlService.restart().then(countdownAndReload(message),
            function () {
                growl.info("Unable to send restart command.");
            }
        )
    }
}
RestartService.$inject = ["blockUI", "$timeout", "$window", "NzbHydraControlService"];

angular
    .module('nzbhydraApp')
    .factory('NzbHydraControlService', NzbHydraControlService);

function NzbHydraControlService($http) {

    return {
        restart: restart,
        shutdown: shutdown
    };

    function restart() {
        return $http.get("internalapi/restart");
    }

    function shutdown() {
        return $http.get("internalapi/shutdown");
    }
}
NzbHydraControlService.$inject = ["$http"];

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
NzbDownloadService.$inject = ["$http", "ConfigService", "CategoriesService"];


angular
    .module('nzbhydraApp')
    .factory('ModalService', ModalService);

function ModalService($uibModal) {
    
    return {
        open: openModal
    };
    
    function openModal(headline, message, ok, cancel) {
        var modalInstance = $uibModal.open({
            templateUrl: 'static/html/modal.ca80df29.html',
            controller: 'ModalInstanceCtrl',
            size: 'md',
            resolve: {
                headline: function () {
                    return headline
                },
                message: function(){ return message},
                ok: function() {
                    return ok;
                },
                cancel: function() {
                    return cancel;
                }
            }
        });

        modalInstance.result.then(function() {
            
        }, function() {
            cancel();
        });
    }
    
}
ModalService.$inject = ["$uibModal"];

angular
    .module('nzbhydraApp')
    .controller('ModalInstanceCtrl', ModalInstanceCtrl);

function ModalInstanceCtrl($scope, $uibModalInstance, headline, message, ok, cancel) {

    $scope.message = message;
    $scope.headline = headline;

    $scope.ok = function () {
        $uibModalInstance.close();
        if(!angular.isUndefined(ok)) {
            ok();
        }
    };

    $scope.cancel = function () {
        $uibModalInstance.dismiss();
        if (!angular.isUndefined(cancel)) {
            cancel();
        }
    };
}
ModalInstanceCtrl.$inject = ["$scope", "$uibModalInstance", "headline", "message", "ok", "cancel"];

angular
    .module('nzbhydraApp')
    .service('GeneralModalService', GeneralModalService);

function GeneralModalService() {
    
    
    this.open = function (msg, template, templateUrl, size, data) {
        
        //Prevent circular dependency
        var myInjector = angular.injector(["ng", "ui.bootstrap"]);
        var $uibModal = myInjector.get("$uibModal");
        var params = {};
        
        if(angular.isUndefined(size)) {
            params["size"] = size;
        }
        if (angular.isUndefined(template)) {
            if (angular.isUndefined(templateUrl)) {
                params["template"] = '<pre>' + msg + '</pre>';
            } else {
                params["templateUrl"] = templateUrl;
            }
        } else {
            params["template"] = template;
        }
        params["resolve"] = 
        {
            data: function () {
                console.log(data);
                return data;
            }
        };
        console.log(params);
        
        var modalInstance = $uibModal.open(params);

        modalInstance.result.then();

    };
    
   
}
var HEADER_NAME = 'MyApp-Handle-Errors-Generically';
var specificallyHandleInProgress = false;

nzbhydraapp.factory('RequestsErrorHandler',  ["$q", "growl", "blockUI", "GeneralModalService", function ($q, growl, blockUI, GeneralModalService) {
    return {
        // --- The user's API for claiming responsiblity for requests ---
        specificallyHandled: function (specificallyHandledBlock) {
            specificallyHandleInProgress = true;
            try {
                return specificallyHandledBlock();
            } finally {
                specificallyHandleInProgress = false;
            }
        },

        // --- Response interceptor for handling errors generically ---
        responseError: function (rejection) {
            blockUI.reset();
            var shouldHandle = (rejection && rejection.config && rejection.config.headers && rejection.config.headers[HEADER_NAME]);
            
            if (shouldHandle) {
                var message = "An error occured :<br>" + rejection.status + ": " + rejection.statusText;

                if (rejection.data) {
                    message += "<br><br>" + rejection.data;
                }
                GeneralModalService.open(message);

            }

            return $q.reject(rejection);
        }
    };
}]);


nzbhydraapp.config(['$provide', '$httpProvider', function ($provide, $httpProvider) {
    $httpProvider.interceptors.push('RequestsErrorHandler');

    // --- Decorate $http to add a special header by default ---

    function addHeaderToConfig(config) {
        config = config || {};
        config.headers = config.headers || {};

        // Add the header unless user asked to handle errors himself
        if (!specificallyHandleInProgress) {
            config.headers[HEADER_NAME] = true;
        }

        return config;
    }

    // The rest here is mostly boilerplate needed to decorate $http safely
    $provide.decorator('$http', ['$delegate', function ($delegate) {
        function decorateRegularCall(method) {
            return function (url, config) {
                return $delegate[method](url, addHeaderToConfig(config));
            };
        }

        function decorateDataCall(method) {
            return function (url, data, config) {
                return $delegate[method](url, data, addHeaderToConfig(config));
            };
        }

        function copyNotOverriddenAttributes(newHttp) {
            for (var attr in $delegate) {
                if (!newHttp.hasOwnProperty(attr)) {
                    if (typeof($delegate[attr]) === 'function') {
                        newHttp[attr] = function () {
                            return $delegate.apply($delegate, arguments);
                        };
                    } else {
                        newHttp[attr] = $delegate[attr];
                    }
                }
            }
        }

        var newHttp = function (config) {
            return $delegate(addHeaderToConfig(config));
        };

        newHttp.get = decorateRegularCall('get');
        newHttp.delete = decorateRegularCall('delete');
        newHttp.head = decorateRegularCall('head');
        newHttp.jsonp = decorateRegularCall('jsonp');
        newHttp.post = decorateDataCall('post');
        newHttp.put = decorateDataCall('put');

        copyNotOverriddenAttributes(newHttp);

        return newHttp;
    }]);
}]);
angular
    .module('nzbhydraApp')
    .config(["formlyConfigProvider", function config(formlyConfigProvider) {
        formlyConfigProvider.extras.removeChromeAutoComplete = true;

        // set templates here
        formlyConfigProvider.setWrapper({
            name: 'horizontalBootstrapLabel',
            template: [
                '<div class="form-group form-horizontal" ng-class="{\'row\': !options.templateOptions.noRow}">',
                '<div style="text-align:right;">',
                '<label for="{{::id}}" class="col-md-7 control-label">',
                '{{to.label}} {{to.required ? "*" : ""}}',
                '</label>',
                '</div>',
                '<div class="col-md-6">',
                '<formly-transclude></formly-transclude>',
                '</div>',
                '<span class="col-md-7 help-block">{{to.help}}</div>',
                '</div>'
            ].join(' ')
        });


        formlyConfigProvider.setWrapper({
            name: 'fieldset',
            template: [
                '<fieldset>',
                '<legend>{{options.templateOptions.label}}</legend>',
                '<formly-transclude></formly-transclude>',
                '</fieldset>'
            ].join(' ')
        });

        formlyConfigProvider.setWrapper({
            name: 'logicalGroup',
            template: [
                '<formly-transclude></formly-transclude>'
            ].join(' ')
        });

        formlyConfigProvider.setType({
            name: 'horizontalInput',
            extends: 'input',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'percentInput',
            template: [
                '<input type="number" class="form-control" placeholder="Percent" ng-model="model[options.key]" ng-pattern="/^[0-9]+(\.[0-9]{1,2})?$/" step="0.01" required />'
            ].join(' ')
        });

        formlyConfigProvider.setType({
            name: 'apiKeyInput',
            template: [
                '<div class="input-group">',
                '<input type="text" class="form-control" ng-model="model[options.key]"/>',
                '<span class="input-group-btn input-group-btn2">',
                '<button class="btn btn-default" type="button" ng-click="generate()"><span class="glyphicon glyphicon-refresh"></span></button>',
                '</div>'
            ].join(' '),
            controller: function ($scope) {
                $scope.generate = function () {
                    $scope.model[$scope.options.key] = (Math.random() * 1e32).toString(36);
                }
            }
        });

        formlyConfigProvider.setType({
            name: 'testConnection',
            templateUrl: 'button-test-connection.html',
            controller: function ($scope) {
                $scope.message = "";

                var testButton = "#button-test-connection-" + $scope.formId;
                var testMessage = "#message-test-connection-" + $scope.formId;

                function showSuccess() {
                    angular.element(testButton).removeClass("btn-default");
                    angular.element(testButton).removeClass("btn-danger");
                    angular.element(testButton).addClass("btn-success");
                }

                function showError() {
                    angular.element(testButton).removeClass("btn-default");
                    angular.element(testButton).removeClass("btn-success");
                    angular.element(testButton).addClass("btn-danger");
                }

                $scope.testConnection = function () {
                    angular.element(testButton).addClass("glyphicon-refresh-animate");
                    var myInjector = angular.injector(["ng"]);
                    var $http = myInjector.get("$http");
                    var url;
                    var params;
                    if ($scope.to.testType == "downloader") {
                        url = "internalapi/test_downloader";
                        params = {name: $scope.to.downloader, username: $scope.model.username, password: $scope.model.password};
                        if ($scope.to.downloader == "sabnzbd") {
                            params.apikey = $scope.model.apikey;
                            params.url = $scope.model.url;
                        } else {
                            params.host = $scope.model.host;
                            params.port = $scope.model.port;
                            params.ssl = $scope.model.ssl;
                        }
                    } else if ($scope.to.testType == "newznab") {
                        url = "internalapi/test_newznab";
                        params = {host: $scope.model.host, apikey: $scope.model.apikey};
                    } else if ($scope.to.testType == "omgwtf") {
                        url = "internalapi/test_omgwtf";
                        params = {username: $scope.model.username, apikey: $scope.model.apikey};
                    }
                    $http.get(url, {params: params}).success(function (result) {
                        //Using ng-class and a scope variable doesn't work for some reason, is only updated at second click 
                        if (result.result) {
                            angular.element(testMessage).text("");
                            showSuccess();
                        } else {
                            angular.element(testMessage).text(result.message);
                            showError();
                        }

                    }).error(function () {
                        angular.element(testMessage).text(result.message);
                        showError();
                    }).finally(function () {
                        angular.element(testButton).removeClass("glyphicon-refresh-animate");
                    })
                }
            }
        });

        formlyConfigProvider.setType({
            name: 'checkCaps',
            templateUrl: 'button-check-caps.html',
            controller: function ($scope) {
                $scope.message = "";

                var testButton = "#button-check-caps-" + $scope.formId;
                var testMessage = "#message-check-caps-" + $scope.formId;

                function showSuccess() {
                    angular.element(testButton).removeClass("btn-default");
                    angular.element(testButton).removeClass("btn-danger");
                    angular.element(testButton).addClass("btn-success");
                }

                function showError() {
                    angular.element(testButton).removeClass("btn-default");
                    angular.element(testButton).removeClass("btn-success");
                    angular.element(testButton).addClass("btn-danger");
                }

                $scope.checkCaps = function () {
                    angular.element(testButton).addClass("glyphicon-refresh-animate");
                    var myInjector = angular.injector(["ng"]);
                    var $http = myInjector.get("$http");
                    var url;
                    var params;

                    url = "internalapi/test_caps";
                    params = {indexer: $scope.model.name, apikey: $scope.model.apikey, host: $scope.model.host};
                    $http.get(url, {params: params}).success(function (result) {
                        //Using ng-class and a scope variable doesn't work for some reason, is only updated at second click 
                        if (result.success) {
                            angular.element(testMessage).text("Supports: " + result.result);
                            $scope.$apply(function () {
                                $scope.model.search_ids = result.result;
                            });
                            showSuccess();
                        } else {
                            angular.element(testMessage).text(result.message);
                            showError();
                        }

                    }).error(function () {
                        angular.element(testMessage).text(result.message);
                        showError();
                    }).finally(function () {
                        angular.element(testButton).removeClass("glyphicon-refresh-animate");
                    })
                }
            }
        });

        formlyConfigProvider.setType({
            name: 'horizontalNewznabPreset',
            wrapper: ['horizontalBootstrapLabel'],
            templateUrl: 'newznab-preset.html',
            controller: function ($scope) {
                $scope.display = "";
                $scope.selectedpreset = undefined;

                $scope.presets = [
                    {
                        name: "None"
                    },
                    {
                        name: "DogNZB",
                        host: "https://api.dognzb.cr",
                        searchIds: ["tvdbid", "rid", "imdbid"]
                    },
                    {
                        name: "NZBs.org",
                        host: "https://nzbs.org",
                        searchIds: ["tvdbid", "rid", "imdbid", "tvmazeid"]
                    },
                    {
                        name: "nzb.su",
                        host: "https://api.nzb.su",
                        searchIds: ["rid", "imdbid"]
                    },
                    {
                        name: "nzbgeek",
                        host: "https://api.nzbgeek.info",
                        searchIds: ["tvdbid", "rid", "imdbid"]
                    },
                    {
                        name: "6box nzedb",
                        host: "https://nzedb.6box.me",
                        searchIds: ["rid", "imdbid"]
                    },
                    {
                        name: "6box nntmux",
                        host: "https://nn-tmux.6box.me",
                        searchIds: ["tvdbid", "rid", "imdbid"]
                    },
                    {
                        name: "6box",
                        host: "https://6box.me",
                        searchIds: ["imdbid"]
                    },
                    {
                        name: "Drunken Slug",
                        host: "https://drunkenslug.com",
                        searchIds: ["tvdbid", "imdbid", "tvmazeid", "traktid", "tmdbid"]
                    }

                ];

                $scope.selectPreset = function (item, model) {
                    if (item.name == "None") {
                        $scope.model.name = "";
                        $scope.model.host = "";
                        $scope.model.apikey = "";
                        $scope.model.score = 0;
                        $scope.model.timeout = null;
                        $scope.model.search_ids = ["tvdbid", "rid", "imdbid"]; //Default
                        $scope.display = "";
                    } else {
                        $scope.model.name = item.name;
                        $scope.model.host = item.host;
                        $scope.model.search_ids = item.searchIds;
                        _.defer(function () {
                            $scope.display = item.name;
                        });

                    }
                };

                $scope.$watch('[model.host]', function () {
                    $scope.display = "";
                }, true);
            }
        });

        formlyConfigProvider.setType({
            name: 'horizontalTestConnection',
            extends: 'testConnection',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'horizontalCheckCaps',
            extends: 'checkCaps',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });


        formlyConfigProvider.setType({
            name: 'horizontalApiKeyInput',
            extends: 'apiKeyInput',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'horizontalPercentInput',
            extends: 'percentInput',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });


        formlyConfigProvider.setType({
            name: 'switch',
            template: [
                '<div style="text-align:left"><input bs-switch type="checkbox" ng-model="model[options.key]"/></div>'
            ].join(' ')

        });


        formlyConfigProvider.setType({
            name: 'duoSetting',
            extends: 'input',
            defaultOptions: {
                className: 'col-md-9',
                templateOptions: {
                    type: 'number',
                    noRow: true,
                    label: ''
                }
            }
        });

        formlyConfigProvider.setType({
            name: 'horizontalSwitch',
            extends: 'switch',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'horizontalSelect',
            extends: 'select',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });


        formlyConfigProvider.setType({
            name: 'ui-select-multiple',
            defaultOptions: {
                templateOptions: {
                    optionsAttr: 'bs-options',
                    ngOptions: 'option[to.valueProp] as option in to.options | filter: $select.search',
                    valueProp: 'id',
                    labelProp: 'label'
                }
            },
            templateUrl: 'ui-select-multiple.html'
        });

        formlyConfigProvider.setType({
            name: 'horizontalMultiselect',
            extends: 'ui-select-multiple',
            templateUrl: 'ui-select-multiple.html',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });


        formlyConfigProvider.setType({
            name: 'label',
            template: '<label class="control-label">{{to.label}}</label>'
        });

        formlyConfigProvider.setType({
            name: 'duolabel',
            extends: 'label',
            defaultOptions: {
                className: 'col-md-2',
                templateOptions: {
                    label: '-'
                }
            }
        });

    }]);

var filters = angular.module('filters', []);

filters.filter('bytes', function() {
	return function(bytes, precision) {
		if (isNaN(parseFloat(bytes)) || !isFinite(bytes) || bytes == 0) return '-';
		if (typeof precision === 'undefined') precision = 1;
		
		var units = ['b', 'kB', 'MB', 'GB', 'TB', 'PB'],
			number = Math.floor(Math.log(bytes) / Math.log(1024));
		return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +   units[number];
	}
});

filters.filter('unsafe', 
	["$sce", function ($sce) {
		return function (value, type) {
			return $sce.trustAs(type || 'html', text);
		};
	}]
);
angular
    .module('nzbhydraApp')
    .factory('ConfigService', ConfigService);

function ConfigService($http, $q, $cacheFactory) {

    var cache = $cacheFactory("nzbhydra.d35d0ead");
    
    return {
        set: set,
        get: get,
        getSafe: getSafe,
        invalidateSafe: invalidateSafe,
        maySeeAdminArea: maySeeAdminArea
    };
    
    
    function set(newConfig) {
        $http.put('internalapi/setsettings', newConfig)
            .then(function (successresponse) {
                console.log("Settings saved. Updating cache");
                cache.put("config", newConfig);
            }, function (errorresponse) {
                console.log("Error saving settings: " + errorresponse);
            });
    }

    function get() {
        var config = cache.get("config");
        if (angular.isUndefined(config)) {
            config = $http.get('internalapi/getconfig').then(function (data) {
                return data.data;
            });
            cache.put("config", config);
        }
        
        return config;
    }

    function getSafe() {
            var safeconfig = cache.get("safeconfig");
            if (angular.isUndefined(safeconfig)) {
                safeconfig = $http.get('internalapi/getsafeconfig').then(function(data) {
                    return data.data;
                });
                cache.put("safeconfig", safeconfig);
            }
        
            return safeconfig;
    }
    
    function invalidateSafe() {
        cache.remove("safeconfig");
    }

    function maySeeAdminArea() {
        function loadAll() {
            var maySeeAdminArea = cache.get("maySeeAdminArea");
            if (!angular.isUndefined(maySeeAdminArea)) {
                var deferred = $q.defer();
                deferred.resolve(maySeeAdminArea);
                return deferred.promise;
            }

            return $http.get('internalapi/mayseeadminarea')
                .then(function (configResponse) {
                    var config = configResponse.data;
                    cache.put("maySeeAdminArea", config);
                    return configResponse.data;
                });
        }

        return loadAll().then(function (maySeeAdminArea) {
            return maySeeAdminArea;
        });
    }
}
ConfigService.$inject = ["$http", "$q", "$cacheFactory"];
angular
    .module('nzbhydraApp')
    .factory('ConfigFields', ConfigFields);

function ConfigFields() {
    
    var restartWatcher;
    
    return {
        getFields: getFields,
        setRestartWatcher: setRestartWatcher
    };
    
    function setRestartWatcher(restartWatcherFunction) {
        restartWatcher = restartWatcherFunction;
    }
    
    
    
    function restartListener(field, newValue, oldValue) {
        if (newValue != oldValue) {
            restartWatcher();
        }
    }

    function getBasicIndexerFieldset(showName, host, apikey, username, searchIds, testConnection, testtype, showpreselect, showCheckCaps) {
        var fieldset = [];

        fieldset.push({
            key: 'enabled',
            type: 'horizontalSwitch',
            templateOptions: {
                type: 'switch',
                label: 'Enabled'
            }
        });

        if (testtype == 'newznab') {
            fieldset.push(
                {
                    key: 'name',
                    type: 'horizontalNewznabPreset',
                    templateOptions: {
                        label: 'Presets'
                    }

                });
        }

        if (showName) {
            fieldset.push(
                {
                    key: 'name',
                    type: 'horizontalInput',
                    hideExpression: '!model.enabled && (model.name == "" || model.name == null)',  //Show if name is given to better identify the entries visually
                    templateOptions: {
                        type: 'text',
                        label: 'Name',
                        help: 'Used for identification. Changing the name will lose all history and stats!'
                    }
                })
        }
        if (host) {
            fieldset.push(
                {
                    key: 'host',
                    type: 'horizontalInput',
                    hideExpression: '!model.enabled',
                    templateOptions: {
                        type: 'text',
                        label: 'Host',
                        placeholder: 'http://www.someindexer.com'
                    }
                }
            )
        }

        if (apikey) {
            fieldset.push(
                {
                    key: 'apikey',
                    type: 'horizontalInput',
                    hideExpression: '!model.enabled',
                    templateOptions: {
                        type: 'text',
                        label: 'API Key'
                    }
                }
            )
        }

        if (username) {
            fieldset.push(
                {
                    key: 'username',
                    type: 'horizontalInput',
                    hideExpression: '!model.enabled',
                    templateOptions: {
                        type: 'text',
                        label: 'Username'
                    }
                }
            )
        }

        fieldset = fieldset.concat([
            {
                key: 'score',
                type: 'horizontalInput',
                hideExpression: '!model.enabled',
                templateOptions: {
                    type: 'number',
                    label: 'Score',
                    help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                }
            },
            {
                key: 'timeout',
                type: 'horizontalInput',
                hideExpression: '!model.enabled',
                templateOptions: {
                    type: 'number',
                    label: 'Timeout',
                    help: 'Supercedes the general timeout in "Searching"'
                }
            },
        ]);


        if (showpreselect) {
            fieldset.push(
                {
                    key: 'preselect',
                    type: 'horizontalSwitch',
                    hideExpression: '!model.enabled || model.accessType == "external"',
                    templateOptions: {
                        type: 'switch',
                        label: 'Preselect',
                        help: 'Preselect this indexer on the search page'
                    }
                }
            );
            fieldset.push(
                {
                    key: 'accessType',
                    type: 'horizontalSelect',
                    hideExpression: '!model.enabled',
                    templateOptions: {
                        label: 'Enable for...',
                        options: [
                            {name: 'Internal searches only', value: 'internal'},
                            {name: 'API searches only', value: 'external'},
                            {name: 'Internal and API searches', value: 'both'}
                        ]
                    }
                }
            )
        }

        if (searchIds) {
            fieldset.push(
                {
                    key: 'search_ids',
                    type: 'horizontalMultiselect',
                    hideExpression: '!model.enabled',
                    templateOptions: {
                        label: 'Search types',
                        options: [
                            {label: 'TVDB', id: 'tvdbid'},
                            {label: 'TVRage', id: 'rid'},
                            {label: 'IMDB', id: 'imdbid'},
                            {label: 'Trakt', id: 'traktid'},
                            {label: 'TVMaze', id: 'tvmazeid'},
                            {label: 'TMDB', id: 'tmdbid'}
                        ]
                    }
                }
            )
        }

        if (testConnection) {
            fieldset.push(
                {
                    type: 'horizontalTestConnection',
                    hideExpression: '!model.enabled || !model.host || !model.apikey || !model.name',
                    templateOptions: {
                        label: 'Test connection',
                        testType: testtype
                    }
                }
            )
        }

        if (showCheckCaps) {
            fieldset.push(
                {
                    type: 'horizontalCheckCaps',
                    hideExpression: '!model.enabled || !model.host || !model.apikey || !model.name',
                    templateOptions: {
                        label: 'Check search types',
                        help: 'Find out what search types the indexer supports. It\'s recommended to do this for every new indexer.'
                    }
                }
            )
        }

        return fieldset;
    }

    function getNewznabFieldset(index) {
        return {
            wrapper: 'fieldset',
            hideExpression: function ($viewValue, $modelValue, scope) {
                if (index > 1 && index <= 40) {
                    var allBeforeNamed = true;
                    for (var i = 1; i < index; i++) {
                        if (!scope.model["newznab" + i].name) {
                            allBeforeNamed = false;
                            break;
                        }
                    }
                    return !allBeforeNamed;
                }
                return false;
            },
            key: 'newznab' + index,
            templateOptions: {label: 'Newznab ' + index},
            fieldGroup: getBasicIndexerFieldset(true, true, true, false, true, true, 'newznab', true, true)
        };
    }

    function getFields() {
        console.log("Called getFields() from ConfigFields");

        return {
            main: [
                {
                    wrapper: 'fieldset',
                    templateOptions: {label: 'Hosting'},
                    fieldGroup: [
                        {
                            key: 'host',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Host',
                                placeholder: 'IPv4 address to bind to',
                                help: 'Requires restart'
                            },
                            watcher: {
                                listener: restartListener
                            }
                        },
                        {
                            key: 'port',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'number',
                                label: 'Port',
                                placeholder: '5050',
                                help: 'Requires restart'
                            },
                            watcher: {
                                listener: restartListener
                            }
                        },
                        {
                            key: 'urlBase',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'URL base',
                                placeholder: '/nzbhydra',
                                help: 'Set when using an external proxy'
                            }
                        },
                        {
                            key: 'externalUrl',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'External URL',
                                placeholder: 'https://www.somedomain.com/nzbhydra/',
                                help: 'Set to the full external URL so machines outside can use the generated NZB links.'
                            }
                        },
                        {
                            key: 'useLocalUrlForApiAccess',
                            type: 'horizontalSwitch',
                            hideExpression: '!model.externalUrl',
                            templateOptions: {
                                type: 'switch',
                                label: 'Use local address in API results',
                                help: 'Disable to make API results use the external URL in NZB links.'
                            }
                        },
                        {
                            key: 'ssl',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Use SSL',
                                help: 'Requires restart'
                            },
                            watcher: {
                                listener: restartListener
                            }
                        },
                        {
                            key: 'sslcert',
                            hideExpression: '!model.ssl',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'SSL certificate file',
                                required: true,
                                help: 'Requires restart'
                            },
                            watcher: {
                                listener: restartListener
                            }
                        },
                        {
                            key: 'sslkey',
                            hideExpression: '!model.ssl',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'SSL key file',
                                required: true,
                                help: 'Requires restart'
                            },
                            watcher: {
                                listener: restartListener
                            }
                        }

                    ]
                },
                {
                    wrapper: 'fieldset',
                    templateOptions: {label: 'Security'},
                    fieldGroup: [
                        {
                            key: 'enableAuth',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Enable authentication'
                            }
                        },
                        {
                            key: 'username',
                            type: 'horizontalInput',
                            hideExpression: '!model.enableAuth',
                            templateOptions: {
                                type: 'text',
                                label: 'Username',
                                required: true
                            }
                        },
                        {
                            key: 'password',
                            hideExpression: '!model.enableAuth',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'password',
                                label: 'Password',
                                required: true
                            }
                        },
                        {
                            key: 'apikey',
                            type: 'horizontalApiKeyInput',
                            templateOptions: {
                                label: 'API key',
                                help: 'Remove to disable. Alphanumeric only'
                            }
                        },
                        {
                            key: 'enableAdminAuth',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Enable admin user',
                                help: 'Enable to protect the config with a separate admin user'
                            }
                        },
                        {
                            key: 'adminUsername',
                            type: 'horizontalInput',
                            hideExpression: '!model.enableAdminAuth',
                            templateOptions: {
                                type: 'text',
                                label: 'Admin username',
                                required: true
                            }
                        },
                        {
                            key: 'adminPassword',
                            hideExpression: '!model.enableAdminAuth',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'password',
                                label: 'Admin password',
                                required: true
                            }
                        },
                        {
                            key: 'enableAdminAuthForStats',
                            type: 'horizontalSwitch',
                            hideExpression: '!model.enableAdminAuth',
                            templateOptions: {
                                type: 'switch',
                                label: 'Enable stats admin',
                                help: 'Enable to protect the history & stats with the admin user'
                            }
                        }


                    ]
                },
                {
                    wrapper: 'fieldset',
                    templateOptions: {label: 'Caching'},
                    fieldGroup: [
                        {
                            key: 'enableCache',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Enable caching'
                            }
                        },
                        {
                            key: 'enableCacheForApi',
                            hideExpression: '!model.enableCache',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Cache API search results',
                                help: 'Enable to reduce load on indexers, disable for always newest results'
                            }
                        },
                        {
                            key: 'cacheType',
                            hideExpression: '!model.enableCache',
                            type: 'horizontalSelect',
                            templateOptions: {
                                type: 'select',
                                label: 'Type',
                                options: [
                                    {name: 'Memory only', value: 'memory'},
                                    {name: 'File sytem', value: 'file'}
                                ]
                            }
                        },
                        {
                            key: 'cacheTimeout',
                            hideExpression: '!model.enableCache',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'number',
                                label: 'Cache timeout',
                                help: 'Time after which cache entries will be discarded',
                                addonRight: {
                                    text: 'minutes'
                                }
                            }
                        },
                        {
                            key: 'cachethreshold',
                            hideExpression: '!model.enableCache',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'number',
                                label: 'Cache threshold',
                                help: 'Max amount of items held in cache',
                                addonRight: {
                                    text: 'items'
                                }
                            }
                        },
                        {
                            key: 'cacheFolder',
                            hideExpression: '!model.enableCache || model.cacheType == "memory"',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Cache folder'
                            }
                        }

                    ]
                },

                {
                    wrapper: 'fieldset',
                    key: 'logging',
                    templateOptions: {label: 'Logging'},
                    fieldGroup: [
                        {
                            key: 'logfile-level',
                            type: 'horizontalSelect',
                            templateOptions: {
                                type: 'select',
                                label: 'Logfile level',
                                options: [
                                    {name: 'Critical', value: 'CRITICAL'},
                                    {name: 'Error', value: 'ERROR'},
                                    {name: 'Warning', value: 'WARNING'},
                                    {name: 'Debug', value: 'DEBUG'},
                                    {name: 'Info', value: 'INFO'}
                                ]
                            },
                            watcher: {
                                listener: restartListener
                            }
                        },
                        {
                            key: 'logfile-filename',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Log file'
                            },
                            watcher: {
                                listener: restartListener
                            }
                        },
                        {
                            key: 'consolelevel',
                            type: 'horizontalSelect',
                            templateOptions: {
                                type: 'select',
                                label: 'Console log level',
                                options: [
                                    {name: 'Critical', value: 'CRITICAL'},
                                    {name: 'Error', value: 'ERROR'},
                                    {name: 'Warning', value: 'WARNING'},
                                    {name: 'Info', value: 'INFO'},
                                    {name: 'Debug', value: 'DEBUG'}
                                ]
                            },
                            watcher: {
                                listener: restartListener
                            }
                        }


                    ]
                },
                {
                    wrapper: 'fieldset',
                    templateOptions: {label: 'Other'},
                    fieldGroup: [
                        {
                            key: 'debug',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Enable debugging',
                                help: "Only do this if you know what and why you're doing it"
                            }
                        },
                        {
                            key: 'runThreaded',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Run threaded server',
                                help: 'Requires restart. Experimental. Please report your experiences.'
                            },
                            watcher: {
                                listener: restartListener
                            }
                        },
                        {
                            key: 'startupBrowser',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Open browser on startup'
                            }
                        },
                        {
                            key: 'branch',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Repository branch',
                                help: 'Stay on master. Seriously...'
                            }
                        }
                    ]
                }
            ],

            searching: [
                {
                    wrapper: 'fieldset',
                    templateOptions: {
                        label: 'Indexer access'
                    },
                    fieldGroup: [
                        {
                            key: 'timeout',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'number',
                                label: 'Timeout when accessing indexers',
                                addonRight: {
                                    text: 'seconds'
                                }
                            }
                        },
                        {
                            key: 'ignoreTemporarilyDisabled',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Ignore temporarily disabled',
                                help: "If enabled access to indexers will never be paused after an error occurred"
                            }
                        },
                        {
                            key: 'ignorePassworded',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Ignore passworded releases',
                                help: "Not all indexers provide this information"
                            }
                        },

                        {
                            key: 'ignoreWords',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Ignore results with ...',
                                placeholder: 'separate, with, commas, like, this',
                                help: "Results with any of these words in the title will be ignored"
                            }
                        },


                        {
                            key: 'generate_queries',
                            type: 'horizontalMultiselect',
                            templateOptions: {
                                label: 'Generate queries',
                                options: [
                                    {label: 'Internal searches', id: 'internal'},
                                    {label: 'API searches', id: 'external'}
                                ],
                                help: "Generate queries for indexers which do not support ID based searches"
                            }
                        },
                        {
                            key: 'userAgent',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'User agent'
                            }
                        }
                    ]
                },
                {
                    wrapper: 'fieldset',
                    templateOptions: {
                        label: 'Result processing'
                    },
                    fieldGroup: [
                        {
                            key: 'htmlParser',
                            type: 'horizontalSelect',
                            templateOptions: {
                                type: 'select',
                                label: 'Type',
                                options: [
                                    {name: 'Default BS (slow)', value: 'html.parser'},
                                    {name: 'LXML (faster, needs to be installed separately)', value: 'lxml'}
                                ]
                            }
                        },
                        {
                            key: 'duplicateSizeThresholdInPercent',
                            type: 'horizontalPercentInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Duplicate size threshold',
                                addonRight: {
                                    text: '%'
                                }

                            }
                        },
                        {
                            key: 'duplicateAgeThreshold',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'number',
                                label: 'Duplicate age threshold',
                                addonRight: {
                                    text: 'seconds'
                                }
                            }
                        },
                        {
                            key: 'removeDuplicatesExternal',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Remove API duplicates',
                                help: 'Remove duplicates when searching via API'
                            }
                        }
                    ]
                },

                {
                    wrapper: 'fieldset',
                    key: 'categorysizes',
                    templateOptions: {label: 'Category sizes'},
                    fieldGroup: [

                        {
                            key: 'enable_category_sizes',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Category sizes',
                                help: "Preset min and max sizes depending on the selected category"
                            }
                        },
                        {
                            wrapper: 'logicalGroup',
                            hideExpression: '!model.enable_category_sizes',
                            fieldGroup: [
                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'Movies'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'moviesmin',
                                            type: 'duoSetting',
                                            templateOptions: {
                                                addonRight: {
                                                    text: 'MB'
                                                }
                                            }
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'moviesmax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },
                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'Movies HD'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'movieshdmin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'movieshdmax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },
                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'Movies SD'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'moviessdmin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'movieshdmin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },

                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'TV'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'tvmin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'tvmax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },

                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'TV HD'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'tvhdmin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'tvhdmax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },

                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'TV SD'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'tvsdmin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'tvsdmax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },

                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'Audio'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'audiomin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'audiomax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },

                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'Audio FLAC'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'flacmin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'flacmax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },

                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'Audio MP3'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'mp3min',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'mp3max',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },

                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'Audiobook'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'audiobookmin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'audiobookmax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },

                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'Console'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'consolemin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'consolemax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },

                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'PC'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'pcmin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'pcmax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                },

                                {
                                    wrapper: 'horizontalBootstrapLabel',
                                    templateOptions: {
                                        label: 'XXX'
                                    },
                                    fieldGroup: [
                                        {
                                            key: 'xxxmin',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        },
                                        {
                                            type: 'duolabel'
                                        },
                                        {
                                            key: 'xxxmax',
                                            type: 'duoSetting', templateOptions: {addonRight: {text: 'MB'}}
                                        }
                                    ]
                                }
                            ]
                        }

                    ]
                }

            ],

            downloader: [
                {
                    key: 'downloader',
                    type: 'horizontalSelect',
                    templateOptions: {
                        type: 'select',
                        label: 'Downloader',
                        options: [
                            {name: 'None', value: 'none'},
                            {name: 'NZBGet', value: 'nzbget'},
                            {name: 'SABnzbd', value: 'sabnzbd'}
                        ]
                    }
                },
                {
                    key: 'nzbaccesstype',
                    type: 'horizontalSelect',
                    templateOptions: {
                        type: 'select',
                        label: 'NZB access type',
                        options: [
                            {name: 'Proxy NZBs from indexer', value: 'serve'},
                            {name: 'Redirect to the indexer', value: 'redirect'}
                        ],
                        help: "How external access to NZBs is provided. Redirecting is recommended."
                    }
                },
                {
                    key: 'nzbAddingType',
                    type: 'horizontalSelect',
                    templateOptions: {
                        type: 'select',
                        label: 'NZB adding type',
                        options: [
                            {name: 'Send link', value: 'link'},
                            {name: 'Upload NZB', value: 'nzb'}
                        ],
                        help: "How NZBs are added to the downloader, either by sending a link to the NZB or by uploading the NZB data"
                    }
                },
                {
                    wrapper: 'fieldset',
                    key: 'nzbget',
                    hideExpression: 'model.downloader!="nzbget"',
                    templateOptions: {label: 'NZBGet'},
                    fieldGroup: [
                        {
                            key: 'host',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Host'
                            }
                        },
                        {
                            key: 'port',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'number',
                                label: 'Port',
                                placeholder: '5050'
                            }
                        },
                        {
                            key: 'ssl',
                            type: 'horizontalSwitch',
                            templateOptions: {
                                type: 'switch',
                                label: 'Use SSL'
                            }
                        },
                        {
                            key: 'username',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Username'
                            }
                        },
                        {
                            key: 'password',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'password',
                                label: 'Password'
                            }
                        },
                        {
                            key: 'defaultCategory',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Default category',
                                help: 'When adding NZBs this category will be used instead of asking for the category'
                            }
                        },
                        {
                            type: 'horizontalTestConnection',
                            templateOptions: {
                                label: 'Test connection',
                                testType: 'downloader',
                                downloader: 'nzbget'
                            }
                        }


                    ]
                },
                {
                    wrapper: 'fieldset',
                    key: 'sabnzbd',
                    hideExpression: 'model.downloader!="sabnzbd"',
                    templateOptions: {label: 'SABnzbd'},
                    fieldGroup: [
                        {
                            key: 'url',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'URL'
                            }
                        },
                        {
                            key: 'username',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Username',
                                help: 'Usually not needed when an API key is used'
                            }
                        },
                        {
                            key: 'password',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'password',
                                label: 'Password',
                                help: 'Usually not needed when an API key is used'
                            }
                        },
                        {
                            key: 'apikey',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'API Key'
                            }
                        },
                        {
                            key: 'defaultCategory',
                            type: 'horizontalInput',
                            templateOptions: {
                                type: 'text',
                                label: 'Default category',
                                help: 'When adding NZBs this category will be used instead of asking for the category'
                            }
                        },
                        {
                            type: 'horizontalTestConnection',
                            templateOptions: {
                                label: 'Test connection',
                                testType: 'downloader',
                                downloader: 'sabnzbd'
                            }
                        }


                    ]
                }
            ],

            indexers: [
                {
                    wrapper: 'fieldset',
                    key: 'Binsearch',
                    templateOptions: {label: 'Binsearch'},
                    fieldGroup: getBasicIndexerFieldset(false, false, false, false, false, false, "binsearch", true)
                },
                {
                    wrapper: 'fieldset',
                    key: 'NZBClub',
                    templateOptions: {label: 'NZBClub'},
                    fieldGroup: getBasicIndexerFieldset(false, false, false, false, false, false, "nzbclub", true)
                },
                {
                    wrapper: 'fieldset',
                    key: 'NZBIndex',
                    templateOptions: {label: 'NZBIndex'},
                    fieldGroup: getBasicIndexerFieldset(false, false, false, false, false, false, "nzbindex", true).concat([{
                        key: 'generalMinSize',
                        type: 'horizontalInput',
                        hideExpression: '!model.enabled',
                        templateOptions: {
                            type: 'number',
                            label: 'Min size',
                            help: 'NZBIndex returns a lot of crap with small file sizes. Set this value and all smaller results will be filtered out no matter the category'
                        }
                    }])
                },
                {
                    wrapper: 'fieldset',
                    key: 'omgwtfnzbs',
                    templateOptions: {label: 'omgwtfnzbs.org'},
                    fieldGroup: getBasicIndexerFieldset(false, false, true, true, false, true, 'omgwtf', true)
                },
                {
                    wrapper: 'fieldset',
                    key: 'Womble',
                    templateOptions: {label: 'Womble'},
                    fieldGroup: getBasicIndexerFieldset(false, false, false, false, false, false, "womble", false)
                },


                getNewznabFieldset(1),
                getNewznabFieldset(2),
                getNewznabFieldset(3),
                getNewznabFieldset(4),
                getNewznabFieldset(5),
                getNewznabFieldset(6),
                getNewznabFieldset(7),
                getNewznabFieldset(8),
                getNewznabFieldset(9),
                getNewznabFieldset(10),
                getNewznabFieldset(11),
                getNewznabFieldset(12),
                getNewznabFieldset(13),
                getNewznabFieldset(14),
                getNewznabFieldset(15),
                getNewznabFieldset(16),
                getNewznabFieldset(17),
                getNewznabFieldset(18),
                getNewznabFieldset(19),
                getNewznabFieldset(20),
                getNewznabFieldset(21),
                getNewznabFieldset(22),
                getNewznabFieldset(23),
                getNewznabFieldset(24),
                getNewznabFieldset(25),
                getNewznabFieldset(26),
                getNewznabFieldset(27),
                getNewznabFieldset(28),
                getNewznabFieldset(29),
                getNewznabFieldset(30),
                getNewznabFieldset(31),
                getNewznabFieldset(32),
                getNewznabFieldset(33),
                getNewznabFieldset(34),
                getNewznabFieldset(35),
                getNewznabFieldset(36),
                getNewznabFieldset(37),
                getNewznabFieldset(38),
                getNewznabFieldset(39),
                getNewznabFieldset(40)


            ]

            


        };
        
        

    }

}
angular
    .module('nzbhydraApp')
    .factory('ConfigModel', function () {
        return {};
    });

angular
    .module('nzbhydraApp')
    .factory('ConfigWatcher', function () {
        var $scope;
        
        return {
            watch: watch
        };
        
        function watch(scope) {
            $scope = scope;
            $scope.$watchGroup(["config.main.host"], function () {
                console.log("Restart needed");
            }, true);
        }
    });


angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);

function ConfigController($scope, ConfigService, config, CategoriesService, ConfigFields, ConfigModel, ModalService, RestartService, $state) {
    $scope.config = config;
    $scope.submit = submit;
    
    $scope.restartRequired = false;
    
    ConfigFields.setRestartWatcher(function() {
        $scope.restartRequired = true;
    });

    function submit(form) {
        ConfigService.set($scope.config);
        ConfigService.invalidateSafe();
        form.$setPristine();
        CategoriesService.invalidate();
        if ($scope.restartRequired) {
            ModalService.open("Restart required", "The changes you have made may require a restart to be effective.<br>Do you want to restart now?", function () {
                RestartService.restart();
            }, function() {
                $scope.restartRequired = false;
            });
        }
    }

    ConfigModel = config;

    $scope.fields = ConfigFields.getFields();

    $scope.formTabs = [
        {
            name: 'Main',
            model: ConfigModel.main,
            fields: $scope.fields.main
        },
        {
            name: 'Searching',
            model: ConfigModel.searching,
            fields: $scope.fields.searching
        },
        {
            name: 'Downloader',
            model: ConfigModel.downloader,
            fields: $scope.fields.downloader
        },
        {
            name: 'Indexers',
            model: ConfigModel.indexers,
            fields: $scope.fields.indexers
        }
    ];

    $scope.allTabs = [
        {
            active: false,
            state: 'config'
        },
        {
            active: false,
            state: 'config.searching'
        },
        {
            active: false,
            state: 'config.downloader'
        },
        {
            active: false,
            state: 'config.indexers'
        }
    ];


    for (var i = 0; i < $scope.allTabs.length; i++) {
        if ($state.is($scope.allTabs[i].state)) {
            $scope.allTabs[i].active = true;
        }
    }

    $scope.isSavingNeeded = function (form) {
        return form.$dirty && !form.$submitted;
    };

    $scope.goToConfigState = function (index) {
        $state.go($scope.allTabs[index].state);
        if (index == 5) {
            $scope.downloadLog();
        }
    };
    
}
ConfigController.$inject = ["$scope", "ConfigService", "config", "CategoriesService", "ConfigFields", "ConfigModel", "ModalService", "RestartService", "$state"];



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
        });
    }

    
    var deferred;
    
    function openCategorySelection() {
        $uibModal.open({
            templateUrl: 'static/html/directives/addable-nzb-modal.ba86ffae.html',
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
CategoriesService.$inject = ["$http", "$q", "$uibModal"];

angular
    .module('nzbhydraApp').controller('CategorySelectionController', ["$scope", "$uibModalInstance", "CategoriesService", "categories", function ($scope, $uibModalInstance, CategoriesService, categories) {
    console.log(categories);
    $scope.categories = categories;
    $scope.select = function (category) {
        CategoriesService.select(category);
        $uibModalInstance.close($scope);
    }
}]);
//# sourceMappingURL=nzbhydra.js.0e693d93.map
