from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap

import datetime as dt
from pynvestor.source.screener import Screener
from pynvestor.source.chart import Chart

today = dt.date(2020, 10, 28)


def create_app():
    flask_app = Flask(__name__)
    Bootstrap(flask_app)
    return flask_app


app = create_app()


@app.route('/')
def index():
    return 'Main Page'


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
                               period='annual', as_of_date=dt.datetime(today.year, today.month, today.day - 1))
    screener_result = equity_screener.run()
    return render_template('screener.html', df=screener_result)


@app.route('/chart/')
def show_chart():
    isin = request.args.get('isin')
    chart = Chart(isin)
    return chart.fig.to_html()


app.run(debug=True)
