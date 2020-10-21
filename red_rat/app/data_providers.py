import requests
import aiohttp
import asyncio
import json
import os
import re
import datetime as dt

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import date
from red_rat import logger
from typing import List, Tuple

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

    def __repr__(self):
        return self.__class__.__name__


class EuronextClient(MarketDataProvider):
    def __init__(self):
        super().__init__()
        self._base_url = "https://live.euronext.com"
        self.isin_to_mic = {stock['isin']: stock['mic'] for stock in self._all_stocks()}

    @staticmethod
    def _all_stocks():
        file_path = os.path.join(current_directory, "static", "Euronext_Equities_2020-10-08.json")
        with open(file_path, 'r') as f:
            data = json.load(f)
            stocks_data = data['aaData']

        all_stocks = [{'isin': stock[1],
                       'symbol': stock[2],
                       'market': stock[3],
                       'mic': re.search(f'/{stock[1]}-' + '([A-Z]{4})/', stock[0]).group(1)} for stock in stocks_data]

        return all_stocks

    @staticmethod
    def _all_indices():
        file_path = os.path.join(current_directory, "static", "Euronext_Indices_2020-09-08.json")
        with open(file_path, 'r') as f:
            data = json.load(f)
            indices_data = data['aaData']

        all_indices = [{'isin': indice[1],
                        'symbol': indice[2],
                        'mic': re.search(f'/{indice[1]}-' + '([A-Z]{4})/', indice[0]).group(1)}
                       for indice in indices_data]

        return all_indices

    @logger
    def search_in_euronext(self, query):
        url = f"https://live.euronext.com/fr/instrumentSearch/searchJSON?q={query}"
        resp = self._session.get(url)
        resp.raise_for_status()
        result = resp.json()
        result.pop(-1)
        return result

    def get_mic_from_isin(self, isin):
        return self.isin_to_mic.get(isin)

    @logger
    def get_instrument_details(self, isin, mic=None):
        if mic is None:
            try:
                mic = self.get_mic_from_isin(isin)
            except AssertionError as e:
                raise AssertionError(f'{e}: specify mic')
        url = f"https://gateway.euronext.com/api/instrumentDetail?code={isin}&codification=ISIN&exchCode={mic}&" \
              f"sessionQuality=RT&view=FULL" \
              f"&authKey={config['euronextapikey']}"
        resp = self._session.get(url, data={'theme_name': 'euronext_live'})
        resp.raise_for_status()
        return resp.json()

    def get_instruments_details(self, isins_mics):
        async def fetch(isin, mic):
            if mic in ['ALXP', 'XMLI']:
                exch_code = 'XPAR'
            elif mic in ['VPXB', 'MLXB', 'ALXB']:
                exch_code = 'XBRU'
            elif mic in ['XESM', 'XMSM']:
                exch_code = 'XDUB'
            elif mic in ['ALXL']:
                exch_code = 'XLIS'
            else:
                exch_code = mic
            url = f"https://gateway.euronext.com/api/instrumentDetail?code={isin}&codification=" \
                  f"ISIN&exchCode={exch_code}&sessionQuality=RT&view=FULL&authKey={config['euronextapikey']}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, data={'theme_name': 'euronext_live'}) as response:
                        response_json = response.json()
                        instr_details = await response_json
                        return {isin: instr_details.get('instr')}
            except aiohttp.ContentTypeError as content_type_error:
                logger.log.warning(f'{isin} {exch_code} - {content_type_error}')
                return {isin: None}

        async def fetch_all(stocks_to_request):
            all_result = await asyncio.gather(*[fetch(isin, mic) for isin, mic in stocks_to_request])
            return all_result

        result = asyncio.run(fetch_all(isins_mics))
        return result

    def get_last_price(self, isin, mic):
        instr_details = self.get_instrument_details(isin, mic)
        return float(instr_details['instr']['currInstrSess']['lastPx'])

    @logger
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

    @logger
    def get_quotes_multiple_stocks(self, isin_mic_period: List[Tuple]) -> List[List[dict]]:
        """
        Get quotes of stocks asynchronously
        :param isin_mic_period: list of tuples with the following format isin, mic and period (max or intraday)
        [('FR123456789', 'XPAR', 'max'), ('FR987654321', 'XPAR', 'intraday')]
        :return:
        """
        async def fetch(isin, mic, period):
            url = f"{self._base_url}/intraday_chart/getChartData/{isin}-{mic}/{period}"
            try:
                assert period in ['max', 'intraday'], f'{isin}: period {period} is not available'
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response_json = response.json()
                        quotes = await response_json
                        for quote in quotes:
                            quote['time'] = dt.datetime.strptime(quote['time'], "%Y-%m-%d %H:%M")
                            quote.update({'isin': isin, 'mic': mic})
                        return quotes
            except aiohttp.ClientOSError as client_os_error:
                logger.log.warning(f'{client_os_error} - Retrying...')
            except AssertionError as assertion_error:
                logger.log.warning(assertion_error)

        async def fetch_all(stocks_to_request):
            final_result = []
            while stocks_to_request:
                response_jsons = await asyncio.gather(*[fetch(isin, mic, period)
                                                        for isin, mic, period in stocks_to_request])
                temp_result = []
                missing_response = []
                for idx, quote in enumerate(response_jsons):
                    if quote is not None:
                        temp_result.append(quote)
                    else:
                        missing_response.append(idx)
                final_result += temp_result
                stocks_to_request = [stocks_to_request[idx] for idx in missing_response]
                if missing_response:
                    logger.log.info(f'Retrying for {len(stocks_to_request)} stocks')
            return final_result

        all_quotes = asyncio.run(fetch_all(isin_mic_period))

        return all_quotes

    def update_stocks_list(self):
        today = date.today().isoformat()
        filename = os.path.join(current_directory, "static", f"Euronext_Equities_{today}.json")
        url = 'https://live.euronext.com/fr/pd/data/stocks?mics=ALXB%2CALXL%2CALXP%2CXPAR%2CXAMS%2CXBRU%2CXLIS%' \
              '2CXMLI%2CMLXB%2CENXB%2CENXL%2CTNLA%2CTNLB%2CXLDN%2CXESM%2CXMSM%2CXATL%2CVPXB&display_datapoints=' \
              'dp_stocks&display_filters=df_stocks'
        resp = self._session.post(url, data={'iDisplayLength': 3000})
        stock_list = resp.json()
        with open(filename, 'w') as f:
            json.dump(stock_list, f)

        return resp.json()

    def update_indices_list(self):
        today = date.today().isoformat()
        filename = os.path.join(current_directory, "static", f"Euronext_Indices_{today}.json")
        url = 'https://live.euronext.com/pd/data/index?mics=XAMS%2CXBRU%2CXLIS%2CXPAR%2CXLDN%2CXDUB&' \
              'display_datapoints=dp_index&display_filters=df_index'
        resp = self._session.post(url, data={'iDisplayLength': 500})
        indices_list = resp.json()
        with open(filename, 'w') as f:
            json.dump(indices_list, f)

        return resp.json()

    @property
    def all_stocks(self):
        return self._all_stocks()

    @property
    def all_indices(self):
        return self._all_indices()


