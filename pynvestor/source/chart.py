from pynvestor.source import yahoo, euronext
from pynvestor.source.helpers import Helpers

import numpy as np
import datetime as dt
import abc


class Chart:
    def __init__(self):
        self._helpers = Helpers()

    @abc.abstractmethod
    def _get_data(self):
        pass


class StockChart(Chart):
    def __init__(self, isin):
        super().__init__()
        self.isin = isin
        self.mic = euronext.get_mic_from_isin(isin)
        self.yahoo_info = yahoo.get_info_from_isin(self.isin)
        self.yahoo_symbol = self.yahoo_info['symbol']
        self.name = self.yahoo_info['longname']
        self.title = f'{self.isin} - {self.name}'
        self.increasing_color = '#03F71B'
        self.decreasing_color = '#ff2626'

        self._get_data()

    def _get_data(self):
        current_data = euronext.get_instrument_details(self.isin)
        current_open = float(current_data['instr']['currInstrSess']['openPx'])
        current_high = float(current_data['instr']['perf'][2]['highPx'])
        current_low = float(current_data['instr']['perf'][2]['lowPx'])
        current_last = float(current_data['instr']['currInstrSess']['lastPx'])
        current_volume = int(float(current_data['instr']['currInstrSess']['tradedQty']))

        current_date = dt.datetime.utcnow().timestamp() * 1000

        data = yahoo.get_quotes(self.yahoo_symbol)
        dates = [d * 1000 for d in data['chart']['result'][0]['timestamp']] + [current_date]
        chart_data = data['chart']['result'][0]['indicators']['quote'][0]
        stock_open = chart_data['open'] + [current_open]
        stock_close = chart_data['close'] + [current_last]
        stock_high = chart_data['high'] + [current_high]
        stock_low = chart_data['low'] + [current_low]
        stock_volume = chart_data['volume'] + [current_volume]

        volume_colors = []
        for c, o in zip(stock_close, stock_open):
            if (c is None and o is None) or (c - o) > 0:
                volume_colors.append(self.increasing_color)
            else:
                volume_colors.append(self.decreasing_color)

        ohlc = [[d, o, h, l, c] for d, o, h, l, c in zip(dates, stock_open, stock_high, stock_low, stock_close)]
        volume = [{'x': d, 'y': v, 'color': c} for (d, v, c) in zip(dates, stock_volume, volume_colors)]

        highcharts_parameters = {
            'series': [
                {
                    'type': 'candlestick',
                    'name': self.name,
                    'data': ohlc
                },
                {
                    'type': 'column',
                    'name': 'Volume',
                    'data': volume,
                    'yAxis': 1
                }
            ],
            'scrollbar': {'enabled': False},
            'plotOptions': {
                'series': {
                    'turboThreshold': 0,
                },

                'candlestick': {
                    'color': f'{self.decreasing_color}',
                    'upColor': f'{self.increasing_color}',
                    'tooltip': {
                        'valueDecimals': 2
                    }
                },
            },
            'rangeSelector': {
                'selected': 4
            },

            'title': {
                'text': f'{self.title}'
            },

            'yAxis': [{
                'labels': {
                    'align': 'left'
                },
                'height': '80%',
                'resize': {
                    'enabled': True
                }
            }, {
                'labels': {
                    'align': 'left'
                },
                'top': '80%',
                'height': '20%',
                'offset': 0
            }],
            'tooltip': {
                'shape': 'square',
                'headerShape': 'callout',
                'borderWidth': 0,
                'shadow': False
            },
            'responsive': {
                'rules': [{
                    'condition': {
                        'maxWidth': 800
                    },
                    'chartOptions': {
                        'rangeSelector': {
                            'inputEnabled': False
                        }
                    }
                }]
            }
        }

        self.highcharts_parameters = highcharts_parameters

        return True


