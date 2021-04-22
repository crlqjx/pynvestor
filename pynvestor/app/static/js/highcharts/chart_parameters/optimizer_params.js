// Parameters and data for the optimizer efficient frontier chart

export function getParams(title, efficientFrontierData, scatterData) {
    var params = {
        chart:
            {
                type: 'spline',
                zoomType: 'x'
            },
        plotOptions:
            {
                series: {
                    point: {
                        events: {
                            click: function() {
                                $.ajax({
                                    data: JSON.stringify({
                                        weights: this.weights
                                    }),
                                    type: 'POST',
                                    url: '/optimizer_portfolio_weights',
                                    contentType: "application/json; charset=UTF-8"
                                })
                                .done(function(data) {
                                    var weightsData = JSON.parse(data);
                                    // Clear block in case there is already data
                                    document.getElementById("onClickWeightsData").innerHTML = ''
                                    // Generate agGrid table
                                    grid("onClickWeightsData", weightsData);
                                    // Turn on display in case it's not already done
                                    document.getElementById("onClickDisplay").style.display = "block";
                                });

                                event.preventDefault()
                            }
                        }
                    }
                }
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
