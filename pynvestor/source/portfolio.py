import datetime as dt
from typing import List

from pandas import DataFrame, Series

from pynvestor.models.asset_type import AssetType
from pynvestor.models.position import Position
from pynvestor.source import euronext, mongo
from pynvestor.source.helpers import Helpers


class Portfolio:
    """
    Object representing a portfolio at a certain date
    """
    def __init__(self, portfolio_date: dt.datetime = None):
        """
        Initialize portfolio at a certain date
        :param portfolio_date: datetime
        """
        self._portfolio_date = portfolio_date
        self._helpers = Helpers()
        self._load_portfolio_positions()
        self._get_euronext_data()
        self._compute()

    def _load_portfolio_positions(self) -> bool:
        """
        method to load and store the portfolio positions
        :return: True
        """
        self._positions = self._get_portfolio_positions_as_of(at_date=self._portfolio_date)

        quantities = {}
        for position in self._positions:
            if position.asset_type is AssetType.CASH:
                self._cash = position.quantity
            else:
                quantities[position.isin] = int(position.quantity)

        self._stocks_quantities = quantities
        assert self._stocks_quantities is not None, 'Could not retrieve quantities'
        return True

    def _get_euronext_data(self) -> bool:
        """
        method that will get and store market data from euronext
        :return: True
        """
        instrument_details = {}
        prices = {}
        names = {}
        perf_since_open = {}
        perf_since_last_close = {}
        prev_session_prices = {}
        for position in self._positions:
            if position.asset_type is not AssetType.CASH:
                isin = position.isin
                mic = position.mic
                euronext_data = euronext.get_instrument_details(isin, mic)['instr']

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
                prev_sess_close = float(euronext_data['prevInstrSess']['lastPx'])
                prev_session_prices[isin] = prev_sess_close
                perf_since_open[isin] = price / price_open - 1

        self._stocks_details = instrument_details
        self._stocks_prices = prices
        self._previous_prices = prev_session_prices
        self._stocks_names = names
        self._stocks_perf_since_open = perf_since_open
        self._stocks_perf_since_last_close = perf_since_last_close
        return True

    @staticmethod
    def get_cash_balance_as_of(at_date: dt.datetime = None) -> Position:
        """
        method to get the cash balance from transactions at a certain date
        :param at_date: datetime
        :return: Position object
        """

        if at_date is None:
            at_date = dt.datetime.today()

        transactions = mongo.find_documents(database_name='transactions',
                                            collection_name='transactions',
                                            projection={'_id': 0, 'net_cashflow': 1},
                                            **{'transaction_date': {'$lte': at_date}})
        transactions = [list(transaction.values())[0] for transaction in transactions]
        cash_balance = Series(transactions).sum()
        return Position(**{'asset_type': 'CASH', 'quantity': cash_balance})

    @staticmethod
    def get_equity_positions_as_of(at_date: dt.datetime = None) -> List[Position]:
        """
        method to get equity positions at a certain date
        :param at_date: datetime
        :return: list of equity position objects
        """
        if at_date is None:
            at_date = dt.datetime.today()

        transactions_quantities = mongo.find_documents(database_name='transactions',
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

    def _get_portfolio_positions_as_of(self, at_date: dt.datetime = None) -> List[Position]:
        """
        Private method to get equity and cash positions at a certain date
        :param at_date: datetime
        :return: list of Position objects
        """
        return self.get_equity_positions_as_of(at_date) + [self.get_cash_balance_as_of(at_date)]

    def _get_weights(self) -> bool:
        """
        method to get and store assets weights
        :return: True
        """
        weights = {}
        for isin, market_value in self._stocks_market_values.items():
            weights[isin] = market_value / self._portfolio_market_value
        self._stocks_weights = weights

        self._cash_weight = self._cash / self._portfolio_market_value
        return True

    def _compute_positions_pnl(self) -> bool:
        """
        Compute and store PnL from equity positions
        :return: True
        """
        positions_pnl = {}
        for position in self._positions:
            if position.asset_type is AssetType.EQUITY:
                isin = position.isin
                transactions = list(mongo.find_documents('transactions',
                                                         'transactions',
                                                         projection={"_id": 0},
                                                         sort=[('transaction_date', 1)],
                                                         **{'isin': isin,
                                                            'transaction_type':
                                                                {"$in": ['BUY', 'SELL', 'STOCK SPLIT']}}))
                cumulative_positions = []
                cum_position = 0
                for trade in transactions:
                    cum_position += trade['quantity']
                    cumulative_positions.append(cum_position)
                buy_transactions = []
                for i in range(len(transactions) - 1, -1, -1):
                    if cumulative_positions[i] == 0:
                        break
                    else:
                        if transactions[i]['transaction_type'] in ['BUY', 'STOCK SPLIT']:
                            buy_transactions.append(transactions[i])

                sum_quantity = sum(trade['quantity'] for trade in buy_transactions)
                weighted_average_price = sum(trade['quantity'] * trade['price']
                                             for trade in buy_transactions if trade['price'] is not None) / sum_quantity
                positions_pnl[isin] = self._stocks_prices[isin] / weighted_average_price - 1

        self._positions_pnl = positions_pnl
        return True

    def _compute_portfolio_navs(self) -> bool:
        """
        method to compute the portfolio net asset values
        :return: bool
        """
        asset_values = mongo.find_documents(database_name='net_asset_values', collection_name='net_asset_values',
                                            projection={'_id': 0})

        df_assets = DataFrame(asset_values).set_index('date')
        df_assets['navs'] = df_assets['assets'] / df_assets['shares']
        self._portfolio_navs = df_assets['navs']
        return True

    def _compute_portfolio_performance(self) -> bool:
        """
        Compute and store portfolio performances
        :return: True
        """
        perf = 0.0
        for isin, mkt_value in self._stocks_market_values.items():
            previous_price = self._previous_prices[isin]
            weight = self.stocks_quantities[isin] * previous_price / self._previous_portfolio_market_value
            perf += self._stocks_perf_since_last_close[isin] * weight

        self._portfolio_perf = perf
        return True

    def _compute_portfolio_returns(self):
        """
        method to compute the portfolio weekly returns from net asset values
        :return:
        """
        self._nav_weekly_returns = self._portfolio_navs.pct_change()
        return True

    @staticmethod
    def add_transaction(transaction: List[dict]) -> bool:
        """
        insert transactions in mongo
        :param transaction: list of transactions in a json format
        :return: True
        """
        mongo.insert_documents(database_name='transactions', collection_name='transactions', documents=transaction)
        return True

    def save_portfolio_nav(self, nav_date, shares=None, cashflows=0.0) -> bool:
        """
        method to insert new net asset values in the mongo
        :param nav_date: date the net asset value
        :param shares: new total amount of shares, if no cashflows, leave it to None
        :param cashflows: amount of cashflows
        :return: True
        """
        if shares is None:
            shares = mongo.find_document('net_asset_values', 'net_asset_values', [("date", -1)])['shares']
        if nav_date is None:
            nav_date = self._portfolio_date

        assets = self._portfolio_market_value
        data = {"date": nav_date,
                "assets": assets,
                "cashflows": cashflows,
                "shares": shares}

        mongo.insert_documents('net_asset_values', 'net_asset_values', [data])
        return True

    def to_df(self) -> DataFrame:
        """
        method to get a dataframe representation of the portfolio data
        :return: dataframe
        """
        data = [self._stocks_names, self._stocks_quantities, self._stocks_weights, self._stocks_prices,
                self._stocks_perf_since_open, self._stocks_perf_since_last_close, self._stocks_market_values,
                self._positions_pnl]
        columns = ['name', 'quantity', 'weight', 'last_price', 'perf_since open', 'perf_since_last_close',
                   'market_value', 'pnl']
        df = DataFrame(data).T
        df.columns = columns

        return df

    def _compute(self) -> bool:
        """
        method to launch to get all the portfolio data
        :return: True
        """
        market_values = {}
        previous_market_values = {}
        self._portfolio_market_value = self._cash
        self._previous_portfolio_market_value = self._cash
        for isin, quantity in self._stocks_quantities.items():
            price = self._stocks_prices[isin]
            previous_price = self._previous_prices[isin]
            market_values[isin] = price * quantity
            previous_market_values[isin] = previous_price * quantity
            self._portfolio_market_value += market_values[isin]
            self._previous_portfolio_market_value += previous_market_values[isin]
        self._stocks_market_values = market_values

        self._get_weights()
        self._compute_positions_pnl()
        self._compute_portfolio_navs()
        self._compute_portfolio_returns()
        self._compute_portfolio_performance()
        return True

    @property
    def portfolio_date(self):
        return self._portfolio_date

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
    def positions(self):
        return self._positions

    @property
    def positions_pnl(self):
        return self._positions_pnl

    @property
    def stocks_perf_since_open(self):
        return self._stocks_perf_since_open

    @property
    def portfolio_perf(self):
        return self._portfolio_perf

    @property
    def stocks_perf_since_last_close(self):
        return self._stocks_perf_since_last_close

    @property
    def portfolio_navs(self):
        return self._portfolio_navs

    @property
    def nav_weekly_returns(self):
        return self._nav_weekly_returns
