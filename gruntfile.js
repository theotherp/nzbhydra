module.exports = function (grunt) {

	grunt.initConfig({
		pkg: grunt.file.readJSON('package.json'),

		bowercopy: {
			options: {
				clean: false
			}, bootstrap: {
				src: 'bootstrap:main', dest: 'static/lib/bootstrap/'
			}, jquery: {
				src: 'jquery:main', dest: 'static/lib/jquery/'
			}, jqueryui: {
				src: 'jquery-ui:main', dest: 'static/lib/jquery-ui/'
			}, angular: {
				src: 'angular:main', dest: 'static/lib/angular/'
			}, angularcookie: {
				src: 'angular-cookie:main', dest: 'static/lib/angular-cookie/'
			}, angularbootstrap: {
				src: 'angular-bootstrap:main', dest: 'static/lib/angular-bootstrap/'
			}, angularroute: {
				src: 'angular-route:main', dest: 'static/lib/angular-route/'
			}, angularloadingbar: {
				src: 'angular-loading-bar:main', dest: 'static/lib/angular-loadingbar/'
			}, angulargrowl2: {
				src: 'angular-growl-2:main', dest: 'static/lib/angular-growl-2/'
			}, angularanimate: {
				src: 'angular-animate:main', dest: 'static/lib/angular-animate/'
			}, animatecss: {
				src: 'animate-css:main', dest: 'static/lib/animate-css/'
			}, typicons: {
				src: 'typicons:main', dest: 'static/lib/typicons/'
			}, underscore: {
				src: 'underscore:main', dest: 'static/lib/underscore/'
			}, momentjs: {
				src: 'momentjs:main', dest: 'static/lib/momentjs/'
			}, angularfilter: {
				src: 'angular-filter:main', dest: 'static/lib/angular-filter/'
			}, reactrouter: {
				src: 'react-router:main', dest: 'static/lib/react-router/'
			}, angularuicalendar: {
				src: 'angular-ui-calendar:main', dest: 'static/lib/angular-ui-calendar/'
			}, fullcalendar: {
				src: 'fullcalendar:main', dest: 'static/lib/fullcalendar/'
			}, angularbusy: {
				src: 'angular-busy:main', dest: 'static/lib/angular-busy/'
			}, rest: {
				options: {
					destPrefix: 'static/lib'
				}, files: {
					src: 'bootstrap/bootstrap-theme.css',
					src: 'bootstrap/bootstrap.css.map',
					src: 'bootstrap/glyphicons-halflings-regular.woff2',
					src: 'bootstrap/bootstrap-theme.css.map',
					src: 'angular-bootstrap/ui-bootstrap-tlps.js',
					src: 'superagent/superagent.js',
					'fullcalendar/gcal.js': 'fullcalendar/dist/gcal.js',
					'filesize/filesize.js': 'filesize/lib/filesize.js'
				}
			}
		},
		
		bower_concat: {
			all: {
				dest: 'static/lib/concatted.js',
				cssDest: 'static/lib/concatted.css',
				mainFiles: {
					'angular-bootstrap': 'ui-bootstrap-tpls.js',
					'superagent': 'superagent.js',
					'filesize':'filesize.js'				
				}
			}
		},
		
		
		ngAnnotate: {
			options: {
				singleQuotes: true
			}, your_target: {
				files: [{
					expand: true, src: ['static/js/**/*.js']
				}]
			}
		},

		clean: {
			options: {
				'no-write': false
			},
			static: ["static/*.*"],
			dist: ["dist/**/*.js", "dist/**/*.css", "dist/index.html", "dist/js/views/**/*.*", "dist/html/*.*"],
			distaftermin: ['dist/lib/**', 'dist/js/**/*.js', 'dist/css/crapture.css', 'dist/css/bootstrap.css', '!dist/js/allTheCrap*.js', '!dist/js/libs*.js']
		},
		

		//My build


		copy: {
			statictodist: {
				files: [{expand: true, flatten: false, cwd: 'static/', src: ['**'], dest: 'dist/'}]
			}
		},	
		
		less: {
			crapture: {
				options: {
					strictMath: true,
					paths: ["static/less"]
				},
				files: {
      				'static/css/crapture.css': 'static/less/crapture.less'
    			}
			},
			bootstrap: {
				options: {
					strictMath: true
				},
				files: {
					'static/css/bootstrap.css': 'static/less/bootstrap/bootstrap.less'
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
						'dist/css/allTheCrap.css',
						'dist/js/allTheCrap.js',
			 			'dist/js/libs.js',
						'dist/js/views/**/*.html',
						'dist/html/*.html'
					]
				}]
			}
		},

		useminPrepare: {
			html: 'dist/index.html',
			options: {
				dest: 'dist'
			}
		},
		
		usemin: {
			html: 'dist/index.html',
			views: 'dist/js/**/*.js',
			generalHtml: 'dist/js/**/*.js',
			options: {
				assetsDirs: ['js', 'css', 'dist/css', 'dist/js', 'dist'],
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
				files: ['static/**/*.*', '!static/less/**/*.less'], tasks: ['shell'], options: {
					livereload: true
				}
			},
			
			crapLess: {
				files: ['static/less/crapture.less'], tasks: ['less:crapture', 'shell']
			},
			
			bootstrapLess: {
				files: ['static/less/bootstrap/**/*.less'], tasks: ['less:bootstrap']
			}
		},

		shell: {
			options: {
				stderr: true
			}, target: {
				command: 'rsync -avzhe  \'ssh -p 2222\' static vagrant@127.0.0.1:/home/vagrant/pyCrapTest'
			}
		}

	});
	
	grunt.registerTask('summary', function() {
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
	
	grunt.loadNpmTasks('grunt-contrib-watch');
	grunt.loadNpmTasks('grunt-contrib-copy');
	grunt.loadNpmTasks('grunt-contrib-less');
	grunt.loadNpmTasks('grunt-shell');
	

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
	
};