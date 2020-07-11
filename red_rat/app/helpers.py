import datetime as dt
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
            quotes = itertools.islice(query_result, window + 1)
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
                                            window=window)
        prices.sort_index(ascending=True, inplace=True)
        result = prices.pct_change()[1:]
        return result

