from flask import Flask, render_template, request, jsonify
from pynvestor.source.portfolio import Portfolio
from pynvestor.source.risk import PortfolioRiskManager
from pynvestor.source.screener import Screener
from pynvestor.source.optimizer import Optimizer
from pynvestor.source.chart import StockChart, PortfolioChart, ValueAtRiskChart, OptimizerChart
from pynvestor.source import euronext

import numpy as np
import datetime as dt
import json

# TODO: find a way to format automatically performances
# TODO: put frames to regroup elements (market news, indices levels, ...)
# TODO: refactor this module; logic should be put elsewhere, put more abstraction


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (dt.date, dt.datetime)):
            return obj.isoformat()
        else:
            return super(JsonEncoder, self).default(obj)


def create_app():
    flask_app = Flask(__name__)
    return flask_app


app = create_app()
app.json_encoder = JsonEncoder


@app.route('/')
def index():
    indices = euronext.get_instruments_details([
        ('FR0003500008', 'XPAR'),  # CAC 40
        ('FR0003999499', 'XPAR'),  # CAC All Tradable
        ('FR0003502079', 'XPAR')   # Euronext 100
    ])
    indices = [list(i.values())[0] for i in indices]
    return render_template('index.html', indices=indices)


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
                           chart_title=ptf_chart.title,
                           ptf_chart_data=json.dumps(ptf_chart.chart_data, cls=JsonEncoder))


@app.route('/risk')
def risk_management():
    risk_manager = PortfolioRiskManager(0.01)
    var_chart = ValueAtRiskChart(risk_manager.simulated_losses, risk_manager.portfolio_values_at_risk,
                                 risk_manager.portfolio_value_at_risk)
    return render_template('risk_management.html',
                           names=list(risk_manager.stocks_names.values()),
                           correlation_matrix=risk_manager.correlation_matrix,
                           ptf_vol=round(risk_manager.annualized_portfolio_volatility, 4),
                           ptf_sharpe_ratio=round(risk_manager.portfolio_sharpe_ratio, 2),
                           ptf_value_at_risk=round(risk_manager.portfolio_value_at_risk, 2),
                           categories=json.dumps(var_chart.categories, cls=JsonEncoder),
                           var_position=var_chart.var_position,
                           end_position=var_chart.end_position,
                           var_chart_data=json.dumps(var_chart.chart_data, cls=JsonEncoder))


@app.route('/optimizer')
def optimizer():
    risk_free_rate = 0.01
    optimizer = Optimizer(risk_free_rate)
    risky_assets_weight = 1 - optimizer.cash_weight
    expected_returns = optimizer.mean_returns

    # Global minimum variance portfolio
    gmv_weigths, gmv_annualized_variance, gmv_expected_return = optimizer.minimum_variance_optimization()
    gmv_annualized_volatility = np.sqrt(gmv_annualized_variance)

    # Current portfolio optimization
    weights_opti, var_opti, ptf_return_opti = optimizer.portfolio_optimization()
    annualized_volatility_opti = np.sqrt(var_opti)

    # Efficient portfolio with a return corresponding to the highest single stock return
    max_return_stock = max(expected_returns) * risky_assets_weight
    max_stock_efficient_weights, max_stock_efficient_var, max_stock_efficient_return = \
        optimizer.minimum_variance_optimization(target_return=max_return_stock)

    # Optimizing for 100 return points between the global min var portfolio and the max return stock efficient portfolio
    returns_array = np.linspace(gmv_expected_return, max_stock_efficient_return, 100)
    efficient_portfolios = [optimizer.minimum_variance_optimization(target_return=r) for r in returns_array]

    efficient_weights, efficient_var, efficient_returns = list(zip(*efficient_portfolios))
    gmv_portfolio = {'weights': gmv_weigths,
                     'vol': gmv_annualized_volatility,
                     'expected_return': gmv_expected_return,
                     'name': 'Global Minimum Variance',
                     'color': 'green',
                     'marker': {'radius': 5}}
    current_portfolio = {'weights': list(optimizer.stocks_weights.values()),
                         'vol': optimizer.annualized_portfolio_volatility,
                         'expected_return': np.dot(np.array(list(optimizer.stocks_weights.values())),
                                                   optimizer.mean_returns),
                         'name': 'Current Portfolio',
                         'color': 'red',
                         'marker': {'radius': 5}}
    portfolio_optimized = {'weights': weights_opti,
                           'vol': annualized_volatility_opti,
                           'expected_return': ptf_return_opti,
                           'name': 'Portfolio Optimized',
                           'color': 'green',
                           'marker': {'radius': 5}}
    scatter_points = [gmv_portfolio, current_portfolio, portfolio_optimized]
    optimizer_chart = OptimizerChart(efficient_weights=efficient_weights,
                                     vol_data=list(np.sqrt(efficient_var)),
                                     expected_return_data=efficient_returns,
                                     scatter_points=scatter_points,
                                     title='Efficient Frontier')

    efficient_frontier_data, scatter_data = optimizer_chart.chart_data

    return render_template('optimizer.html',
                           efficient_frontier_data=json.dumps(efficient_frontier_data, cls=JsonEncoder),
                           scatter_data=json.dumps(scatter_data, cls=JsonEncoder))


@app.route('/screener')
def screener():
    return render_template('screener.html')


@app.route('/run_screener', methods=['POST'])
def run_screener():
    screening_data = request.json
    period = screening_data['period']
    fields_filters = screening_data['fields']
    equity_screener = Screener(fields_filters, period=period)
    df_screener_result = equity_screener.run()
    df_screener_result['date'] = df_screener_result['date'].dt.date
    columns_definition = [{'field': col} if col != 'isin' else {'field': col, 'cellRenderer': 'isinCellRenderer'}
                          for col in list(df_screener_result.columns)]
    row_data = df_screener_result.to_dict(orient='records')
    options = {'defaultColDef': {'resizable': True,
                                 'sortable': True},
               'domLayout': 'autoHeight'}

    result = {'columnDefs': columns_definition}
    result.update({'rowData': row_data})
    result.update(options)
    return json.dumps(result, cls=JsonEncoder)


@app.route('/chart')
def show_chart():
    isin = request.args.get('isin')
    stock_chart = StockChart(isin)
    ohlc_data, volume_data = stock_chart.chart_data
    return render_template('stock.html',
                           stock_name=stock_chart.name,
                           chart_title=stock_chart.title,
                           ohlc_data=json.dumps(ohlc_data, cls=JsonEncoder),
                           volume_data=json.dumps(volume_data, cls=JsonEncoder)
                           )


app.run(debug=False)
