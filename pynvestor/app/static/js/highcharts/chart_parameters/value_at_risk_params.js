// Parameters and data for the value at risk chart

export function getParams(chartData, valueAtRisk, categories, varPosition, endPosition) {
    var params = {
        chart: {zoomType: 'x'},
        title: {text: 'Value At Risk 95%'},
        plotOptions: {
            column: {
                pointPadding: 0,
                borderWidth: 0,
                groupPadding: 0,
                shadow: false,
                colorByPoint: false
            }
        },
        xAxis: {
            categories: categories,
            plotBands: {
                from: varPosition,
                to: endPosition,
                color: '#ff9999',
                label: {text: `VaR 95%: ${valueAtRisk} EUR`,
                    align: 'left',
                    x: 30,
                    y: 50,
                    style: {
                        fontSize: 12,
                        fontWeight: 'bold'
                        }
                    }
            }
        },
        yAxis: [{
            labels: {
                align: 'left'
            },
            resize: {
                enabled: true
                }
            }
        ],
        series: [
            {
                type: 'column',
                data: chartData,
                color: '#99c2ff'
            }
        ]
    }
    return params
};