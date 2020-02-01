import requests

from red_rat.app.mongo_connector import MongoConnector

mongo_connector = MongoConnector()


class ReutersClient:
    def __init__(self):
        self._url = rf"https://www.reuters.com/companies/api/"

    def get_financial_data(self, ric):
        resp = requests.get(f'{self._url}getFetchCompanyFinancials/{ric}')
        return resp.json()

    def get_company_profile(self, ric):
        resp = requests.get(f'{self._url}getFetchCompanyProfile/{ric}')
        return resp.json()
