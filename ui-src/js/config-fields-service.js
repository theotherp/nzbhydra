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
                        label: 'Check search types'
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
                                help: 'Stay with master...'
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


            ],

            system: [
                {
                    key: 'shutdown',
                    type: 'shutdown',
                    templateOptions: {
                        type: 'button',
                        label: 'Shutdown'
                    }
                },
                {
                    key: 'restart',
                    type: 'restart',
                    templateOptions: {
                        type: 'button',
                        label: 'Restart'
                    }
                }
            ]


        };
        
        

    }

}