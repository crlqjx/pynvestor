// Load and plot optimizer chart

import { getParams } from './chart_parameters/optimizer_params.js';

export function optimizerChart(toElementId, title, efficientFrontierData, scatterData) {
    // load chart data
    var params = getParams(title, efficientFrontierData, scatterData);
    Highcharts.chart(toElementId, params)
    }
;