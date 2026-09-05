"""
DuPont Analysis
Comprehensive DuPont analysis for decomposing return on equity
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from .financial_models import FinancialRatio, FinancialMetrics


@dataclass
class DuPontComponents:
    """DuPont analysis components"""
    net_profit_margin: float
    asset_turnover: float
    equity_multiplier: float
    roe: float

    # Extended DuPont components
    tax_burden: float
    interest_burden: float
    ebit_margin: float

    # Three-way decomposition
    operating_margin: float
    non_operating_margin: float


@dataclass
class DuPontAnalysis:
    """Complete DuPont analysis results"""
    symbol: str
    period: str
    components: DuPontComponents
    industry_comparison: Optional[Dict[str, float]] = None
    trend_analysis: Optional[Dict[str, str]] = None
    decomposition_quality: float = 0.0
    insights: List[str] = None

    def __post_init__(self):
        if self.insights is None:
            self.insights = []


class DuPontAnalyzer:
    """Comprehensive DuPont analysis calculator"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.industry_benchmarks = self._load_industry_benchmarks()

    def _load_industry_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Load industry benchmark data for DuPont components"""
        return {
            "Technology": {
                "net_profit_margin": 15.0,
                "asset_turnover": 0.8,
                "equity_multiplier": 1.5,
                "roe": 18.0
            },
            "Manufacturing": {
                "net_profit_margin": 8.0,
                "asset_turnover": 1.2,
                "equity_multiplier": 2.0,
                "roe": 19.2
            },
            "Finance": {
                "net_profit_margin": 12.0,
                "asset_turnover": 0.1,
                "equity_multiplier": 10.0,
                "roe": 12.0
            },
            "Healthcare": {
                "net_profit_margin": 20.0,
                "asset_turnover": 0.6,
                "equity_multiplier": 1.8,
                "roe": 21.6
            },
            "Retail": {
                "net_profit_margin": 5.0,
                "asset_turnover": 2.0,
                "equity_multiplier": 2.5,
                "roe": 25.0
            }
        }

    def calculate_basic_dupont(self, financial_data: Dict) -> Optional[DuPontComponents]:
        """Calculate basic three-way DuPont analysis"""
        try:
            # Extract required data
            net_income = financial_data.get('net_income', 0)
            revenue = financial_data.get('revenue', 1)
            total_assets = financial_data.get('total_assets', 1)
            shareholders_equity = financial_data.get('shareholders_equity', 1)

            # Calculate components
            net_profit_margin = (net_income / revenue) * 100 if revenue > 0 else 0
            asset_turnover = revenue / total_assets if total_assets > 0 else 0
            equity_multiplier = total_assets / shareholders_equity if shareholders_equity > 0 else 1

            # Calculate ROE
            roe = net_profit_margin * asset_turnover * equity_multiplier / 100

            return DuPontComponents(
                net_profit_margin=net_profit_margin,
                asset_turnover=asset_turnover,
                equity_multiplier=equity_multiplier,
                roe=roe,
                tax_burden=0,
                interest_burden=0,
                ebit_margin=0,
                operating_margin=0,
                non_operating_margin=0
            )

        except Exception as e:
            self.logger.error(f"Error calculating basic DuPont analysis: {str(e)}")
            return None

    def calculate_extended_dupont(self, financial_data: Dict) -> Optional[DuPontComponents]:
        """Calculate extended five-way DuPont analysis"""
        try:
            # Extract required data
            net_income = financial_data.get('net_income', 0)
            ebt = financial_data.get('ebt', 1)  # Earnings Before Tax
            ebit = financial_data.get('ebit', 1)  # Earnings Before Interest and Taxes
            revenue = financial_data.get('revenue', 1)
            total_assets = financial_data.get('total_assets', 1)
            shareholders_equity = financial_data.get('shareholders_equity', 1)

            # Calculate extended components
            tax_burden = net_income / ebt if ebt > 0 else 1
            interest_burden = ebt / ebit if ebit > 0 else 1
            ebit_margin = (ebit / revenue) * 100 if revenue > 0 else 0
            asset_turnover = revenue / total_assets if total_assets > 0 else 0
            equity_multiplier = total_assets / shareholders_equity if shareholders_equity > 0 else 1

            # Calculate ROE
            roe = tax_burden * interest_burden * ebit_margin * asset_turnover * equity_multiplier

            return DuPontComponents(
                net_profit_margin=(net_income / revenue) * 100 if revenue > 0 else 0,
                asset_turnover=asset_turnover,
                equity_multiplier=equity_multiplier,
                roe=roe,
                tax_burden=tax_burden,
                interest_burden=interest_burden,
                ebit_margin=ebit_margin,
                operating_margin=0,
                non_operating_margin=0
            )

        except Exception as e:
            self.logger.error(f"Error calculating extended DuPont analysis: {str(e)}")
            return None

    def calculate_detailed_dupont(self, financial_data: Dict) -> Optional[DuPontComponents]:
        """Calculate detailed DuPont analysis with operating/non-operating breakdown"""
        try:
            # Extract detailed data
            net_income = financial_data.get('net_income', 0)
            operating_income = financial_data.get('operating_income', 0)
            non_operating_income = financial_data.get('non_operating_income', 0)
            revenue = financial_data.get('revenue', 1)
            total_assets = financial_data.get('total_assets', 1)
            shareholders_equity = financial_data.get('shareholders_equity', 1)

            # Calculate detailed components
            operating_margin = (operating_income / revenue) * 100 if revenue > 0 else 0
            non_operating_margin = (non_operating_income / revenue) * 100 if revenue > 0 else 0
            asset_turnover = revenue / total_assets if total_assets > 0 else 0
            equity_multiplier = total_assets / shareholders_equity if shareholders_equity > 0 else 1

            # Calculate ROE
            total_margin = operating_margin + non_operating_margin
            roe = total_margin * asset_turnover * equity_multiplier / 100

            return DuPontComponents(
                net_profit_margin=total_margin,
                asset_turnover=asset_turnover,
                equity_multiplier=equity_multiplier,
                roe=roe,
                tax_burden=0,
                interest_burden=0,
                ebit_margin=0,
                operating_margin=operating_margin,
                non_operating_margin=non_operating_margin
            )

        except Exception as e:
            self.logger.error(f"Error calculating detailed DuPont analysis: {str(e)}")
            return None

    def analyze_dupont_trends(self, historical_data: List[Dict]) -> Optional[Dict[str, str]]:
        """Analyze trends in DuPont components over time"""
        if len(historical_data) < 2:
            return None

        try:
            # Calculate DuPont components for each period
            components_history = []
            for period_data in historical_data:
                components = self.calculate_basic_dupont(period_data)
                if components:
                    components_history.append(components)

            if len(components_history) < 2:
                return None

            # Analyze trends
            trends = {}
            latest = components_history[-1]
            previous = components_history[-2]

            # Analyze each component
            component_names = ['net_profit_margin', 'asset_turnover', 'equity_multiplier', 'roe']

            for component in component_names:
                latest_value = getattr(latest, component)
                previous_value = getattr(previous, component)

                if latest_value > previous_value * 1.05:
                    trends[component] = "Increasing"
                elif latest_value < previous_value * 0.95:
                    trends[component] = "Decreasing"
                else:
                    trends[component] = "Stable"

            return trends

        except Exception as e:
            self.logger.error(f"Error analyzing DuPont trends: {str(e)}")
            return None

    def compare_to_industry(self, components: DuPontComponents, industry: str) -> Dict[str, float]:
        """Compare DuPont components to industry benchmarks"""
        comparison = {}

        if industry not in self.industry_benchmarks:
            return comparison

        benchmarks = self.industry_benchmarks[industry]

        # Calculate relative performance
        component_mapping = {
            'net_profit_margin': 'net_profit_margin',
            'asset_turnover': 'asset_turnover',
            'equity_multiplier': 'equity_multiplier',
            'roe': 'roe'
        }

        for component, benchmark_key in component_mapping.items():
            if hasattr(components, component) and benchmark_key in benchmarks:
                actual_value = getattr(components, component)
                benchmark_value = benchmarks[benchmark_key]

                if benchmark_value > 0:
                    comparison[component] = (actual_value / benchmark_value) * 100
                else:
                    comparison[component] = 100

        return comparison

    def generate_dupont_insights(self, components: DuPontComponents,
                               industry_comparison: Optional[Dict] = None,
                               trend_analysis: Optional[Dict] = None) -> List[str]:
        """Generate insights from DuPont analysis"""
        insights = []

        # ROE analysis
        if components.roe > 20:
            insights.append("Exceptional ROE performance indicates strong value creation")
        elif components.roe > 15:
            insights.append("Strong ROE performance above market average")
        elif components.roe > 10:
            insights.append("Moderate ROE performance - room for improvement")
        elif components.roe > 0:
            insights.append("Low ROE performance - investigate profitability drivers")
        else:
            insights.append("Negative ROE - urgent attention required")

        # Profit margin analysis
        if components.net_profit_margin > 20:
            insights.append("High profit margin suggests strong pricing power or cost control")
        elif components.net_profit_margin > 10:
            insights.append("Solid profit margin indicates good operational efficiency")
        elif components.net_profit_margin > 5:
            insights.append("Moderate profit margin - competitive pressure may exist")
        elif components.net_profit_margin > 0:
            insights.append("Low profit margin - consider cost reduction or price optimization")

        # Asset turnover analysis
        if components.asset_turnover > 2:
            insights.append("High asset turnover indicates efficient asset utilization")
        elif components.asset_turnover > 1:
            insights.append("Good asset turnover efficiency")
        elif components.asset_turnover > 0.5:
            insights.append("Moderate asset turnover - potential for optimization")
        else:
            insights.append("Low asset turnover suggests underutilized assets")

        # Leverage analysis
        if components.equity_multiplier > 3:
            insights.append("High leverage - monitor financial risk")
        elif components.equity_multiplier > 2:
            insights.append("Moderate leverage - acceptable within industry norms")
        elif components.equity_multiplier > 1.5:
            insights.append("Conservative leverage - strong financial position")
        else:
            insights.append("Very low leverage - potential underutilization of debt capacity")

        # Extended analysis if available
        if components.tax_burden > 0:
            if components.tax_burden < 0.7:
                insights.append("High tax burden - consider tax optimization strategies")
            elif components.tax_burden > 0.8:
                insights.append("Efficient tax management")

        if components.interest_burden > 0:
            if components.interest_burden < 0.8:
                insights.append("High interest burden - evaluate debt structure")
            elif components.interest_burden > 0.95:
                insights.append("Low interest burden - healthy debt structure")

        # Industry comparison
        if industry_comparison:
            for component, relative_performance in industry_comparison.items():
                if relative_performance > 120:
                    insights.append(f"Superior {component} compared to industry peers")
                elif relative_performance < 80:
                    insights.append(f"{component} underperforms industry benchmarks")

        # Trend analysis
        if trend_analysis:
            for component, trend in trend_analysis.items():
                if trend == "Increasing":
                    if component in ['net_profit_margin', 'asset_turnover', 'roe']:
                        insights.append(f"Improving {component} trend")
                    elif component == 'equity_multiplier':
                        insights.append(f"Increasing leverage trend - monitor risk")
                elif trend == "Decreasing":
                    if component in ['net_profit_margin', 'asset_turnover', 'roe']:
                        insights.append(f"Declining {component} requires attention")
                    elif component == 'equity_multiplier':
                        insights.append(f"Decreasing leverage trend - conservative approach")

        return insights

    def calculate_dupont_analysis(self, financial_data: Dict,
                                 historical_data: List[Dict] = None,
                                 industry: str = None,
                                 symbol: str = None,
                                 period: str = "annual") -> Optional[DuPontAnalysis]:
        """Perform complete DuPont analysis"""
        try:
            # Calculate detailed DuPont components
            components = self.calculate_detailed_dupont(financial_data)
            if not components:
                return None

            # Extended analysis if basic is available
            if components.net_profit_margin == 0:  # Fallback to extended if detailed failed
                components = self.calculate_extended_dupont(financial_data)
            if not components.net_profit_margin:  # Fallback to basic if extended failed
                components = self.calculate_basic_dupont(financial_data)

            # Industry comparison
            industry_comparison = None
            if industry:
                industry_comparison = self.compare_to_industry(components, industry)

            # Trend analysis
            trend_analysis = None
            if historical_data and len(historical_data) > 1:
                trend_analysis = self.analyze_dupont_trends(historical_data)

            # Generate insights
            insights = self.generate_dupont_insights(components, industry_comparison, trend_analysis)

            # Calculate decomposition quality
            decomposition_quality = self._calculate_decomposition_quality(components)

            return DuPontAnalysis(
                symbol=symbol or "UNKNOWN",
                period=period,
                components=components,
                industry_comparison=industry_comparison,
                trend_analysis=trend_analysis,
                decomposition_quality=decomposition_quality,
                insights=insights
            )

        except Exception as e:
            self.logger.error(f"Error performing DuPont analysis: {str(e)}")
            return None

    def _calculate_decomposition_quality(self, components: DuPontComponents) -> float:
        """Calculate the quality of DuPont decomposition"""
        try:
            # Check if the decomposition is mathematically sound
            calculated_roe = (components.net_profit_margin * components.asset_turnover *
                            components.equity_multiplier) / 100

            # Compare with actual ROE
            roe_difference = abs(calculated_roe - components.roe)

            # Quality score based on mathematical accuracy
            if roe_difference < 0.1:
                quality_score = 1.0
            elif roe_difference < 1.0:
                quality_score = 0.8
            elif roe_difference < 5.0:
                quality_score = 0.6
            else:
                quality_score = 0.4

            # Adjust for component reasonableness
            if (components.net_profit_margin < -50 or components.net_profit_margin > 100):
                quality_score *= 0.7

            if (components.asset_turnover < 0 or components.asset_turnover > 10):
                quality_score *= 0.7

            if (components.equity_multiplier < 0.5 or components.equity_multiplier > 20):
                quality_score *= 0.7

            return max(quality_score, 0.0)

        except Exception as e:
            self.logger.error(f"Error calculating decomposition quality: {str(e)}")
            return 0.0

    def create_dupont_report(self, analysis: DuPontAnalysis) -> str:
        """Create a detailed DuPont analysis report"""
        if not analysis:
            return "No DuPont analysis available"

        report = f"""
