import json
from pathlib import Path
from red_rat.app.market_data_provider import EuronextClient
from red_rat.app.mongo_connector import MongoConnector
from pandas import DataFrame


class Portfolio:
    def __init__(self, portfolio_path=None):
        if portfolio_path is None:
            portfolio_path = Path(__file__).parent.parent.joinpath('portfolio.json')
        self._portfolio_path = portfolio_path
        self._euronext = EuronextClient()
        self._mongo = MongoConnector()
        self._stocks_positions = None
        self._stocks_prices = None
        self._stocks_quantities = None
        self._stocks_market_values = None
        self._cash = None
        self._portfolio_market_value = None
        self._stocks_weights = None
        self._cash_weight = None
        self._stocks_details = None
        self._stocks_names = None
        self._portfolio_navs = None
        self._stocks_perf_since_open = None
        self._stocks_perf_since_last_close = None
        self._portfolio_weekly_returns = None
        self._get_portfolio()

    def _load_portfolio_positions(self):
        with open(self._portfolio_path, 'r') as ptf:
            position = json.load(ptf)
        self._stocks_positions = position

        quantities = {}
        for position in self._stocks_positions:
            if position['type'].lower() == 'cash':
                self._cash = position['quantity']
            else:
                quantities[position['isin']] = int(position['quantity'])

        self._stocks_quantities = quantities
        assert self._stocks_quantities is not None, 'Could not retrieve quantities'
        return

    def _get_euronext_data(self):
        instrument_details = {}
        prices = {}
        names = {}
        perf_since_open = {}
        perf_since_last_close = {}
        for position in self._stocks_positions:
            if position['type'] != 'Cash':
                isin = position['isin']
                mic = position['mic']
                euronext_data = self._euronext.get_instrument_details(isin, mic)['instr']

                # Get instrument details
                instrument_details[isin] = euronext_data
                # Get prices
                price = float(euronext_data['currInstrSess']['lastPx'])
                prices[isin] = price
                # Get names
                names[isin] = euronext_data['longNm']
                # Get perfs
                for perf in euronext_data['perf']:
                    if perf['perType'] == 'D':
                        perf_since_last_close[isin] = float(perf['var'])
                        break
                price_open = float(euronext_data['currInstrSess']['openPx'])
                perf_since_open[isin] = price / price_open - 1

        self._stocks_details = instrument_details
        self._stocks_prices = prices
        self._stocks_names = names
        self._stocks_perf_since_open = perf_since_open
        self._stocks_perf_since_last_close = perf_since_last_close
        return

    def _get_portfolio(self):
        self._load_portfolio_positions()
        self._get_euronext_data()

        market_values = {}
        self._portfolio_market_value = self._cash
        for isin, quantity in self._stocks_quantities.items():
            price = self._stocks_prices[isin]
            market_values[isin] = price * quantity
            self._portfolio_market_value += market_values[isin]

        self._stocks_market_values = market_values

        self._get_weights()
        self._compute_portfolio_navs()
        self._compute_portfolio_returns()
        return

    def _get_weights(self):
        weights = {}
        for isin, market_value in self._stocks_market_values.items():
            weights[isin] = market_value / self._portfolio_market_value
        self._stocks_weights = weights

        self._cash_weight = self._cash / self._portfolio_market_value
        return

    def _compute_portfolio_navs(self):
        asset_values = self._mongo.find_documents(database_name='net_asset_values', collection_name='net_asset_values',
                                                  projection={'_id': 0})

        df_assets = DataFrame(asset_values).set_index('date')
        df_assets['navs'] = df_assets['assets'] / df_assets['shares']
        self._portfolio_navs = df_assets['navs']
        return

    def _compute_portfolio_returns(self):
        self._portfolio_weekly_returns = self._portfolio_navs.pct_change()
        return

    def to_df(self):
        data = [self._stocks_names, self._stocks_quantities, self._stocks_weights, self._stocks_prices, self._stocks_perf_since_open,
                self._stocks_perf_since_last_close, self._stocks_market_values]
        columns = ['name', 'quantity', 'weight', 'last price', 'perf since open', 'perf since last close',
                   'market value']
        df = DataFrame(data).T
        df.columns = columns

        return df

    @property
    def stocks_quantities(self):
        return self._stocks_quantities

    @property
    def stocks_prices(self):
        return self._stocks_prices

    @property
    def cash(self):
        return self._cash

    @property
    def get_portfolio(self):
        return self._get_portfolio()

    @property
    def stocks_weights(self):
        return self._stocks_weights

    @property
    def cash_weight(self):
        return self._cash_weight

    @property
    def stocks_market_values(self):
        return self._stocks_market_values

    @property
    def portfolio_market_value(self):
        return self._portfolio_market_value

    @property
    def stocks_names(self):
        return self._stocks_names

    @property
    def stocks_perf_since_open(self):
        return self._stocks_perf_since_open

    @property
    def stocks_perf_since_last_close(self):
        return self._stocks_perf_since_last_close

    @property
    def portfolio_navs(self):
        return self._portfolio_navs

    @property
    def portfolio_weekly_returns(self):
        return self._portfolio_weekly_returns
