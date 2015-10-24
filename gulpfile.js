var gulp = require('gulp');
var print = require('gulp-print');
var wiredep = require('wiredep');
var inject = require('gulp-inject');
var copy = require('gulp-copy');
var flatten = require('gulp-flatten');
var angularFilesort = require('gulp-angular-filesort');
var ngAnnotate = require('gulp-ng-annotate');
var merge = require('merge-stream');
var less = require('gulp-less-sourcemap');
var livereload = require('gulp-livereload');
var concat = require('gulp-concat');
var sourcemaps = require('gulp-sourcemaps');
var uglify = require('gulp-uglify');
var changed = require('gulp-changed');


gulp.task('less', function () {
    gulp.src('nzbhydra/ui-src/less/nzbhydra.less')
        .pipe(less())
        .pipe(gulp.dest('nzbhydra/ui-src/css'));
});


gulp.task('vendor-scripts', function () {
    var dest = 'nzbhydra/static/js';
    return gulp.src(wiredep().js)
        .pipe(flatten())
        .pipe(sourcemaps.init())
        .pipe(concat('alllibs.js'))
        .pipe(changed(dest))//Important: Put behind concat, otherwise it will always think the sources changed
        .pipe(uglify())
        .pipe(sourcemaps.write("."))
        .pipe(gulp.dest(dest));
});

gulp.task('vendor-css', function () {
    return gulp.src(wiredep().css)
        .pipe(flatten())
        .pipe(concat('alllibs.css'))
        
        .pipe(gulp.dest('nzbhydra/static/css'));

});

gulp.task('scripts', function () {
    var dest = 'nzbhydra/static/js';
    return gulp.src("nzbhydra/ui-src/js/**/*.js")
        .pipe(ngAnnotate())
        .pipe(angularFilesort())
        .pipe(sourcemaps.init())
        .pipe(concat('nzbhydra.js'))
        .pipe(changed(dest))
        .pipe(uglify())
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest(dest));

});

gulp.task('css', function () {
    return gulp.src("nzbhydra/ui-src/css/**/*.css")
        .pipe(concat('nzbhydra.css'))
        .pipe(gulp.dest('nzbhydra/static/css'));

});

gulp.task('copy-assets', function () {
    
    
    var imgDest = 'nzbhydra/static/img';
    var img = gulp.src("nzbhydra/ui-src/img/**/*")
        .pipe(changed(imgDest))
        .pipe(gulp.dest(imgDest));

    var htmlDest = 'nzbhydra/static/html';
    var html = gulp.src(["nzbhydra/ui-src/html/**/*", "bower_components/angularUtils-pagination/dirPagination.tpl.html"])
        .pipe(changed(htmlDest))
        .pipe(gulp.dest(htmlDest));

    return merge(img, html);

});

gulp.task('index', ['scripts', 'css', 'vendor-scripts', 'vendor-css', 'copy-assets'], function () {

    return gulp.src('nzbhydra/ui-src/index.html')
        .pipe(gulp.dest('nzbhydra/static'))
        .pipe(livereload());
});


gulp.task('default', function () {
    livereload.listen();
    gulp.watch(['nzbhydra/ui-src/less/*'], ['less']);
    gulp.watch(['nzbhydra/ui-src/**/*', '!nzbhydra/ui-src/less/**/*'], ['index']);
});