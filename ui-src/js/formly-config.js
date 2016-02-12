angular
    .module('nzbhydraApp')
    .config(function config(formlyConfigProvider) {
        formlyConfigProvider.extras.removeChromeAutoComplete = true;
        formlyConfigProvider.extras.explicitAsync = true;
        formlyConfigProvider.disableWarnings = window.onProd;
        
        
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

    });
