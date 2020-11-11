from flask import Flask, render_template, request
from pynvestor.source.portfolio import Portfolio
from pynvestor.source.screener import Screener
from pynvestor.source.chart import StockChart, PortfolioChart

import datetime as dt

screener_date = dt.date(2020, 11, 5)


def create_app():
    flask_app = Flask(__name__)
    return flask_app


app = create_app()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/portfolio')
def portfolio():
    ptf_date = request.args.get('ptf_date')
    if ptf_date is None:
        ptf_date = 'today'
        ptf = Portfolio()
    else:
        ptf_date = dt.date.fromisoformat(ptf_date)
        ptf = Portfolio(dt.datetime(ptf_date.year, ptf_date.month, ptf_date.day))
    df_ptf = ptf.to_df()
    df_ptf.index.name = 'isin'
    df_ptf.reset_index(inplace=True)

    ptf_chart = PortfolioChart('FR0003500008')
    return render_template('portfolio.html',
                           df=df_ptf,
                           ptf=ptf,
                           ptf_date=ptf_date,
                           ptf_chart_html=ptf_chart.fig.to_html(full_html=False))


@app.route('/run_screener')
def run_screener():
    return


@app.route('/screener')
def screener():
    equity_screener = Screener({'eps': (0, 100),
                                'per': (0, 15),
                                'roe': (0.10, 1),
                                'gearing': (0, 1),
                                'operating_margin': (0.05, 10)},
                               period='annual',
                               as_of_date=dt.datetime(screener_date.year, screener_date.month, screener_date.day - 1))
    screener_result = equity_screener.run()
    return render_template('screener.html', df=screener_result)


@app.route('/chart')
def show_chart():
    isin = request.args.get('isin')
    chart = StockChart(isin)
    return chart.fig.to_html()


app.run(debug=True)