class ReutersClient(MarketDataProvider):
    def __init__(self):
        super().__init__()
        self._url = rf"https://www.reuters.com/companies/api/"

    @logger
    def get_financial_data(self, ric):
        resp = self._session.get(f'{self._url}getFetchCompanyFinancials/{ric}')
        resp.raise_for_status()
        return resp.json()

    @logger
    def get_company_profile(self, ric):
        resp = self._session.get(f'{self._url}getFetchCompanyProfile/{ric}')
        resp.raise_for_status()
        return resp.json()

    @logger
    def get_companies_profile(self, rics):
        async def fetch(reuters_code):
            url = rf"https://www.reuters.com/companies/api/getFetchCompanyProfile/{reuters_code}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response_json = response.json(content_type=None)
                    response_status = response.status
                    return response_status, reuters_code, await response_json

        async def fetch_all(stocks_to_request):
            retry_counter = 0
            final_result = []
            while stocks_to_request:
                response_jsons = await asyncio.gather(*[fetch(stock) for stock in stocks_to_request])
                temp_result = []
                missing_response = []

                for idx, (status, ric, profile) in enumerate(response_jsons):
                    if status >= 404:
                        print(status, profile)
                        missing_response.append(idx)
                    else:
                        print(status)
                        temp_result.append(profile)

                final_result += temp_result
                if stocks_to_request == [stocks_to_request[idx] for idx in missing_response]:
                    retry_counter += 1
                if retry_counter >= 5:
                    logger.log.warning('Retried too many times for the same stocks, aborting')
                    break

                stocks_to_request = [stocks_to_request[idx] for idx in missing_response]

                if missing_response:
                    logger.log.info(f'Retrying for {len(stocks_to_request)} stocks: {stocks_to_request}')
                    await asyncio.sleep(5)

            return final_result

        company_profiles = asyncio.run(fetch_all(rics))

        return company_profiles