DuPont Analysis Report for {analysis.symbol}
===========================================

Period: {analysis.period}

Three-Way DuPont Decomposition:
- ROE = Net Profit Margin × Asset Turnover × Equity Multiplier
- {analysis.components.roe:.2f}% = {analysis.components.net_profit_margin:.2f}% × {analysis.components.asset_turnover:.2f} × {analysis.components.equity_multiplier:.2f}

Component Analysis:
"""

        # Add detailed component analysis
        report += f"""
1. Net Profit Margin: {analysis.components.net_profit_margin:.2f}%
   - Shows profitability after all expenses
   - Higher margins indicate better pricing power or cost control

2. Asset Turnover: {analysis.components.asset_turnover:.2f}
   - Measures efficiency of asset utilization
   - Higher ratios indicate more efficient use of assets

3. Equity Multiplier: {analysis.components.equity_multiplier:.2f}
   - Indicates financial leverage
   - Higher ratios show more debt financing
"""

        # Add extended analysis if available
        if analysis.components.tax_burden > 0:
            report += f"""
Extended DuPont Analysis:
- Tax Burden: {analysis.components.tax_burden:.2f}
- Interest Burden: {analysis.components.interest_burden:.2f}
- EBIT Margin: {analysis.components.ebit_margin:.2f}%
"""

        # Add detailed analysis if available
        if analysis.components.operating_margin > 0:
            report += f"""
