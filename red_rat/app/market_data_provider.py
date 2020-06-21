import requests
import json
import os
import re

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import date
from random import shuffle
from red_rat import logger

# documentation : https://www.worldtradingdata.com/documentation

current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WorldTradingData:
    def __init__(self):
        with open(os.path.join(current_directory, 'config.json'), 'r') as f:
            config = json.load(f)
        self._tokens_already_used = []
        self._api_tokens = config['worldtradingdataapikey']
        self._api_token = self.select_random_token()
        self._url = r'https://api.worldtradingdata.com/api/v1'

        file_path = os.path.join(current_directory, "static", "world_trading_data_list.json")
        with open(file_path, "r") as f:
            self._all_stocks = (stock for stock in json.load(f))

        assert self._api_tokens is not None, 'missing api_token'

    @property
    def url(self):
        return self._url

    @property
    def all_stocks(self):
        return self._all_stocks

    def select_random_token(self):
        """Select randomly an unused token from the tokens available"""

        assert len(set(self._tokens_already_used)) < len(self._api_tokens), "No more tokens available"

        tokens = self._api_tokens.copy()
        shuffle(tokens)
        if tokens[0] not in self._tokens_already_used:
            selected_token = tokens[0]
        else:
            selected_token = self.select_random_token()
        self._tokens_already_used.append(selected_token)

        logger.log.info(f"connecting with token : {selected_token}")
        return selected_token

    def query(self, end_point: str, method: str, params=None):
        req = getattr(requests, method)(f'{self._url}/{end_point}&api_token={self._api_token}', params)
        while "You have reached your request limit for the day".lower() not in req.text.lower():
            return req
        else:
            # Reset token and rerun query
            self._api_token = self.select_random_token()
            req = self.query(end_point=end_point, method=method, params=params)
            return req

    def get_historical_quotes(self, symbol: str, date_from: date = None, date_to: date = None, sort: bool = None,
                              output: str = None, formatted: bool = None):
        """
        Get end of day history of a given stock, index or mutual fund
        :param symbol: stock, index or mutual fund symbol (same as reuters)
        :param date_from: starting date yyyy-mm-dd (optional)
        :param date_to: ending date yyyy-mm-dd (optional)
        :param formatted: alter JSON data format. Does not affect CSV (optional, default is false)
        :param output: change output to CSV (optional, default is json)
        :param sort: sort by date; accept 'newest', 'oldest', 'asc', 'desc' (optional, default is 'newest')
        :return: json dict (or csv)
        """

        end_point = f'history?symbol={symbol}&sort={sort}'
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

        end_point = 'stock_search?'
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


class EuronextClient:
    def __init__(self):
        self._base_url = "https://live.euronext.com"
        self._session = requests.Session()
        retry = Retry(total=5)
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def _all_stocks(self):
        file_path = os.path.join(current_directory, "static", "Euronext_Equities_2020-06-17.json")
        with open(file_path, 'r') as f:
            data = json.load(f)
            stocks_data = data['aaData']

        all_stocks = [{'isin': stock[1],
                       'symbol': stock[2],
                       'market': stock[3],
                       'mic': re.search(f'/{stock[1]}-' + '([A-Z]{4})/', stock[0]).group(1)} for stock in stocks_data]

        return all_stocks

    def get_quotes(self, isin, mic, period):
        assert period in ['max', 'intraday'], f'period {period} is not available'

        url = f"{self._base_url}/intraday_chart/getChartData/{isin}-{mic}/{period}"
        resp = self._session.get(url)
        result = []
        for quote in resp.json():
            quote.update({'isin': isin, 'mic': mic, '_id': f'{isin}-{quote["time"]}'})
            result.append(quote)
        if not result:
            logger.log.warning(f'No quotes for {isin}-{mic}')
        return result

    def get_historical_data(self, isin, market, start_date, end_date):
        url = 'https://live.euronext.com/fr/ajax/getHistoricalPricePopup/FR0000045072-XPAR'

    def update_stocks_list(self):
        today = date.today().isoformat()
        filename = os.path.join(current_directory, "static", f"Euronext_Equities_{today}.json")
        url = 'https://live.euronext.com/fr/pd/data/stocks?mics=ALXB%2CALXL%2CALXP%2CXPAR%2CXAMS%2CXBRU%2CXLIS%2CXMLI%2CMLXB%2CENXB%2CENXL%2CTNLA%2CTNLB%2CXLDN%2CXESM%2CXMSM%2CXATL%2CVPXB&display_datapoints=dp_stocks&display_filters=df_stocks'
        resp = self._session.post(url, data={'iDisplayLength': 3000})
        stock_list = resp.json()
        with open(filename, 'w') as f:
            json.dump(stock_list, f)

        return resp.json()

    @property
    def all_stocks(self):
        return self._all_stocks()
