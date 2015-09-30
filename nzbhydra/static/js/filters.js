//Filters that are needed at several places. Probably possible to do tha another way but I dunno how
var filters = angular.module('filters', []);

filters.filter('qualityLabel', function () {
	return function (qualityScore) {
		var value = parseInt(qualityScore);
		if (value == "NaN" || !value) {
			return "label-default"
		} else if (value >= 90) {
			return "label-success"
		} else if (value >= 60) {
			return "label-info"
		} else if (value >= 50) {
			return "label-warning"
		} else {
			return "label-danger";
		}
	};
});

filters.filter('bytes', function() {
	return function(bytes, precision) {
		if (isNaN(parseFloat(bytes)) || !isFinite(bytes) || bytes == 0) return '-';
		if (typeof precision === 'undefined') precision = 1;
		
		var units = ['b', 'kB', 'MB', 'GB', 'TB', 'PB'],
			number = Math.floor(Math.log(bytes) / Math.log(1024));
		//if(units[number] == "MB" || units[number] == "kB" || units[number] == "b")
		//precision = 0;
		return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +   units[number];
	}
});

filters.filter('unsafe', ['$sce', function ($sce) {
	return $sce.trustAsHtml;
}]);

filters.filter('statusLabel', function () {
	return function (value) {
		if (value == "Completed" ) {
			return "label-success"
		} else if (value == "Downloading") {
			return "label-info"
		} else if (value == "Failed") {
			return "label-danger"
		} else if (value == "Added") {
			return "label-warning"
		} else if (value == "Old"){
			return "label-default";
		}
	};
});


filters.filter('fileIcon', function()  {
	return function(name) {
		var icons = new Array();
		icons["7z"] = "/img/fileicons/7z.png";
		icons["ai"] = "/img/fileicons/ai.png";
		icons["aiff"] = "/img/fileicons/aiff.png";
		icons["asc"] = "/img/fileicons/asc.png";
		icons["audio"] = "/img/fileicons/audio.png";
		icons["avi"] = "/img/fileicons/avi.png";
		icons["bin"] = "/img/fileicons/bin.png";
		icons["bz2"] = "/img/fileicons/bz2.png";
		icons["c"] = "/img/fileicons/c.png";
		icons["cfc"] = "/img/fileicons/cfc.png";
		icons["cfm"] = "/img/fileicons/cfm.png";
		icons["chm"] = "/img/fileicons/chm.png";
		icons["class"] = "/img/fileicons/class.png";
		icons["conf"] = "/img/fileicons/conf.png";
		icons["cpp"] = "/img/fileicons/cpp.png";
		icons["cs"] = "/img/fileicons/cs.png";
		icons["css"] = "/img/fileicons/css.png";
		icons["csv"] = "/img/fileicons/csv.png";
		icons["deb"] = "/img/fileicons/deb.png";
		icons["default"] = "/img/fileicons/default.png";
		icons["directory"] = "/img/fileicons/directory.png";
		icons["divx"] = "/img/fileicons/divx.png";
		icons["doc"] = "/img/fileicons/doc.png";
		icons["dot"] = "/img/fileicons/dot.png";
		icons["eml"] = "/img/fileicons/eml.png";
		icons["enc"] = "/img/fileicons/enc.png";
		icons["file"] = "/img/fileicons/file.png";
		icons["gif"] = "/img/fileicons/gif.png";
		icons["gz"] = "/img/fileicons/gz.png";
		icons["hlp"] = "/img/fileicons/hlp.png";
		icons["htm"] = "/img/fileicons/htm.png";
		icons["html"] = "/img/fileicons/html.png";
		icons["image"] = "/img/fileicons/image.png";
		icons["iso"] = "/img/fileicons/iso.png";
		icons["jar"] = "/img/fileicons/jar.png";
		icons["java"] = "/img/fileicons/java.png";
		icons["jpeg"] = "/img/fileicons/jpeg.png";
		icons["jpg"] = "/img/fileicons/jpg.png";
		icons["js"] = "/img/fileicons/js.png";
		icons["lua"] = "/img/fileicons/lua.png";
		icons["m"] = "/img/fileicons/m.png";
		icons["mkv"] = "/img/fileicons/mkv.png";
		icons["mm"] = "/img/fileicons/mm.png";
		icons["mov"] = "/img/fileicons/mov.png";
		icons["mp3"] = "/img/fileicons/mp3.png";
		icons["mp4"] = "/img/fileicons/mp4.png";
		icons["mpg"] = "/img/fileicons/mpg.png";
		icons["odc"] = "/img/fileicons/odc.png";
		icons["odf"] = "/img/fileicons/odf.png";
		icons["odg"] = "/img/fileicons/odg.png";
		icons["odi"] = "/img/fileicons/odi.png";
		icons["odp"] = "/img/fileicons/odp.png";
		icons["ods"] = "/img/fileicons/ods.png";
		icons["odt"] = "/img/fileicons/odt.png";
		icons["ogg"] = "/img/fileicons/ogg.png";
		icons["pdf"] = "/img/fileicons/pdf.png";
		icons["pgp"] = "/img/fileicons/pgp.png";
		icons["php"] = "/img/fileicons/php.png";
		icons["pl"] = "/img/fileicons/pl.png";
		icons["png"] = "/img/fileicons/png.png";
		icons["ppt"] = "/img/fileicons/ppt.png";
		icons["ps"] = "/img/fileicons/ps.png";
		icons["py"] = "/img/fileicons/py.png";
		icons["ram"] = "/img/fileicons/ram.png";
		icons["rar"] = "/img/fileicons/rar.png";
		icons["rb"] = "/img/fileicons/rb.png";
		icons["rm"] = "/img/fileicons/rm.png";
		icons["rpm"] = "/img/fileicons/rpm.png";
		icons["rtf"] = "/img/fileicons/rtf.png";
		icons["sig"] = "/img/fileicons/sig.png";
		icons["sql"] = "/img/fileicons/sql.png";
		icons["swf"] = "/img/fileicons/swf.png";
		icons["sxc"] = "/img/fileicons/sxc.png";
		icons["sxd"] = "/img/fileicons/sxd.png";
		icons["sxi"] = "/img/fileicons/sxi.png";
		icons["sxw"] = "/img/fileicons/sxw.png";
		icons["tar"] = "/img/fileicons/tar.png";
		icons["tex"] = "/img/fileicons/tex.png";
		icons["tgz"] = "/img/fileicons/tgz.png";
		icons["txt"] = "/img/fileicons/txt.png";
		icons["vcf"] = "/img/fileicons/vcf.png";
		icons["video"] = "/img/fileicons/video.png";
		icons["vsd"] = "/img/fileicons/vsd.png";
		icons["wav"] = "/img/fileicons/wav.png";
		icons["wma"] = "/img/fileicons/wma.png";
		icons["wmv"] = "/img/fileicons/wmv.png";
		icons["xls"] = "/img/fileicons/xls.png";
		icons["xml"] = "/img/fileicons/xml.png";
		icons["xpi"] = "/img/fileicons/xpi.png";
		icons["xvid"] = "/img/fileicons/xvid.png";
		icons["zip"] = "/img/fileicons/zip.png";
		
		if (typeof name == 'undefined') {
			return icons["default"];
		}
		var ext =  name.split('.').pop();
		if (ext in icons) {
			return icons[ext];
		}
		return icons["default"];
				
	};
});