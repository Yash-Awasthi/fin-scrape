"""
Risk Analyzer
Comprehensive risk analysis and assessment system
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

from .risk_models import (
    RiskMetric, VaRResult, StressTestResult, RiskAssessment, PortfolioRisk,
    RiskCategory, RiskLevel, RiskModels
)


class RiskProfile(Enum):
    """Investor risk profiles"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    SPECULATIVE = "speculative"


@dataclass
class RiskBudget:
    """Risk budget allocation"""
    category: RiskCategory
    budget_limit: float
    current_usage: float
    utilization_rate: float
    status: str  # "within_budget", "near_limit", "over_budget"


@dataclass
class RiskAttribution:
    """Risk attribution analysis"""
    factor_name: str
    contribution_to_risk: float
    marginal_risk: float
    percentage_contribution: float


class RiskAnalyzer:
    """Comprehensive risk analysis system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.risk_models = RiskModels()
        self.risk_profiles = self._initialize_risk_profiles()

    def _initialize_risk_profiles(self) -> Dict[RiskProfile, Dict[str, float]]:
        """Initialize risk profile parameters"""
        return {
            RiskProfile.CONSERVATIVE: {
                "max_volatility": 0.10,
                "max_drawdown": 0.15,
                "max_var_95": 0.05,
                "min_sharpe_ratio": 0.8,
                "max_concentration": 0.25
            },
            RiskProfile.MODERATE: {
                "max_volatility": 0.18,
                "max_drawdown": 0.25,
                "max_var_95": 0.08,
                "min_sharpe_ratio": 0.6,
                "max_concentration": 0.40
            },
            RiskProfile.AGGRESSIVE: {
                "max_volatility": 0.30,
                "max_drawdown": 0.40,
                "max_var_95": 0.12,
                "min_sharpe_ratio": 0.4,
                "max_concentration": 0.60
            },
            RiskProfile.SPECULATIVE: {
                "max_volatility": 0.50,
                "max_drawdown": 0.60,
                "max_var_95": 0.20,
                "min_sharpe_ratio": 0.2,
                "max_concentration": 0.80
            }
        }

    def analyze_comprehensive_risk(self, returns_data: Dict[str, List[float]],
                                weights: List[float] = None,
                                portfolio_value: float = 1000000,
                                risk_profile: RiskProfile = RiskProfile.MODERATE) -> Optional[RiskAssessment]:
        """Perform comprehensive risk analysis"""
        try:
            # Convert to DataFrame for easier analysis
            returns_df = pd.DataFrame(returns_data)
            portfolio_returns = self._calculate_portfolio_returns(returns_df, weights)

            # Calculate VaR results
            var_results = self.risk_models.calculate_comprehensive_var(
                portfolio_returns, portfolio_value=portfolio_value
            )

            # Perform stress testing
            stress_scenarios = self.risk_models.create_stress_scenarios()
            stress_test_results = self.risk_models.perform_stress_testing(
                portfolio_returns, stress_scenarios, portfolio_value
            )

            # Calculate risk metrics
            risk_metrics = self._calculate_all_risk_metrics(returns_df, portfolio_returns, portfolio_value)

            # Calculate risk factors
            risk_factors = self._analyze_risk_factors(returns_df)

            # Calculate overall risk score
            risk_score, risk_level = self.risk_models.calculate_risk_score(risk_metrics)

            # Generate recommendations
            recommendations = self.risk_models.generate_risk_recommendations(risk_metrics, risk_level)

            # Compare against risk profile
            profile_comparison = self._compare_to_risk_profile(risk_metrics, risk_profile)

            return RiskAssessment(
                symbol="portfolio",
                assessment_date=datetime.now(),
                overall_risk_score=risk_score,
                risk_level=risk_level,
                risk_metrics=risk_metrics,
                var_results=var_results,
                stress_test_results=stress_test_results,
                risk_factors=risk_factors,
                recommendations=recommendations + profile_comparison
            )

        except Exception as e:
            self.logger.error(f"Error performing comprehensive risk analysis: {str(e)}")
            return None

    def _calculate_portfolio_returns(self, returns_df: pd.DataFrame, weights: List[float] = None) -> List[float]:
        """Calculate portfolio returns from individual asset returns"""
        if weights is None:
            weights = [1.0 / len(returns_df.columns)] * len(returns_df.columns)

        portfolio_returns = (returns_df * weights).sum(axis=1)
        return portfolio_returns.tolist()

    def _calculate_all_risk_metrics(self, returns_df: pd.DataFrame, portfolio_returns: List[float],
                                   portfolio_value: float) -> List[RiskMetric]:
        """Calculate all risk metrics"""
        risk_metrics = []

        try:
            # Market risk metrics
            volatility = np.std(portfolio_returns) * np.sqrt(252)  # Annualized
            risk_metrics.append(RiskMetric(
                name="volatility",
                value=volatility,
                category=RiskCategory.MARKET_RISK,
                level=self._get_risk_level(volatility, "volatility"),
                threshold=0.20,
                description="Annualized portfolio volatility",
                calculation_method="Standard deviation of returns * sqrt(252)"
            ))

            # VaR metrics
            var_95 = abs(np.percentile(portfolio_returns, 5) * portfolio_value)
            risk_metrics.append(RiskMetric(
                name="var_95_1d",
                value=var_95 / portfolio_value,
                category=RiskCategory.MARKET_RISK,
                level=self._get_risk_level(var_95 / portfolio_value, "var_95"),
                threshold=0.05,
                description="1-day 95% Value at Risk",
                calculation_method="5th percentile of returns distribution"
            ))

            # Maximum drawdown
            cumulative_returns = np.cumprod(1 + np.array(portfolio_returns))
            peak = np.maximum.accumulate(cumulative_returns)
            drawdown = (peak - cumulative_returns) / peak
            max_drawdown = np.max(drawdown)
            risk_metrics.append(RiskMetric(
                name="max_drawdown",
                value=max_drawdown,
                category=RiskCategory.MARKET_RISK,
                level=self._get_risk_level(max_drawdown, "max_drawdown"),
                threshold=0.20,
                description="Maximum historical drawdown",
                calculation_method="Maximum peak to trough decline"
            ))

            # Liquidity risk metrics
            avg_daily_volume = returns_df.mean().mean()  # Simplified proxy
            risk_metrics.append(RiskMetric(
                name="liquidity_risk",
                value=avg_daily_volume,
                category=RiskCategory.LIQUIDITY_RISK,
                level=self._get_risk_level(avg_daily_volume, "liquidity"),
                threshold=0.02,
                description="Portfolio liquidity risk",
                calculation_method="Average daily volume proxy"
            ))

            # Concentration risk
            if weights is not None:
                concentration_risk = sum(w**2 for w in weights)
                risk_metrics.append(RiskMetric(
                    name="concentration_risk",
                    value=concentration_risk,
                    category=RiskCategory.CONCENTRATION_RISK,
                    level=self._get_risk_level(concentration_risk, "concentration"),
                    threshold=0.25,
                    description="Portfolio concentration risk (HHI)",
                    calculation_method="Herfindahl-Hirschman Index"
                ))

            # Skewness and kurtosis
            skewness = stats.skew(portfolio_returns)
            kurtosis = stats.kurtosis(portfolio_returns)

            risk_metrics.append(RiskMetric(
                name="skewness",
                value=skewness,
                category=RiskCategory.MARKET_RISK,
                level=self._get_risk_level(abs(skewness), "skewness"),
                threshold=1.0,
                description="Return distribution skewness",
                calculation_method="Third moment of returns"
            ))

            risk_metrics.append(RiskMetric(
                name="kurtosis",
                value=kurtosis,
                category=RiskCategory.MARKET_RISK,
                level=self._get_risk_level(kurtosis, "kurtosis"),
                threshold=3.0,
                description="Return distribution kurtosis",
                calculation_method="Fourth moment of returns"
            ))

        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {str(e)}")

        return risk_metrics

    def _get_risk_level(self, value: float, metric_type: str) -> RiskLevel:
        """Determine risk level based on metric value and type"""
        thresholds = self.risk_models.risk_thresholds.get(metric_type, {})

        if value <= thresholds.get("low", float('inf')):
            return RiskLevel.LOW
        elif value <= thresholds.get("medium", float('inf')):
            return RiskLevel.MEDIUM
        elif value <= thresholds.get("high", float('inf')):
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _analyze_risk_factors(self, returns_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze risk factors using PCA"""
        try:
            if len(returns_df.columns) < 2:
                return {}

            # Standardize returns
            scaler = StandardScaler()
            scaled_returns = scaler.fit_transform(returns_df)

            # Perform PCA
            pca = PCA()
            pca.fit(scaled_returns)

            # Extract risk factors
            risk_factors = {}
            for i, (component, explained_variance) in enumerate(zip(pca.components_, pca.explained_variance_ratio_)):
                if i < 3:  # Top 3 factors
                    factor_name = f"Factor_{i+1}"
                    risk_factors[factor_name] = explained_variance

            return risk_factors

        except Exception as e:
            self.logger.error(f"Error analyzing risk factors: {str(e)}")
            return {}

    def _compare_to_risk_profile(self, risk_metrics: List[RiskMetric], risk_profile: RiskProfile) -> List[str]:
        """Compare current risk levels to risk profile limits"""
        recommendations = []

        if risk_profile not in self.risk_profiles:
            return recommendations

        profile_limits = self.risk_profiles[risk_profile]

        # Create metric mapping
        metric_mapping = {
            "volatility": "max_volatility",
            "max_drawdown": "max_drawdown",
            "var_95_1d": "max_var_95",
            "concentration_risk": "max_concentration"
        }

        for metric in risk_metrics:
            if metric.name in metric_mapping:
                limit_name = metric_mapping[metric.name]
                if limit_name in profile_limits:
                    limit = profile_limits[limit_name]
                    if metric.value > limit:
                        recommendations.append(
                            f"{metric.name.replace('_', ' ').title()} ({metric.value:.2f}) exceeds "
                            f"{risk_profile.value} profile limit ({limit:.2f})"
                        )

        return recommendations

    def calculate_risk_budget(self, portfolio_value: float, risk_profile: RiskProfile) -> List[RiskBudget]:
        """Calculate risk budget allocation"""
        risk_budgets = []

        if risk_profile not in self.risk_profiles:
            return risk_budgets

        profile_limits = self.risk_profiles[risk_profile]

        # Create risk budgets for each category
        category_mapping = {
            RiskCategory.MARKET_RISK: ["max_volatility", "max_drawdown", "max_var_95"],
            RiskCategory.CONCENTRATION_RISK: ["max_concentration"]
        }

        for category, limit_names in category_mapping.items():
            total_budget = 0
            current_usage = 0

            for limit_name in limit_names:
                if limit_name in profile_limits:
                    total_budget += profile_limits[limit_name]

            # For this example, we'll assume current usage is 70% of budget
            current_usage = total_budget * 0.7
            utilization_rate = current_usage / total_budget if total_budget > 0 else 0

            # Determine status
            if utilization_rate < 0.8:
                status = "within_budget"
            elif utilization_rate < 0.95:
                status = "near_limit"
            else:
                status = "over_budget"

            risk_budgets.append(RiskBudget(
                category=category,
                budget_limit=total_budget,
                current_usage=current_usage,
                utilization_rate=utilization_rate,
                status=status
            ))

        return risk_budgets

    def perform_risk_attribution(self, returns_df: pd.DataFrame, weights: List[float]) -> List[RiskAttribution]:
        """Perform risk attribution analysis"""
        risk_attributions = []

        try:
            # Calculate portfolio variance
            portfolio_variance = np.dot(weights, np.dot(returns_df.cov(), weights))

            # Calculate marginal VaR for each asset
            for i, asset in enumerate(returns_df.columns):
                # Marginal contribution to risk
                marginal_risk = 2 * np.dot(returns_df.cov().iloc[i], weights)
                contribution_to_risk = weights[i] * marginal_risk

                # Percentage contribution
                percentage_contribution = (contribution_to_risk / portfolio_variance) * 100 if portfolio_variance > 0 else 0

                risk_attributions.append(RiskAttribution(
                    factor_name=asset,
                    contribution_to_risk=contribution_to_risk,
                    marginal_risk=marginal_risk,
                    percentage_contribution=percentage_contribution
                ))

        except Exception as e:
            self.logger.error(f"Error performing risk attribution: {str(e)}")

        return risk_attributions

    def calculate_risk_adjusted_returns(self, returns: List[float], benchmark_returns: List[float] = None,
                                      risk_free_rate: float = 0.02) -> Dict[str, float]:
        """Calculate risk-adjusted performance metrics"""
        try:
            returns_array = np.array(returns)
            excess_returns = returns_array - risk_free_rate / 252

            metrics = {}

            # Sharpe ratio
            if len(excess_returns) > 0:
                sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
                metrics['sharpe_ratio'] = sharpe_ratio * np.sqrt(252)  # Annualized

            # Sortino ratio
            downside_returns = excess_returns[excess_returns < 0]
            if len(downside_returns) > 0:
                sortino_ratio = np.mean(excess_returns) / np.std(downside_returns)
                metrics['sortino_ratio'] = sortino_ratio * np.sqrt(252)
            else:
                metrics['sortino_ratio'] = 0

            # Treynor ratio (if benchmark provided)
            if benchmark_returns is not None:
                benchmark_array = np.array(benchmark_returns)
                if len(returns_array) == len(benchmark_array):
                    covariance = np.cov(returns_array, benchmark_array)[0, 1]
                    benchmark_variance = np.var(benchmark_array)
                    beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0
                    treynor_ratio = np.mean(excess_returns) / beta if beta != 0 else 0
                    metrics['treynor_ratio'] = treynor_ratio * 252

            # Information ratio (if benchmark provided)
            if benchmark_returns is not None:
                if len(returns_array) == len(benchmark_array):
                    active_returns = returns_array - benchmark_array
                    tracking_error = np.std(active_returns)
                    information_ratio = np.mean(active_returns) / tracking_error if tracking_error > 0 else 0
                    metrics['information_ratio'] = information_ratio * np.sqrt(252)

            # Calmar ratio
            cumulative_returns = np.cumprod(1 + returns_array)
            peak = np.maximum.accumulate(cumulative_returns)
            drawdown = (peak - cumulative_returns) / peak
            max_drawdown = np.max(drawdown)
            annual_return = np.mean(returns_array) * 252
            calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
            metrics['calmar_ratio'] = calmar_ratio

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating risk-adjusted returns: {str(e)}")
            return {}

    def generate_risk_report(self, risk_assessment: RiskAssessment) -> str:
        """Generate comprehensive risk analysis report"""
        if not risk_assessment:
            return "No risk assessment available"

        report = f"""
Comprehensive Risk Analysis Report
===================================

Assessment Date: {risk_assessment.assessment_date.strftime('%Y-%m-%d')}
Overall Risk Score: {risk_assessment.overall_risk_score:.2f}
Risk Level: {risk_assessment.risk_level.value.upper()}

Value at Risk Analysis:
"""
        # Add VaR results
        for var_result in risk_assessment.var_results:
            report += f"- {var_result.confidence_level*100:.0f}% VaR (1d): ${var_result.var_value:,.0f}\n"
            report += f"  Expected Shortfall: ${var_result.expected_shortfall:,.0f}\n"

        # Add stress test results
        report += "\nStress Testing Results:\n"
        for stress_result in risk_assessment.stress_test_results:
            report += f"- {stress_result.scenario_name}: {stress_result.percentage_loss:.1f}% loss\n"
            if stress_result.recovery_period:
                report += f"  Estimated recovery period: {stress_result.recovery_period} days\n"

        # Add key risk metrics
        report += "\nKey Risk Metrics:\n"
        for metric in risk_assessment.risk_metrics[:5]:  # Top 5 metrics
            report += f"- {metric.name.replace('_', ' ').title()}: {metric.value:.2f} ({metric.level.value})\n"

        # Add risk factors
        if risk_assessment.risk_factors:
            report += "\nPrincipal Risk Factors:\n"
            for factor, contribution in risk_assessment.risk_factors.items():
                report += f"- {factor}: {contribution:.1%} of variance explained\n"

        # Add recommendations
        if risk_assessment.recommendations:
            report += "\nRecommendations:\n"
            for i, rec in enumerate(risk_assessment.recommendations, 1):
                report += f"{i}. {rec}\n"

        return report

    def monitor_risk_limits(self, risk_assessment: RiskAssessment, limits: Dict[str, Dict[str, float]]) -> Dict[str, str]:
        """Monitor risk against predefined limits"""
        limit_status = {}

        for metric in risk_assessment.risk_metrics:
            metric_name = metric.name
            if metric_name in limits:
                limit_info = limits[metric_name]
                if metric.value > limit_info.get('warning', float('inf')):
                    limit_status[metric_name] = "WARNING"
                elif metric.value > limit_info.get('critical', float('inf')):
                    limit_status[metric_name] = "CRITICAL"
                else:
                    limit_status[metric_name] = "OK"

        return limit_status

    def calculate_risk_measures_time_series(self, returns_series: pd.Series, window: int = 30) -> pd.DataFrame:
        """Calculate rolling risk measures"""
        try:
            rolling_metrics = pd.DataFrame(index=returns_series.index)

            # Rolling volatility
            rolling_metrics['volatility'] = returns_series.rolling(window=window).std() * np.sqrt(252)

            # Rolling VaR
            rolling_metrics['var_95'] = returns_series.rolling(window=window).quantile(0.05)
            rolling_metrics['var_99'] = returns_series.rolling(window=window).quantile(0.01)

            # Rolling maximum drawdown
            rolling_metrics['max_drawdown'] = returns_series.rolling(window=window).apply(
                lambda x: self._calculate_max_drawdown(x.values)
            )

            # Rolling Sharpe ratio
            risk_free_daily = 0.02 / 252
            rolling_metrics['sharpe_ratio'] = (
                (returns_series.rolling(window=window).mean() - risk_free_daily) /
                returns_series.rolling(window=window).std()
            ) * np.sqrt(252)

            return rolling_metrics.dropna()

        except Exception as e:
            self.logger.error(f"Error calculating rolling risk measures: {str(e)}")
            return pd.DataFrame()

    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown for a series of returns"""
        cumulative = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = (peak - cumulative) / peak
        return np.max(drawdown) if len(drawdown) > 0 else 0.0

    def export_risk_data(self, risk_assessment: RiskAssessment, format: str = "json") -> str:
        """Export risk assessment data"""
        try:
            if format.lower() == "json":
                import json
                data = {
                    "assessment_date": risk_assessment.assessment_date.isoformat(),
                    "overall_risk_score": risk_assessment.overall_risk_score,
                    "risk_level": risk_assessment.risk_level.value,
                    "risk_metrics": [
                        {
                            "name": metric.name,
                            "value": metric.value,
                            "category": metric.category.value,
                            "level": metric.level.value,
                            "description": metric.description
                        }
                        for metric in risk_assessment.risk_metrics
                    ],
                    "var_results": [
                        {
                            "confidence_level": var_result.confidence_level,
                            "var_value": var_result.var_value,
                            "expected_shortfall": var_result.expected_shortfall,
                            "method": var_result.method
                        }
                        for var_result in risk_assessment.var_results
                    ],
                    "stress_test_results": [
                        {
                            "scenario_name": stress_result.scenario_name,
                            "percentage_loss": stress_result.percentage_loss,
                            "recovery_period": stress_result.recovery_period
                        }
                        for stress_result in risk_assessment.stress_test_results
                    ],
                    "recommendations": risk_assessment.recommendations
                }
                return json.dumps(data, indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            self.logger.error(f"Error exporting risk data: {str(e)}")
            return ""