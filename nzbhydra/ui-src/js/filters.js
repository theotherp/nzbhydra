//Filters that are needed at several places. Probably possible to do tha another way but I dunno how
var filters = angular.module('filters', []);


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



