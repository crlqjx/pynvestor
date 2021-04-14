import pandas as pd
import datetime as dt

from typing import Dict

from pynvestor.source import euronext, mongo
from pynvestor.source.data_providers import ReutersClient
from pynvestor.source.helpers import Helpers
from pynvestor import logger

reuters = ReutersClient()
helpers = Helpers()


class Screener:
    def __init__(self, screen_filters: Dict, period: str, as_of_date: dt.date = None):
        """
        Class to screen stocks from fundamental data stored in the database
        :param screen_filters: dictionary with metric name as key and 2 element list representing the upper
        and lower limits
        :param period: interim or annual
        :param as_of_date: date of the metrics
        """
        self._period = period
        self._date = as_of_date
        self._df_screener = pd.DataFrame()
        available_screen_filters = ('eps', 'per', 'roe', 'gearing', 'operating_margin')
        for screen_filter in list(screen_filters.keys()):
            assert screen_filter in available_screen_filters, f'{screen_filter} must be in {available_screen_filters}'
        self.screen_filters = screen_filters

    @logger
    def _get_data(self, statement: str, report_elem: str, period: str):
        """
        get financial data from mongo of all stocks
        :param statement: "income", "balance_sheet", "cash_flow"
        :param report_elem: name of the report element in mongo
        :param period: annual or interim
        :return: dataframe
        """
        report_date = dt.datetime.today() if self._date is None else self._date
        pipeline = [{"$match": {"report_elem": report_elem, "period": period, "date": {"$lte": report_date}}},
                    {"$sort": {"ric": 1, "date": -1}},
                    {"$group": {"_id": {"ric": "$ric", "report_elem": "$report_elem"},
                                "ric": {"$first": "$ric"},
                                "date": {"$first": "$date"},
                                report_elem.lower().replace(' ', '_'): {"$first": "$value"}}},
                    {"$project": {"_id": 0}}]
        results = mongo.aggregate_documents('financials', statement, pipeline)
        df = pd.DataFrame(results)
        return df

    def _get_isin_and_mic(self):
        if 'isin' not in self._df_screener.columns or 'ric' not in self._df_screener.columns:
            rics = list(self._df_screener.groupby('ric').groups.keys())
            isins = {ric: helpers.transco_isin_ric(ric=ric)[0] for ric in rics}
            df_isin = pd.DataFrame.from_dict(isins, orient='index').reset_index()
            df_isin.columns = ['ric', 'isin']
            df_isin['mic'] = df_isin['isin'].apply(lambda x: euronext.get_mic_from_isin(x))
            self._df_screener = self._df_screener.merge(df_isin, how='left', on='ric')
        return True

    def _get_shares_details(self):
        if 'shares_outstanding' not in self._df_screener.columns:
            isins_mics = self._df_screener[['isin', 'mic']].values.tolist()
            instr_details = euronext.get_instruments_details(isins_mics)
            shares_outstanding = {}
            names = {}
            subsectors = {}
            for instrument_details in instr_details:
                for isin, details in instrument_details.items():
                    if details is not None:
                        shares_outstanding[isin] = int(details.get('nbShare'))
                        names[isin] = details.get('longNm')
                        if details.get('instrRel') is not None:
                            subsectors[isin] = details.get('instrRel')[3].get('instrLst').get('lstLbl').strip()
                        else:
                            subsectors[isin] = None

            df_shares_details = pd.DataFrame([shares_outstanding, names, subsectors]).T.reset_index()
            df_shares_details.columns = ['isin', 'shares_outstanding', 'names', 'subsectors']
            self._df_screener = self._df_screener.merge(df_shares_details, how='left', on='isin')
        return True

    def _get_prices(self):
        if 'price' not in self._df_screener.columns:
            if self._date is None:
                self._df_screener['price'] = self._df_screener['isin'].apply(
                    lambda x: helpers.get_last_price_in_mongo(x))
            else:
                self._df_screener['price'] = self._df_screener['isin'].apply(
                    lambda x: helpers.get_price_from_mongo(x, self._date))

    @logger
    def _compute_eps(self):
        if 'net_income' not in self._df_screener.columns:
            # Get net incomes
            self._df_screener = self._get_data('income', 'Net Income', self._period)
        if 'isin' not in self._df_screener.columns:
            # Get transco isin from rics
            self._get_isin_and_mic()

        if 'shares_outstanding' not in self._df_screener.columns:
            # Get shares outstanding
            self._get_shares_details()

        if 'price' not in self._df_screener.columns:
            # Get last prices
            self._get_prices()

        # Compute EPS
        self._df_screener['eps'] = (self._df_screener['net_income'] * 1000000) / self._df_screener['shares_outstanding']

        return True

    @logger
    def _compute_per(self):
        if 'eps' not in self._df_screener.columns:
            self._compute_eps()

        # Compute PER
        self._df_screener['eps'].replace(0.0, None, inplace=True)  # To avoir zero division error
        self._df_screener['per'] = self._df_screener['price'] / self._df_screener['eps']
        return True

    @logger
    def _compute_roe(self):
        if 'total_equity' not in self._df_screener.columns:
            df_total_equity = self._get_data('balance_sheet', 'Total Equity', self._period)
            self._df_screener = self._df_screener.merge(df_total_equity[['ric', 'total_equity']],
                                                        how='left', left_on='ric', right_on='ric')
        if 'net_income' not in self._df_screener.columns:
            df_net_income = self._get_data('income', 'Net Income', self._period)
            self._df_screener = self._df_screener.merge(df_net_income['ric', 'net_income'],
                                                        how='left', left_on='ric', right_on='ric')

        # Compute ROE
        self._df_screener['roe'] = self._df_screener['net_income'] / self._df_screener['total_equity']
        return True

    @logger
    def _compute_gearing(self):
        if 'total_debt' not in self._df_screener.columns:
            df_total_debt = self._get_data('balance_sheet', 'Total Debt', self._period)
            self._df_screener = self._df_screener.merge(df_total_debt[['ric', 'total_debt']],
                                                        how='left', left_on='ric', right_on='ric')
        if 'total_equity' not in self._df_screener.columns:
            df_total_equity = self._get_data('balance_sheet', 'Total Equity', self._period)
            self._df_screener = self._df_screener.merge(df_total_equity[['ric', 'total_equity']],
                                                        how='left', left_on='ric', right_on='ric')

        # Compute gearing
        self._df_screener['gearing'] = self._df_screener['total_debt'] / self._df_screener['total_equity']
        return True

    @logger
    def _compute_operating_margin(self):
        if 'operating_income' not in self._df_screener.columns:
            df_operating_income = self._get_data('income', 'Operating Income', self._period)
            self._df_screener = self._df_screener.merge(df_operating_income[['ric', 'operating_income']],
                                                        how='left', left_on='ric', right_on='ric')

        if 'revenue' not in self._df_screener.columns:
            df_revenue = self._get_data('income', 'Revenue', self._period)
            self._df_screener = self._df_screener.merge(df_revenue[['ric', 'revenue']],
                                                        how='left', left_on='ric', right_on='ric')

        # Compute operating margin
        self._df_screener['operating_margin'] = self._df_screener['operating_income'] / self._df_screener['revenue']
        return True

    @logger
    def run(self):
        results_df = {}
        for screen_name, (lower_limit, upper_limit) in list(self.screen_filters.items()):
            # Get required data
            get_metrics = self.__getattribute__(f'_compute_{screen_name}')
            get_metrics()

            # Apply filter
            conditions = (self._df_screener[screen_name] > lower_limit) & (self._df_screener[screen_name] < upper_limit)
            results_df[screen_name] = self._df_screener[conditions]

        frames = list(results_df.values())
        result = pd.concat(frames, axis=1, join='inner')
        result = result.loc[:, ~result.columns.duplicated()]
        return result
