import datetime as dt
import numpy as np
import pandas as pd
import itertools
from red_rat.app.mongo_connector import MongoConnector


class Helpers:
    def __init__(self):
        self._mongo = MongoConnector()

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
        quotes_series = pd.DataFrame(quotes).set_index('time')['price']
        quotes_series.index = quotes_series.index.normalize()
        return quotes_series

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
    def compute_sharpe_ratio(mean_annualized_return, portfolio_vol, risk_free_rate):
        result = ((mean_annualized_return - risk_free_rate) / portfolio_vol)
        return result

    @staticmethod
    def compute_portfolio_variance(weights, returns):
        cov_matrix = np.cov(returns) * 252
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        return portfolio_variance, cov_matrix
