import requests
import json
from os import environ
from datetime import date

# documentation : https://www.worldtradingdata.com/documentation


class WorldTradingDataClient:
    def __init__(self):
        self._api_token = environ.get('WorldTradingDataAPIKey')
        self._url = r'https://api.worldtradingdata.com/api/v1'

        assert self._api_token is not None, 'missing api_token'

    def query(self, end_point: str, method: str, params=None):
        query = getattr(requests, method)(f'{self._url}/{end_point}', params)
        return query

    def get_historical_quotes(self, symbol: str, date_from: date = None, date_to: date = None, sort: bool = None,
                              output: str = None, formatted: bool = None):
        """
        Get end of day history of a given stock, index or mutual fund
        :param symbol: stock, index or mutual fund symbol (same as reuters)
        :param date_from: starting date (optional)
        :param date_to: ending date (optional)
        :param formatted: alter JSON data format. Does not affect CSV (optional, default is false)
        :param output: change output to CSV (optional, default is json)
        :param sort: sort by date; accept 'newest', 'oldest', 'asc', 'desc' (optional, default is 'newest')
        :return: json dict (or csv)
        """

        end_point = f'history?symbol={symbol}&sort={sort}&api_token={self._api_token}'
        if date_from is not None:
            end_point = f'{end_point}&date_from={date_from}'
        if date_to is not None:
            end_point = f'{end_point}&date_to={date_to}'
        if sort is not None:
            end_point = f'{end_point}&sort={sort}'
        if output is not None:
            end_point = f'{end_point}&output={output}'
        if formatted is not None:
            end_point = f'{end_point}&formatted={formatted}'

        resp = self.query(end_point, 'get')

        return json.loads(resp.content)

    def stock_search(self, search_term: str = None, search_by: str = None, stock_exchange: str = None,
                     currency: str = None, limit: int = 5, sort_by: str = None, sort_order: str = None,
                     output: str = None):
        """
        search and filter the stock and index database
        :param search_term: optional - Search term you wish to find stocks for (example: SNAP)
        :param search_by: optional - Search by only symbol or name, or both
        :param stock_exchange: optional - Filter by a comma seperated list of stock exchange
        :param currency: optional - Filter by a comma seperated list of currencies
        :param limit: optional - Limit the number of results returned (max 5)
        :param sort_by: optional - Sort by a specific column
        :param sort_order: optional - Sort order of the sort_by column
        :param output: optional - Change output to CSV
        :return: json or csv
        """

        end_point = f'stock_search?api_token={self._api_token}'
        if search_term is not None:
            end_point = f'{end_point}&search_term={search_term}'
        if search_by is not None:
            end_point = f'{end_point}&search_by={search_by}'
        if stock_exchange is not None:
            end_point = f'{end_point}&stock_exchange={stock_exchange}'
        if currency is not None:
            end_point = f'{end_point}&currency={currency}'
        if limit is not None:
            end_point = f'{end_point}&limit={limit}'
        if sort_by is not None:
            end_point = f'{end_point}&sort_by={sort_by}'
        if sort_order is not None:
            end_point = f'{end_point}&sort_order={sort_order}'
        if output is not None:
            end_point = f'{end_point}&output={output}'

        resp = self.query(end_point, 'get')

        return json.loads(resp.content)
