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
var RevAll = require('gulp-rev-all');
var rename = require("gulp-rename");
var clean = require('gulp-clean');


gulp.task('vendor-scripts', function () {
    var dest = '.tmp/static/js';
    return gulp.src(wiredep().js)
        .pipe(sourcemaps.init())
        .pipe(concat('alllibs.js'))
        .pipe(changed(dest))//Important: Put behind concat, otherwise it will always think the sources changed
        //.pipe(uglify())
        .pipe(sourcemaps.write("./"))
        .pipe(gulp.dest(dest));
});

gulp.task('vendor-css', function () {
    var dest = '.tmp/static/css';
    return gulp.src(wiredep().css)
        .pipe(sourcemaps.init())
        .pipe(concat('alllibs.css'))
        .pipe(changed(dest))
        .pipe(sourcemaps.write("."))
        .pipe(gulp.dest(dest));

});

gulp.task('scripts', function () {
    var dest = '.tmp/static/js';
    return gulp.src("ui-src/js/**/*.js")
        .pipe(ngAnnotate())
        .on('error', swallowError)
        .pipe(angularFilesort())
        .on('error', swallowError)
        .pipe(sourcemaps.init())
        .pipe(concat('nzbhydra.js'))
        .on('error', swallowError)
        .pipe(changed(dest))
        //.pipe(uglify()) //Deactive when developing, even with source maps not nice to handle
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest(dest));

});

gulp.task('less', function () {
    var dest = '.tmp/static/css';
    gulp.src('ui-src/less/nzbhydra.less')
        .pipe(sourcemaps.init())
        .pipe(less())
        .on('error', swallowError)
        .pipe(sourcemaps.write("."))
        .pipe(gulp.dest(dest));
});

gulp.task('copy-assets', function () {
    var fontDest = '.tmp/static/fonts';
    var fonts = gulp.src("bower_components/bootstrap/fonts/*")
        .pipe(gulp.dest(fontDest));

    var imgDest = '.tmp/static/img';
    var img = gulp.src("ui-src/img/**/*")
        .pipe(gulp.dest(imgDest));

    var htmlDest = '.tmp/static/html';
    var html = gulp.src("ui-src/html/**/*")
        .pipe(gulp.dest(htmlDest));

    var htmlIndex = '.tmp/';
    var html = gulp.src("ui-src/index.html")
        .pipe(gulp.dest(htmlIndex));

    return merge(img, html, fonts);

});

gulp.task('add', function () {
    return gulp.src('static/*')
        .pipe(git.add({args: '--all'}));
});

gulp.task('clean-static', function () {
    return gulp.src('static', {read: false})
        .pipe(clean());
});

gulp.task('clean-tmp', function () {
    return gulp.src('.tmp', {read: false})
        .pipe(clean());
});

gulp.task('move-indexhtml', function () {
    return gulp.src('index.html')
        .pipe(gulp.dest('templates'));
});

gulp.task('clean-indexhtml', function () {
    return gulp.src('index.html*', {read: false})
        .pipe(clean());
});

gulp.task('revision', ['scripts', 'less', 'vendor-scripts', 'vendor-css', 'copy-assets'], function () {

    var revAll = new RevAll({dontRenameFile: [/^\/favicon.ico$/g, /^\/index.html/g], dontSearchFile: ['alllibs.js']});
    return gulp.src(".tmp/**", { base:".tmp"}).pipe(revAll.revision()).pipe(gulp.dest(""), {cwd:"static", base:"static"});
});

gulp.task('reload', function () {
    return gulp.src('templates/index.html')
        .pipe(livereload());
});

gulp.task('index', function () {
    runSequence(['clean-static', 'clean-tmp'], 'revision', 'move-indexhtml', 'clean-indexhtml', 'add', 'reload', 'clean-tmp');
});

function swallowError(error) {
    console.log(error.toString());
    this.emit('end');
}


gulp.task('default', function () {
    livereload.listen();
    gulp.watch(['ui-src/**/*'], ['index']);
});