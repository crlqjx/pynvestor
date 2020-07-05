import json
from pathlib import Path
from red_rat.app.market_data_provider import EuronextClient


class Portfolio:
    def __init__(self, portfolio_path=None):
        if portfolio_path is None:
            portfolio_path = Path(__file__).parent.parent.joinpath('portfolio.json')
        self._portfolio_path = portfolio_path
        self._positions = None
        self._prices = None
        self._quantities = None
        self._market_values = None
        self._cash = None
        self._portfolio_market_value = None
        self._weights = None
        self._euronext = EuronextClient()
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

    def _get_prices(self):
        prices = {}
        for position in self._positions:
            if position['type'] != 'Cash':
                prices[position['isin']] = \
                    float(self._euronext.get_instrument_details(
                        position['isin'], position['mic'])['instr']['currInstrSess']['lastPx'])
        self._prices = prices
        assert self._prices is not None, 'Could not retrieve prices'
        return

    def _get_portfolio(self):
        self._load_portfolio_positions()
        self._get_prices()

        market_values = {}
        self._portfolio_market_value = self._cash
        for isin, quantity in self._quantities.items():
            price = self._prices[isin]
            market_values[isin] = price * quantity
            self._portfolio_market_value += market_values[isin]

        self._market_values = market_values
        return

    def _get_weights(self):
        weights = {}
        for isin, market_value in self._market_values.items():
            weights[isin] = market_value / self._portfolio_market_value

        self._weights = weights
        return

    @property
    def quantities(self):
        return self._quantities

    @property
    def prices(self):
        self._get_prices()
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
    def to_df(self):
        # TODO
        return
