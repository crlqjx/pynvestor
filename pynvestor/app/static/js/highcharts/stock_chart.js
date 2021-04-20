// Load and plot stock ohlc chart

import { getParams } from './chart_parameters/stock_params.js';

export function stockChart(toElementId, stockName, chartTitle, ohlcData, volumeData) {
    // load chart data
    var params = getParams(stockName, chartTitle, ohlcData, volumeData);
    Highcharts.stockChart(toElementId, params)
    }
;