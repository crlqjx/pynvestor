from pynvestor.source import yahoo
from pynvestor.source.helpers import Helpers
from plotly.subplots import make_subplots

import plotly.graph_objects as go
import plotly.express as px
import datetime as dt


class StockChart:
    def __init__(self, isin):
        self._helpers = Helpers()
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


class PortfolioChart:
    def __init__(self, portfolio_navs):
        # TODO: add index levels in dataframe
        # TODO: show total perf on the chart
        self._portfolio_navs = portfolio_navs.copy()
        self._portfolio_navs.name = 'Net Asset Value'
        self._plot_data()

    def _plot_data(self):
        self.fig = px.line(self._portfolio_navs, y=self._portfolio_navs.name)
        return True
