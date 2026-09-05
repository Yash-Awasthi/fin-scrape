"""
Risk Models
Comprehensive risk assessment models for financial analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from scipy import stats
from sklearn.covariance import LedoitWolf


class RiskCategory(Enum):
    """Risk categories"""
    MARKET_RISK = "market_risk"
    CREDIT_RISK = "credit_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    OPERATIONAL_RISK = "operational_risk"
    CONCENTRATION_RISK = "concentration_risk"
    CURRENCY_RISK = "currency_risk"
    INTEREST_RATE_RISK = "interest_rate_risk"


class RiskLevel(Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetric:
    """Individual risk metric"""
    name: str
    value: float
    category: RiskCategory
    level: RiskLevel
    threshold: float
    description: str = ""
    calculation_method: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VaRResult:
    """Value at Risk calculation result"""
    confidence_level: float
    time_horizon: str
    var_value: float
    expected_shortfall: float
    method: str
    portfolio_value: float
    historical_var: Optional[float] = None
    parametric_var: Optional[float] = None
    monte_carlo_var: Optional[float] = None


@dataclass
class StressTestResult:
    """Stress test result"""
    scenario_name: str
    portfolio_value_before: float
    portfolio_value_after: float
    percentage_loss: float
    risk_metrics: Dict[str, float]
    recovery_period: Optional[int] = None
    tail_risk: Optional[float] = None


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment"""
    symbol: str
    assessment_date: datetime
    overall_risk_score: float
    risk_level: RiskLevel
    risk_metrics: List[RiskMetric]
    var_results: List[VaRResult]
    stress_test_results: List[StressTestResult]
    risk_factors: Dict[str, float]
    recommendations: List[str] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class PortfolioRisk:
    """Portfolio risk analysis"""
    portfolio_id: str
    total_value: float
    positions: Dict[str, float]
    var_95_1d: float
    var_99_1d: float
    expected_shortfall_95: float
    beta: float
    alpha: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    information_ratio: Optional[float] = None
    tracking_error: Optional[float] = None
    concentration_risk: float = 0.0
    liquidity_risk: float = 0.0


