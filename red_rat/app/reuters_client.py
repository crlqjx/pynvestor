import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from red_rat.app.mongo_connector import MongoConnector

mongo_connector = MongoConnector()


class ReutersClient:
    def __init__(self):
        self._session = requests.Session()
        retry = Retry(total=5)
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)
        self._url = rf"https://www.reuters.com/companies/api/"

    def get_financial_data(self, ric):
        resp = self._session.get(f'{self._url}getFetchCompanyFinancials/{ric}')
        resp.raise_for_status()
        return resp.json()

    def get_company_profile(self, ric):
        resp = self._session.get(f'{self._url}getFetchCompanyProfile/{ric}')
        resp.raise_for_status()
        return resp.json()
