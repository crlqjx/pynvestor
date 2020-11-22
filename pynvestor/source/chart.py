from pynvestor.source import yahoo, euronext
from pynvestor.source.helpers import Helpers
from plotly.subplots import make_subplots

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import datetime as dt
import abc


class Chart:
    def __init__(self):
        self._helpers = Helpers()

    @abc.abstractmethod
    def _get_data(self):
        pass

    @abc.abstractmethod
    def _plot_data(self):
        pass


class StockChart(Chart):
    def __init__(self, isin):
        super().__init__()
        self.isin = isin
        self.yahoo_info = yahoo.get_info_from_isin(self.isin)
        self.yahoo_symbol = self.yahoo_info['symbol']
        self.name = self.yahoo_info['longname']

        self._get_data()
        self._plot_data()

    def _get_data(self):
        data = yahoo.get_quotes(self.yahoo_symbol)
        self._data = data
        return True

    def _plot_data(self):
        title = f'{self.isin} - {self.name}'
        increasing_color = '#03F71B'
        decreasing_color = '#ff2626'

        dates = [dt.date.fromtimestamp(d) for d in self._data['chart']['result'][0]['timestamp']]
        chart_data = self._data['chart']['result'][0]['indicators']['quote'][0]
        stock_open = chart_data['open']
        stock_close = chart_data['close']
        stock_high = chart_data['high']
        stock_low = chart_data['low']
        stock_volume = chart_data['volume']
        volume_colors = []
        for c, o in zip(stock_close, stock_open):
            if (c is None and o is None) or (c - o) > 0:
                volume_colors.append(increasing_color)
            else:
                volume_colors.append(decreasing_color)

        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, specs=[[{'rowspan': 3}],
                                                                      [None],
                                                                      [None],
                                                                      [{'rowspan': 1}]])
        price_chart = go.Candlestick(x=dates, open=stock_open, high=stock_high, low=stock_low, close=stock_close,
                                     showlegend=False)
        price_chart.increasing.fillcolor = increasing_color
        price_chart.increasing.line.color = increasing_color
        price_chart.decreasing.fillcolor = decreasing_color
        price_chart.decreasing.line.color = decreasing_color
        volume_chart = go.Bar(x=dates, y=stock_volume, showlegend=False)
        volume_chart.marker.color = volume_colors
        fig.add_trace(price_chart, row=1, col=1)
        fig.add_trace(volume_chart, row=4, col=1)
        fig.update_layout(title=title, xaxis_rangeslider_visible=False, yaxis_title='Stock Price')
        fig.update_xaxes(rangebreaks=[dict(bounds=['sat', 'mon'])])
        self.fig = fig
        return True


class PortfolioChart(Chart):
    def __init__(self, portfolio_navs, isin_reference_index, mic):
        super().__init__()
        self._isin_reference_index = isin_reference_index
        self._mic = mic
        self._portfolio_navs = portfolio_navs
        self._get_data()
        self._plot_data()

    def _get_data(self):
        self._portfolio_navs = self._portfolio_navs.to_frame()
        self._portfolio_navs.name = 'Net Asset Value'
        reference_index_details = euronext.get_instrument_details(self._isin_reference_index, self._mic)
        index_name = reference_index_details['instr']['longNm']
        index_prices = self._helpers.get_prices_from_mongo(self._isin_reference_index,
                                                           self._portfolio_navs.index[0],
                                                           dt.datetime.today()).to_frame()
        chart_data = self._portfolio_navs.join(index_prices)
        chart_data['index_return'] = chart_data['price'].pct_change().fillna(0)

        perfs = []
        perf = 100
        for r in chart_data['index_return'].values:
            perf *= (1 + r)
            perfs.append(perf)
        chart_data[index_name] = perfs

        self._chart_data = chart_data[['navs', index_name]]

        return True

    def _plot_data(self):
        self.fig = px.line(self._chart_data, labels={'value': 'performance'})
        self.fig.data[0].name = 'Portfolio'
        self.fig.update_layout(legend={'orientation': 'h'})
        return True


class ValueAtRiskChart:
    def __init__(self, losses, values_at_risk, value_at_risk):
        self._losses = losses
        self._values_at_risk = values_at_risk
        self._value_at_risk = value_at_risk

        self._plot_data()

    def _plot_data(self):
        lower_bound = int(np.floor(self._losses[0] / 10) * 10)
        upper_bound = int(np.ceil(self._losses[-1] / 10) * 10)
        counts, bins = np.histogram(self._losses, bins=range(lower_bound, upper_bound + 10, 10))
        lower_bounds = bins[:-1]
        upper_bounds = bins[1:]
        bins = 0.5 * (bins[:-1] + bins[1:])
        bins_names = []
        bins_colors = []
        for lb, ub in zip(lower_bounds, upper_bounds):
            bins_names.append(f'[{lb}; {ub}]')
            bins_colors.append('cornflowerblue')
            if lb > self._value_at_risk:
                bins_colors[-1] = 'red'
        df = pd.DataFrame.from_dict(
            {'lower_bounds': lower_bounds, 'upper_bounds': upper_bounds, 'bins_names': bins_names,
             'counts': counts})
        self.fig = px.bar(data_frame=df,
                          x=bins,
                          y=counts,
                          labels={'x': 'losses', 'y': 'frequency'},
                          hover_data=['bins_names'])
        self.fig.update_traces(hovertemplate='losses=%{customdata[0]}<extra></extra><br>frequency=%{y}',
                               marker_color=bins_colors)
        self.fig.add_shape(type='line',
                           y0=0,
                           y1=max(counts)/2,
                           x0=self._value_at_risk,
                           x1=self._value_at_risk,
                           line={'color': 'red', 'width': 4, 'dash': 'dashdot'})
        self.fig.add_trace(go.Scatter(
            x=[self._value_at_risk + 5],
            y=[max(counts)/2.2],
            text=[f'VaR: {round(self._value_at_risk, 2)}'],
            mode='text',
            textposition='top right',
            textfont={'color': 'red', 'size': 18},
            showlegend=False
        ))
        self.fig.update_layout(bargap=0.1)
        return True
