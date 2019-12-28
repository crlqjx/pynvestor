import requests


class Fundamentals:
    def __init__(self, ric):
        self._ric = ric
        self._url = rf"https://www.reuters.com/companies/api/getFetchCompanyFinancials/{ric}"

    def get_financial_data(self):
        resp = requests.get(self._url)
        return resp.json()


fundamentals = Fundamentals('PLVP.PA').get_financial_data()
pass