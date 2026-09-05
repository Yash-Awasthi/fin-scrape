"""
Portfolio Optimizer
Advanced portfolio optimization using modern portfolio theory and machine learning
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from scipy import stats, optimize
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf, MinCovDet
from sklearn.preprocessing import StandardScaler
import cvxpy as cp


class OptimizationObjective(Enum):
    """Portfolio optimization objectives"""
    MAXIMIZE_SHARPE = "maximize_sharpe"
    MINIMIZE_VOLATILITY = "minimize_volatility"
    MAXIMIZE_RETURN = "maximize_return"
    RISK_PARITY = "risk_parity"
    MAXIMUM_DIVERSIFICATION = "maximum_diversification"
    HIERARCHICAL_RISK_PARITY = "hierarchical_risk_parity"
    MINIMUM_CORRELATION = "minimum_correlation"


class ConstraintType(Enum):
    """Portfolio constraint types"""
    NO_SHORT = "no_short"
    BOUNDED_WEIGHTS = "bounded_weights"
    SECTOR_LIMITS = "sector_limits"
    FACTOR_LIMITS = "factor_limits"
    TURNOVER_LIMITS = "turnover_limits"
    BETA_LIMITS = "beta_limits"
    CONCENTRATION_LIMITS = "concentration_limits"


@dataclass
class OptimizationConstraint:
    """Portfolio optimization constraint"""
    constraint_type: ConstraintType
    parameters: Dict[str, float]
    description: str = ""


@dataclass
class OptimizationResult:
    """Portfolio optimization result"""
    portfolio_id: str
    objective: OptimizationObjective
    optimal_weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    tracking_error: Optional[float] = None
    maximum_drawdown: Optional[float] = None
    diversification_ratio: Optional[float] = None
    effective_number_of_assets: Optional[float] = None
    factor_exposures: Optional[Dict[str, float]] = None
    turnover: Optional[float] = None
    optimization_time: datetime = field(default_factory=datetime.now)
    constraints_satisfied: bool = True
    convergence_status: str = "success"


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    information_ratio: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None
    win_rate: float = 0.0
    profit_factor: float = 0.0


class PortfolioOptimizer:
    """Advanced portfolio optimization system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.risk_free_rate = 0.02

    def optimize_portfolio(self, returns_data: pd.DataFrame,
                          objective: OptimizationObjective = OptimizationObjective.MAXIMIZE_SHARPE,
                          constraints: List[OptimizationConstraint] = None,
                          benchmark_weights: Dict[str, float] = None,
                          risk_aversion: float = 1.0) -> Optional[OptimizationResult]:
        """Optimize portfolio weights based on specified objective"""
        try:
            # Prepare data
            assets = returns_data.columns.tolist()
            n_assets = len(assets)
            expected_returns = self._estimate_expected_returns(returns_data)
            covariance_matrix = self._estimate_covariance_matrix(returns_data)

            # Initialize optimization variables
            weights = cp.Variable(n_assets)

            # Set up optimization problem based on objective
            if objective == OptimizationObjective.MAXIMIZE_SHARPE:
                problem = self._maximize_sharpe_ratio(weights, expected_returns, covariance_matrix)
            elif objective == OptimizationObjective.MINIMIZE_VOLATILITY:
                problem = self._minimize_volatility(weights, expected_returns, covariance_matrix)
            elif objective == OptimizationObjective.MAXIMIZE_RETURN:
                problem = self._maximize_return(weights, expected_returns, constraints)
            elif objective == OptimizationObjective.RISK_PARITY:
                problem = self._risk_parity_optimization(weights, covariance_matrix)
            elif objective == OptimizationObjective.MAXIMUM_DIVERSIFICATION:
                problem = self._maximum_diversification_optimization(weights, expected_returns, covariance_matrix)
            else:
                raise ValueError(f"Unsupported optimization objective: {objective}")

            # Add constraints
            constraints_list = self._build_constraints(weights, constraints, assets, benchmark_weights)
            problem.constraints.extend(constraints_list)

            # Solve optimization
            problem.solve()

            # Extract results
            if problem.status == 'optimal':
                optimal_weights = weights.value
                portfolio_return = expected_returns @ optimal_weights
                portfolio_volatility = np.sqrt(optimal_weights.T @ covariance_matrix @ optimal_weights)
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0

                # Calculate additional metrics
                tracking_error = self._calculate_tracking_error(optimal_weights, benchmark_weights, covariance_matrix) if benchmark_weights else None
                max_drawdown = self._estimate_maximum_drawdown(optimal_weights, expected_returns, covariance_matrix)
                diversification_ratio = self._calculate_diversification_ratio(optimal_weights, covariance_matrix)
                effective_assets = self._calculate_effective_number_of_assets(optimal_weights)

                return OptimizationResult(
                    portfolio_id="optimized_portfolio",
                    objective=objective,
                    optimal_weights=dict(zip(assets, optimal_weights)),
                    expected_return=portfolio_return,
                    expected_volatility=portfolio_volatility,
                    sharpe_ratio=sharpe_ratio,
                    tracking_error=tracking_error,
                    maximum_drawdown=max_drawdown,
                    diversification_ratio=diversification_ratio,
                    effective_number_of_assets=effective_assets,
                    convergence_status=problem.status
                )
            else:
                self.logger.warning(f"Optimization failed with status: {problem.status}")
                return None

        except Exception as e:
            self.logger.error(f"Error optimizing portfolio: {str(e)}")
            return None

    def _estimate_expected_returns(self, returns_data: pd.DataFrame, method: str = "historical") -> np.ndarray:
        """Estimate expected returns using various methods"""
        if method == "historical":
            return returns_data.mean().values
        elif method == "shrinkage":
            # James-Stein shrinkage estimator
            historical_returns = returns_data.mean().values
            mean_return = np.mean(historical_returns)
            shrinkage_factor = 0.5
            return shrinkage_factor * mean_return + (1 - shrinkage_factor) * historical_returns
        elif method == "black_litterman":
            # Black-Litterman approach (simplified)
            historical_returns = returns_data.mean().values
            market_weights = np.ones(len(historical_returns)) / len(historical_returns)
            market_return = market_weights @ historical_returns
            confidence = 0.5
            return confidence * historical_returns + (1 - confidence) * market_return
        else:
            return returns_data.mean().values

    def _estimate_covariance_matrix(self, returns_data: pd.DataFrame, method: str = "ledoit_wolf") -> np.ndarray:
        """Estimate covariance matrix using various methods"""
        if method == "sample":
            return returns_data.cov().values
        elif method == "ledoit_wolf":
            lw = LedoitWolf()
            lw.fit(returns_data)
            return lw.covariance_
        elif method == "minimum_covariance_determinant":
            mcd = MinCovDet()
            mcd.fit(returns_data)
            return mcd.covariance_
        elif method == "exponential":
            # Exponential weighting
            lambda_param = 0.94
            weights = np.array([(1 - lambda_param) * lambda_param**i for i in range(len(returns_data))][::-1])
            weights = weights / weights.sum()
            weighted_returns = returns_data.multiply(weights, axis=0)
            return weighted_returns.cov().values
        else:
            return returns_data.cov().values

    def _maximize_sharpe_ratio(self, weights: cp.Variable, expected_returns: np.ndarray,
                              covariance_matrix: np.ndarray) -> cp.Problem:
        """Maximize Sharpe ratio optimization"""
        portfolio_return = expected_returns.T @ weights
        portfolio_variance = cp.quad_form(weights, covariance_matrix)
        portfolio_volatility = cp.sqrt(portfolio_variance)

        # Maximize (return - risk_free_rate) / volatility
        # Equivalent to minimizing volatility / (return - risk_free_rate)
        objective = cp.Minimize(portfolio_volatility / (portfolio_return - self.risk_free_rate))

        constraints = [cp.sum(weights) == 1]
        return cp.Problem(objective, constraints)

    def _minimize_volatility(self, weights: cp.Variable, expected_returns: np.ndarray,
                            covariance_matrix: np.ndarray) -> cp.Problem:
        """Minimize volatility optimization"""
        portfolio_variance = cp.quad_form(weights, covariance_matrix)
        objective = cp.Minimize(portfolio_variance)

        constraints = [
            cp.sum(weights) == 1,
            expected_returns.T @ weights >= 0.01  # Minimum return constraint
        ]
        return cp.Problem(objective, constraints)

    def _maximize_return(self, weights: cp.Variable, expected_returns: np.ndarray,
                        constraints: List[OptimizationConstraint]) -> cp.Problem:
        """Maximize return optimization"""
        portfolio_return = expected_returns.T @ weights
        objective = cp.Maximize(portfolio_return)

        cvx_constraints = [cp.sum(weights) == 1]

        # Add volatility constraint if specified
        if constraints:
            for constraint in constraints:
                if constraint.constraint_type == ConstraintType.BOUNDED_WEIGHTS:
                    min_weight = constraint.parameters.get('min_weight', 0.0)
                    max_weight = constraint.parameters.get('max_weight', 1.0)
                    cvx_constraints.extend([weights >= min_weight, weights <= max_weight])

        return cp.Problem(objective, cvx_constraints)

    def _risk_parity_optimization(self, weights: cp.Variable, covariance_matrix: np.ndarray) -> cp.Problem:
        """Risk parity optimization"""
        portfolio_risk = cp.sqrt(cp.quad_form(weights, covariance_matrix))
        marginal_risk = covariance_matrix @ weights

        # Equalize risk contributions
        risk_contributions = cp.multiply(weights, marginal_risk)
        target_risk_contribution = portfolio_risk / len(weights)

        # Minimize squared difference between risk contributions
        objective = cp.Minimize(cp.sum_squares(risk_contributions - target_risk_contribution))

        constraints = [cp.sum(weights) == 1, weights >= 0]
        return cp.Problem(objective, constraints)

    def _maximum_diversification_optimization(self, weights: cp.Variable, expected_returns: np.ndarray,
                                            covariance_matrix: np.ndarray) -> cp.Problem:
        """Maximum diversification optimization"""
        portfolio_volatility = cp.sqrt(cp.quad_form(weights, covariance_matrix))
        weighted_volatility = weights.T @ np.sqrt(np.diag(covariance_matrix))

        # Maximize diversification ratio
        objective = cp.Maximize(weighted_volatility / portfolio_volatility)

        constraints = [cp.sum(weights) == 1, weights >= 0]
        return cp.Problem(objective, constraints)

    def _build_constraints(self, weights: cp.Variable, constraints: List[OptimizationConstraint],
                          assets: List[str], benchmark_weights: Dict[str, float] = None) -> List[cp.Constraint]:
        """Build optimization constraints"""
        cvx_constraints = []

        if constraints is None:
            return cvx_constraints

        for constraint in constraints:
            if constraint.constraint_type == ConstraintType.NO_SHORT:
                cvx_constraints.append(weights >= 0)
            elif constraint.constraint_type == ConstraintType.BOUNDED_WEIGHTS:
                min_weight = constraint.parameters.get('min_weight', 0.0)
                max_weight = constraint.parameters.get('max_weight', 1.0)
                cvx_constraints.extend([weights >= min_weight, weights <= max_weight])
            elif constraint.constraint_type == ConstraintType.TURNOVER_LIMITS:
                if benchmark_weights:
                    benchmark_array = np.array([benchmark_weights.get(asset, 0) for asset in assets])
                    max_turnover = constraint.parameters.get('max_turnover', 0.2)
                    turnover = cp.sum(cp.abs(weights - benchmark_array))
                    cvx_constraints.append(turnover <= max_turnover)
            elif constraint.constraint_type == ConstraintType.CONCENTRATION_LIMITS:
                max_concentration = constraint.parameters.get('max_concentration', 0.1)
                cvx_constraints.append(weights <= max_concentration)

        return cvx_constraints

    def _calculate_tracking_error(self, weights: np.ndarray, benchmark_weights: Dict[str, float],
                                 covariance_matrix: np.ndarray) -> float:
        """Calculate tracking error vs benchmark"""
        if benchmark_weights is None:
            return 0.0

        benchmark_array = np.array([benchmark_weights.get(asset, 0) for asset in range(len(weights))])
        active_weights = weights - benchmark_array
        tracking_error = np.sqrt(active_weights.T @ covariance_matrix @ active_weights)
        return tracking_error

    def _estimate_maximum_drawdown(self, weights: np.ndarray, expected_returns: np.ndarray,
                                 covariance_matrix: np.ndarray) -> float:
        """Estimate maximum drawdown using parametric approach"""
        portfolio_return = expected_returns @ weights
        portfolio_volatility = np.sqrt(weights.T @ covariance_matrix @ weights)

        # Simplified parametric drawdown estimation
        # In practice, this would use more sophisticated methods
        estimated_max_dd = 2.33 * portfolio_volatility  # Assuming normal distribution
        return min(estimated_max_dd, 0.5)  # Cap at 50%

    def _calculate_diversification_ratio(self, weights: np.ndarray, covariance_matrix: np.ndarray) -> float:
        """Calculate diversification ratio"""
        weighted_volatility = weights.T @ np.sqrt(np.diag(covariance_matrix))
        portfolio_volatility = np.sqrt(weights.T @ covariance_matrix @ weights)
        return weighted_volatility / portfolio_volatility if portfolio_volatility > 0 else 1.0

    def _calculate_effective_number_of_assets(self, weights: np.ndarray) -> float:
        """Calculate effective number of assets (diversification measure)"""
        # Herfindahl-Hirschman Index
        hhi = np.sum(weights**2)
        return 1 / hhi if hhi > 0 else 0

    def perform_monte_carlo_optimization(self, returns_data: pd.DataFrame,
                                       n_simulations: int = 10000,
                                       objective: OptimizationObjective = OptimizationObjective.MAXIMIZE_SHARPE) -> pd.DataFrame:
        """Perform Monte Carlo simulation for portfolio optimization"""
        try:
            n_assets = len(returns_data.columns)
            expected_returns = returns_data.mean().values
            covariance_matrix = returns_data.cov().values

            results = []

            for i in range(n_simulations):
                # Generate random weights
                weights = np.random.random(n_assets)
                weights = weights / np.sum(weights)

                # Calculate portfolio metrics
                portfolio_return = expected_returns @ weights
                portfolio_volatility = np.sqrt(weights.T @ covariance_matrix @ weights)
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0

                results.append({
                    'return': portfolio_return,
                    'volatility': portfolio_volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'weights': weights
                })

            results_df = pd.DataFrame(results)
            return results_df

        except Exception as e:
            self.logger.error(f"Error performing Monte Carlo optimization: {str(e)}")
            return pd.DataFrame()

    def calculate_efficient_frontier(self, returns_data: pd.DataFrame,
                                    n_points: int = 100) -> pd.DataFrame:
        """Calculate efficient frontier"""
        try:
            expected_returns = returns_data.mean().values
            covariance_matrix = returns_data.cov().values

            # Find minimum and maximum returns
            min_return, max_return = expected_returns.min(), expected_returns.max()

            # Generate target returns
            target_returns = np.linspace(min_return, max_return, n_points)

            efficient_points = []

            for target_return in target_returns:
                try:
                    # Minimize volatility for target return
                    n_assets = len(expected_returns)
                    weights = cp.Variable(n_assets)

                    objective = cp.Minimize(cp.quad_form(weights, covariance_matrix))
                    constraints = [
                        cp.sum(weights) == 1,
                        expected_returns.T @ weights >= target_return,
                        weights >= 0
                    ]

                    problem = cp.Problem(objective, constraints)
                    problem.solve()

                    if problem.status == 'optimal':
                        portfolio_volatility = np.sqrt(weights.value.T @ covariance_matrix @ weights.value)
                        efficient_points.append({
                            'return': target_return,
                            'volatility': portfolio_volatility,
                            'sharpe_ratio': (target_return - self.risk_free_rate) / portfolio_volatility,
                            'weights': weights.value
                        })

                except Exception as e:
                    self.logger.warning(f"Error calculating efficient frontier point: {str(e)}")
                    continue

            return pd.DataFrame(efficient_points)

        except Exception as e:
            self.logger.error(f"Error calculating efficient frontier: {str(e)}")
            return pd.DataFrame()

    def backtest_portfolio(self, returns_data: pd.DataFrame, weights: Dict[str, float],
                          rebalance_freq: str = 'M') -> PortfolioMetrics:
        """Backtest portfolio performance"""
        try:
            # Convert weights to array
            assets = returns_data.columns.tolist()
            weights_array = np.array([weights.get(asset, 0) for asset in assets])

            # Calculate portfolio returns
            portfolio_returns = (returns_data * weights_array).sum(axis=1)

            # Calculate metrics
            total_return = (1 + portfolio_returns).prod() - 1
            annualized_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
            volatility = portfolio_returns.std() * np.sqrt(252)
            sharpe_ratio = (annualized_return - self.risk_free_rate) / volatility if volatility > 0 else 0

            # Sortino ratio
            downside_returns = portfolio_returns[portfolio_returns < 0]
            sortino_ratio = (annualized_return - self.risk_free_rate) / (downside_returns.std() * np.sqrt(252)) if len(downside_returns) > 0 else 0

            # Maximum drawdown
            cumulative_returns = np.cumprod(1 + portfolio_returns)
            peak = np.maximum.accumulate(cumulative_returns)
            drawdown = (peak - cumulative_returns) / peak
            max_drawdown = np.max(drawdown)

            # Calmar ratio
            calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0

            # Win rate and profit factor
            win_rate = (portfolio_returns > 0).mean()
            profit_factor = portfolio_returns[portfolio_returns > 0].sum() / abs(portfolio_returns[portfolio_returns < 0].sum()) if len(portfolio_returns[portfolio_returns < 0]) > 0 else 0

            return PortfolioMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                calmar_ratio=calmar_ratio,
                win_rate=win_rate,
                profit_factor=profit_factor
            )

        except Exception as e:
            self.logger.error(f"Error backtesting portfolio: {str(e)}")
            return PortfolioMetrics(0, 0, 0, 0, 0, 0, 0)

    def generate_optimization_report(self, optimization_result: OptimizationResult) -> str:
        """Generate comprehensive optimization report"""
        if not optimization_result:
            return "No optimization result available"

        report = f"""
Portfolio Optimization Report
============================

Portfolio ID: {optimization_result.portfolio_id}
Objective: {optimization_result.objective.value.replace('_', ' ').title()}
Optimization Date: {optimization_result.optimization_time.strftime('%Y-%m-%d %H:%M:%S')}
Status: {optimization_result.convergence_status}

Performance Metrics:
- Expected Return: {optimization_result.expected_return:.2%}
- Expected Volatility: {optimization_result.expected_volatility:.2%}
- Sharpe Ratio: {optimization_result.sharpe_ratio:.3f}
"""

        if optimization_result.tracking_error is not None:
            report += f"- Tracking Error: {optimization_result.tracking_error:.2%}\n"

        if optimization_result.maximum_drawdown is not None:
            report += f"- Maximum Drawdown: {optimization_result.maximum_drawdown:.2%}\n"

        if optimization_result.diversification_ratio is not None:
            report += f"- Diversification Ratio: {optimization_result.diversification_ratio:.3f}\n"

        if optimization_result.effective_number_of_assets is not None:
            report += f"- Effective Number of Assets: {optimization_result.effective_number_of_assets:.1f}\n"

        report += "\nOptimal Weights:\n"
        for asset, weight in optimization_result.optimal_weights.items():
            if weight > 0.001:  # Only show significant weights
                report += f"- {asset}: {weight:.2%}\n"

        if optimization_result.factor_exposures:
            report += "\nFactor Exposures:\n"
            for factor, exposure in optimization_result.factor_exposures.items():
                report += f"- {factor}: {exposure:.3f}\n"

        return report

    def compare_portfolios(self, portfolios: Dict[str, OptimizationResult]) -> pd.DataFrame:
        """Compare multiple optimized portfolios"""
        comparison_data = []

        for portfolio_name, result in portfolios.items():
            if result:
                comparison_data.append({
                    'Portfolio': portfolio_name,
                    'Objective': result.objective.value,
                    'Return': result.expected_return,
                    'Volatility': result.expected_volatility,
                    'Sharpe Ratio': result.sharpe_ratio,
                    'Effective Assets': result.effective_number_of_assets,
                    'Diversification Ratio': result.diversification_ratio
                })

        return pd.DataFrame(comparison_data)

    def calculate_robustness_metrics(self, optimization_result: OptimizationResult,
                                  returns_data: pd.DataFrame,
                                  n_bootstrap: int = 100) -> Dict[str, float]:
        """Calculate robustness metrics for optimization results"""
        try:
            if not optimization_result:
                return {}

            weights_array = np.array(list(optimization_result.optimal_weights.values()))
            n_assets = len(weights_array)

            # Bootstrap resampling
            bootstrap_weights = []
            bootstrap_returns = []
            bootstrap_volatilities = []

            for _ in range(n_bootstrap):
                # Resample returns with replacement
                sampled_returns = returns_data.sample(n=len(returns_data), replace=True)
                sampled_expected_returns = sampled_returns.mean().values
                sampled_covariance = sampled_returns.cov().values

                # Calculate metrics for bootstrap sample
                bootstrap_return = sampled_expected_returns @ weights_array
                bootstrap_volatility = np.sqrt(weights_array.T @ sampled_covariance @ weights_array)
                bootstrap_returns.append(bootstrap_return)
                bootstrap_volatilities.append(bootstrap_volatility)

            # Calculate robustness metrics
            return_std = np.std(bootstrap_returns)
            volatility_std = np.std(bootstrap_volatilities)
            return_range = np.max(bootstrap_returns) - np.min(bootstrap_returns)
            volatility_range = np.max(bootstrap_volatilities) - np.min(bootstrap_volatilities)

            return {
                'return_stability': 1 - (return_std / np.mean(bootstrap_returns)) if np.mean(bootstrap_returns) > 0 else 0,
                'volatility_stability': 1 - (volatility_std / np.mean(bootstrap_volatilities)) if np.mean(bootstrap_volatilities) > 0 else 0,
                'return_range': return_range,
                'volatility_range': volatility_range,
                'sharpe_ratio_stability': 1 - (np.std(bootstrap_returns) / np.mean(bootstrap_returns)) if np.mean(bootstrap_returns) > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Error calculating robustness metrics: {str(e)}")
            return {}