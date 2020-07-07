from red_rat.app.portfolio import Portfolio


class PortfolioRiskManager(Portfolio):
    def __init__(self, risk_free_rate: float, is_volatility_from_nav: bool = True, portfolio_path: str = None):
        super().__init__(portfolio_path)

        self._is_volatility_from_nav = is_volatility_from_nav

        self._portfolio_volatility = None
        self._portfolio_sharpe_ratios = None

        self._compute_portfolio_volatility()
        self._compute_portfolio_sharpe_ratios(risk_free_rate)

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

    def _compute_portfolio_value_at_risk(self):
        return

    @property
    def portfolio_volatility(self):
        return self._portfolio_volatility

    @property
    def portfolio_sharpe_ratios(self):
        return self._portfolio_sharpe_ratios
