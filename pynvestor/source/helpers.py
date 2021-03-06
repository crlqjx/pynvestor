import datetime as dt
import numpy as np
import pandas as pd
import itertools
import json
from pathlib import Path
from pynvestor import logger
from pynvestor.source import mongo


class Helpers:
    def __init__(self):
        self._mongo = mongo
        self._init()

    def _init(self):
        app_path = Path(__file__).parents[1]
        with open(rf"{app_path}\static\rics.json", 'r') as f:
            self._isins_to_rics = json.load(f)
            self._rics_to_isins = {value: key for key, value in self._isins_to_rics.items()}

    def get_prices_from_mongo(self, isin: str,
                              start_date: dt.datetime = dt.datetime(2000, 1, 1),
                              end_date: dt.datetime = dt.datetime.today(),
                              sort: list = None,
                              window: int = None):
        fields_required = {'_id': 0, 'time': 1, 'price': 1}
        query_filter = {'isin': isin, 'time': {'$gte': start_date, '$lt': end_date}}
        query_result = self._mongo.find_documents(database_name='quotes', collection_name='equities',
                                                  projection=fields_required, sort=sort, **query_filter)
        if window is not None:
            quotes = itertools.islice(query_result, window)
        else:
            quotes = query_result
        try:
            quotes_series = pd.DataFrame(quotes).set_index('time')['price']
        except KeyError as key_error:
            raise KeyError(f'could not find quotes for {isin} between {start_date} and {end_date}- {key_error}')
        quotes_series.index = quotes_series.index.normalize()
        return quotes_series

    def get_price_from_mongo(self, isin, price_date):
        try:
            price = self.get_prices_from_mongo(isin, price_date, price_date + dt.timedelta(days=1))
            assert len(price) == 1, f'more than one last price founded for {isin} on {price_date}'
            result = price[0]
        except KeyError:
            logger.log.warning(f'Could not find price in mongo for {isin} on {price_date}')
            result = None
        return result

    def get_returns(self, isin: str,
                    start_date: dt.datetime = dt.datetime(2000, 1, 1),
                    end_date: dt.datetime = dt.datetime.today(),
                    sort: list = None,
                    window: int = None):
        prices = self.get_prices_from_mongo(isin=isin,
                                            start_date=start_date,
                                            end_date=end_date,
                                            sort=sort,
                                            window=window + 1)
        prices.sort_index(ascending=True, inplace=True)
        result = prices.pct_change()[1:]
        return result

    @staticmethod
    def get_last_price_in_mongo(isin):
        try:
            result = mongo.find_documents('quotes',
                                          'equities',
                                          sort=[('time', -1)],
                                          projection={'_id': 0},
                                          limit=1,
                                          **{'isin': isin})[0]
            price_date = result.get('time')
            result = result.get('price')
            logger.log.info(f'price for {isin} on date {price_date.year}-{price_date.month}-{price_date.day} : '
                            f'{result}')
        except IndexError:
            logger.log.warning(f'Could not find any price in mongo for {isin}')
            result = None
        return result

    @staticmethod
    def compute_sharpe_ratio(mean_annualized_return, portfolio_vol, risk_free_rate):
        result = ((mean_annualized_return - risk_free_rate) / portfolio_vol)
        return result

    @staticmethod
    def compute_portfolio_variance(weights, returns):
        cov_matrix = np.cov(returns) * 252
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        return portfolio_variance, cov_matrix

    def transco_isin_ric(self, **isin_or_ric):
        isin = isin_or_ric.get('isin')
        ric = isin_or_ric.get('ric')

        if (isin is None and ric is None) or (isin is not None and ric is not None):
            raise ValueError('Enter either isin or ric')

        if isin is not None and ric is None:
            ric = self._isins_to_rics.get(isin)

        if ric is not None and isin is None:
            isin = self._rics_to_isins.get(ric)

        return isin, ric

    @staticmethod
    def compute_ytd_returns(time_series: pd.Series):
        """
        Compute year-to-date from a pandas time series
        :param time_series: pandas time series
        :return: pandas time series
        """

        ytd_returns = []

        group_by_object = time_series.groupby(pd.Grouper(freq='A'))
        for group_name, indexes in group_by_object.indices.items():
            start_index = indexes[0] - 1 if indexes[0] > 0 else indexes[0]
            for idx in indexes:
                ytd_return = time_series[idx] / time_series[start_index] - 1.0
                ytd_returns.append(ytd_return)

        result = pd.Series(index=time_series.index, data=ytd_returns)
        assert len(result) == len(time_series)

        return result
