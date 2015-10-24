var gulp = require('gulp');
var mainBowerFiles = require('main-bower-files');
var print = require('gulp-print');
var wiredep = require('wiredep');
var inject = require('gulp-inject');
var copy = require('gulp-copy');
var flatten = require('gulp-flatten');
var angularFilesort = require('gulp-angular-filesort');
var ngAnnotate = require('gulp-ng-annotate');
var merge = require('merge-stream');



gulp.task('main-bowerfiles', function () {
    return gulp.src(mainBowerFiles(/* options */), {base: 'bower_components'})
        .pipe(flatten())
        .pipe(gulp.dest("nzbhydra/ui-src/lib")
    );
});

gulp.task('vendor-scripts', function () {
    return gulp.src(wiredep().js)
        .pipe(flatten())
        .pipe(gulp.dest('nzbhydra/static/lib'));

});

gulp.task('vendor-css', function () {
    return gulp.src(wiredep().css)
        .pipe(flatten())
        .pipe(gulp.dest('nzbhydra/static/lib'));

});

gulp.task('scripts', function () {
    return gulp.src("nzbhydra/ui-src/js/**/*.js")
        .pipe(ngAnnotate())
        .pipe(angularFilesort())
        .pipe(gulp.dest('nzbhydra/static/js'));

});

gulp.task('css', function () {
    return gulp.src("nzbhydra/ui-src/css/**/*.css")
        .pipe(gulp.dest('nzbhydra/static/css'));

});

gulp.task('copy-assets', function () {
    var img =  gulp.src("nzbhydra/ui-src/img/**/*")
        .pipe(gulp.dest('nzbhydra/static/img'));
    
    var html =  gulp.src("nzbhydra/ui-src/html/**/*")
        .pipe(gulp.dest('nzbhydra/static/html'));
    
    return merge(img, html);

});

gulp.task('index', ['scripts', 'css', 'vendor-scripts', 'vendor-css', 'copy-assets'], function () {

    return gulp.src('nzbhydra/ui-src/index.html')
        .pipe(wiredep.stream({
            fileTypes: {
                html: {
                    replace: {
                        js: function (filePath) {
                            return '<script src="/static/lib/' + filePath.split('/').pop() + '"></script>';
                        },
                        css: function (filePath) {
                            return '<link rel="stylesheet" href="/static/lib/' + filePath.split('/').pop() + '"/>';
                        }
                    }
                }
            }
        }))

        .pipe(inject(
            gulp.src(['nzbhydra/ui-src/js/*.js'], {read: false}), {
                addRootSlash: false,
                transform: function (filePath, file, i, length) {
                    return '<script src="' + filePath.replace('nzbhydra/ui-src', '/static') + '"></script>';
                }
            }))

        .pipe(inject(
            gulp.src(['nzbhydra/ui-src/css/*.css'], {read: false}), {
                addRootSlash: false,
                transform: function (filePath, file, i, length) {
                    return '<link rel="stylesheet" href="' + filePath.replace('nzbhydra/ui-src', '/static') + '"/>';
                }
            }))
        .pipe(gulp.dest('nzbhydra/static'));
});