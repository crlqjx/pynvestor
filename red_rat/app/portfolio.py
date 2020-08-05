import json
import datetime as dt
from pathlib import Path
from red_rat import euronext, helpers, mongo
from red_rat.models.position import Position
from red_rat.models.asset_type import AssetType
from pandas import DataFrame, Series


class Portfolio:
    def __init__(self, portfolio_path=None):
        """
        Class to load portfolio positions and market data
        :param portfolio_path: path to the portfolio file in json
        """
        if portfolio_path is None:
            portfolio_path = Path(__file__).parent.parent.joinpath('portfolio.json')
        self._portfolio_path = portfolio_path
        self._euronext = euronext
        self._mongo = mongo
        self._helpers = helpers
        self._get_portfolio()

    def _load_portfolio_positions(self):
        """
        method to load and store the portfolio positions
        :return:
        """
        with open(self._portfolio_path, 'r') as ptf:
            position_json = json.load(ptf)
        self._stocks_positions = [Position(**pos) for pos in position_json]

        quantities = {}
        for position in self._stocks_positions:
            if position.asset_type is AssetType.CASH:
                self._cash = position.quantity
            else:
                quantities[position.isin] = int(position.quantity)

        self._stocks_quantities = quantities
        assert self._stocks_quantities is not None, 'Could not retrieve quantities'
        return True

    def _get_euronext_data(self):
        """
        method to get market data from euronext
        :return:
        """
        instrument_details = {}
        prices = {}
        names = {}
        perf_since_open = {}
        perf_since_last_close = {}
        for position in self._stocks_positions:
            if position.asset_type is not AssetType.CASH:
                isin = position.isin
                mic = position.mic
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
        return True

    def _get_cash_balance_as_of(self, at_date: dt.datetime):
        """
        method to get the cash balance from transactions
        :param at_date: datetime
        :return: float
        """

        transactions = self._mongo.find_documents(database_name='transactions',
                                                  collection_name='transactions',
                                                  projection={'_id': 0, 'net_cashflow': 1},
                                                  **{'transaction_date': {'$lte': at_date}})
        transactions = [list(transaction.values())[0] for transaction in transactions]
        cash_balance = Series(transactions).sum()
        return cash_balance

    def _get_positions_as_of(self, at_date: dt.datetime):

        transactions_quantities = self._mongo.find_documents(database_name='transactions',
                                                             collection_name='transactions',
                                                             projection={'_id': 0, 'isin': 1, 'quantity': 1, 'mic': 1},
                                                             **{'transaction_date': {'$lte': at_date},
                                                                'isin': {'$ne': None}})
        transactions_quantities = [transactions for transactions in transactions_quantities]
        df = DataFrame(transactions_quantities).groupby('isin').sum()
        positions = df[df['quantity'] != 0.0]
        positions['asset_type'] = 'equity'
        positions.reset_index(inplace=True)

        return [Position(**pos) for pos in positions.to_dict('records')]

    def _get_weights(self):
        """
        method to get and store assets weights
        :return:
        """
        weights = {}
        for isin, market_value in self._stocks_market_values.items():
            weights[isin] = market_value / self._portfolio_market_value
        self._stocks_weights = weights

        self._cash_weight = self._cash / self._portfolio_market_value
        return True

    def _compute_portfolio_navs(self):
        """
        method to compute the portfolio net asset values
        :return:
        """
        asset_values = self._mongo.find_documents(database_name='net_asset_values', collection_name='net_asset_values',
                                                  projection={'_id': 0})

        df_assets = DataFrame(asset_values).set_index('date')
        df_assets['navs'] = df_assets['assets'] / df_assets['shares']
        self._portfolio_navs = df_assets['navs']
        return True

    def _compute_portfolio_returns(self):
        """
        method to compute the portfolio weekly returns from net asset values
        :return:
        """
        self._nav_weekly_returns = self._portfolio_navs.pct_change()
        return True

    def compute_portfolio_nav(self, nav_date: dt.datetime):
        stocks_valuation = {}
        for isin, quantity in self._stocks_quantities.items():
            price = self._helpers.get_price_from_mongo(isin, nav_date)
            valuation = price * quantity
            stocks_valuation[isin] = valuation

        nav = Series(list(stocks_valuation.values())).sum() + self._cash

        return nav

    @staticmethod
    def save_portfolio_nav(self, nav, nav_date, cashflows=0.0, shares=None):
        pass

    def to_df(self):
        """
        method to get a dataframe representation of the portfolio data
        :return: dataframe
        """
        data = [self._stocks_names, self._stocks_quantities, self._stocks_weights, self._stocks_prices,
                self._stocks_perf_since_open, self._stocks_perf_since_last_close, self._stocks_market_values]
        columns = ['name', 'quantity', 'weight', 'last price', 'perf since open', 'perf since last close',
                   'market value']
        df = DataFrame(data).T
        df.columns = columns

        return df

    def _get_portfolio(self):
        """
        method to launch to get all the portfolio data
        :return:
        """
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
        return True

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
    def stocks_positions(self):
        return self._stocks_positions

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
    def nav_weekly_returns(self):
        return self._nav_weekly_returns
