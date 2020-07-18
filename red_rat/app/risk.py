import pandas as pd
import numpy as np

from red_rat.app.portfolio import Portfolio
from red_rat.app.helpers import Helpers

helpers = Helpers()


class PortfolioRiskManager(Portfolio):
    """
    class to manage portfolio risks
    """

    def __init__(self, risk_free_rate: float, portfolio_path: str = None):
        super().__init__(portfolio_path)

        self._compute_nav_volatility()
        self._compute_portfolio_volatility()
        self._compute_portfolio_sharpe_ratio(risk_free_rate)
        self._compute_portfolio_value_at_risk()

    def _compute_portfolio_volatility(self, lookback_days: int = 500):
        """
        compute portfolio volatility from the assets covariance matrix
        :param lookback_days: number of days to look back from today
        :return:
        """
        weights = np.array(list(self.stocks_weights.values()))
        returns = []
        for isin, _ in self.stocks_weights.items():
            returns.append(helpers.get_returns(isin=isin,
                                               sort=[("time", -1)],
                                               window=lookback_days + 1).values)

        returns = np.stack(returns)

        portfolio_variance, cov_matrix = helpers.compute_portfolio_variance(weights, returns)
        self._covariance_matrix = cov_matrix
        self._assets_std = {list(self.stocks_weights.keys())[i]: cov_matrix[i][i] for i in range(len(weights))}
        self._portfolio_volatility = np.sqrt(portfolio_variance)
        return

    def _compute_nav_volatility(self):
        """
        Compute portfolio volatility of NAV since inception
        :return: float value
        """
        self._nav_volatility = self.nav_weekly_returns.std()

    def _compute_portfolio_sharpe_ratio(self, risk_free_rate: float, lookback_days: int = 500):
        """
        compute portfolio sharpe ratios compared to a fixed risk-free rate
        :param risk_free_rate: float
        :return: series
        """

        weights = np.array(list(self.stocks_weights.values()))
        mean_returns = []
        for isin, _ in self._stocks_weights.items():
            mean_returns.append(helpers.get_returns(isin=isin,
                                                    sort=[("time", -1)],
                                                    window=lookback_days + 1).values.mean())
        mean_returns = np.array(mean_returns)
        portfolio_return = np.sum(weights * mean_returns) * 252

        sharpe_ratio = helpers.compute_sharpe_ratio(portfolio_return, self._portfolio_volatility, risk_free_rate)
        self._portfolio_sharpe_ratio = sharpe_ratio

        return

    def _compute_portfolio_value_at_risk(self,
                                         method: str = "historical",
                                         lookback_days: int = 500,
                                         percentile: int = 5):
        """
        compute portfolio Value At Risk
        :param method: method of computation for the value at risk
        :param lookback_days: window range to look from today
        :param percentile: confidence interval
        :return:
        """

        if method == "historical":

            # Get simulated historical portfolio value
            df_assets_market_values = pd.DataFrame()
            for isin, quantity in self.stocks_quantities.items():
                prices_series = helpers.get_prices_from_mongo(isin=isin,
                                                              sort=[("time", -1)],
                                                              window=lookback_days)
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
    def assets_std(self):
        return self._assets_std

    @property
    def nav_volatility(self):
        return self._nav_volatility

    @property
    def portfolio_volatility(self):
        return self._portfolio_volatility

    @property
    def portfolio_sharpe_ratio(self):
        return self._portfolio_sharpe_ratio

    @property
    def portfolio_value_at_risk(self):
        return self._portfolio_value_at_risk
