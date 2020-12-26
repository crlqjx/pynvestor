import pandas as pd
import datetime as dt
from pynvestor.source.portfolio import Portfolio
from pynvestor.source import euronext


class PerformanceAttribution:
    def __init__(self, isin_benchmark, mic_benchmark, breakdown, method):
        assert breakdown in ['sector', 'subsector'], 'Groups must be in ["sector", subsector"]'
        self.isin_benchmark = isin_benchmark
        self.mic_benchmark = mic_benchmark
        self.breakdown = breakdown
        self.method = method
        self._benchmark_details = euronext.get_instrument_details(isin_benchmark, mic_benchmark)
        self._previous_trading_date = dt.datetime.strptime(
            self._benchmark_details['instr']['prevInstrSess']['dateTime'].split('-')[0], "%Y%m%d")
        self._df_benchmark = self._get_benchmark_composition()
        self._df_benchmark_groups = self._get_benchmark_groups()
        self._df_portfolio_groups = self._get_portfolio_groups()

    def _get_benchmark_composition(self):
        benchmark_compo = euronext.get_index_composition(self.isin_benchmark, self.mic_benchmark)
        mics_components = [euronext.get_exch_code_from_trading_location(trading_location.upper())
                           for trading_location in benchmark_compo['Trading Location']]

        details_components = euronext.get_instruments_details(zip(benchmark_compo['ISIN'], mics_components))

        benchmark_data = []

        for detail in details_components:
            row_data = {}
            isin = list(detail.values())[0]['cdStand']
            market_cap = float(detail[isin]['currInstrSess']['marketCapitalisation'])
            daily_return = float(detail[isin]['currInstrSess']['lastPx']) / \
                           float(detail[isin]['prevInstrSess']['closPx']) - 1
            sector = None
            subsector = None
            weight_in_bench = None
            for elem in detail[isin]['instrRel']:
                if elem['instrLst'].get('lstType') == 'SEC' and elem['instrLst'].get('lstLvl') == '1':
                    sector = elem['instrLst']['lstLbl']
                if elem['instrLst'].get('lstType') == 'SEC' and elem['instrLst'].get('lstLvl') == '2':
                    subsector = elem['instrLst']['lstLbl']
                if elem['instrLst'].get('lstType') == 'NDX':
                    for transco in elem['instrLst']['transco']:
                        if transco['code'] == self.isin_benchmark:
                            weight_in_bench = float(elem['stockWeight']) / 100
                            break
            row_data['isin'] = isin
            row_data['market_cap'] = market_cap
            row_data['sector'] = sector
            row_data['subsector'] = subsector
            row_data['weight'] = weight_in_bench
            row_data['daily_return'] = daily_return

            benchmark_data.append(row_data)

        df_benchmark = pd.DataFrame(benchmark_data)
        df_benchmark['contribution_b'] = df_benchmark['weight'] * df_benchmark['daily_return']
        self._df_benchmark = df_benchmark
        return df_benchmark

    def _get_benchmark_groups(self):
        return self._df_benchmark.groupby(self.breakdown).sum()[['weight', 'contribution_b']]

    def _get_portfolio_groups(self):
        ptf_0 = Portfolio(self._previous_trading_date)
        ptf_1 = Portfolio()
        data = {}
        sector = None
        subsector = None
        for isin, weight in ptf_0.stocks_weights.items():
            details = euronext.get_instrument_details(isin)
            stock_return = ptf_1.stocks_perf_since_last_close[isin]
            for elem in details['instr']['instrRel']:
                if elem['instrLst'].get('lstType') == 'SEC' and elem['instrLst'].get('lstLvl') == '1':
                    sector = elem['instrLst']['lstLbl']
                if elem['instrLst'].get('lstType') == 'SEC' and elem['instrLst'].get('lstLvl') == '2':
                    subsector = elem['instrLst']['lstLbl']

            data[isin] = [weight, stock_return, sector, subsector]
        data['CASH'] = [ptf_0.cash_weight, 0.0, 'Cash', 'Cash']
        df_portfolio = pd.DataFrame.from_dict(data, orient='index')
        df_portfolio.columns = ['weight', 'stock_return', 'sector', 'subsector']
        df_portfolio.reset_index(inplace=True)
        df_portfolio.rename({'index': 'isin'}, inplace=True)
        df_portfolio['contribution_p'] = df_portfolio['weight'] * df_portfolio['stock_return']

        return df_portfolio.groupby(self.breakdown).sum()[['weight', 'contribution_p']]

    @staticmethod
    def _compute_allocation(df, method):
        if method == 'BHB':
            df['allocation'] = (df['weight_p'] - df['weight_b']) * df['return_b']
        elif method == 'BF':
            df['allocation'] = (df['weight_p'] - df['weight_b']) * (df['return_b'])
        else:
            raise ValueError(f'method {method} not valid')
        return True

    @staticmethod
    def _compute_selection(df):
        df['selection'] = df['weight_b'] * (df['return_p'] - df['return_b'])
        return True

    @staticmethod
    def _compute_interaction(df):
        df['interaction'] = (df['weight_p'] - df['weight_b']) * (df['return_p'] - df['return_b'])
        return True

    def compute_performance_attribution(self):
        df_attribution = pd.concat([self._df_benchmark_groups.rename(columns={'weight': 'weight_b'}),
                                    self._df_portfolio_groups.rename(columns={'weight': 'weight_p'})],
                                   axis=1)
        df_attribution.fillna(0.0, inplace=True)
        df_attribution['return_p'] = df_attribution['contribution_p'] / df_attribution['weight_p']
        df_attribution['return_b'] = df_attribution['contribution_b'] / df_attribution['weight_b']
        df_attribution.fillna(0.0, inplace=True)
        self._compute_allocation(df_attribution, method=self.method)
        self._compute_selection(df_attribution)
        self._compute_interaction(df_attribution)
        return df_attribution
