import numpy as np
from scipy import optimize

from pynvestor.source.helpers import Helpers
from pynvestor.source.risk import PortfolioRiskManager


class Optimizer(PortfolioRiskManager):
    def __init__(self, risk_free_rate: float):
        super().__init__(risk_free_rate)

    def minimum_variance_optimization(self, target_return: float = 0.0):

        initial_weights = np.array(len(self.stocks_weights) * [(1 - self.cash_weight) / len(self.stocks_weights)])

        def func_to_minimize(w, r): return Helpers.compute_portfolio_variance(w, r)[0]

        constraints = (
            # stock weights + cash weight must equal 1
            {'type': 'eq', 'fun': lambda w: np.sum(w) + self.cash_weight - 1},
            # portfolio expected return must equals or greater than a target return
            {'type': 'ineq', 'fun': lambda w: np.dot(w, self._mean_returns) - target_return}
        )
        bounds = tuple((0.0, 1.0) for _ in range(len(self.stocks_weights)))

        result = optimize.minimize(func_to_minimize,
                                   initial_weights,
                                   args=(self._histo_returns,),
                                   method='SLSQP',
                                   bounds=bounds,
                                   constraints=constraints)

        assert result.status == 0, result.message
        optimal_weights = result.x
        min_var = result.fun

        ptf_mean_return = np.dot(optimal_weights, self._mean_returns)

        return optimal_weights, min_var, ptf_mean_return

    def portfolio_optimization(self):
        weights = np.array(list(self.stocks_weights.values()))
        portfolio_expected_return = np.dot(weights, self._mean_returns)
        return self.minimum_variance_optimization(target_return=float(portfolio_expected_return))
