// Parameters and data for the optimizer efficient frontier chart

export function getParams(title, efficientFrontierData, scatterData) {
    var params = {
        chart:
            {
                type: 'spline',
                zoomType: 'x'
            },
        legend:
            {
                enabled: false
            },
            title:
            {
                text: title
            },
            series:
                [
                    {
                        type: 'line',
                        name: 'Efficient Frontier',
                        data: efficientFrontierData
                    },
                    {
                        type: 'scatter',
                        opacity: 0.5,
                        tooltip: {
                            headerFormat: '{point.key}<br>'
                        },
                    marker:
                        {
                        symbol: 'circle'
                        },
                    data: scatterData
                    }
            ]
        }
    return params
    };
