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
var less = require('gulp-less');
var livereload = require('gulp-livereload');
var concat = require('gulp-concat');



gulp.task('less', function () {
    gulp.src('nzbhydra/ui-src/less/nzbhydra.less')
        .pipe(less())
        .pipe(gulp.dest('nzbhydra/ui-src/css'));
});


gulp.task('main-bowerfiles', function () {
    return gulp.src(mainBowerFiles(/* options */), {base: 'bower_components'})
        .pipe(flatten())
        .pipe(gulp.dest("nzbhydra/ui-src/lib")
    );
});

gulp.task('vendor-scripts', function () {
    return gulp.src(wiredep().js)
        .pipe(flatten())
        .pipe(concat('alllibs.js'))
        .pipe(gulp.dest('nzbhydra/static/js'));

});

gulp.task('vendor-css', function () {
    return gulp.src(wiredep().css)
        .pipe(flatten())
        .pipe(concat('alllibs.css'))
        .pipe(gulp.dest('nzbhydra/static/css'));

});

gulp.task('scripts', function () {
    return gulp.src("nzbhydra/ui-src/js/**/*.js")
        .pipe(ngAnnotate())
        .pipe(angularFilesort())
        .pipe(concat('nzbhydra.js'))
        .pipe(gulp.dest('nzbhydra/static/js'));

});

gulp.task('css', function () {
    return gulp.src("nzbhydra/ui-src/css/**/*.css")
        .pipe(concat('nzbhydra.css'))
        .pipe(gulp.dest('nzbhydra/static/css'));

});

gulp.task('copy-assets', function () {
    var img = gulp.src("nzbhydra/ui-src/img/**/*")
        .pipe(gulp.dest('nzbhydra/static/img'));

    var html = gulp.src("nzbhydra/ui-src/html/**/*")
        .pipe(gulp.dest('nzbhydra/static/html'));

    return merge(img, html);

});

gulp.task('index', ['scripts', 'css', 'vendor-scripts', 'vendor-css', 'copy-assets'], function () {

    return gulp.src('nzbhydra/ui-src/index.html')
        .pipe(gulp.dest('nzbhydra/static'))
        .pipe(livereload());
});


gulp.task('watch', function () {
    livereload.listen();
    gulp.watch(['nzbhydra/ui-src/less/*'], ['less']);
    gulp.watch(['nzbhydra/ui-src/**/*', '!nzbhydra/ui-src/less/**/*'], ['index']);
});