class RiskModels:
    """Comprehensive risk analysis models"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.risk_thresholds = self._initialize_risk_thresholds()

    def _initialize_risk_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize risk thresholds for different metrics"""
        return {
            "var_95_1d": {"low": 0.02, "medium": 0.05, "high": 0.10, "critical": 0.15},
            "beta": {"low": 0.8, "medium": 1.2, "high": 1.5, "critical": 2.0},
            "max_drawdown": {"low": 0.10, "medium": 0.20, "high": 0.30, "critical": 0.40},
            "volatility": {"low": 0.15, "medium": 0.25, "high": 0.35, "critical": 0.50},
            "sharpe_ratio": {"low": 0.5, "medium": 1.0, "high": 1.5, "critical": 2.0},
            "concentration": {"low": 0.20, "medium": 0.40, "high": 0.60, "critical": 0.80},
            "liquidity": {"low": 0.10, "medium": 0.20, "high": 0.30, "critical": 0.40}
        }

    def calculate_historical_var(self, returns: List[float], confidence_level: float = 0.95,
                               portfolio_value: float = 1000000) -> Optional[VaRResult]:
        """Calculate Historical Value at Risk"""
        if len(returns) < 30:
            self.logger.warning("Insufficient data for Historical VaR calculation")
            return None

        try:
            returns_array = np.array(returns)
            var_percentile = (1 - confidence_level) * 100
            var_value = np.percentile(returns_array, var_percentile) * portfolio_value

            # Calculate Expected Shortfall (CVaR)
            tail_returns = returns_array[returns_array <= np.percentile(returns_array, var_percentile)]
            expected_shortfall = np.mean(tail_returns) * portfolio_value if len(tail_returns) > 0 else var_value

            return VaRResult(
                confidence_level=confidence_level,
                time_horizon="1d",
                var_value=abs(var_value),
                expected_shortfall=abs(expected_shortfall),
                method="historical",
                portfolio_value=portfolio_value,
                historical_var=abs(var_value)
            )

        except Exception as e:
            self.logger.error(f"Error calculating Historical VaR: {str(e)}")
            return None

    def calculate_parametric_var(self, returns: List[float], confidence_level: float = 0.95,
                               portfolio_value: float = 1000000) -> Optional[VaRResult]:
        """Calculate Parametric Value at Risk using normal distribution"""
        if len(returns) < 30:
            self.logger.warning("Insufficient data for Parametric VaR calculation")
            return None

        try:
            returns_array = np.array(returns)
            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array)

            # Calculate VaR using normal distribution
            z_score = stats.norm.ppf(1 - confidence_level)
            var_value = (mean_return + z_score * std_return) * portfolio_value

            # Calculate Expected Shortfall
            expected_shortfall = (mean_return - std_return * stats.norm.pdf(z_score) / (1 - confidence_level)) * portfolio_value

            return VaRResult(
                confidence_level=confidence_level,
                time_horizon="1d",
                var_value=abs(var_value),
                expected_shortfall=abs(expected_shortfall),
                method="parametric",
                portfolio_value=portfolio_value,
                parametric_var=abs(var_value)
            )

        except Exception as e:
            self.logger.error(f"Error calculating Parametric VaR: {str(e)}")
            return None

    def calculate_monte_carlo_var(self, returns: List[float], confidence_level: float = 0.95,
                                portfolio_value: float = 1000000, simulations: int = 10000) -> Optional[VaRResult]:
        """Calculate Monte Carlo Value at Risk"""
        if len(returns) < 30:
            self.logger.warning("Insufficient data for Monte Carlo VaR calculation")
            return None

        try:
            returns_array = np.array(returns)
            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array)

            # Generate Monte Carlo simulations
            simulated_returns = np.random.normal(mean_return, std_return, simulations)
            var_percentile = (1 - confidence_level) * 100
            var_value = np.percentile(simulated_returns, var_percentile) * portfolio_value

            # Calculate Expected Shortfall
            tail_returns = simulated_returns[simulated_returns <= np.percentile(simulated_returns, var_percentile)]
            expected_shortfall = np.mean(tail_returns) * portfolio_value if len(tail_returns) > 0 else var_value

            return VaRResult(
                confidence_level=confidence_level,
                time_horizon="1d",
                var_value=abs(var_value),
                expected_shortfall=abs(expected_shortfall),
                method="monte_carlo",
                portfolio_value=portfolio_value,
                monte_carlo_var=abs(var_value)
            )

        except Exception as e:
            self.logger.error(f"Error calculating Monte Carlo VaR: {str(e)}")
            return None

    def calculate_comprehensive_var(self, returns: List[float], confidence_levels: List[float] = None,
                                   portfolio_value: float = 1000000) -> List[VaRResult]:
        """Calculate VaR using multiple methods and confidence levels"""
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]

        results = []

        for confidence_level in confidence_levels:
            # Calculate using all methods
            historical_var = self.calculate_historical_var(returns, confidence_level, portfolio_value)
            parametric_var = self.calculate_parametric_var(returns, confidence_level, portfolio_value)
            monte_carlo_var = self.calculate_monte_carlo_var(returns, confidence_level, portfolio_value)

            # Create comprehensive result
            if historical_var and parametric_var and monte_carlo_var:
                comprehensive_var = VaRResult(
                    confidence_level=confidence_level,
                    time_horizon="1d",
                    var_value=np.mean([historical_var.var_value, parametric_var.var_value, monte_carlo_var.var_value]),
                    expected_shortfall=np.mean([historical_var.expected_shortfall, parametric_var.expected_shortfall, monte_carlo_var.expected_shortfall]),
                    method="comprehensive",
                    portfolio_value=portfolio_value,
                    historical_var=historical_var.var_value,
                    parametric_var=parametric_var.var_value,
                    monte_carlo_var=monte_carlo_var.var_value
                )
                results.append(comprehensive_var)

        return results

    def perform_stress_testing(self, current_returns: List[float], scenarios: Dict[str, Dict[str, float]],
                             portfolio_value: float = 1000000) -> List[StressTestResult]:
        """Perform stress testing under various scenarios"""
        results = []

        try:
            base_metrics = self._calculate_risk_metrics(current_returns)

            for scenario_name, scenario_params in scenarios.items():
                # Apply scenario to returns
                stressed_returns = self._apply_stress_scenario(current_returns, scenario_params)

                # Calculate stressed portfolio value
                cumulative_return = np.prod(1 + np.array(stressed_returns)) - 1
                stressed_value = portfolio_value * (1 + cumulative_return)

                # Calculate stress test metrics
                stressed_metrics = self._calculate_risk_metrics(stressed_returns)

                # Calculate tail risk
                tail_risk = self._calculate_tail_risk(stressed_returns)

                result = StressTestResult(
                    scenario_name=scenario_name,
                    portfolio_value_before=portfolio_value,
                    portfolio_value_after=stressed_value,
                    percentage_loss=cumulative_return * 100,
                    risk_metrics=stressed_metrics,
                    recovery_period=self._estimate_recovery_period(stressed_returns),
                    tail_risk=tail_risk
                )

                results.append(result)

        except Exception as e:
            self.logger.error(f"Error performing stress testing: {str(e)}")

        return results

    def _apply_stress_scenario(self, returns: List[float], scenario_params: Dict[str, float]) -> List[float]:
        """Apply stress scenario parameters to returns"""
        stressed_returns = []

        for ret in returns:
            stressed_return = ret

            # Apply shock
            if 'shock' in scenario_params:
                stressed_return += scenario_params['shock']

            # Apply volatility multiplier
            if 'volatility_multiplier' in scenario_params:
                stressed_return *= scenario_params['volatility_multiplier']

            # Apply correlation breakdown
            if 'correlation_breakdown' in scenario_params and scenario_params['correlation_breakdown']:
                stressed_return += np.random.normal(0, abs(stressed_return) * 0.5)

            stressed_returns.append(stressed_return)

        return stressed_returns

    def _calculate_risk_metrics(self, returns: List[float]) -> Dict[str, float]:
        """Calculate basic risk metrics"""
        if not returns:
            return {}

        try:
            returns_array = np.array(returns)
            metrics = {
                'volatility': np.std(returns_array),
                'sharpe_ratio': np.mean(returns_array) / np.std(returns_array) if np.std(returns_array) > 0 else 0,
                'max_drawdown': self._calculate_max_drawdown(returns_array),
                'skewness': stats.skew(returns_array),
                'kurtosis': stats.kurtosis(returns_array),
                'value_at_risk_95': np.percentile(returns_array, 5),
                'expected_shortfall_95': np.mean(returns_array[returns_array <= np.percentile(returns_array, 5)])
            }

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {str(e)}")
            return {}

    def _calculate_tail_risk(self, returns: List[float]) -> float:
        """Calculate tail risk measure"""
        try:
            returns_array = np.array(returns)
            var_95 = np.percentile(returns_array, 5)
            tail_returns = returns_array[returns_array <= var_95]

            if len(tail_returns) > 0:
                return np.std(tail_returns)
            return 0.0

        except Exception as e:
            self.logger.error(f"Error calculating tail risk: {str(e)}")
            return 0.0

    def _estimate_recovery_period(self, stressed_returns: List[float]) -> Optional[int]:
        """Estimate recovery period in days"""
        try:
            cumulative_returns = np.cumprod(1 + np.array(stressed_returns))
            peak = np.maximum.accumulate(cumulative_returns)
            drawdown = (peak - cumulative_returns) / peak

            # Find when drawdown returns to less than 5%
            recovery_points = np.where(drawdown < 0.05)[0]
            if len(recovery_points) > 0:
                return recovery_points[0]

            return None

        except Exception as e:
            self.logger.error(f"Error estimating recovery period: {str(e)}")
            return None

    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        cumulative = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = (peak - cumulative) / peak
        return np.max(drawdown) if len(drawdown) > 0 else 0.0

    def calculate_portfolio_risk(self, returns_matrix: pd.DataFrame, weights: List[float],
                               benchmark_returns: List[float] = None, risk_free_rate: float = 0.02) -> Optional[PortfolioRisk]:
        """Calculate comprehensive portfolio risk metrics"""
        try:
            if len(weights) != len(returns_matrix.columns):
                raise ValueError("Weights length must match number of assets")

            weights_array = np.array(weights)

            # Calculate portfolio returns
            portfolio_returns = (returns_matrix * weights_array).sum(axis=1)

            # Calculate basic metrics
            portfolio_value = 1000000  # Assume $1M portfolio
            volatility = np.std(portfolio_returns)

            # Calculate VaR
            var_95_1d = abs(np.percentile(portfolio_returns, 5) * portfolio_value)
            var_99_1d = abs(np.percentile(portfolio_returns, 1) * portfolio_value)
            expected_shortfall_95 = abs(np.mean(portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 5)]) * portfolio_value)

            # Calculate beta and alpha
            if benchmark_returns is not None:
                benchmark_returns_array = np.array(benchmark_returns)
                if len(portfolio_returns) == len(benchmark_returns_array):
                    covariance = np.cov(portfolio_returns, benchmark_returns_array)[0, 1]
                    benchmark_variance = np.var(benchmark_returns_array)
                    beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0
                    alpha = np.mean(portfolio_returns) - beta * np.mean(benchmark_returns_array)
                else:
                    beta = 1.0
                    alpha = 0.0
            else:
                beta = 1.0
                alpha = 0.0

            # Calculate risk-adjusted returns
            excess_returns = portfolio_returns - risk_free_rate / 252  # Daily risk-free rate
            sharpe_ratio = np.mean(excess_returns) / np.std(portfolio_returns) if np.std(portfolio_returns) > 0 else 0

            # Calculate Sortino ratio (downside risk)
            downside_returns = excess_returns[excess_returns < 0]
            sortino_ratio = np.mean(excess_returns) / np.std(downside_returns) if len(downside_returns) > 0 else 0

            # Calculate maximum drawdown
            max_drawdown = self._calculate_max_drawdown(portfolio_returns)

            # Calculate Calmar ratio
            annual_return = np.mean(portfolio_returns) * 252
            calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0

            # Calculate concentration risk
            concentration_risk = self._calculate_concentration_risk(weights)

            # Calculate liquidity risk (simplified)
            liquidity_risk = self._calculate_liquidity_risk(returns_matrix)

            return PortfolioRisk(
                portfolio_id="portfolio_1",
                total_value=portfolio_value,
                positions={col: weight * portfolio_value for col, weight in zip(returns_matrix.columns, weights)},
                var_95_1d=var_95_1d,
                var_99_1d=var_99_1d,
                expected_shortfall_95=expected_shortfall_95,
                beta=beta,
                alpha=alpha,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                calmar_ratio=calmar_ratio,
                concentration_risk=concentration_risk,
                liquidity_risk=liquidity_risk
            )

        except Exception as e:
            self.logger.error(f"Error calculating portfolio risk: {str(e)}")
            return None

    def _calculate_concentration_risk(self, weights: List[float]) -> float:
        """Calculate concentration risk using Herfindahl-Hirschman Index"""
        try:
            hhi = sum(w**2 for w in weights)
            return hhi
        except Exception as e:
            self.logger.error(f"Error calculating concentration risk: {str(e)}")
            return 0.0

    def _calculate_liquidity_risk(self, returns_matrix: pd.DataFrame) -> float:
        """Calculate simplified liquidity risk based on return gaps"""
        try:
            # Calculate average absolute daily change as proxy for liquidity
            daily_changes = returns_matrix.diff().abs().mean()
            avg_daily_change = daily_changes.mean()
            return avg_daily_change if not np.isnan(avg_daily_change) else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating liquidity risk: {str(e)}")
            return 0.0

    def calculate_risk_score(self, risk_metrics: List[RiskMetric]) -> Tuple[float, RiskLevel]:
        """Calculate overall risk score and level"""
        if not risk_metrics:
            return 0.0, RiskLevel.LOW

        try:
            # Weight different risk categories
            category_weights = {
                RiskCategory.MARKET_RISK: 0.4,
                RiskCategory.CREDIT_RISK: 0.2,
                RiskCategory.LIQUIDITY_RISK: 0.2,
                RiskCategory.OPERATIONAL_RISK: 0.1,
                RiskCategory.CONCENTRATION_RISK: 0.1
            }

            category_scores = {}
            for metric in risk_metrics:
                category = metric.category
                if category not in category_scores:
                    category_scores[category] = []

                # Normalize metric value (0-1 scale)
                normalized_value = self._normalize_risk_metric(metric)
                category_scores[category].append(normalized_value)

            # Calculate weighted average
            total_score = 0.0
            total_weight = 0.0

            for category, scores in category_scores.items():
                if scores and category in category_weights:
                    avg_category_score = np.mean(scores)
                    weight = category_weights[category]
                    total_score += avg_category_score * weight
                    total_weight += weight

            final_score = total_score / total_weight if total_weight > 0 else 0.0

            # Determine risk level
            if final_score < 0.3:
                risk_level = RiskLevel.LOW
            elif final_score < 0.6:
                risk_level = RiskLevel.MEDIUM
            elif final_score < 0.8:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.CRITICAL

            return final_score, risk_level

        except Exception as e:
            self.logger.error(f"Error calculating risk score: {str(e)}")
            return 0.0, RiskLevel.LOW

    def _normalize_risk_metric(self, metric: RiskMetric) -> float:
        """Normalize risk metric to 0-1 scale"""
        try:
            # Use metric-specific normalization
            if metric.name in ["var_95_1d", "var_99_1d", "max_drawdown"]:
                # These are percentage values, cap at 50%
                return min(metric.value / 0.5, 1.0)
            elif metric.name in ["volatility", "tracking_error"]:
                # Annualized volatility, cap at 100%
                return min(metric.value / 1.0, 1.0)
            elif metric.name in ["beta"]:
                # Beta values, cap at 3.0
                return min(metric.value / 3.0, 1.0)
            elif metric.name in ["sharpe_ratio", "sortino_ratio"]:
                # Higher is better, so invert
                return max(0, 1.0 - metric.value / 3.0)
            else:
                # Default normalization
                return min(metric.value, 1.0)

        except Exception as e:
            self.logger.error(f"Error normalizing risk metric: {str(e)}")
            return 0.5

    def generate_risk_recommendations(self, risk_metrics: List[RiskMetric], risk_level: RiskLevel) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []

        # High-level recommendations based on risk level
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("IMMEDIATE ACTION REQUIRED: Implement emergency risk reduction measures")
            recommendations.append("Consider reducing portfolio exposure by 25-50%")
            recommendations.append("Increase cash position to 20-30% of portfolio")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Implement risk reduction strategies within 30 days")
            recommendations.append("Consider reducing portfolio exposure by 15-25%")
            recommendations.append("Increase cash position to 15-20% of portfolio")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("Monitor risk levels closely and implement gradual de-risking")
            recommendations.append("Maintain defensive positioning in high-risk assets")
        else:
            recommendations.append("Maintain current risk profile with regular monitoring")

        # Specific recommendations based on individual metrics
        for metric in risk_metrics:
            if metric.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                if metric.category == RiskCategory.MARKET_RISK:
                    recommendations.append(f"Consider hedging {metric.name} exposure")
                    recommendations.append("Reduce position size in volatile assets")
                elif metric.category == RiskCategory.CREDIT_RISK:
                    recommendations.append("Improve credit quality of holdings")
                    recommendations.append("Consider credit default swaps for protection")
                elif metric.category == RiskCategory.LIQUIDITY_RISK:
                    recommendations.append("Increase allocation to liquid assets")
                    recommendations.append("Establish lines of credit for emergency liquidity")
                elif metric.category == RiskCategory.CONCENTRATION_RISK:
                    recommendations.append("Diversify concentrated positions")
                    recommendations.append("Implement position size limits")

        return recommendations

    def create_stress_scenarios(self) -> Dict[str, Dict[str, float]]:
        """Create standard stress testing scenarios"""
        return {
            "Market Crash": {
                "shock": -0.15,
                "volatility_multiplier": 2.0,
                "correlation_breakdown": True
            },
            "Interest Rate Shock": {
                "shock": -0.08,
                "volatility_multiplier": 1.5,
                "correlation_breakdown": False
            },
            "Liquidity Crisis": {
                "shock": -0.10,
                "volatility_multiplier": 3.0,
                "correlation_breakdown": True
            },
            "Credit Event": {
                "shock": -0.12,
                "volatility_multiplier": 2.5,
                "correlation_breakdown": True
            },
            "Currency Crisis": {
                "shock": -0.20,
                "volatility_multiplier": 2.0,
                "correlation_breakdown": True
            }
        }