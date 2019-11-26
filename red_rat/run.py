import datetime as dt

from red_rat.mongo import MongoConnector
from red_rat.market_data_provider import MarketDataProvider


def update_quotes():
    mongo_connector = MongoConnector()
    market_data_provider = MarketDataProvider()
    tickers = ['PVL.PA', 'FR.PA']
    for ticker in tickers:
        mongo_quotes = mongo_connector.find_document(database_name='historical_quotes',
                                                     collection_name='stocks',
                                                     name=ticker)
        assert mongo_quotes is not None, f'no quotes for {ticker}'

        document_id = mongo_quotes['_id']
        dates = list(mongo_quotes['history'].keys())
        dates.sort(reverse=True)
        last_date = dt.datetime.strptime(dates[0], "%Y-%m-%d")
        date_from = (last_date + dt.timedelta(1)).date()

        quotes_to_update = market_data_provider.get_historical_quotes(ticker, date_from)
        mongo_connector.update_document(database_name='historical_quotes',
                                        collection_name='stocks',
                                        document_id=document_id,
                                        data_to_update={"history": quotes_to_update},
                                        name=ticker)

        pass
    return


if __name__ == '__main__':
    update_quotes()