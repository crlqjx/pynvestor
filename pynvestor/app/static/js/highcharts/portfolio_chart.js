// Load and plot portfolio chart

import { getParams } from './chart_parameters/portfolio_params.js';

export function portfolioChart(toElementId, title, chartData) {
    // load chart data
    var params = getParams(title, chartData);
    Highcharts.stockChart(toElementId, params)
    }
;