class PortfolioChart(Chart):
    def __init__(self, portfolio_navs, isin_reference_index, mic):
        super().__init__()
        self._isin_reference_index = isin_reference_index
        self._mic = mic
        self._portfolio_navs = portfolio_navs
        self.title = "Portfolio Performance"
        self._get_data()

    def _get_data(self):
        reference_index_details = euronext.get_instrument_details(self._isin_reference_index, self._mic)
        self._index_name = reference_index_details['instr']['longNm']
        index_prices = self._helpers.get_prices_from_mongo(self._isin_reference_index,
                                                           self._portfolio_navs.index[0],
                                                           dt.datetime.today()).to_frame()
        chart_data = self._portfolio_navs.to_frame().join(index_prices)
        chart_data['index_return'] = chart_data['price'].pct_change().fillna(0)
        perfs = []
        perf = 100
        for r in chart_data['index_return'].values:
            perf *= (1 + r)
            perfs.append(perf)
        chart_data['reference_index_base100'] = perfs

        dates = [d.timestamp() * 1000 for d in chart_data.index]
        reference_index = [[d, index_base100] for d, index_base100 in
                           zip(dates, tuple(chart_data['reference_index_base100'].values))]
        portfolio_navs = [[d, nav] for d, nav in zip(dates, tuple(chart_data['navs'].values))]

        highcharts_data = [{'data': reference_index,
                            'name': self._index_name,
                            'tooltip': {'valueDecimals': 2},
                            'color': '#ff2626',
                            'opacity': 0.3},
                           {'data': portfolio_navs,
                            'name': 'Portfolio',
                            'tooltip': {'valueDecimals': 2},
                            'color': '#ffdf00'}]

        highcharts_parameters = {'rangeSelector': {'selected': 5},
                                 'navigator': {'enabled': False},
                                 'scrollbar': {'enabled': False},
                                 'title': {'text': self.title},
                                 'series': highcharts_data}

        self._highcharts_parameters = highcharts_parameters

        return True

    @property
    def highcharts_parameters(self):
        return self._highcharts_parameters


class ValueAtRiskChart:
    def __init__(self, losses, values_at_risk, value_at_risk):
        self._losses = losses
        self._values_at_risk = values_at_risk
        self._value_at_risk = value_at_risk

        self._get_data()

    def _get_data(self):
        bin_size = 10
        lower_bound = int(np.floor(self._losses[0] / bin_size) * bin_size)
        upper_bound = int(np.ceil(self._losses[-1] / bin_size) * bin_size)
        counts, bins = np.histogram(self._losses, bins=range(lower_bound, upper_bound + bin_size, bin_size))
        lower_bounds = bins[:-1]
        upper_bounds = bins[1:]
        bins_names = []
        var_position = None
        for idx, (lb, ub) in enumerate(zip(lower_bounds, upper_bounds)):
            bins_names.append(f'[{lb}; {ub}]')
            if lb < self._value_at_risk < ub:
                var_position = idx + (self._value_at_risk - lb) / bin_size - 0.5

        highcharts_parameters = {
            'chart': {'zoomType': 'x'},
            'title': {'text': 'Value At Risk 95%'},
            'plotOptions': {
                'column': {
                    'pointPadding': 0,
                    'borderWidth': 0,
                    'groupPadding': 0,
                    'shadow': False,
                    'colorByPoint': False
                }
            },
            'xAxis': {
                'categories': bins_names,
                'plotBands': {
                    'from': var_position,
                    'to': len(bins) - 1,
                    'color': '#ff9999',
                    'label': {'text': f'VaR 95%: {round(self._value_at_risk, 2)} EUR',
                              'align': 'left',
                              'x': 30,
                              'y': 50,
                              'style': {
                                  'fontSize': 12,
                                  'fontWeight': 'bold'
                              }
                              }
                }
            },
            'yAxis': [{
                'labels': {
                    'align': 'left'
                },
                'resize': {
                    'enabled': True
                }
            }],
            'series': [
                {
                    'type': 'column',
                    'data': counts,
                    'color': '#99c2ff'
                }
            ]
        }
        self._highcharts_parameters = highcharts_parameters

        return True

    @property
    def highcharts_parameters(self):
        return self._highcharts_parameters

