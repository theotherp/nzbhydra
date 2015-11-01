angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);

angular
    .module('nzbhydraApp')
    .config(function config(formlyConfigProvider) {
        // set templates here
        formlyConfigProvider.setWrapper({
            name: 'horizontalBootstrapLabel',
            template: [
                '<div class="row form-group form-horizontal">',
                '<div style="text-align:right;">',
                '<label for="{{::id}}" class="col-md-6 control-label">',
                '{{to.label}} {{to.required ? "*" : ""}}',
                '</label>',
                '</div>',
                '<div class="col-md-8">',
                '<formly-transclude></formly-transclude>',
                '</div>',
                '<span class="help-block">{{to.help}}</div>',
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

        formlyConfigProvider.setType({
            name: 'horizontalInput',
            extends: 'input',
            wrapper: ['horizontalBootstrapLabel', 'bootstrapHasError']
        });


        formlyConfigProvider.setType({
            name: 'switch',
            template: [
                '<div style="text-align:left"><input bs-switch type="checkbox" ng-model="model[options.key]"/></div>'
            ].join(' ')

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

    });


function ConfigController($scope, ConfigService, configPromise) {

    console.log(configPromise);
    $scope.config = configPromise.settings;

    $scope.fields = {
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
                            placeholder: 'IPv4 address to bind to'
                        }
                    },
                    {
                        key: 'port',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
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
                        key: 'sslcert',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'SSL certificate file'
                        }
                    },
                    {
                        key: 'sslkey',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'SSL key file'
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
                        templateOptions: {
                            type: 'text',
                            label: 'Username',
                            help: 'Only applies if authentication is enabled'
                        }
                    },
                    {
                        key: 'password',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Password',
                            help: 'Only applies if authentication is enabled'
                        }
                    },
                    {
                        key: 'apikey',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'API key'
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
                        key: 'cacheType',
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
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Cache timeout',
                            help: 'Only applies if authentication is enabled'
                        }
                    },
                    {
                        key: 'cachethreshold',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Cache threshold'
                        }
                    },
                    {
                        key: 'cacheFolder',
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
                    }
                ]
            }]
    };
    
    
    


    $scope.onSubmit = function (form) {
        // First we broadcast an event so all fields validate themselves
        $scope.$broadcast('schemaFormValidate');

        // Then we check if the form is valid
        if (form.$valid) {
            ConfigService.set($scope.config);
        }
    }
}


