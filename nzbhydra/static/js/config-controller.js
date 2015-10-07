angular
    .module('nzbhydraApp')
    .controller('ConfigController', ConfigController);


ConfigController.$inject = ['$scope', '$http', 'schemaForm'];
function ConfigController($scope, $http, schemaForm) {

    //Current procedure: Get flat dict with all lists converted to strings (because schema form cannot read the resulting schema), then generate a schema using http://jsonschema.net and copy it here
    //http://jeremydorn.com/json-editor supports the schema better but is kinda fugly

    //The form will have to be generated manually...

    $scope.schema =
    {
  "properties": {
    "downloader": {
      "properties": {
        "downloader": {
          "type": "string"
        },
        "nzbAddingType": {
          "type": "string"
        },
        "nzbaccesstype": {
          "type": "string"
        },
        "nzbget": {
          "properties": {
            "host": {
              "type": "string"
            },
            "password": {
              "type": "string"
            },
            "port": {
              "type": "integer"
            },
            "ssl": {
              "type": "checkbox"
            },
            "username": {
              "type": "string"
            }
          },
          "title": "nzbget",
          "type": "object"
        },
        "sabnzbd": {
          "properties": {
            "apikey": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "password": {
              "type": "string"
            },
            "port": {
              "type": "integer"
            },
            "ssl": {
              "type": "checkbox"
            }
          },
          "title": "sabnzbd",
          "type": "object"
        }
      },
      "title": "downloader",
      "type": "object"
    },
    "main": {
      "properties": {
        "apikey": {
          "type": "string"
        },
        "cacheFolder": {
          "type": "string"
        },
        "cacheTimeout": {
          "type": "integer"
        },
        "cacheType": {
          "type": "string"
        },
        "cachethreshold": {
          "type": "integer"
        },
        "debug": {
          "type": "checkbox"
        },
        "enableAuth": {
          "type": "checkbox"
        },
        "enableCache": {
          "type": "checkbox"
        },
        "host": {
          "type": "string"
        },
        "logging": {
          "properties": {
            "consolelevel": {
              "type": "string"
            },
            "logfile": {
              "properties": {
                "filename": {
                  "type": "string"
                },
                "level": {
                  "type": "string"
                }
              },
              "title": "logfile",
              "type": "object"
            }
          },
          "title": "logging",
          "type": "object"
        },
        "password": {
          "type": "string"
        },
        "port": {
          "type": "integer"
        },
        "ssl": {
          "type": "checkbox"
        },
        "sslcert": {
          "type": "string"
        },
        "sslkey": {
          "type": "string"
        },
        "username": {
          "type": "string"
        }
      },
      "title": "main",
      "type": "object"
    },
    "providers": {
      "properties": {
        "binsearch": {
          "properties": {
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "binsearch",
          "type": "object"
        },
        "newznab1": {
          "properties": {
            "apikey": {
              "type": "string"
            },
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "newznab1",
          "type": "object"
        },
        "newznab2": {
          "properties": {
            "apikey": {
              "type": "string"
            },
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "newznab2",
          "type": "object"
        },
        "newznab3": {
          "properties": {
            "apikey": {
              "type": "string"
            },
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "newznab3",
          "type": "object"
        },
        "newznab4": {
          "properties": {
            "apikey": {
              "type": "string"
            },
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "newznab4",
          "type": "object"
        },
        "newznab5": {
          "properties": {
            "apikey": {
              "type": "string"
            },
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "newznab5",
          "type": "object"
        },
        "newznab6": {
          "properties": {
            "apikey": {
              "type": "string"
            },
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "newznab6",
          "type": "object"
        },
        "newznab7": {
          "properties": {
            "apikey": {
              "type": "string"
            },
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "newznab7",
          "type": "object"
        },
        "newznab8": {
          "properties": {
            "apikey": {
              "type": "string"
            },
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "newznab8",
          "type": "object"
        },
        "nzbclub": {
          "properties": {
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "nzbclub",
          "type": "object"
        },
        "nzbindex": {
          "properties": {
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            }
          },
          "title": "nzbindex",
          "type": "object"
        },
        "womble": {
          "properties": {
            "enabled": {
              "type": "checkbox"
            },
            "generate_queries": {
              "type": "string"
            },
            "host": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "search_ids": {
              "type": "string"
            },
            "womble": {
              "type": "string"
            }
          },
          "title": "womble",
          "type": "object"
        }
      },
      "title": "providers",
      "type": "object"
    },
    "resultProcessing": {
      "properties": {
        "duplicateAgeThreshold": {
          "type": "integer"
        },
        "duplicateSizeThresholdInPercent": {
          "type": "number"
        }
      },
      "title": "resultProcessing",
      "type": "object"
    },
    "searching": {
      "properties": {
        "allowQueryGeneration": {
          "type": "string"
        },
        "ignoreTemporarilyDisabled": {
          "type": "checkbox"
        },
        "timeout": {
          "type": "integer"
        }
      },
      "title": "searching",
      "type": "object"
    }
  },
  "type": "object"
};


    $scope.form = [
        "*",
        {
            type: "submit",
            title: "Save"
        }
    ];

    $scope.model = {};
}


