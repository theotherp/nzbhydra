var filters = angular.module('filters', []);

filters.filter('bytes', function() {
	return function(bytes, precision) {
		if (isNaN(parseFloat(bytes)) || !isFinite(bytes) || bytes == 0) return '-';
		if (typeof precision === 'undefined') precision = 1;
		
		var units = ['b', 'kB', 'MB', 'GB', 'TB', 'PB'],
			number = Math.floor(Math.log(bytes) / Math.log(1024));
		return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +   units[number];
	}
});

filters.filter('unsafe', 
	function ($sce) {
		return function (value, type) {
			return $sce.trustAs(type || 'html', text);
		};
	}
);