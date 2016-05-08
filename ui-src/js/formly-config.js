hashCode = function (s) {
    return s.split("").reduce(function (a, b) {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a
    }, 0);
};

angular
    .module('nzbhydraApp')
    .config(function config(formlyConfigProvider) {
        formlyConfigProvider.extras.removeChromeAutoComplete = true;
        formlyConfigProvider.extras.explicitAsync = true;
        formlyConfigProvider.disableWarnings = window.onProd;


        formlyConfigProvider.setWrapper({
            name: 'settingWrapper',
            templateUrl: 'setting-wrapper.html'
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

        formlyConfigProvider.setType({
            name: 'help',
            template: [
                '<div class="panel panel-default">',
                '<div class="panel-body">',
                '<div ng-repeat="line in options.templateOptions.lines">{{ line }}</div>',
                '</div>',
                '</div>'
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
            wrapper: ['settingWrapper', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'timeOfDay',
            extends: 'horizontalInput',
            controller: ['$scope', function ($scope) {
                var date = new Date($scope.model[$scope.options.key]);
                $scope.model[$scope.options.key] = new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds());
            }]
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
            templateUrl: 'button-test-connection.html'
        });

        formlyConfigProvider.setType({
            name: 'checkCaps',
            templateUrl: 'button-check-caps.html',
            controller: function ($scope) {
                $scope.message = "";
                $scope.uniqueId = hashCode($scope.model.name) + hashCode($scope.model.host);

                var testButton = "#button-check-caps-" + $scope.uniqueId;
                var testMessage = "#message-check-caps-" + $scope.uniqueId;

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
                            angular.element(testMessage).text("Supports: " + result.ids + "," + result.types);
                            $scope.$apply(function () {
                                $scope.model.search_ids = result.ids;
                                $scope.model.searchTypes = result.types;
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
            name: 'horizontalTestConnection',
            extends: 'testConnection',
            wrapper: ['settingWrapper', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'horizontalCheckCaps',
            extends: 'checkCaps',
            wrapper: ['settingWrapper', 'bootstrapHasError']
        });


        formlyConfigProvider.setType({
            name: 'horizontalApiKeyInput',
            extends: 'apiKeyInput',
            wrapper: ['settingWrapper', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'horizontalPercentInput',
            extends: 'percentInput',
            wrapper: ['settingWrapper', 'bootstrapHasError']
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
            wrapper: ['settingWrapper', 'bootstrapHasError']
        });

        formlyConfigProvider.setType({
            name: 'horizontalSelect',
            extends: 'select',
            wrapper: ['settingWrapper', 'bootstrapHasError']
        });


        formlyConfigProvider.setType({
            name: 'horizontalMultiselect',
            defaultOptions: {
                templateOptions: {
                    optionsAttr: 'bs-options',
                    ngOptions: 'option[to.valueProp] as option in to.options | filter: $select.search',
                    valueProp: 'id',
                    labelProp: 'label'
                }
            },
            templateUrl: 'ui-select-multiple.html',
            wrapper: ['settingWrapper', 'bootstrapHasError']
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

        formlyConfigProvider.setType({
            name: 'repeatSection',
            templateUrl: 'repeatSection.html',
            controller: function ($scope) {
                $scope.formOptions = {formState: $scope.formState};
                $scope.addNew = addNew;
                $scope.remove = remove;
                $scope.copyFields = copyFields;

                function copyFields(fields) {
                    fields = angular.copy(fields);
                    $scope.repeatfields = fields;
                    return fields;
                }

                $scope.clear = function (field) {
                    return _.mapObject(field, function (key, val) {
                        if (typeof val === 'object') {
                            return $scope.clear(val);
                        }
                        return undefined;

                    });
                };


                function addNew() {
                    $scope.model[$scope.options.key] = $scope.model[$scope.options.key] || [];
                    var repeatsection = $scope.model[$scope.options.key];
                    var newsection = angular.copy($scope.options.templateOptions.defaultModel);
                    repeatsection.push(newsection);
                }

                function remove($index) {
                    $scope.model[$scope.options.key].splice($index, 1);
                }
            }
        });

        formlyConfigProvider.setType({
            name: 'indexers',
            templateUrl: 'indexers.html',
            controller: function ($scope, $uibModal) {
                $scope.formOptions = {formState: $scope.formState};
                $scope._showIndexerBox = _showIndexerBox;
                $scope.showIndexerBox = showIndexerBox;
                $scope.orderIndexer = orderIndexer;
                $scope.isInitial = false;

                $scope.presets = [
                    {
                        name: "6box",
                        host: "https://6box.me",
                        searchIds: ["imdbid"]
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
                        name: "DogNZB",
                        host: "https://api.dognzb.cr",
                        searchIds: ["tvdbid", "rid", "imdbid"]
                    },
                    {
                        name: "Drunken Slug",
                        host: "https://drunkenslug.com",
                        searchIds: ["tvdbid", "imdbid", "tvmazeid", "traktid", "tmdbid"]
                    },
                    {
                        name: "NZB Finder",
                        host: "https://nzbfinder.ws",
                        searchIds: ["tvdbid", "rid", "imdbid", "tvmazeid", "traktid", "tmdbid"]
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
                        name: "NZBGeek",
                        host: "https://api.nzbgeek.info",
                        searchIds: ["tvdbid", "rid", "imdbid"]
                    }
                ];

                function _showIndexerBox(model, parentModel, isInitial, callback) {
                    var modalInstance = $uibModal.open({
                        templateUrl: 'indexerModal.html',
                        controller: 'IndexerModalInstanceController',
                        size: 'lg',
                        resolve: {
                            model: function () {
                                return model;
                            },
                            fields: function () {
                                var fieldset = [];


                                fieldset.push({
                                    key: 'enabled',
                                    type: 'horizontalSwitch',
                                    templateOptions: {
                                        type: 'switch',
                                        label: 'Enabled'
                                    }
                                });

                                if (model.type == 'newznab') {
                                    fieldset.push(
                                        {
                                            key: 'name',
                                            type: 'horizontalInput',
                                            hideExpression: '!model.enabled',
                                            templateOptions: {
                                                type: 'text',
                                                label: 'Name',
                                                required: true,
                                                help: 'Used for identification. Changing the name will lose all history and stats!'
                                            }
                                        })
                                }
                                if (model.type == 'newznab') {
                                    fieldset.push(
                                        {
                                            key: 'host',
                                            type: 'horizontalInput',
                                            hideExpression: '!model.enabled',
                                            templateOptions: {
                                                type: 'text',
                                                label: 'Host',
                                                required: true,
                                                placeholder: 'http://www.someindexer.com'
                                            },
                                            watcher: {
                                                listener: function (field, newValue, oldValue, scope) {
                                                    if (newValue != oldValue) {
                                                        scope.$parent.needsConnectionTest = true;
                                                    }
                                                }
                                            }
                                        }
                                    )
                                }

                                if (model.type == 'newznab' || model.type == 'omgwtf') {
                                    fieldset.push(
                                        {
                                            key: 'apikey',
                                            type: 'horizontalInput',
                                            hideExpression: '!model.enabled',
                                            templateOptions: {
                                                type: 'text',
                                                required: true,
                                                label: 'API Key'
                                            },
                                            watcher: {
                                                listener: function (field, newValue, oldValue, scope) {
                                                    if (newValue != oldValue) {
                                                        scope.$parent.needsConnectionTest = true;
                                                    }
                                                }
                                            }
                                        }
                                    )
                                }

                                if (model.type == 'omgwtf') {
                                    fieldset.push(
                                        {
                                            key: 'username',
                                            type: 'horizontalInput',
                                            hideExpression: '!model.enabled',
                                            templateOptions: {
                                                type: 'text',
                                                required: true,
                                                label: 'Username'
                                            },
                                            watcher: {
                                                listener: function (field, newValue, oldValue, scope) {
                                                    if (newValue != oldValue) {
                                                        scope.$parent.needsConnectionTest = true;
                                                    }
                                                }
                                            }
                                        }
                                    )
                                }

                                fieldset.push(
                                    {
                                        key: 'score',
                                        type: 'horizontalInput',
                                        hideExpression: '!model.enabled',
                                        templateOptions: {
                                            type: 'number',
                                            label: 'Priority',
                                            required: true,
                                            help: 'When duplicate search results are found the result from the indexer with the highest number will be selected'
                                        }
                                    });

                                fieldset.push(
                                    {
                                        key: 'timeout',
                                        type: 'horizontalInput',
                                        hideExpression: '!model.enabled',
                                        templateOptions: {
                                            type: 'number',
                                            label: 'Timeout',
                                            help: 'Supercedes the general timeout in "Searching"'
                                        }
                                    });

                                if (model.type == "newznab") {
                                    fieldset.push(
                                        {
                                            key: 'hitLimit',
                                            type: 'horizontalInput',
                                            hideExpression: '!model.enabled',
                                            templateOptions: {
                                                type: 'number',
                                                label: 'API hit limit',
                                                help: 'Maximum number of API hits since "API hit reset time"'
                                            }
                                        }
                                    );
                                    fieldset.push(
                                        {
                                            key: 'hitLimitResetTime',
                                            type: 'timeOfDay',
                                            hideExpression: '!model.enabled || !model.hitLimit',
                                            templateOptions: {
                                                type: 'time',
                                                label: 'API hit reset time',
                                                help: 'UTC time at which the API hit counter is reset'
                                            }
                                        });
                                    fieldset.push(
                                        {
                                            key: 'username',
                                            type: 'horizontalInput',
                                            hideExpression: '!model.enabled',
                                            templateOptions: {
                                                type: 'text',
                                                required: false,
                                                label: 'Username',
                                                help: 'Only needed if indexer requires HTTP auth for API access (rare)'
                                            },
                                            watcher: {
                                                listener: function (field, newValue, oldValue, scope) {
                                                    if (newValue != oldValue) {
                                                        scope.$parent.needsConnectionTest = true;
                                                    }
                                                }
                                            }
                                        }
                                    );
                                    fieldset.push(
                                        {
                                            key: 'password',
                                            type: 'horizontalInput',
                                            hideExpression: '!model.enabled || !model.username',
                                            templateOptions: {
                                                type: 'text',
                                                required: false,
                                                label: 'Password',
                                                help: 'Only needed if indexer requires HTTP auth for API access (rare)'
                                            }
                                        }
                                    )

                                }


                                if (model.type != "womble") {
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

                                if (model.type == 'newznab') {
                                    fieldset.push(
                                        {
                                            key: 'search_ids',
                                            type: 'horizontalMultiselect',
                                            hideExpression: '!model.enabled',
                                            templateOptions: {
                                                label: 'Search IDs',
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
                                    );
                                    fieldset.push(
                                        {
                                            key: 'searchTypes',
                                            type: 'horizontalMultiselect',
                                            hideExpression: '!model.enabled',
                                            templateOptions: {
                                                label: 'Search types',
                                                options: [
                                                    {label: 'Movies', id: 'movie'},
                                                    {label: 'TV', id: 'tvsearch'},
                                                    {label: 'Ebooks', id: 'book'},
                                                    {label: 'Audio', id: 'audio'}
                                                ]
                                            }
                                        }
                                    )
                                }

                                if (model.type == 'newznab') {
                                    fieldset.push(
                                        {
                                            type: 'horizontalCheckCaps',
                                            hideExpression: '!model.enabled || !model.host || !model.apikey || !model.name || angular.isUndefined(model.searchTypes)',
                                            templateOptions: {
                                                label: 'Check search types',
                                                help: 'Find out what search types the indexer supports. Done automatically for new indexers.'
                                            }
                                        }
                                    )
                                }

                                if (model.type == 'nzbindex') {
                                    fieldset.push(
                                        {
                                            key: 'generalMinSize',
                                            type: 'horizontalInput',
                                            hideExpression: '!model.enabled',
                                            templateOptions: {
                                                type: 'number',
                                                label: 'Min size',
                                                help: 'NZBIndex returns a lot of crap with small file sizes. Set this value and all smaller results will be filtered out no matter the category'
                                            }
                                        }
                                    );
                                }

                                return fieldset;
                            },
                            isInitial: function () {
                                return isInitial
                            },
                            parentModel: function () {
                                return parentModel;
                            }
                        }
                    });

                    modalInstance.result.then(function () {
                        $scope.form.$setDirty(true);
                        if (angular.isDefined(callback)) {
                            callback(true);
                        }
                    }, function () {
                        console.log("Indexer cancelled");
                        if (angular.isDefined(callback)) {
                            callback(false);
                        }
                    });
                }

                function showIndexerBox(model, parentModel) {
                    $scope._showIndexerBox(model, parentModel, false)
                }
                
                function orderIndexer(a, b) {
                    console.log(a);
                    console.log(b);
                    // if (a.score = b.score) {
                    //     return a.name < b.name;
                    // } else {
                    //     return a.score < b.score;
                    // }
                    return 0;
                }

                $scope.addIndexer = function (indexers, preset) {
                    var model = {
                        enabled: true,
                        host: null,
                        apikey: null,
                        hitLimit: null,
                        hitLimitResetTime: new Date(0),
                        timeout: null,
                        name: null,
                        showOnSearch: true,
                        score: 0,
                        username: null,
                        password: null,
                        preselect: true,
                        type: 'newznab',
                        accessType: "both",
                        search_ids: undefined, //["imdbid", "rid", "tvdbid"],
                        searchTypes: undefined, //["tvsearch", "movie"]
                    };
                    if (angular.isDefined(preset)) {
                        model.name = preset.name;
                        model.host = preset.host;
                        model.search_ids = preset.searchIds;
                    }

                    $scope.isInitial = true;

                    $scope._showIndexerBox(model, indexers, true, function (isSubmitted) {
                        if (isSubmitted) {
                            console.log("Pusing to model");
                            indexers.push(model);
                        }
                    });
                };

            }

        });

    });

angular
    .module('nzbhydraApp').run(function (formlyConfig, formlyValidationMessages) {

    formlyValidationMessages.addStringMessage('required', 'This field is required');

    formlyConfig.extras.errorExistsAndShouldBeVisibleExpression = 'fc.$touched || form.$submitted';

});


angular.module('nzbhydraApp').controller('IndexerModalInstanceController', function ($scope, $uibModalInstance, $http, model, fields, isInitial, parentModel, growl, ModalService, blockUI) {

    $scope.model = model;
    $scope.fields = fields;
    $scope.isInitial = isInitial;
    $scope.spinnerActive = false;
    $scope.needsConnectionTest = false;

    console.log($uibModalInstance);


    function checkConnection(onSuccess, onUnsuccessful, onError) {
        console.log("Connection test needed");
        $scope.spinnerActive = true;
        var url;
        var params;
        if (model.type == "newznab") {
            url = "internalapi/test_newznab";
            params = {host: model.host, apikey: model.apikey};
        } else if (model.type == "omgwtf") {
            url = "internalapi/test_omgwtf";
            params = {username: model.username, apikey: model.apikey};
        }

        $http.get(url, {params: params}).success(function (result) {
            //Using ng-class and a scope variable doesn't work for some reason, is only updated at second click 
            if (result.result) {
                if (angular.isDefined(onSuccess)) {
                    onSuccess();
                }
            } else {
                if (angular.isDefined(onUnsuccessful)) {
                    onUnsuccessful(result.message);
                }
            }

        }).error(function (result) {
            if (angular.isDefined(onError)) {
                onError(result.message);
            }
        }).finally(function () {
            $scope.spinnerActive = false;
        });
    }

    function checkCaps(onSuccess, onError) {
        $scope.spinnerActive = true;
        var url;
        var params;

        url = "internalapi/test_caps";
        params = {indexer: model.name, apikey: model.apikey, host: model.host};
        $http.get(url, {params: params}).success(function (result) {
            //Using ng-class and a scope variable doesn't work for some reason, is only updated at second click 
            if (result.success) {
                if (angular.isDefined(onSuccess)) {
                    onSuccess(result.ids, result.types);
                }
            } else {
                if (angular.isDefined(onError)) {
                    onError();
                }
            }

        }).error(function () {
            if (angular.isDefined(onError)) {
                onError(result.message);
            }
        }).finally(function () {
            $scope.spinnerActive = false;
        })
    }

    function checkCapsOrSubmit() {
        if (angular.isUndefined(model.search_ids) || angular.isUndefined(model.searchTypes)) {
            console.log("We need to check the caps first");
            blockUI.start("New indexer found. Testing its capabilities. This may take a bit...");
            checkCaps(
                function (ids, types) {
                    blockUI.reset();
                    growl.info("Successfully tested capabilites of indexer. Supports: " + ids + "," + types);
                    model.search_ids = ids;
                    model.searchTypes = types;
                    $uibModalInstance.close($scope);
                },
                function () {
                    blockUI.reset();
                    ModalService.open("Error testing capabilities", "The capabilities of the indexer could not be checked. The indexer won't be used for ID based searches (IMDB, TVDB, etc.). You may repeat the check manually at any time.", function () {
                        $uibModalInstance.close($scope);
                    });
                    model.search_ids = [];
                    model.searchTypes = [];
                })
        } else {
            $uibModalInstance.close($scope);
        }
    }

    $scope.obSubmit = function () {
        if ($scope.form.$valid) {
            if ($scope.needsConnectionTest) {
                checkConnection(
                    function () {
                        console.log("Form is valid and connection was tested successfully");
                        checkCapsOrSubmit();
                    },
                    function (message) {
                        console.log("Form is valid but connection was not tested successfully");
                        growl.error("The connection to the indexer failed: " + message);
                    },
                    function () {
                        console.log("Form is valid but connection was not tested successfully");
                        growl.error("The connection to the indexer could not be tested, sorry");
                    });
            } else {
                console.log("No connection test needed");
                checkCapsOrSubmit();
            }
        } else {
            growl.error("Config invalid. Please check your settings.");
            console.log($scope);
            angular.forEach($scope.form.$error.required, function (field) {
                field.$setTouched();
            });
        }
    };

    $scope.reset = function () {
        console.log("Cancelling");
        $scope.reset();
    };

    $scope.deleteIndexer = function () {
        parentModel.splice(parentModel.indexOf(model), 1);
        $uibModalInstance.close($scope);
    };

    $scope.reset = function () {
        console.log("Resetting to original model");
        for (var i = 0; i < $scope.fields.length; i++) {
            if (angular.isDefined($scope.fields[i].resetModel)) {
                $scope.fields[i].resetModel();
            }
        }

    };

    $scope.$on("modal.closing", function (targetScope, reason, c) {
        console.log("Closing");

        if (reason == "backdrop click") {
            $scope.reset();
        }
    });
});