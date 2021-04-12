import matplotlib.pyplot as plt
import numpy as np

from pynvestor.source.optimizer import Optimizer


# References: Portfolio Theory With Matrix Algebra - Eric Zivot

optimizer = Optimizer(0.01)
equity_weight = 1 - optimizer.cash_weight
expected_returns = optimizer._mean_returns

# Global minimum variance portfolio
gmv_weigths, gmv_annualized_variance, gmv_expected_return = optimizer.minimum_variance_optimization()
gmv_annualized_volatility = np.sqrt(gmv_annualized_variance)


# Current portfolio optimization
weights_opti, var_opti, ptf_return_opti = optimizer.portfolio_optimization()
annualized_volatility_opti = np.sqrt(var_opti)


# Efficient portfolio with max return
max_return_stock_index = list(expected_returns).index(max(expected_returns))
max_return_stock = max(expected_returns) * equity_weight

efficient_weights, efficient_var, efficient_return = \
    optimizer.minimum_variance_optimization(target_return=max_return_stock)
efficient_vol = np.sqrt(efficient_var)

# Efficient Frontier
alphas = np.arange(-1.0, 1.0, 0.01)
z_weights = [a * gmv_weigths + (1 - a) * efficient_weights for a in alphas]

efficient_frontier_returns = [np.dot(z, np.array(expected_returns)) for z in z_weights]
efficient_frontier_vol = [np.sqrt(np.dot(z, np.dot(optimizer._covariance_matrix, z))) for z in z_weights]

# Plot data
efficient_portfolios_from_stocks = [optimizer.minimum_variance_optimization(target_return=r * equity_weight) for r in list(expected_returns)]


# plt.plot(efficient_frontier_vol, efficient_frontier_returns)
plt.scatter([gmv_annualized_volatility] + [np.sqrt(e[1]) for e in efficient_portfolios_from_stocks],
            [gmv_expected_return] + [e[2] for e in efficient_portfolios_from_stocks])


returns_array = np.linspace(gmv_expected_return, efficient_return, 100)
efficient_portfolios = [optimizer.minimum_variance_optimization(target_return=r) for r in returns_array]
plt.plot([np.sqrt(ptf[1]) for ptf in efficient_portfolios], [ptf[2] for ptf in efficient_portfolios])
plt.show()

# TODO: tangency portfolio with risk-free asset

pass