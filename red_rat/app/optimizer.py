import numpy as np
from scipy import optimize
from red_rat.app.risk import PortfolioRiskManager, helpers


class Optimizer(PortfolioRiskManager):
    def __init__(self, risk_free_rate: float, portfolio_path: str = None):
        super().__init__(risk_free_rate, portfolio_path)

    def portfolio_min_var(self, lookback_days: int = 500):
        weights = np.array(list(self.stocks_weights.values()))
        initial_weights = np.array(len(weights) * [(1 - self.cash_weight) / len(weights)])
        returns = []
        for isin, _ in self.stocks_weights.items():
            returns.append(helpers.get_returns(isin=isin,
                                               sort=[("time", -1)],
                                               window=lookback_days).values)

        returns = np.stack(returns)

        fun = lambda w, r: helpers.compute_portfolio_variance(w, r)[0]
        constraint = ({'type': 'eq', 'fun': lambda w: np.sum(w) + self.cash_weight - 1})
        bounds = tuple((0.0, 1.0) for _ in range(len(weights)))

        result = optimize.minimize(fun, initial_weights, returns, method='SLSQP', bounds=bounds,
                                   constraints=constraint)

        assert result.status == 0, result.message

        return result.x
