import datetime as dt
from red_rat.app import euronext, mongo
from red_rat.app.helpers import Helpers
from red_rat.models.position import Position
from red_rat.models.asset_type import AssetType
from pandas import DataFrame, Series


class Portfolio:
    def __init__(self, portfolio_date: dt.datetime = None):
        self._portfolio_date = portfolio_date
        self._euronext = euronext
        self._mongo = mongo
        self._helpers = Helpers()
        self._load_portfolio_positions()
        self._get_euronext_data()
        self._compute()

    def _load_portfolio_positions(self):
        """
        method to load and store the portfolio positions
        :return:
        """
        self._stocks_positions = self._get_portfolio_positions_as_of(at_date=self._portfolio_date)

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
                if self._portfolio_date is None:
                    price = float(euronext_data['currInstrSess']['lastPx'])
                else:
                    price = self._helpers.get_price_from_mongo(isin, self._portfolio_date)
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

    def _get_cash_balance_as_of(self, at_date: dt.datetime = None):
        """
        method to get the cash balance from transactions
        :param at_date: datetime
        :return: float
        """

        if at_date is None:
            at_date = dt.datetime.today()

        transactions = self._mongo.find_documents(database_name='transactions',
                                                  collection_name='transactions',
                                                  projection={'_id': 0, 'net_cashflow': 1},
                                                  **{'transaction_date': {'$lte': at_date}})
        transactions = [list(transaction.values())[0] for transaction in transactions]
        cash_balance = Series(transactions).sum()
        return Position(**{'asset_type': 'CASH', 'quantity': cash_balance})

    def _get_equity_positions_as_of(self, at_date: dt.datetime = None):
        if at_date is None:
            at_date = dt.datetime.today()

        transactions_quantities = self._mongo.find_documents(database_name='transactions',
                                                             collection_name='transactions',
                                                             projection={'_id': 0, 'isin': 1, 'quantity': 1, 'mic': 1},
                                                             **{'transaction_date': {'$lte': at_date},
                                                                'isin': {'$ne': None}})
        transactions_quantities = [transactions for transactions in transactions_quantities]
        if transactions_quantities:
            df = DataFrame(transactions_quantities).groupby(['isin', 'mic']).sum()
            positions = df[df['quantity'] != 0.0]
            positions['asset_type'] = 'EQUITY'
            positions.reset_index(inplace=True)
            result = [Position(**pos) for pos in positions.to_dict('records')]
        else:
            result = []

        return result

    def _get_portfolio_positions_as_of(self, at_date: dt.datetime = None):
        return self._get_equity_positions_as_of(at_date) + [self._get_cash_balance_as_of(at_date)]

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

    def save_portfolio_nav(self, shares, cashflows=0.0):
        if self._portfolio_date is None:
            today = dt.date.today()
            nav_date = dt.datetime(today.year, today.month, today.day)
        else:
            nav_date = self._portfolio_date

        assets = self._portfolio_market_value
        data = {"date": nav_date,
                "assets": assets,
                "cashflows": cashflows,
                "shares": shares}

        mongo.insert_documents('net_asset_values', 'net_asset_values', [data])
        return True

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

    def _compute(self):
        """
        method to launch to get all the portfolio data
        :return:
        """

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
        return self._compute()

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
        return round(self._portfolio_market_value, 5)

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