Detailed Analysis:
- Operating Margin: {analysis.components.operating_margin:.2f}%
- Non-Operating Margin: {analysis.components.non_operating_margin:.2f}%
"""

        # Add industry comparison
        if analysis.industry_comparison:
            report += "\nIndustry Comparison (% of Industry Average):\n"
            for component, performance in analysis.industry_comparison.items():
                report += f"- {component.replace('_', ' ').title()}: {performance:.0f}%\n"

        # Add trend analysis
        if analysis.trend_analysis:
            report += "\nTrend Analysis:\n"
            for component, trend in analysis.trend_analysis.items():
                report += f"- {component.replace('_', ' ').title()}: {trend}\n"

        # Add insights
        if analysis.insights:
            report += "\nKey Insights:\n"
            for i, insight in enumerate(analysis.insights, 1):
                report += f"{i}. {insight}\n"

        # Add quality assessment
        report += f"\nAnalysis Quality Score: {analysis.decomposition_quality:.1%}"

        return report

    def export_dupont_to_dataframe(self, analysis: DuPontAnalysis) -> pd.DataFrame:
        """Export DuPont analysis to pandas DataFrame"""
        data = {
            'symbol': [analysis.symbol],
            'period': [analysis.period],
            'roe': [analysis.components.roe],
            'net_profit_margin': [analysis.components.net_profit_margin],
            'asset_turnover': [analysis.components.asset_turnover],
            'equity_multiplier': [analysis.components.equity_multiplier],
            'tax_burden': [analysis.components.tax_burden],
            'interest_burden': [analysis.components.interest_burden],
            'ebit_margin': [analysis.components.ebit_margin],
            'operating_margin': [analysis.components.operating_margin],
            'non_operating_margin': [analysis.components.non_operating_margin],
            'quality_score': [analysis.decomposition_quality]
        }

        return pd.DataFrame(data)

    def calculate_roe_drivers(self, components: DuPontComponents) -> Dict[str, float]:
        """Calculate the relative contribution of each component to ROE"""
        try:
            # Calculate logarithmic contributions (for multiplicative relationships)
            log_contribution = {}

            if components.net_profit_margin > 0:
                log_contribution['net_profit_margin'] = np.log(components.net_profit_margin)

            if components.asset_turnover > 0:
                log_contribution['asset_turnover'] = np.log(components.asset_turnover)

            if components.equity_multiplier > 0:
                log_contribution['equity_multiplier'] = np.log(components.equity_multiplier)

            # Convert to percentage contributions
            total_log = sum(log_contribution.values())
            if total_log != 0:
                percentage_contributions = {
                    k: (v / total_log) * 100 for k, v in log_contribution.items()
                }
            else:
                percentage_contributions = {
                    k: 33.33 for k in log_contribution.keys()
                }

            return percentage_contributions

        except Exception as e:
            self.logger.error(f"Error calculating ROE drivers: {str(e)}")
            return {}

    def simulate_dupont_scenarios(self, base_components: DuPontComponents,
                                 scenarios: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Simulate ROE under different scenarios"""
        scenario_results = {}

        for scenario_name, changes in scenarios.items():
            try:
                # Apply changes to base components
                simulated_margin = base_components.net_profit_margin * (1 + changes.get('margin_change', 0))
                simulated_turnover = base_components.asset_turnover * (1 + changes.get('turnover_change', 0))
                simulated_multiplier = base_components.equity_multiplier * (1 + changes.get('multiplier_change', 0))

                # Calculate simulated ROE
                simulated_roe = (simulated_margin * simulated_turnover * simulated_multiplier) / 100
                scenario_results[scenario_name] = simulated_roe

            except Exception as e:
                self.logger.error(f"Error simulating scenario {scenario_name}: {str(e)}")
                scenario_results[scenario_name] = None

        return scenario_results