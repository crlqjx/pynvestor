import json
import os
from pathlib import Path
from red_rat.app.market_data_provider import EuronextClient


class Portfolio:
    def __init__(self, portfolio_path=None):
        if portfolio_path is None:
            portfolio_path = Path(os.getcwd()).joinpath(r'red_rat/portfolio.json')
        self._portfolio_path = portfolio_path
        self._positions = None
        self._prices = None
        self._euronext = EuronextClient()
        self._load_portfolio_positions()

    def _load_portfolio_positions(self):
        with open(self._portfolio_path, 'r') as ptf:
            position = json.load(ptf)
        self._positions = position
        return

    def _get_prices(self):
        prices = {}
        for position in self._positions:
            prices[position['isin']] = \
                self._euronext.get_instrument_details(
                    position['isin'], position['mic'])['instr']['currInstrSess']['lastPx']
        self._prices = prices
        return

    def get_total_value(self):
        #TODO
        pass

    @property
    def positions(self):
        return self._positions

    @property
    def prices(self):
        self._get_prices()
        return self._prices
