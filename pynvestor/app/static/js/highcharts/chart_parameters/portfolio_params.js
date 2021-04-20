// Parameters and data for the portfolio chart

export function getParams(title, chartData) {
    var params = {
            chart: {zoomType: 'x'},
            rangeSelector: {selected: 5},
            navigator: {enabled: false},
            scrollbar: {enabled: false},
            title: {text: title},
            series: chartData,
            yAxis: {offset: 30}
        }
    return params
}