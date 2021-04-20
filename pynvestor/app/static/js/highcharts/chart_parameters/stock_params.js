// Parameters and data for the stock ohlc chart

export function getParams(stockName, chartTitle, ohlcData, volumeData) {
    var params = {
        series: [
            {
                type: 'candlestick',
                name: stockName,
                data: ohlcData
            },
            {
                type: 'column',
                name: 'Volume',
                data: volumeData,
                yAxis: 1
            }
        ],
        scrollbar: {enabled: false},
        plotOptions: {
            series: {
                turboThreshold: 0,
            },

            candlestick: {
                color: '#ff2626',
                upColor: '#03F71B',
                tooltip: {
                    valueDecimals: 2
                }
            },
        },
        rangeSelector: {
            selected: 4
        },

        title: {
            text: chartTitle
        },

        yAxis: [{
            labels: {
                align: 'left'
            },
            height: '80%',
            resize: {
                enabled: true
            }
        }, {
            labels: {
                align: 'left'
            },
            top: '80%',
            height: '20%',
            offset: 0
        }],
        tooltip: {
            shape: 'square',
            headerShape: 'callout',
            borderWidth: 0,
            shadow: false
        },
        responsive: {
            rules: [{
                condition: {
                    maxWidth: 800
                },
                chartOptions: {
                    rangeSelector: {
                        inputEnabled: false
                    }
                }
            }]
        }
    };
    return params
};