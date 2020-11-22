from flask import Flask, render_template, request
from pynvestor.source.portfolio import Portfolio
from pynvestor.source.risk import PortfolioRiskManager
from pynvestor.source.screener import Screener
from pynvestor.source.chart import StockChart, PortfolioChart, ValueAtRiskChart

import datetime as dt


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

    ptf_chart = PortfolioChart(ptf.portfolio_navs, 'FR0003500008', 'XPAR')
    return render_template('portfolio.html',
                           df=df_ptf,
                           ptf=ptf,
                           ptf_date=ptf_date,
                           ptf_chart_html=ptf_chart.fig.to_html(full_html=False))


@app.route('/risk')
def risk_management():
    risk_manager = PortfolioRiskManager(0.01)
    var_chart = ValueAtRiskChart(risk_manager.simulated_losses, risk_manager.portfolio_values_at_risk,
                                 risk_manager.portfolio_value_at_risk)
    return render_template('risk_management.html',
                           names=list(risk_manager.stocks_names.values()),
                           correlation_matrix=risk_manager.correlation_matrix,
                           ptf_vol=risk_manager.annualized_portfolio_volatility,
                           ptf_sharpe_ratio=risk_manager.portfolio_sharpe_ratio,
                           ptf_value_at_risk=risk_manager.portfolio_value_at_risk,
                           var_chart_html=var_chart.fig.to_html(full_html=False))


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
                               period='annual')
    screener_result = equity_screener.run()
    return render_template('screener.html', df=screener_result)


@app.route('/chart')
def show_chart():
    isin = request.args.get('isin')
    chart = StockChart(isin)
    return chart.fig.to_html()


app.run(debug=True)
