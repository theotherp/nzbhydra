module.exports = function (grunt) {

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        bowercopy: {
            options: {
                clean: false
            },
            bootstrap: {
                src: 'bootstrap:main', dest: 'nzbhydra/static/lib/bootstrap/'
            }, jquery: {
                src: 'jquery:main', dest: 'nzbhydra/static/lib/jquery/'
            }, jqueryui: {
                src: 'jquery-ui:main', dest: 'nzbhydra/static/lib/jquery-ui/'
            }, angular: {
                src: 'angular:main', dest: 'nzbhydra/static/lib/angular/'
            }, angularcookie: {
                src: 'angular-cookie:main', dest: 'nzbhydra/static/lib/angular-cookie/'
            }, angularbootstrap: {
                src: 'angular-bootstrap:main', dest: 'nzbhydra/static/lib/angular-bootstrap/'
            }, angularroute: {
                src: 'angular-route:main', dest: 'nzbhydra/static/lib/angular-route/'
            }, angularloadingbar: {
                src: 'angular-loading-bar:main', dest: 'nzbhydra/static/lib/angular-loadingbar/'
            }, angulargrowl2: {
                src: 'angular-growl-2:main', dest: 'nzbhydra/static/lib/angular-growl-2/'
            }, angularanimate: {
                src: 'angular-animate:main', dest: 'nzbhydra/static/lib/angular-animate/'
            }, animatecss: {
                src: 'animate-css:main', dest: 'nzbhydra/static/lib/animate-css/'
            }, typicons: {
                src: 'typicons:main', dest: 'nzbhydra/static/lib/typicons/'
            }, underscore: {
                src: 'underscore:main', dest: 'nzbhydra/static/lib/underscore/'
            }, momentjs: {
                src: 'momentjs:main', dest: 'nzbhydra/static/lib/momentjs/'
            }, angularfilter: {
                src: 'angular-filter:main', dest: 'nzbhydra/static/lib/angular-filter/'
            }, reactrouter: {
                src: 'react-router:main', dest: 'nzbhydra/static/lib/react-router/'
            }, angularbusy: {
                src: 'angular-busy:main', dest: 'nzbhydra/static/lib/angular-busy/'
            }, rest: {
                options: {
                    destPrefix: 'nzbhydra/static/lib'
                }, files: {
                    src: 'bootstrap/bootstrap-theme.css',
                    src: 'bootstrap/bootstrap.css.map',
                    src: 'bootstrap/glyphicons-halflings-regular.woff2',
                    src: 'bootstrap/bootstrap-theme.css.map',
                    src: 'angular-bootstrap/ui-bootstrap-tlps.js',
                    src: 'superagent/superagent.js'
                }
            }
        },

        bower_concat: {
            all: {
                dest: 'nzbhydra/static/lib/concatted.js',
                cssDest: 'nzbhydra/static/lib/concatted.css',
                mainFiles: {
                    'angular-bootstrap': 'ui-bootstrap-tpls.js',
                    'superagent': 'superagent.js',
                    'filesize': 'filesize.js'
                }
            }
        },


        ngAnnotate: {
            options: {
                singleQuotes: true
            }, your_target: {
                files: [{
                    expand: true, src: ['nzbhydra/static/js/**/*.js']
                }]
            }
        },

        clean: {
            options: {
                'no-write': false
            },
            static: ["nzbhydra/static/*.*"],
            dist: ["nzbhydra/dist/**/*.js", "nzbhydra/dist/**/*.css", "nzbhydra/dist/index.html", "nzbhydra/dist/js/views/**/*.*", "nzbhydra/dist/html/*.*"],
            distaftermin: ['nzbhydra/dist/lib/**', 'nzbhydra/dist/js/**/*.js', 'nzbhydra/dist/css/nzbhydra.css', 'nzbhydra/dist/css/bootstrap.css', '!nzbhydra/dist/js/nzbhydra*.js', '!nzbhydra/dist/js/libs*.js']
        },


        //My build


        copy: {
            statictodist: {
                files: [{expand: true, flatten: false, cwd: 'nzbhydra/static/', src: ['**'], dest: 'nzbhydra/dist/'}]
            }
        },

        less: {
            nzbhydra: {
                options: {
                    strictMath: true,
                    paths: ["nzbhydra/static/less"]
                },
                files: {
                    'nzbhydra/static/css/nzbhydra.css': 'nzbhydra/static/less/nzbhydra.less'
                }
            },
            bootstrap: {
                options: {
                    strictMath: true
                },
                files: {
                    'nzbhydra/static/lib/bootstrap/bootstrap.css': 'nzbhydra/static/lib/bootstrap/less/bootstrap.less'
                }
            },
            slider: {
                files: {
                    'nzbhydra/static/lib/seiyria-bootstrap-slider/bootstrap-slider.css': 'nzbhydra/static/lib/seiyria-bootstrap-slider/bootstrap-slider.less'
                }
            }
        },

        filerev: {
            options: {
                algorithm: 'md5',
                length: 8
            },
            source: {
                files: [{
                    src: [
                        'nzbhydra/dist/css/nzbhydra.css',
                        'nzbhydra/dist/js/nzbhydra.js',
                        'nzbhydra/dist/js/libs.js',
                        'nzbhydra/dist/js/views/**/*.html',
                        'nzbhydra/dist/html/*.html'
                    ]
                }]
            }
        },

        useminPrepare: {
            html: 'nzbhydra/dist/index.html',
            options: {
                dest: 'dist'
            }
        },

        usemin: {
            html: 'nzbhydra/dist/index.html',
            views: 'nzbhydra/dist/js/**/*.js',
            generalHtml: 'nzbhydra/dist/js/**/*.js',
            options: {
                assetsDirs: ['js', 'css', 'nzbhydra/dist/css', 'nzbhydra/dist/js', 'dist'],
                patterns: {
                    views: [
                        [/templateUrl[ =:]+["|'](\/js\/views\/[a-z]*\/[a-zA-Z0-9]*\.html)["|']/img, 'Template replacement in js files']
                    ],
                    generalHtml: [
                        [/templateUrl[ =:]+["|'](\/html\/[a-zA-Z0-9]*\.html)["|']/img, 'Template replacement in js files']
                    ]
                }
            }

        },


        watch: {
            mystuff: {
                files: ['nzbhydra/static/**/*.*', '!nzbhydra/static/less/**/*.less'], options: {
                    livereload: true
                }
            },

            crapLess: {
                files: ['nzbhydra/static/less/nzbhydra.less', 'nzbhydra/static/less/bootstrap/variables.less'], tasks: ['less:nzbhydra']
            },

            bootstrapLess: {
                files: ['nzbhydra/static/less/bootstrap/**/*.less'], tasks: ['less:bootstrap']
            }
        },

        bower: {
            install: {
                options: {
                    targetDir: 'nzbhydra/static/lib',
                    layout: 'byType',
                    install: false,
                    verbose: false,
                    cleanTargetDir: false,
                    cleanBowerDir: false,
                    bowerOptions: {}
                }
            }
        }

    });

    grunt.registerTask('summary', function () {
        grunt.log.writeln(JSON.stringify(grunt.filerev.summary));
    });


    grunt.loadNpmTasks('grunt-bowercopy');
    grunt.loadNpmTasks('grunt-bower-concat');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-filerev');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-usemin');
    grunt.loadNpmTasks('grunt-ng-annotate');
    grunt.loadNpmTasks('grunt-filerev-replace');
    grunt.loadNpmTasks('grunt-userev');
    grunt.loadNpmTasks('grunt-bower-task');

    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-less');


    grunt.registerTask(
        'builddist',
        [
            'clean:dist',
            'less',
            'copy:statictodist',
            'useminPrepare',
            'concat:generated',
            'cssmin:generated',
            'uglify:generated',
            'filerev',
            'usemin',
            'clean:distaftermin',
            'summary'
        ]
    );


    grunt.registerTask('default', ['watch']);

    grunt.registerTask('copy', ['bowercopy']);

};