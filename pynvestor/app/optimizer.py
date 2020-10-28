import numpy as np
import pandas as pd
from scipy import optimize
from pynvestor.app.risk import PortfolioRiskManager
from pynvestor.app.helpers import Helpers


class Optimizer(PortfolioRiskManager):
    def __init__(self, risk_free_rate: float, portfolio_path: str = None):
        super().__init__(risk_free_rate, portfolio_path)

    def min_var(self, method: str = 'algo', mc_simulations: int = 100000):
        returns = self._histo_returns
        mean_returns = self._mean_returns

        # Algorithmic method using minimize function of scipy
        if method.lower() == 'algo':
            weights = np.array(list(self.stocks_weights.values()))
            initial_weights = np.array(len(weights) * [(1 - self.cash_weight) / len(weights)])

            def fun(w, r): return Helpers.compute_portfolio_variance(w, r)[0]

            constraint = ({'type': 'eq', 'fun': lambda w: np.sum(w) + self.cash_weight - 1})
            bounds = tuple((0.0, 1.0) for _ in range(len(weights)))

            result = optimize.minimize(fun, initial_weights, returns, method='SLSQP', bounds=bounds,
                                       constraints=constraint)

            assert result.status == 0, result.message
            optimal_weights = result.x
            min_var = result.fun

        # Monte Carlo method
        elif method.lower() == 'mc':
            simulated_results = np.zeros((2 + len(returns), mc_simulations))
            for i in range(mc_simulations):
                weights = np.random.random(len(returns))
                weights /= weights.sum()
                weights *= (1 - self.cash_weight)

                ptf_variance = Helpers.compute_portfolio_variance(weights, returns)[0]
                simulated_results[0, i] = ptf_variance
                simulated_results[1, i] = np.dot(weights, mean_returns)
                for j in range(len(weights)):
                    simulated_results[2 + j, i] = weights[j]

            df_result = pd.DataFrame(simulated_results.T)
            df_result.columns = ['ptf_variance', 'ptf_return'] + list(self.stocks_weights.keys())
            optimal_weights = df_result.iloc[df_result['ptf_variance'].idxmin()][2:].values
            min_var = df_result.iloc[df_result['ptf_variance'].idxmin()][0]

        else:
            raise AttributeError('Method should be "algo" or "mc"')

        ptf_mean_return = np.dot(optimal_weights, mean_returns)

        return optimal_weights, min_var, ptf_mean_return
