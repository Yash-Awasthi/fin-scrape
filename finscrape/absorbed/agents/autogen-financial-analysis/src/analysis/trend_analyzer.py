"""
Trend Analyzer
Comprehensive trend analysis for financial data and metrics
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from .financial_models import FinancialRatio, FinancialMetrics


class TrendDirection(Enum):
    """Trend direction enumeration"""
    STRONG_INCREASING = "strong_increasing"
    MODERATE_INCREASING = "moderate_increasing"
    STABLE = "stable"
    MODERATE_DECREASING = "moderate_decreasing"
    STRONG_DECREASING = "strong_decreasing"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    metric_name: str
    direction: TrendDirection
    magnitude: float
    confidence: float
    period: str
    start_value: Optional[float] = None
    end_value: Optional[float] = None
    percent_change: Optional[float] = None
    cagr: Optional[float] = None
    volatility: Optional[float] = None
    seasonality: Optional[Dict] = None
    forecast: Optional[Dict] = None
    turning_points: Optional[List[datetime]] = None


@dataclass
class ComparativeTrend:
    """Comparative trend analysis between multiple metrics"""
    base_metric: str
    comparison_metrics: List[str]
    correlation_matrix: Dict[str, float]
    lead_lag_relationships: Dict[str, int]
    divergence_points: List[datetime]
    convergence_points: List[datetime]


class TrendAnalyzer:
    """Comprehensive trend analysis for financial metrics"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.min_data_points = 3

    def analyze_trend(self, data_series: List[float], dates: List[datetime] = None,
                    metric_name: str = "Unknown", period: str = "annual") -> Optional[TrendAnalysis]:
        """Analyze trend in a time series"""
        if len(data_series) < self.min_data_points:
            return None

        try:
            # Basic trend calculations
            start_value = data_series[0]
            end_value = data_series[-1]
            percent_change = ((end_value - start_value) / start_value) * 100 if start_value != 0 else 0

            # Calculate CAGR
            periods = len(data_series) - 1
            cagr = self._calculate_cagr(start_value, end_value, periods)

            # Calculate volatility
            volatility = self._calculate_volatility(data_series)

            # Determine trend direction and magnitude
            direction, magnitude, confidence = self._determine_trend_characteristics(data_series, dates)

            # Detect turning points
            turning_points = self._detect_turning_points(data_series, dates)

            # Forecast future values
            forecast = self._generate_forecast(data_series, dates)

            return TrendAnalysis(
                metric_name=metric_name,
                direction=direction,
                magnitude=magnitude,
                confidence=confidence,
                period=period,
                start_value=start_value,
                end_value=end_value,
                percent_change=percent_change,
                cagr=cagr,
                volatility=volatility,
                seasonality=None,
                forecast=forecast,
                turning_points=turning_points
            )

        except Exception as e:
            self.logger.error(f"Error analyzing trend for {metric_name}: {str(e)}")
            return None

    def _calculate_cagr(self, start_value: float, end_value: float, periods: int) -> Optional[float]:
        """Calculate Compound Annual Growth Rate"""
        if start_value <= 0 or periods <= 0:
            return None

        try:
            return ((end_value / start_value) ** (1 / periods) - 1) * 100
        except Exception as e:
            self.logger.error(f"Error calculating CAGR: {str(e)}")
            return None

    def _calculate_volatility(self, data_series: List[float]) -> float:
        """Calculate volatility as coefficient of variation"""
        if len(data_series) < 2:
            return 0.0

        try:
            mean_val = np.mean(data_series)
            if mean_val == 0:
                return 0.0

            std_dev = np.std(data_series)
            return (std_dev / abs(mean_val)) * 100
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {str(e)}")
            return 0.0

    def _determine_trend_characteristics(self, data_series: List[float],
                                       dates: List[datetime] = None) -> Tuple[TrendDirection, float, float]:
        """Determine trend direction, magnitude, and confidence"""
        try:
            # Calculate linear regression
            x = np.arange(len(data_series)).reshape(-1, 1)
            y = np.array(data_series)

            model = LinearRegression()
            model.fit(x, y)

            slope = model.coef_[0]
            r_squared = model.score(x, y)

            # Normalize slope by mean value
            mean_value = np.mean(data_series)
            if mean_value != 0:
                normalized_slope = (slope / mean_value) * len(data_series)
            else:
                normalized_slope = slope

            # Determine direction
            if abs(normalized_slope) < 0.01:
                direction = TrendDirection.STABLE
            elif normalized_slope > 0.05:
                direction = TrendDirection.STRONG_INCREASING
            elif normalized_slope > 0.01:
                direction = TrendDirection.MODERATE_INCREASING
            elif normalized_slope < -0.05:
                direction = TrendDirection.STRONG_DECREASING
            else:
                direction = TrendDirection.MODERATE_DECREASING

            # Check for volatility
            volatility = self._calculate_volatility(data_series)
            if volatility > 30:
                direction = TrendDirection.VOLATILE

            confidence = max(0, min(1, r_squared))

            return direction, normalized_slope, confidence

        except Exception as e:
            self.logger.error(f"Error determining trend characteristics: {str(e)}")
            return TrendDirection.INSUFFICIENT_DATA, 0.0, 0.0

    def _detect_turning_points(self, data_series: List[float],
                             dates: List[datetime] = None) -> List[datetime]:
        """Detect turning points in the time series"""
        turning_points = []

        if len(data_series) < 3:
            return turning_points

        try:
            # Use second derivative to detect inflection points
            for i in range(1, len(data_series) - 1):
                prev_val = data_series[i-1]
                curr_val = data_series[i]
                next_val = data_series[i+1]

                # Check for local maximum or minimum
                if (curr_val > prev_val and curr_val > next_val) or \
                   (curr_val < prev_val and curr_val < next_val):
                    if dates and i < len(dates):
                        turning_points.append(dates[i])
                    else:
                        turning_points.append(i)

        except Exception as e:
            self.logger.error(f"Error detecting turning points: {str(e)}")

        return turning_points

    def _generate_forecast(self, data_series: List[float],
                         dates: List[datetime] = None, periods: int = 3) -> Optional[Dict]:
        """Generate simple forecast using linear regression"""
        if len(data_series) < 3:
            return None

        try:
            # Fit linear regression
            x = np.arange(len(data_series)).reshape(-1, 1)
            y = np.array(data_series)

            model = LinearRegression()
            model.fit(x, y)

            # Generate forecast
            last_x = len(data_series) - 1
            forecast_x = np.arange(last_x + 1, last_x + 1 + periods).reshape(-1, 1)
            forecast_y = model.predict(forecast_x)

            # Calculate confidence intervals (simplified)
            residuals = y - model.predict(x)
            mse = np.mean(residuals**2)
            std_error = np.sqrt(mse)

            forecast = {
                'values': forecast_y.tolist(),
                'confidence_lower': (forecast_y - 1.96 * std_error).tolist(),
                'confidence_upper': (forecast_y + 1.96 * std_error).tolist(),
                'method': 'linear_regression',
                'r_squared': model.score(x, y)
            }

            return forecast

        except Exception as e:
            self.logger.error(f"Error generating forecast: {str(e)}")
            return None

    def analyze_seasonality(self, data_series: List[float], dates: List[datetime]) -> Optional[Dict]:
        """Analyze seasonality patterns in the data"""
        if len(data_series) < 12:  # Need at least 1 year of monthly data
            return None

        try:
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame({'value': data_series, 'date': dates})
            df['month'] = df['date'].dt.month
            df['year'] = df['date'].dt.year

            # Calculate monthly averages
            monthly_avg = df.groupby('month')['value'].mean()
            overall_avg = df['value'].mean()

            # Calculate seasonal factors
            seasonal_factors = (monthly_avg / overall_avg).to_dict()

            # Test for seasonality using ANOVA
            anova_result = stats.f_oneway(*[df[df['month'] == m]['value'] for m in range(1, 13)])

            seasonality = {
                'seasonal_factors': seasonal_factors,
                'is_seasonal': anova_result.pvalue < 0.05,
                'seasonality_strength': anova_result.statistic,
                'p_value': anova_result.pvalue
            }

            return seasonality

        except Exception as e:
            self.logger.error(f"Error analyzing seasonality: {str(e)}")
            return None

    def compare_trends(self, metrics_data: Dict[str, List[float]],
                      dates: List[datetime] = None) -> Optional[ComparativeTrend]:
        """Compare trends between multiple metrics"""
        if len(metrics_data) < 2:
            return None

        try:
            metric_names = list(metrics_data.keys())
            base_metric = metric_names[0]
            comparison_metrics = metric_names[1:]

            # Calculate correlation matrix
            correlation_matrix = {}
            for metric in comparison_metrics:
                if len(metrics_data[base_metric]) == len(metrics_data[metric]):
                    correlation, _ = stats.pearsonr(metrics_data[base_metric], metrics_data[metric])
                    correlation_matrix[metric] = correlation

            # Analyze lead-lag relationships
            lead_lag_relationships = self._analyze_lead_lag(metrics_data)

            # Detect divergence and convergence points
            divergence_points = self._detect_divergence_points(metrics_data, dates)
            convergence_points = self._detect_convergence_points(metrics_data, dates)

            return ComparativeTrend(
                base_metric=base_metric,
                comparison_metrics=comparison_metrics,
                correlation_matrix=correlation_matrix,
                lead_lag_relationships=lead_lag_relationships,
                divergence_points=divergence_points,
                convergence_points=convergence_points
            )

        except Exception as e:
            self.logger.error(f"Error comparing trends: {str(e)}")
            return None

    def _analyze_lead_lag(self, metrics_data: Dict[str, List[float]]) -> Dict[str, int]:
        """Analyze lead-lag relationships between metrics"""
        lead_lag = {}
        base_metric = list(metrics_data.keys())[0]
        base_data = metrics_data[base_metric]

        for metric_name, metric_data in metrics_data.items():
            if metric_name == base_metric:
                continue

            try:
                max_lag = min(len(base_data), len(metric_data)) // 4
                correlations = []

                for lag in range(-max_lag, max_lag + 1):
                    if lag < 0:
                        # Negative lag means metric lags base
                        corr = np.corrcoef(base_data[:lag], metric_data[-lag:])[0, 1]
                    elif lag > 0:
                        # Positive lag means metric leads base
                        corr = np.corrcoef(base_data[lag:], metric_data[:-lag])[0, 1]
                    else:
                        corr = np.corrcoef(base_data, metric_data)[0, 1]

                    correlations.append((lag, corr))

                # Find lag with maximum correlation
                best_lag, best_corr = max(correlations, key=lambda x: abs(x[1]))
                lead_lag[metric_name] = best_lag

            except Exception as e:
                self.logger.error(f"Error analyzing lead-lag for {metric_name}: {str(e)}")
                lead_lag[metric_name] = 0

        return lead_lag

    def _detect_divergence_points(self, metrics_data: Dict[str, List[float]],
                                dates: List[datetime] = None) -> List[datetime]:
        """Detect points where metrics diverge from their historical correlation"""
        divergence_points = []

        if len(metrics_data) < 2:
            return divergence_points

        try:
            metric_names = list(metrics_data.keys())
            base_data = metrics_data[metric_names[0]]

            for i in range(1, len(base_data)):
                window_start = max(0, i - 12)  # Use 12-period window
                window_correlations = []

                for j in range(1, len(metric_names)):
                    metric_data = metrics_data[metric_names[j]]
                    if i < len(metric_data):
                        window_base = base_data[window_start:i+1]
                        window_metric = metric_data[window_start:i+1]

                        if len(window_base) > 1:
                            corr = np.corrcoef(window_base, window_metric)[0, 1]
                            window_correlations.append(corr)

                if window_correlations:
                    avg_correlation = np.mean(window_correlations)
                    if avg_correlation < 0.5:  # Low correlation threshold
                        if dates and i < len(dates):
                            divergence_points.append(dates[i])
                        else:
                            divergence_points.append(i)

        except Exception as e:
            self.logger.error(f"Error detecting divergence points: {str(e)}")

        return divergence_points

    def _detect_convergence_points(self, metrics_data: Dict[str, List[float]],
                                 dates: List[datetime] = None) -> List[datetime]:
        """Detect points where metrics converge to similar values"""
        convergence_points = []

        if len(metrics_data) < 2:
            return convergence_points

        try:
            metric_names = list(metrics_data.keys())

            for i in range(len(metrics_data[metric_names[0]])):
                values = []
                for metric_name in metric_names:
                    if i < len(metrics_data[metric_name]):
                        values.append(metrics_data[metric_name][i])

                if len(values) >= 2:
                    # Calculate coefficient of variation
                    cv = np.std(values) / np.mean(values) if np.mean(values) != 0 else 1
                    if cv < 0.1:  # Low variation threshold
                        if dates and i < len(dates):
                            convergence_points.append(dates[i])
                        else:
                            convergence_points.append(i)

        except Exception as e:
            self.logger.error(f"Error detecting convergence points: {str(e)}")

        return convergence_points

    def analyze_financial_trends(self, financial_metrics: FinancialMetrics,
                               historical_data: List[FinancialMetrics] = None) -> Dict[str, TrendAnalysis]:
        """Analyze trends for all financial metrics"""
        trend_analyses = {}

        if not historical_data or len(historical_data) < self.min_data_points:
            return trend_analyses

        try:
            # Extract time series data for each metric
            metric_series = self._extract_metric_series(financial_metrics, historical_data)

            # Analyze trends for each metric
            for metric_name, data_series in metric_series.items():
                dates = [metric.analysis_date for metric in historical_data if metric.analysis_date]
                trend_analysis = self.analyze_trend(
                    data_series, dates, metric_name, financial_metrics.data_period
                )
                if trend_analysis:
                    trend_analyses[metric_name] = trend_analysis

        except Exception as e:
            self.logger.error(f"Error analyzing financial trends: {str(e)}")

        return trend_analyses

    def _extract_metric_series(self, current_metrics: FinancialMetrics,
                             historical_data: List[FinancialMetrics]) -> Dict[str, List[float]]:
        """Extract time series data from historical metrics"""
        metric_series = {}

        # Combine current and historical data
        all_metrics = historical_data + [current_metrics]

        # Get all ratio fields
        ratio_fields = [field.name for field in current_metrics.__dataclass_fields__.values()
                       if field.type == Optional[FinancialRatio]]

        for field_name in ratio_fields:
            series = []
            for metrics in all_metrics:
                ratio = getattr(metrics, field_name, None)
                if ratio and ratio.value is not None:
                    series.append(ratio.value)
            if len(series) >= self.min_data_points:
                metric_series[field_name] = series

        return metric_series

    def generate_trend_report(self, trend_analyses: Dict[str, TrendAnalysis]) -> str:
        """Generate comprehensive trend analysis report"""
        if not trend_analyses:
            return "No trend analysis available"

        report = "Financial Trend Analysis Report\n"
        report += "=" * 50 + "\n\n"

        # Summary statistics
        increasing_trends = sum(1 for analysis in trend_analyses.values()
                               if analysis.direction in [TrendDirection.STRONG_INCREASING, TrendDirection.MODERATE_INCREASING])
        decreasing_trends = sum(1 for analysis in trend_analyses.values()
                               if analysis.direction in [TrendDirection.STRONG_DECREASING, TrendDirection.MODERATE_DECREASING])
        stable_trends = sum(1 for analysis in trend_analyses.values()
                           if analysis.direction == TrendDirection.STABLE)

        report += f"Summary:\n"
        report += f"- Total metrics analyzed: {len(trend_analyses)}\n"
        report += f"- Increasing trends: {increasing_trends}\n"
        report += f"- Decreasing trends: {decreasing_trends}\n"
        report += f"- Stable trends: {stable_trends}\n\n"

        # Detailed analysis for each metric
        for metric_name, analysis in trend_analyses.items():
            report += f"{metric_name.replace('_', ' ').title()}:\n"
            report += f"  Direction: {analysis.direction.value.replace('_', ' ').title()}\n"
            report += f"  Magnitude: {analysis.magnitude:.2f}%\n"
            report += f"  Confidence: {analysis.confidence:.1%}\n"
            report += f"  Period: {analysis.period}\n"

            if analysis.percent_change is not None:
                report += f"  Total Change: {analysis.percent_change:.1f}%\n"

            if analysis.cagr is not None:
                report += f"  CAGR: {analysis.cagr:.1f}%\n"

            if analysis.volatility is not None:
                report += f"  Volatility: {analysis.volatility:.1f}%\n"

            if analysis.turning_points:
                report += f"  Turning Points: {len(analysis.turning_points)}\n"

            if analysis.forecast:
                report += f"  Forecast (next 3 periods): {analysis.forecast['values']}\n"

            report += "\n"

        return report

    def export_trends_to_dataframe(self, trend_analyses: Dict[str, TrendAnalysis]) -> pd.DataFrame:
        """Export trend analyses to pandas DataFrame"""
        data = []
        for metric_name, analysis in trend_analyses.items():
            data.append({
                'metric': metric_name,
                'direction': analysis.direction.value,
                'magnitude': analysis.magnitude,
                'confidence': analysis.confidence,
                'period': analysis.period,
                'start_value': analysis.start_value,
                'end_value': analysis.end_value,
                'percent_change': analysis.percent_change,
                'cagr': analysis.cagr,
                'volatility': analysis.volatility,
                'turning_points_count': len(analysis.turning_points) if analysis.turning_points else 0
            })

        return pd.DataFrame(data)

    def detect_anomalies(self, data_series: List[float], threshold: float = 2.0) -> List[int]:
        """Detect anomalies in time series using statistical methods"""
        anomalies = []

        if len(data_series) < 5:
            return anomalies

        try:
            # Use Z-score method
            z_scores = np.abs(stats.zscore(data_series))
            anomalies = np.where(z_scores > threshold)[0].tolist()

            # Use IQR method for additional detection
            q1 = np.percentile(data_series, 25)
            q3 = np.percentile(data_series, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            for i, value in enumerate(data_series):
                if value < lower_bound or value > upper_bound:
                    if i not in anomalies:
                        anomalies.append(i)

        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {str(e)}")

        return anomalies

    def calculate_momentum(self, data_series: List[float], period: int = 3) -> List[float]:
        """Calculate momentum indicators for the time series"""
        if len(data_series) < period:
            return []

        try:
            momentum = []
            for i in range(period, len(data_series)):
                current_value = data_series[i]
                past_value = data_series[i - period]
                momentum_value = ((current_value - past_value) / past_value) * 100
                momentum.append(momentum_value)

            return momentum

        except Exception as e:
            self.logger.error(f"Error calculating momentum: {str(e)}")
            return []

    def calculate_moving_averages(self, data_series: List[float], periods: List[int] = None) -> Dict[int, List[float]]:
        """Calculate moving averages for specified periods"""
        if periods is None:
            periods = [3, 6, 12]

        moving_averages = {}

        try:
            for period in periods:
                if len(data_series) >= period:
                    ma = []
                    for i in range(period - 1, len(data_series)):
                        window = data_series[i - period + 1:i + 1]
                        ma.append(np.mean(window))
                    moving_averages[period] = ma

        except Exception as e:
            self.logger.error(f"Error calculating moving averages: {str(e)}")

        return moving_averages