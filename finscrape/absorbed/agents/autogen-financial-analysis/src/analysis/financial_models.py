"""
Financial Analysis Models
Structured data models for financial analysis results
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal
import pandas as pd


@dataclass
class FinancialRatio:
    """Financial ratio data class"""
    name: str
    value: float
    unit: str = "%"
    description: str = ""
    benchmark: Optional[float] = None
    percentile: Optional[float] = None
    trend: Optional[str] = None
    category: str = "general"
    calculation_method: str = ""
    confidence_level: Optional[float] = None
    data_quality_score: float = 1.0

    def __post_init__(self):
        # Validate value range
        if self.unit == "%" and not -1000 <= self.value <= 1000:
            raise ValueError(f"Percentage ratio {self.name} has unreasonable value: {self.value}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
            "benchmark": self.benchmark,
            "percentile": self.percentile,
            "trend": self.trend,
            "category": self.category,
            "calculation_method": self.calculation_method,
            "confidence_level": self.confidence_level,
            "data_quality_score": self.data_quality_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinancialRatio':
        """Create from dictionary"""
        return cls(**data)

    def get_grade(self) -> str:
        """Get performance grade based on percentile"""
        if self.percentile is None:
            return "N/A"

        if self.percentile >= 90:
            return "A+"
        elif self.percentile >= 80:
            return "A"
        elif self.percentile >= 70:
            return "B+"
        elif self.percentile >= 60:
            return "B"
        elif self.percentile >= 50:
            return "C+"
        elif self.percentile >= 40:
            return "C"
        elif self.percentile >= 30:
            return "D"
        else:
            return "F"

    def is_favorable(self) -> Optional[bool]:
        """Determine if higher value is favorable for this ratio"""
        favorable_ratios = {
            "ROE", "ROA", "gross_margin", "net_margin", "current_ratio", "quick_ratio",
            "asset_turnover", "inventory_turnover", "receivables_turnover", "debt_ratio"
        }

        ratio_name_lower = self.name.lower()
        if any(fav in ratio_name_lower for fav in ["roe", "roa", "margin", "turnover"]):
            return True
        elif any(fav in ratio_name_lower for fav in ["debt", "liability"]):
            return False
        else:
            return None


@dataclass
class FinancialMetrics:
    """Comprehensive financial metrics container"""
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    analysis_date: Optional[datetime] = None

    # Profitability Ratios
    roe: Optional[FinancialRatio] = None
    roa: Optional[FinancialRatio] = None
    gross_margin: Optional[FinancialRatio] = None
    net_margin: Optional[FinancialRatio] = None
    ebit_margin: Optional[FinancialRatio] = None
    operating_margin: Optional[FinancialRatio] = None
    return_on_equity: Optional[FinancialRatio] = None
    return_on_assets: Optional[FinancialRatio] = None
    return_on_invested_capital: Optional[FinancialRatio] = None

    # Liquidity Ratios
    current_ratio: Optional[FinancialRatio] = None
    quick_ratio: Optional[FinancialRatio] = None
    cash_ratio: Optional[FinancialRatio] = None
    working_capital_ratio: Optional[FinancialRatio] = None
    operating_cash_flow_ratio: Optional[FinancialRatio] = None

    # Efficiency Ratios
    asset_turnover: Optional[FinancialRatio] = None
    inventory_turnover: Optional[FinancialRatio] = None
    receivables_turnover: Optional[FinancialRatio] = None
    payables_turnover: Optional[FinancialRatio] = None
    working_capital_turnover: Optional[FinancialRatio] = None
    fixed_asset_turnover: Optional[FinancialRatio] = None

    # Leverage Ratios
    debt_to_equity: Optional[FinancialRatio] = None
    debt_to_assets: Optional[FinancialRatio] = None
    equity_multiplier: Optional[FinancialRatio] = None
    interest_coverage: Optional[FinancialRatio] = None
    debt_service_coverage: Optional[FinancialRatio] = None

    # Growth Ratios
    revenue_growth: Optional[FinancialRatio] = None
    earnings_growth: Optional[FinancialRatio] = None
    book_value_growth: Optional[FinancialRatio] = None
    cash_flow_growth: Optional[FinancialRatio] = None

    # Market Ratios
    price_to_earnings: Optional[FinancialRatio] = None
    price_to_book: Optional[FinancialRatio] = None
    price_to_sales: Optional[FinancialRatio] = None
    price_to_cash_flow: Optional[FinancialRatio] = None
    dividend_yield: Optional[FinancialRatio] = None
    earnings_yield: Optional[FinancialRatio] = None

    # Cash Flow Ratios
    operating_cash_flow_to_sales: Optional[FinancialRatio] = None
    free_cash_flow_to_sales: Optional[FinancialRatio] = None
    capital_expenditure_ratio: Optional[FinancialRatio] = None
    cash_flow_to_debt: Optional[FinancialRatio] = None

    # Additional Metrics
    altman_z_score: Optional[FinancialRatio] = None
    piotroski_score: Optional[FinancialRatio] = None
    beneish_m_score: Optional[FinancialRatio] = None

    # Quality Scores
    overall_quality_score: float = 0.0
    profitability_score: float = 0.0
    liquidity_score: float = 0.0
    efficiency_score: float = 0.0
    leverage_score: float = 0.0
    growth_score: float = 0.0

    # Analysis Metadata
    data_period: str = "annual"
    currency: str = "USD"
    data_sources: List[str] = field(default_factory=list)
    calculation_methods: Dict[str, str] = field(default_factory=dict)
    confidence_level: float = 1.0
    data_quality_score: float = 1.0

    def __post_init__(self):
        if self.analysis_date is None:
            self.analysis_date = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "sector": self.sector,
            "industry": self.industry,
            "analysis_date": self.analysis_date.isoformat() if self.analysis_date else None,
            "data_period": self.data_period,
            "currency": self.currency,
            "data_sources": self.data_sources,
            "calculation_methods": self.calculation_methods,
            "confidence_level": self.confidence_level,
            "data_quality_score": self.data_quality_score,
            "overall_quality_score": self.overall_quality_score,
            "profitability_score": self.profitability_score,
            "liquidity_score": self.liquidity_score,
            "efficiency_score": self.efficiency_score,
            "leverage_score": self.leverage_score,
            "growth_score": self.growth_score
        }

        # Add all ratio fields
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, FinancialRatio) and field_name not in ["overall_quality_score"]:
                result[field_name] = field_value.to_dict()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinancialMetrics':
        """Create from dictionary"""
        # Create instance without ratios first
        basic_fields = {
            k: v for k, v in data.items()
            if k not in [f.name for f in cls.__dataclass_fields__.values()
                         if f.type == Optional[FinancialRatio]]
        }

        instance = cls(**basic_fields)

        # Add ratio fields
        for field_name, field_value in data.items():
            if field_name in instance.__dict__ and isinstance(instance.__dict__[field_name], type(None)):
                if field_value and isinstance(field_value, dict):
                    setattr(instance, field_name, FinancialRatio.from_dict(field_value))

        return instance

    def get_all_ratios(self) -> List[FinancialRatio]:
        """Get all calculated ratios"""
        ratios = []
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, FinancialRatio):
                ratios.append(field_value)
        return sorted(ratios, key=lambda x: x.category)

    def get_ratios_by_category(self, category: str) -> List[FinancialRatio]:
        """Get ratios filtered by category"""
        return [ratio for ratio in self.get_all_ratios() if ratio.category == category]

    def get_key_metrics(self) -> Dict[str, float]:
        """Get key financial metrics for summary"""
        return {
            "ROE": self.roe.value if self.roe else None,
            "ROA": self.roa.value if self.roa else None,
            "Gross Margin": self.gross_margin.value if self.gross_margin else None,
            "Net Margin": self.net_margin.value if self.net_margin else None,
            "Current Ratio": self.current_ratio.value if self.current_ratio else None,
            "Debt to Equity": self.debt_to_equity.value if self.debt_to_equity else None,
            "Asset Turnover": self.asset_turnover.value if self.asset_turnover else None,
            "Quality Score": self.overall_quality_score
        }

    def calculate_z_score(self) -> Optional[float]:
        """Calculate Altman Z-Score"""
        # Z = 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 1.0X5
        # X1 = Working Capital / Total Assets
        # X2 = Retained Earnings / Total Assets
        # X3 = EBIT / Total Assets
        # X4 = Market Value of Equity / Total Liabilities
        # X5 = Sales / Total Assets

        # This would require additional data from financial statements
        # For now, return the pre-calculated value if available
        return self.altman_z_score.value if self.altman_z_score else None

    def get_distress_signals(self) -> List[str]:
        """Get potential financial distress signals"""
        signals = []

        # Low profitability
        if self.roe and self.roe.value < 5:
            signals.append(f"Low ROE: {self.roe.value:.1f}%")
        if self.net_margin and self.net_margin.value < 2:
            signals.append(f"Low net margin: {self.net_margin.value:.1f}%")

        # Liquidity issues
        if self.current_ratio and self.current_ratio.value < 1.0:
            signals.append(f"Low current ratio: {self.current_ratio.value:.2f}")
        if self.quick_ratio and self.quick_ratio.value < 0.5:
            signals.append(f"Low quick ratio: {self.quick_ratio.value:.2f}")

        # High leverage
        if self.debt_to_equity and self.debt_to_equity.value > 2.0:
            signals.append(f"High debt-to-equity: {self.debt_to_equity.value:.2f}")
        if self.debt_to_assets and self.debt_to_assets.value > 0.7:
            signals.append(f"High debt-to-assets: {self.debt_to_assets.value:.1f}%")

        # Negative growth
        if self.revenue_growth and self.revenue_growth.value < 0:
            signals.append(f"Negative revenue growth: {self.revenue_growth.value:.1f}%")
        if self.earnings_growth and self.earnings_growth.value < -10:
            signals.append(f"Significant earnings decline: {self.earnings_growth.value:.1f}%")

        return signals

    def get_strengths(self) -> List[str]:
        """Get financial strengths"""
        strengths = []

        # High profitability
        if self.roe and self.roe.value > 15:
            strengths.append(f"Strong ROE: {self.roe.value:.1f}%")
        if self.net_margin and self.net_margin.value > 15:
            strengths.append(f"High net margin: {self.net_margin.value:.1f}%")

        # Strong liquidity
        if self.current_ratio and self.current_ratio.value > 2.0:
            strengths.append(f"Strong current ratio: {self.current_ratio.value:.2f}")
        if self.quick_ratio and self.quick_ratio.value > 1.5:
            strengths.append(f"Strong quick ratio: {self.quick_ratio.value:.2f}")

        # Efficient operations
        if self.asset_turnover and self.asset_turnover.value > 1.5:
            strengths.append(f"High asset turnover: {self.asset_turnover.value:.2f}")
        if self.inventory_turnover and self.inventory_turnover.value > 6:
            strengths.append(f"High inventory turnover: {self.inventory_turnover.value:.1f}")

        # Low leverage
        if self.debt_to_equity and self.debt_to_equity.value < 0.5:
            strengths.append(f"Low debt-to-equity: {self.debt_to_equity.value:.2f}")

        # Strong growth
        if self.revenue_growth and self.revenue_growth.value > 10:
            strengths.append(f"Strong revenue growth: {self.revenue_growth.value:.1f}%")
        if self.earnings_growth and self.earnings_growth.value > 15:
            strengths.append(f"Strong earnings growth: {self.earnings_growth.value:.1f}%")

        return strengths

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for analysis"""
        ratios_data = []
        for ratio in self.get_all_ratios():
            ratios_data.append({
                "name": ratio.name,
                "value": ratio.value,
                "unit": ratio.unit,
                "category": ratio.category,
                "benchmark": ratio.benchmark,
                "percentile": ratio.percentile,
                "trend": ratio.trend,
                "grade": ratio.get_grade(),
                "is_favorable": ratio.is_favorable()
            })

        return pd.DataFrame(ratios_data)

    def generate_summary(self) -> str:
        """Generate text summary of financial analysis"""
        summary = f"Financial Analysis Summary for {self.symbol}\n"
        summary += "=" * 50 + "\n\n"

        # Overall assessment
        if self.overall_quality_score > 0.8:
            summary += "Overall Financial Health: EXCELLENT\n"
        elif self.overall_quality_score > 0.6:
            summary += "Overall Financial Health: GOOD\n"
        elif self.overall_quality_score > 0.4:
            summary += "Overall Financial Health: FAIR\n"
        else:
            summary += "Overall Financial Health: POOR\n"

        summary += f"Quality Score: {self.overall_quality_score:.1%}\n\n"

        # Key strengths
        strengths = self.get_strengths()
        if strengths:
            summary += "Key Strengths:\n"
            for strength in strengths:
                summary += f"  ✓ {strength}\n"
            summary += "\n"

        # Areas of concern
        distress_signals = self.get_distress_signals()
        if distress_signals:
            summary += "Areas of Concern:\n"
            for signal in distress_signals:
                summary += f"  ⚠ {signal}\n"
            summary += "\n"

        # Key metrics
        key_metrics = self.get_key_metrics()
        summary += "Key Financial Metrics:\n"
        for metric, value in key_metrics.items():
            if value is not None:
                summary += f"  {metric}: {value:.2f}\n"

        return summary

    def compare_to_industry(self, industry_benchmarks: Dict[str, float]) -> Dict[str, str]:
        """Compare metrics to industry benchmarks"""
        comparison = {}

        for ratio_name, benchmark_value in industry_benchmarks.items():
            ratio = getattr(self, ratio_name.lower().replace(" ", "_").replace("/", "_"), None)
            if ratio and ratio.value is not None:
                if ratio.value > benchmark_value * 1.1:
                    comparison[ratio_name] = "Above Average"
                elif ratio.value < benchmark_value * 0.9:
                    comparison[ratio_name] = "Below Average"
                else:
                    comparison[ratio_name] = "Average"

        return comparison