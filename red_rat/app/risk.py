import pandas as pd

from red_rat.app.portfolio import Portfolio
from red_rat.app.helpers import Helpers


class PortfolioRiskManager(Portfolio):
    def __init__(self, risk_free_rate: float, is_volatility_from_nav: bool = True, portfolio_path: str = None):
        super().__init__(portfolio_path)

        self._is_volatility_from_nav = is_volatility_from_nav

        self._compute_portfolio_volatility()
        self._compute_portfolio_sharpe_ratios(risk_free_rate)
        self._compute_portfolio_value_at_risk()

    def _compute_portfolio_volatility(self):
        """
        Compute portfolio volatility since inception
        :return: float value
        """
        if self._is_volatility_from_nav:
            self._portfolio_volatility = self.portfolio_weekly_returns.std()
        else:
            # TODO: compute portfolio vol from stocks vol and corr
            pass
        return

    def _compute_portfolio_sharpe_ratios(self, risk_free_rate):
        """
        compute portfolio sharpe ratios compared to a fixed risk-free rate
        :param risk_free_rate: float
        :return: series
        """

        sharpe_ratios = (self.portfolio_weekly_returns - risk_free_rate) / self._portfolio_volatility
        self._portfolio_sharpe_ratios = sharpe_ratios

        return

    def _compute_portfolio_value_at_risk(self,
                                         method: str = "historical",
                                         lookback_days: int = 500,
                                         percentile: int = 5):
        helpers = Helpers()

        if method == "historical":

            # Get simulated historical portfolio value
            df_assets_market_values = pd.DataFrame()
            for isin, quantity in self.stocks_quantities.items():
                prices_series = helpers.get_prices_from_mongo(isin=isin,
                                                              sort=[("time", -1)],
                                                              window=lookback_days + 1)
                total_market_value = prices_series * quantity
                df_assets_market_values[isin] = total_market_value

            portfolio_market_values_series = df_assets_market_values.sum(axis=1)
            portfolio_market_values_series.sort_index(inplace=True)
            portfolio_changes_series = portfolio_market_values_series * portfolio_market_values_series.pct_change()
            portfolio_changes_series.dropna(inplace=True)

            sorted_results = portfolio_changes_series.values
            percentile_loc = int(round(percentile / 100 * len(sorted_results), 0))
            value_at_risk = sorted_results[percentile_loc]

        elif method == "normal":
            raise NotImplementedError

        else:
            raise NotImplementedError

        self._portfolio_value_at_risk = value_at_risk
        return

    @property
    def portfolio_volatility(self):
        return self._portfolio_volatility

    @property
    def portfolio_sharpe_ratios(self):
        return self._portfolio_sharpe_ratios

    @property
    def portfolio_value_at_risk(self):
        return self._portfolio_value_at_risk
