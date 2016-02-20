var gulp = require('gulp');
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
var sourcemaps = require('gulp-sourcemaps');
var uglify = require('gulp-uglify');
var changed = require('gulp-changed');
var newer = require('gulp-newer');
var git = require('gulp-git');
var runSequence = require('run-sequence');
var print = require('gulp-print');
var rename = require("gulp-rename");
var clean = require('gulp-clean');


gulp.task('vendor-scripts', function () {
    var dest = 'static/js';
    return gulp.src(wiredep().js)
        .pipe(sourcemaps.init())
        .pipe(concat('alllibs.js'))
        .pipe(changed(dest))//Important: Put behind concat, otherwise it will always think the sources changed
        //.pipe(uglify())
        .pipe(sourcemaps.write("./"))
        .pipe(newer(dest))
        .pipe(gulp.dest(dest));
});

gulp.task('vendor-css', function () {
    var dest = 'static/css';
    return gulp.src(wiredep().css)
        .pipe(sourcemaps.init())
        .pipe(concat('alllibs.css'))
        .pipe(changed(dest))
        .pipe(sourcemaps.write("."))
        .pipe(newer(dest))
        .pipe(gulp.dest(dest));

});

gulp.task('scripts', function () {
    var dest = 'static/js';
    return gulp.src("ui-src/js/**/*.js")
        .pipe(ngAnnotate())
        .on('error', swallowError)
        .pipe(angularFilesort())
        .on('error', swallowError)
        .pipe(sourcemaps.init())
        .pipe(concat('nzbhydra.js'))
        .on('error', swallowError)
        .pipe(changed(dest))
        //.pipe(uglify())
        .pipe(sourcemaps.write('./'))
        .pipe(newer(dest))
        .pipe(gulp.dest(dest));

});

gulp.task('less', function () {
    var dest = 'static/css';
    gulp.src('ui-src/less/nzbhydra.less')
        .pipe(sourcemaps.init())
        .pipe(less())
        .on('error', swallowError)
        .pipe(sourcemaps.write("."))
        .pipe(newer(dest))
        .pipe(gulp.dest(dest));
});

gulp.task('copy-assets', function () {
    var fontDest = 'static/fonts';
    var fonts = gulp.src("bower_components/bootstrap/fonts/*")
        .pipe(newer(fontDest))
        .pipe(gulp.dest(fontDest));

    var imgDest = 'static/img';
    var img = gulp.src("ui-src/img/**/*")
        .pipe(newer(imgDest))
        .pipe(gulp.dest(imgDest));

    var htmlDest = 'static/html';
    var html = gulp.src("ui-src/html/**/*")
        .pipe(newer(htmlDest))
        .pipe(gulp.dest(htmlDest));

    return merge(img, html, fonts);
});


gulp.task('add', function () {
    return gulp.src('static/*')
        .pipe(git.add({args: '--all'}));
});


gulp.task('reload', function () {
    return gulp.src('templates/index.html')
        .pipe(livereload());
});


gulp.task('index', function () {
    runSequence(['scripts', 'less', 'vendor-scripts', 'vendor-css', 'copy-assets'],  'add', 'reload');
});

function swallowError(error) {
    console.log(error.toString());
    this.emit('end');
}


gulp.task('default', function () {
    livereload.listen();
    gulp.watch(['ui-src/**/*'], ['index']);
});