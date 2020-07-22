import requests
import json
import os
import re
import datetime as dt

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import date
from red_rat import logger

current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(current_directory, 'config.json'), 'r') as config_file:
    config = json.load(config_file)


class MarketDataProvider:
    def __init__(self):
        self._session = requests.Session()
        retry = Retry(total=5)
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)


class EuronextClient(MarketDataProvider):
    def __init__(self):
        super().__init__()
        self._base_url = "https://live.euronext.com"

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

    def get_instrument_details(self, isin, mic):
        url = f"https://gateway.euronext.com/api/instrumentDetail?code={isin}&codification=ISIN&exchCode={mic}&" \
              f"sessionQuality=RT&view=FULL" \
              f"&authKey={config['euronextapikey']}"
        resp = self._session.get(url, data={'theme_name': 'euronext_live'})
        resp.raise_for_status()
        return resp.json()

    def get_quotes(self, isin, mic, period):
        assert period in ['max', 'intraday'], f'period {period} is not available'

        url = f"{self._base_url}/intraday_chart/getChartData/{isin}-{mic}/{period}"
        resp = self._session.get(url)
        result = []
        for quote in resp.json():
            quote['time'] = dt.datetime.strptime(quote['time'], "%Y-%m-%d %H:%M")
            quote.update({'isin': isin, 'mic': mic})
            result.append(quote)
        if not result:
            logger.log.warning(f'No quotes for {isin}-{mic}')
        return result

    def get_historical_data(self, isin, market, start_date, end_date):
        # TODO
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


class ReutersClient(MarketDataProvider):
    def __init__(self):
        super().__init__()
        self._url = rf"https://www.reuters.com/companies/api/"

    def get_financial_data(self, ric):
        resp = self._session.get(f'{self._url}getFetchCompanyFinancials/{ric}')
        resp.raise_for_status()
        return resp.json()

    def get_company_profile(self, ric):
        resp = self._session.get(f'{self._url}getFetchCompanyProfile/{ric}')
        resp.raise_for_status()
        return resp.json()
