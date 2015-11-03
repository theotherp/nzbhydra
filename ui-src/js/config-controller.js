angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);

angular
    .module('nzbhydraApp')
    .config(function config(formlyConfigProvider) {
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
                '<span class="input-group-btn">',
                '<button class="btn btn-default" type="button" ng-click="generate()"><span class="glyphicon glyphicon-refresh"></span></button>',
                '</div>'
            ].join(' '),
            controller: function($scope) {
                $scope.generate = function() {
                    $scope.model[$scope.options.key] = Array(31).join((Math.random().toString(36) + '00000000000000000').slice(2, 18)).slice(0, 30);
                }
            }
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
            extends: 'select',
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


function ConfigController($scope, ConfigService, configPromise) {
    $scope.config = configPromise.settings;

    $scope.submit = submit;

    function submit() {
        console.log("Submit:");
        console.log($scope.config);
        ConfigService.set($scope.config);
    }


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
                        hideExpression: '!model.ssl',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'SSL certificate file',
                            required: true
                        }
                    },
                    {
                        key: 'sslkey',
                        hideExpression: '!model.ssl',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'SSL key file',
                            required: true
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
                                text: 'seconds'
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
                        }
                    },
                    {
                        key: 'logfile-filename',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Log file'
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
                                {name: 'Debug', value: 'DEBUG'},
                                {name: 'Info', value: 'INFO'}
                            ]
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
                        {name: 'NZBGet', value: 'nzbget'},
                        {name: 'SabNZBd', value: 'sabnzbd'}
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
                        {name: 'Redirect to the indexer', value: 'redirect'},
                        {name: 'Use direct links', value: 'direct'}
                    ],
                    help: "How external access to NZBs is provided. Proxying NZBs is recommended."
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
                    }


                ]
            },
            {
                wrapper: 'fieldset',
                key: 'sabnzbd',
                hideExpression: 'model.downloader!="sabnzbd"',
                templateOptions: {label: 'SabNZBd'},
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
                        key: 'apikey',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'API Key'
                        }
                    }


                ]
            }
        ],

        indexers: [
            {
                wrapper: 'fieldset',
                key: 'binsearch',
                templateOptions: {label: 'Binsearch'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },
            {
                wrapper: 'fieldset',
                key: 'nzbclub',
                templateOptions: {label: 'NZBClub'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }

                ]
            },
            {
                wrapper: 'fieldset',
                key: 'nzbindex',
                templateOptions: {label: 'NZBIndex'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'generalMinSize',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Min size',
                            help: 'NZBIndex returns a lot of crap with small file sizes. Set this value and all smaller results will be filtered out no matter the category'
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },
            {
                wrapper: 'fieldset',
                key: 'womble',
                templateOptions: {label: 'Womble'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },

            {
                wrapper: 'fieldset',
                key: 'newznab1',
                templateOptions: {label: 'Newznab 1'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'name',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Name',
                            help: 'Used for identification. Changing the name will lose all history and stats!'
                        }
                    },
                    {
                        key: 'host',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Host'
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
                        key: 'search_ids',
                        type: 'horizontalMultiselect',
                        templateOptions: {
                            label: 'Search types',
                            options: [
                                {label: 'TVDB', id: 'tvdbid'},
                                {label: 'TVRage', id: 'rid'},
                                {label: 'IMDB', id: 'imdbid'}
                            ]
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },
            {
                wrapper: 'fieldset',
                hideExpression: '!model.newznab1.name',
                key: 'newznab2',
                templateOptions: {label: 'Newznab 2'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'name',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Name',
                            help: 'Used for identification. Changing the name will lose all history and stats!'
                        }
                    },
                    {
                        key: 'host',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Host'
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
                        key: 'search_ids',
                        type: 'horizontalMultiselect',
                        templateOptions: {
                            label: 'Search types',
                            options: [
                                {label: 'TVDB', id: 'tvdbid'},
                                {label: 'TVRage', id: 'rid'},
                                {label: 'IMDB', id: 'imdbid'}
                            ]
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },
            {
                wrapper: 'fieldset',
                hideExpression: '!model.newznab2.name',
                key: 'newznab3',
                templateOptions: {label: 'Newznab 3'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'name',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Name',
                            help: 'Used for identification. Changing the name will lose all history and stats!'
                        }
                    },
                    {
                        key: 'host',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Host'
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
                        key: 'search_ids',
                        type: 'horizontalMultiselect',
                        templateOptions: {
                            label: 'Search types',
                            options: [
                                {label: 'TVDB', id: 'tvdbid'},
                                {label: 'TVRage', id: 'rid'},
                                {label: 'IMDB', id: 'imdbid'}
                            ]
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },
            {
                wrapper: 'fieldset',
                hideExpression: '!model.newznab3.name',
                key: 'newznab4',
                templateOptions: {label: 'Newznab 4'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'name',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Name',
                            help: 'Used for identification. Changing the name will lose all history and stats!'
                        }
                    },
                    {
                        key: 'host',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Host'
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
                        key: 'search_ids',
                        type: 'horizontalMultiselect',
                        templateOptions: {
                            label: 'Search types',
                            options: [
                                {label: 'TVDB', id: 'tvdbid'},
                                {label: 'TVRage', id: 'rid'},
                                {label: 'IMDB', id: 'imdbid'}
                            ]
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },
            {
                wrapper: 'fieldset',
                key: 'newznab5',
                hideExpression: '!model.newznab4.name',
                templateOptions: {label: 'Newznab 5'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'name',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Name',
                            help: 'Used for identification. Changing the name will lose all history and stats!'
                        }
                    },
                    {
                        key: 'host',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Host'
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
                        key: 'search_ids',
                        type: 'horizontalMultiselect',
                        templateOptions: {
                            label: 'Search types',
                            options: [
                                {label: 'TVDB', id: 'tvdbid'},
                                {label: 'TVRage', id: 'rid'},
                                {label: 'IMDB', id: 'imdbid'}
                            ]
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            },
            {
                wrapper: 'fieldset',
                hideExpression: '!model.newznab5.name',
                key: 'newznab6',
                templateOptions: {label: 'Newznab 6'},
                fieldGroup: [
                    {
                        key: 'enabled',
                        type: 'horizontalSwitch',
                        templateOptions: {
                            type: 'switch',
                            label: 'Enabled'
                        }
                    },
                    {
                        key: 'name',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Name',
                            help: 'Used for identification. Changing the name will lose all history and stats!'
                        }
                    },
                    {
                        key: 'host',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'text',
                            label: 'Host'
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
                        key: 'search_ids',
                        type: 'horizontalMultiselect',
                        templateOptions: {
                            label: 'Search types',
                            options: [
                                {label: 'TVDB', id: 'tvdbid'},
                                {label: 'TVRage', id: 'rid'},
                                {label: 'IMDB', id: 'imdbid'}
                            ]
                        }
                    },
                    {
                        key: 'score',
                        type: 'horizontalInput',
                        templateOptions: {
                            type: 'number',
                            label: 'Score',
                            help: 'When duplicate search results are found the result from the indexer with the highest score will be shown'
                        }
                    }
                ]
            }
        ]
    };

    $scope.tabs = [
        {
            name: 'Main',
            model: $scope.config.main,
            fields: $scope.fields.main,
            active: true
        },
        {
            name: 'Searching',
            model: $scope.config.searching,
            fields: $scope.fields.searching,
            active: false
        },
        {
            name: 'Downloader',
            model: $scope.config.downloader,
            fields: $scope.fields.downloader,
            active: false
        },
        {
            name: 'Indexers',
            model: $scope.config.indexers,
            fields: $scope.fields.indexers,
            active: false
        }
    ];


    $scope.onSubmit = function (form) {
        // First we broadcast an event so all fields validate themselves
        $scope.$broadcast('schemaFormValidate');

        // Then we check if the form is valid
        if (form.$valid) {
            ConfigService.set($scope.config);
        }
    }
}


