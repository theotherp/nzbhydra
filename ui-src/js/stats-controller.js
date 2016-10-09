angular
    .module('nzbhydraApp')
    .controller('StatsController', StatsController);

function StatsController($scope, $filter, stats) {

    stats = stats.data;
    $scope.nzbDownloads = null;
    $scope.avgResponseTimes = stats.avgResponseTimes;
    $scope.avgIndexerSearchResultsShares = stats.avgIndexerSearchResultsShares;
    $scope.avgIndexerAccessSuccesses = stats.avgIndexerAccessSuccesses;
    $scope.indexerDownloadShares = stats.indexerDownloadShares;
    $scope.downloadsPerHourOfDay = stats.timeBasedDownloadStats.perHourOfDay;
    $scope.downloadsPerDayOfWeek = stats.timeBasedDownloadStats.perDayOfWeek;
    $scope.searchesPerHourOfDay = stats.timeBasedSearchStats.perHourOfDay;
    $scope.searchesPerDayOfWeek = stats.timeBasedSearchStats.perDayOfWeek;

    function getChart(chartType, values, xKey, yKey, xAxisLabel, yAxisLabel) {
        return {
            options: {
                chart: {
                    type: chartType,
                    height: 350,
                    margin: {
                        top: 20,
                        right: 20,
                        bottom: 100,
                        left: 50
                    },
                    x: function (d) {
                        return d[xKey];
                    },
                    y: function (d) {
                        return d[yKey];
                    },
                    showValues: true,
                    valueFormat: function (d) {
                        return d;
                    },
                    color: function () {
                        return "red"
                    },
                    showControls: false,
                    showLegend: false,
                    duration: 100,
                    xAxis: {
                        axisLabel: xAxisLabel,
                        tickFormat: function (d) {
                            return d;
                        },
                        rotateLabels: 30,
                        axisLabelDistance: -10,
                        showMaxMin: false,
                        color: function () {
                            return "white"
                        }
                    },
                    yAxis: {
                        axisLabel: yAxisLabel,
                        axisLabelDistance: -10,
                        tickFormat: function (d) {
                            return d;
                        }
                    },
                    tooltip: {
                        enabled: false
                    },
                    zoom: {
                        enabled: true,
                        scaleExtent: [1, 10],
                        useFixedDomain: false,
                        useNiceScale: false,
                        horizontalOff: false,
                        verticalOff: true,
                        unzoomEventType: 'dblclick.zoom'
                    }
                }
            }, data: [{
                "key": "doesntmatter",
                "bar": true,
                "values": values
            }]
        };
    }

    $scope.avgResponseTimesChart = getChart("multiBarHorizontalChart", $scope.avgResponseTimes, "name", "avgResponseTime", "", "Response time");
    $scope.avgResponseTimesChart.options.chart.margin.left = 100;
    $scope.avgResponseTimesChart.options.chart.yAxis.axisLabelDistance = 0;

    $scope.downloadsPerHourOfDayChart = getChart("discreteBarChart", $scope.downloadsPerHourOfDay, "hour", "count", "Hour of day", 'Downloads');
    $scope.downloadsPerDayOfWeekChart = getChart("discreteBarChart", $scope.downloadsPerDayOfWeek, "day", "count", "Day of week", 'Downloads');

    $scope.searchesPerHourOfDayChart = getChart("discreteBarChart", $scope.searchesPerHourOfDay, "hour", "count", "Hour of day", 'Searches');
    $scope.searchesPerDayOfWeekChart = getChart("discreteBarChart", $scope.searchesPerDayOfWeek, "day", "count", "Day of week", 'Searches');


    //Was unable to use the function above for this and gave up
    $scope.resultsSharesChart = {
        options: {
            chart: {
                type: 'multiBarChart',
                height: 350,
                margin: {
                    top: 20,
                    right: 20,
                    bottom: 100,
                    left: 45
                },

                clipEdge: true,
                duration: 500,
                stacked: false,
                reduceXTicks: false,
                showValues: true,
                tooltip: {
                    enabled: true,
                    valueFormatter: function (d) {
                        return d + "%";
                    }
                },
                showControls: false,
                xAxis: {
                    axisLabel: '',
                    showMaxMin: false,
                    rotateLabels: 30,
                    axisLabelDistance: 30,
                    tickFormat: function (d) {
                        return d;
                    }
                },
                yAxis: {
                    axisLabel: 'Share (%)',
                    axisLabelDistance: -20,
                    tickFormat: function (d) {
                        return d;
                    }
                }
            }
        },

        data: [
            {
                key: "Results",
                values: _.map($scope.avgIndexerSearchResultsShares, function (stats) {
                    return {series: 0, y: stats.avgResultsShare, x: stats.name}
                })
            },
            {
                key: "Unique results",
                values: _.map($scope.avgIndexerSearchResultsShares, function (stats) {
                    return {series: 1, y: stats.avgUniqueResults, x: stats.name}
                })
            }
        ]
    };

    $scope.indexerDownloadSharesChart = {
        options: {
            chart: {
                type: 'pieChart',
                height: 500,
                x: function (d) {
                    return d.name;
                },
                y: function (d) {
                    return d.share;
                },
                showLabels: true,
                duration: 500,
                labelThreshold: 0.01,
                labelSunbeamLayout: true,
                tooltip: {
                    valueFormatter: function (d, i) {
                        return $filter('number')(d, 2) + "%";
                    }
                },
                legend: {
                    margin: {
                        top: 5,
                        right: 35,
                        bottom: 5,
                        left: 0
                    }
                }
            }
        },
        data: $scope.indexerDownloadShares
    };


}
