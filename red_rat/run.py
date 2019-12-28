import datetime as dt
import hashlib

from red_rat.mongo_connector import MongoConnector
from red_rat.market_data_provider import WorldTradingData
from red_rat import logger

mongo_connector = MongoConnector()
market_data_provider = WorldTradingData()

#TODO:
# 1. insert fundamental data into mongo
# 2. make a database of stocks with transcodification


@logger
def update_quotes():
    french_stocks = [stock for stock in market_data_provider.all_stocks if stock[3:] == ".PA"]
    for symbol in french_stocks:
        logger.log.info(f'updating {symbol}')
        quotes_to_insert = market_data_provider.get_historical_quotes(symbol)
        try:
            insert_quotes(quotes_to_insert)
        except KeyError:
            if quotes_to_insert['Message'].lower() == 'Error! The requested stock could not be found.'.lower():
                logger.log.warning(f"{symbol} not found")
        except Exception as e:
            raise e
    return


def insert_quotes(quotes):
    data_to_insert = []
    for close_date, daily_quote in quotes['history'].items():
        _id = hashlib.sha1(str(quotes['name'] + close_date).encode()).hexdigest()
        single_quote_to_insert = {
            '_id': _id,
            'name': quotes['name'],
            'date': dt.datetime.fromisoformat(close_date),
            'open': float(daily_quote['open']) if daily_quote.get('open') is not None else None,
            'close': float(daily_quote['close']) if daily_quote.get('close') is not None else None,
            'high': float(daily_quote['high']) if daily_quote.get('high') is not None else None,
            'low': float(daily_quote['low']) if daily_quote.get('low') is not None else None,
            'volume': float(daily_quote['volume']) if daily_quote.get('volume') is not None else None,
            'source': market_data_provider.url
        }
        # single_quote_to_insert.update(daily_quote)
        data_to_insert.append(single_quote_to_insert)
    mongo_connector.insert_documents(database_name='historical_quotes',
                                     collection_name='stocks',
                                     documents=data_to_insert)


if __name__ == '__main__':
    update_quotes()
