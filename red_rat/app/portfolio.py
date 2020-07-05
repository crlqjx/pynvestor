import json
from pathlib import Path
from red_rat.app.market_data_provider import EuronextClient
from pandas import DataFrame


class Portfolio:
    def __init__(self, portfolio_path=None):
        if portfolio_path is None:
            portfolio_path = Path(__file__).parent.parent.joinpath('portfolio.json')
        self._portfolio_path = portfolio_path
        self._euronext = EuronextClient()
        self._positions = None
        self._prices = None
        self._quantities = None
        self._market_values = None
        self._cash = None
        self._portfolio_market_value = None
        self._weights = None
        self._instrument_details = None
        self._names = None
        self._perf_since_open = None
        self._perf_since_last_close = None
        self._get_portfolio()

    def _load_portfolio_positions(self):
        with open(self._portfolio_path, 'r') as ptf:
            position = json.load(ptf)
        self._positions = position

        quantities = {}
        for position in self._positions:
            if position['type'].lower() == 'cash':
                self._cash = position['quantity']
            else:
                quantities[position['isin']] = int(position['quantity'])

        self._quantities = quantities
        assert self._quantities is not None, 'Could not retrieve quantities'
        return

    def _get_euronext_data(self):
        instrument_details = {}
        prices = {}
        names = {}
        perf_since_open = {}
        perf_since_last_close = {}
        for position in self._positions:
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

        self._instrument_details = instrument_details
        self._prices = prices
        self._names = names
        self._perf_since_open = perf_since_open
        self._perf_since_last_close = perf_since_last_close
        return

    def _get_portfolio(self):
        self._load_portfolio_positions()
        self._get_euronext_data()

        market_values = {}
        self._portfolio_market_value = self._cash
        for isin, quantity in self._quantities.items():
            price = self._prices[isin]
            market_values[isin] = price * quantity
            self._portfolio_market_value += market_values[isin]

        self._market_values = market_values

        self._get_weights()
        return

    def _get_weights(self):
        weights = {}
        for isin, market_value in self._market_values.items():
            weights[isin] = market_value / self._portfolio_market_value

        self._weights = weights
        return

    def to_df(self):
        data = [self._names, self._quantities, self._weights, self._prices, self._perf_since_open,
                self._perf_since_last_close, self._market_values]
        columns = ['name', 'quantity', 'weight', 'last price', 'perf since open', 'perf since last close',
                   'market value']
        df = DataFrame(data).T
        df.columns = columns

        return df

    @property
    def quantities(self):
        return self._quantities

    @property
    def prices(self):
        return self._prices

    @property
    def cash(self):
        return self._cash

    @property
    def get_portfolio(self):
        return self._get_portfolio()

    @property
    def weights(self):
        return self._weights

    @property
    def market_values(self):
        return self._market_values

    @property
    def portfolio_market_value(self):
        return self._portfolio_market_value

    @property
    def names(self):
        return self._names

    @property
    def perf_since_open(self):
        return self._perf_since_open

    @property
    def perf_since_last_close(self):
        return self._perf_since_last_close