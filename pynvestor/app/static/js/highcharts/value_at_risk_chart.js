// Load and plot value at risk chart

import { getParams } from './chart_parameters/value_at_risk_params.js';

export function valueAtRiskChart(toElementId, chartData, valueAtRisk, categories, varPosition, endPosition) {
    // load chart data
    var params = getParams(chartData, valueAtRisk, categories, varPosition, endPosition);
    Highcharts.chart(toElementId, params)
    }
;