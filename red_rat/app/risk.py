from red_rat.app.portfolio import Portfolio


class PortfolioRiskManager(Portfolio):
    def __init__(self, portfolio_path=None):
        super().__init__(portfolio_path)

    def portfolio_volatility(self, start, period):
        return

    def portfolio_sharpe_ratio(self, risk_free_rate):
        return

    def portfolio_value_at_risk(self):
        return
