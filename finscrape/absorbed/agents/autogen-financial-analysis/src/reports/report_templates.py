"""
Report Templates
Pre-built report templates for various financial analysis scenarios
"""

import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from .report_generator import ReportTemplate, ReportSection, ReportConfig, ReportType, ReportFormat

logger = logging.getLogger(__name__)


@dataclass
class TemplateVariable:
    """Template variable definition"""
    name: str
    description: str
    data_type: str
    required: bool = True
    default_value: Any = None


class FinancialReportTemplate:
    """Financial analysis report template"""

    def __init__(self):
        self.name = "Financial Analysis Report"
        self.description = "Comprehensive financial analysis with ratios and trends"
        self.variables = self._define_variables()
        self.sections = self._create_sections()

    def _define_variables(self) -> List[TemplateVariable]:
        """Define template variables"""
        return [
            TemplateVariable("company_name", "Company name", "string", True),
            TemplateVariable("analysis_period", "Analysis period", "string", True, "5 years"),
            TemplateVariable("revenue_data", "Revenue data", "dict", True),
            TemplateVariable("profit_data", "Profit data", "dict", True),
            TemplateVariable("balance_sheet_data", "Balance sheet data", "dict", True),
            TemplateVariable("cash_flow_data", "Cash flow data", "dict", True),
            TemplateVariable("financial_ratios", "Financial ratios", "dict", True),
            TemplateVariable("industry_benchmarks", "Industry benchmarks", "dict", False),
            TemplateVariable("analyst_recommendations", "Analyst recommendations", "string", False)
        ]

    def _create_sections(self) -> List[ReportSection]:
        """Create report sections"""
        return [
            ReportSection(
                title="Executive Summary",
                content="This report provides a comprehensive analysis of {{company_name}}'s financial performance over the {{analysis_period}} period. Key findings and recommendations are summarized below.",
                section_type="summary",
                order=1
            ),
            ReportSection(
                title="Company Overview",
                content="{{company_name}} operates in the [industry sector] with a focus on [business description]. The analysis covers financial performance metrics, operational efficiency, and strategic positioning.",
                section_type="overview",
                order=2
            ),
            ReportSection(
                title="Revenue Analysis",
                content="Revenue analysis shows the company's top-line performance over the analysis period.",
                section_type="revenue",
                data={"type": "time_series", "metric": "revenue"},
                charts=["revenue_trend", "revenue_growth"],
                tables=["revenue_summary"],
                order=3
            ),
            ReportSection(
                title="Profitability Analysis",
                content="Profitability metrics indicate the company's ability to generate earnings relative to its revenue and assets.",
                section_type="profitability",
                data={"type": "metrics", "categories": ["gross_margin", "net_margin", "roe", "roa"]},
                charts=["profitability_trends", "margin_comparison"],
                tables=["profitability_summary"],
                order=4
            ),
            ReportSection(
                title="Financial Health Assessment",
                content="The company's financial health is evaluated through liquidity ratios, solvency metrics, and efficiency indicators.",
                section_type="financial_health",
                data={"type": "ratios", "categories": ["liquidity", "solvency", "efficiency"]},
                charts=["liquidity_ratios", "solvency_ratios"],
                tables=["financial_health_summary"],
                order=5
            ),
            ReportSection(
                title="Cash Flow Analysis",
                content="Cash flow analysis examines the company's ability to generate cash from operations, investments, and financing activities.",
                section_type="cash_flow",
                data={"type": "cash_flow", "categories": ["operating", "investing", "financing"]},
                charts=["cash_flow_trends", "free_cash_flow"],
                tables=["cash_flow_summary"],
                order=6
            ),
            ReportSection(
                title="Industry Comparison",
                content="Performance metrics are compared against industry benchmarks to assess relative competitiveness.",
                section_type="industry_comparison",
                data={"type": "benchmark", "metrics": ["roe", "debt_ratio", "current_ratio"]},
                charts=["industry_comparison", "percentile_analysis"],
                tables=["benchmark_comparison"],
                order=7
            ),
            ReportSection(
                title="Investment Outlook",
                content="Based on the comprehensive analysis, investment recommendations and future outlook are provided.",
                section_type="investment_outlook",
                data={"type": "outlook", "factors": ["growth", "risk", "valuation"]},
                charts=["valuation_trends", "risk_return_profile"],
                tables=["investment_summary"],
                order=8
            ),
            ReportSection(
                title="Recommendations",
                content="{{analyst_recommendations}}",
                section_type="recommendations",
                order=9
            )
        ]

    def generate_report_config(self, variables: Dict[str, Any]) -> ReportConfig:
        """Generate report configuration from variables"""
        return ReportConfig(
            title=f"Financial Analysis Report - {variables.get('company_name', 'Unknown')}",
            author="AutoGen Financial Analysis System",
            report_type=ReportType.FINANCIAL,
            format=ReportFormat.HTML,
            template=self.name
        )


class RiskReportTemplate:
    """Risk assessment report template"""

    def __init__(self):
        self.name = "Risk Analysis Report"
        self.description = "Comprehensive risk assessment with VaR and stress testing"
        self.variables = self._define_variables()
        self.sections = self._create_sections()

    def _define_variables(self) -> List[TemplateVariable]:
        """Define template variables"""
        return [
            TemplateVariable("portfolio_name", "Portfolio name", "string", True),
            TemplateVariable("var_metrics", "VaR metrics", "dict", True),
            TemplateVariable("stress_test_results", "Stress test results", "dict", True),
            TemplateVariable("risk_contribution", "Risk contribution analysis", "dict", True),
            TemplateVariable("correlation_analysis", "Correlation analysis", "dict", True),
            TemplateVariable("risk_measures", "Risk measures", "dict", True),
            TemplateVariable("mitigation_strategies", "Risk mitigation strategies", "string", False)
        ]

    def _create_sections(self) -> List[ReportSection]:
        """Create report sections"""
        return [
            ReportSection(
                title="Risk Assessment Overview",
                content="This report provides a comprehensive risk assessment for {{portfolio_name}}. The analysis includes Value at Risk (VaR) calculations, stress testing scenarios, and risk attribution.",
                section_type="overview",
                order=1
            ),
            ReportSection(
                title="Value at Risk (VaR) Analysis",
                content="VaR analysis quantifies the potential loss in portfolio value under normal market conditions.",
                section_type="var_analysis",
                data={"type": "var", "confidence_levels": [95, 99]},
                charts=["var_distribution", "var_trends"],
                tables=["var_summary"],
                order=2
            ),
            ReportSection(
                title="Stress Testing Results",
                content="Stress testing evaluates portfolio performance under extreme market scenarios.",
                section_type="stress_testing",
                data={"type": "stress_test", "scenarios": ["market_crash", "interest_rate_shock", "currency_crisis"]},
                charts=["stress_test_results", "scenario_comparison"],
                tables=["stress_test_summary"],
                order=3
            ),
            ReportSection(
                title="Risk Contribution Analysis",
                content="Risk contribution analysis identifies the sources of portfolio risk.",
                section_type="risk_contribution",
                data={"type": "attribution", "categories": ["asset_class", "sector", "geography"]},
                charts=["risk_contribution_pie", "marginal_var"],
                tables=["risk_contribution_summary"],
                order=4
            ),
            ReportSection(
                title="Correlation Analysis",
                content="Correlation analysis examines the relationships between different assets in the portfolio.",
                section_type="correlation",
                data={"type": "correlation", "matrix": True},
                charts=["correlation_heatmap", "correlation_trends"],
                tables=["correlation_summary"],
                order=5
            ),
            ReportSection(
                title="Risk Metrics Summary",
                content="Comprehensive risk metrics provide a holistic view of portfolio risk.",
                section_type="risk_metrics",
                data={"type": "metrics", "categories": ["volatility", "sharpe", "sortino", "max_drawdown"]},
                charts=["risk_metrics_dashboard"],
                tables=["risk_metrics_summary"],
                order=6
            ),
            ReportSection(
                title="Risk Mitigation Strategies",
                content="{{mitigation_strategies}}",
                section_type="mitigation",
                order=7
            )
        ]

    def generate_report_config(self, variables: Dict[str, Any]) -> ReportConfig:
        """Generate report configuration from variables"""
        return ReportConfig(
            title=f"Risk Analysis Report - {variables.get('portfolio_name', 'Unknown')}",
            author="AutoGen Risk Analysis System",
            report_type=ReportType.RISK,
            format=ReportFormat.HTML,
            template=self.name
        )


class PortfolioReportTemplate:
    """Portfolio analysis report template"""

    def __init__(self):
        self.name = "Portfolio Analysis Report"
        self.description = "Portfolio performance, allocation, and optimization analysis"
        self.variables = self._define_variables()
        self.sections = self._create_sections()

    def _define_variables(self) -> List[TemplateVariable]:
        """Define template variables"""
        return [
            TemplateVariable("portfolio_name", "Portfolio name", "string", True),
            TemplateVariable("current_allocation", "Current asset allocation", "dict", True),
            TemplateVariable("performance_metrics", "Performance metrics", "dict", True),
            TemplateVariable("risk_metrics", "Risk metrics", "dict", True),
            TemplateVariable("optimization_results", "Portfolio optimization results", "dict", True),
            TemplateVariable("benchmark_comparison", "Benchmark comparison", "dict", False),
            TemplateVariable("rebalancing_recommendations", "Rebalancing recommendations", "string", False)
        ]

    def _create_sections(self) -> List[ReportSection]:
        """Create report sections"""
        return [
            ReportSection(
                title="Portfolio Overview",
                content="This report provides a comprehensive analysis of {{portfolio_name}}'s performance, asset allocation, and optimization opportunities.",
                section_type="overview",
                order=1
            ),
            ReportSection(
                title="Current Asset Allocation",
                content="The current asset allocation shows the distribution of investments across different asset classes.",
                section_type="allocation",
                data={"type": "allocation", "categories": ["equity", "bonds", "cash", "alternatives"]},
                charts=["allocation_pie", "allocation_comparison"],
                tables=["allocation_summary"],
                order=2
            ),
            ReportSection(
                title="Performance Analysis",
                content="Performance analysis evaluates the portfolio's returns relative to benchmarks and risk-adjusted metrics.",
                section_type="performance",
                data={"type": "performance", "metrics": ["returns", "alpha", "beta", "information_ratio"]},
                charts=["performance_trends", "risk_return_scatter"],
                tables=["performance_summary"],
                order=3
            ),
            ReportSection(
                title="Risk Analysis",
                content="Risk analysis assesses the portfolio's risk profile and risk-adjusted performance.",
                section_type="risk",
                data={"type": "risk", "metrics": ["volatility", "sharpe", "sortino", "max_drawdown"]},
                charts=["risk_metrics", "drawdown_analysis"],
                tables=["risk_summary"],
                order=4
            ),
            ReportSection(
                title="Portfolio Optimization",
                content="Portfolio optimization analysis identifies opportunities to improve risk-adjusted returns.",
                section_type="optimization",
                data={"type": "optimization", "method": "mean_variance"},
                charts=["efficient_frontier", "optimization_results"],
                tables=["optimization_summary"],
                order=5
            ),
            ReportSection(
                title="Benchmark Comparison",
                content="Benchmark comparison evaluates the portfolio's performance against relevant market indices.",
                section_type="benchmark",
                data={"type": "benchmark", "indices": ["S&P500", "MSCI World", "Bloomberg Aggregate"]},
                charts=["benchmark_comparison", "tracking_error"],
                tables=["benchmark_summary"],
                order=6
            ),
            ReportSection(
                title="Rebalancing Recommendations",
                content="{{rebalancing_recommendations}}",
                section_type="rebalancing",
                order=7
            )
        ]

    def generate_report_config(self, variables: Dict[str, Any]) -> ReportConfig:
        """Generate report configuration from variables"""
        return ReportConfig(
            title=f"Portfolio Analysis Report - {variables.get('portfolio_name', 'Unknown')}",
            author="AutoGen Portfolio Analysis System",
            report_type=ReportType.PORTFOLIO,
            format=ReportFormat.HTML,
            template=self.name
        )


class AnalysisReportTemplate:
    """Technical analysis report template"""

    def __init__(self):
        self.name = "Technical Analysis Report"
        self.description = "Technical analysis with indicators and trading signals"
        self.variables = self._define_variables()
        self.sections = self._create_sections()

    def _define_variables(self) -> List[TemplateVariable]:
        """Define template variables"""
        return [
            TemplateVariable("symbol", "Trading symbol", "string", True),
            TemplateVariable("price_data", "Price data", "dict", True),
            TemplateVariable("technical_indicators", "Technical indicators", "dict", True),
            TemplateVariable("trading_signals", "Trading signals", "dict", True),
            TemplateVariable("support_resistance", "Support and resistance levels", "dict", True),
            TemplateVariable("market_sentiment", "Market sentiment analysis", "dict", False),
            TemplateVariable("trading_recommendations", "Trading recommendations", "string", False)
        ]

    def _create_sections(self) -> List[ReportSection]:
        """Create report sections"""
        return [
            ReportSection(
                title="Technical Analysis Overview",
                content="This report provides a comprehensive technical analysis of {{symbol}}. The analysis includes price action, technical indicators, and trading signals.",
                section_type="overview",
                order=1
            ),
            ReportSection(
                title="Price Action Analysis",
                content="Price action analysis examines the historical price movements and key levels.",
                section_type="price_action",
                data={"type": "price", "indicators": ["support", "resistance", "trendlines"]},
                charts=["price_chart", "candlestick_patterns"],
                tables=["price_levels"],
                order=2
            ),
            ReportSection(
                title="Technical Indicators",
                content="Technical indicators provide quantitative measures of price momentum, trend, and volatility.",
                section_type="indicators",
                data={"type": "indicators", "categories": ["momentum", "trend", "volatility", "volume"]},
                charts=["indicator_dashboard", "signal_history"],
                tables=["indicator_summary"],
                order=3
            ),
            ReportSection(
                title="Trading Signals",
                content="Trading signals identify potential entry and exit points based on technical analysis.",
                section_type="signals",
                data={"type": "signals", "strategies": ["moving_average", "rsi", "macd"]},
                charts=["signal_chart", "performance_backtest"],
                tables=["signal_summary"],
                order=4
            ),
            ReportSection(
                title="Support and Resistance",
                content="Support and resistance levels identify key price zones where buying and selling pressure may emerge.",
                section_type="support_resistance",
                data={"type": "levels", "timeframes": ["daily", "weekly", "monthly"]},
                charts=["support_resistance_chart", "price_zones"],
                tables=["levels_summary"],
                order=5
            ),
            ReportSection(
                title="Market Sentiment",
                content="Market sentiment analysis evaluates the overall market psychology and positioning.",
                section_type="sentiment",
                data={"type": "sentiment", "indicators": ["put_call_ratio", "volatility_index", "futures_positions"]},
                charts=["sentiment_indicators", "fear_greed_index"],
                tables=["sentiment_summary"],
                order=6
            ),
            ReportSection(
                title="Trading Recommendations",
                content="{{trading_recommendations}}",
                section_type="recommendations",
                order=7
            )
        ]

    def generate_report_config(self, variables: Dict[str, Any]) -> ReportConfig:
        """Generate report configuration from variables"""
        return ReportConfig(
            title=f"Technical Analysis Report - {variables.get('symbol', 'Unknown')}",
            author="AutoGen Technical Analysis System",
            report_type=ReportType.ANALYSIS,
            format=ReportFormat.HTML,
            template=self.name
        )


class ExecutiveReportTemplate:
    """Executive summary report template"""

    def __init__(self):
        self.name = "Executive Summary Report"
        self.description = "High-level executive summary with key metrics and insights"
        self.variables = self._define_variables()
        self.sections = self._create_sections()

    def _define_variables(self) -> List[TemplateVariable]:
        """Define template variables"""
        return [
            TemplateVariable("company_name", "Company name", "string", True),
            TemplateVariable("key_metrics", "Key performance metrics", "dict", True),
            TemplateVariable("financial_highlights", "Financial highlights", "dict", True),
            TemplateVariable("risk_summary", "Risk summary", "dict", True),
            TemplateVariable("market_position", "Market position analysis", "dict", True),
            TemplateVariable("strategic_initiatives", "Strategic initiatives", "string", False),
            TemplateVariable("executive_recommendations", "Executive recommendations", "string", False)
        ]

    def _create_sections(self) -> List[ReportSection]:
        """Create report sections"""
        return [
            ReportSection(
                title="Executive Summary",
                content="This executive summary provides a high-level overview of {{company_name}}'s financial performance, market position, and strategic outlook.",
                section_type="summary",
                order=1
            ),
            ReportSection(
                title="Key Performance Metrics",
                content="Key performance metrics provide a snapshot of the company's financial health and operational efficiency.",
                section_type="metrics",
                data={"type": "kpi", "categories": ["financial", "operational", "market"]},
                charts=["kpi_dashboard", "performance_trends"],
                tables=["kpi_summary"],
                order=2
            ),
            ReportSection(
                title="Financial Highlights",
                content="Financial highlights summarize the company's revenue growth, profitability, and cash flow performance.",
                section_type="financial_highlights",
                data={"type": "highlights", "periods": ["current", "previous", "projected"]},
                charts=["financial_highlights", "growth_comparison"],
                tables=["highlights_summary"],
                order=3
            ),
            ReportSection(
                title="Risk Summary",
                content="Risk summary identifies key risk factors and mitigation strategies.",
                section_type="risk",
                data={"type": "risk", "categories": ["financial", "operational", "strategic"]},
                charts=["risk_heatmap", "risk_trends"],
                tables=["risk_summary"],
                order=4
            ),
            ReportSection(
                title="Market Position",
                content="Market position analysis evaluates the company's competitive landscape and market share.",
                section_type="market",
                data={"type": "market", "metrics": ["market_share", "competitor_analysis", "growth_potential"]},
                charts=["market_position", "competitive_landscape"],
                tables=["market_summary"],
                order=5
            ),
            ReportSection(
                title="Strategic Initiatives",
                content="{{strategic_initiatives}}",
                section_type="initiatives",
                order=6
            ),
            ReportSection(
                title="Executive Recommendations",
                content="{{executive_recommendations}}",
                section_type="recommendations",
                order=7
            )
        ]

    def generate_report_config(self, variables: Dict[str, Any]) -> ReportConfig:
        """Generate report configuration from variables"""
        return ReportConfig(
            title=f"Executive Summary Report - {variables.get('company_name', 'Unknown')}",
            author="AutoGen Executive Analysis System",
            report_type=ReportType.EXECUTIVE,
            format=ReportFormat.HTML,
            template=self.name
        )


# Template registry
TEMPLATE_REGISTRY = {
    "financial": FinancialReportTemplate,
    "risk": RiskReportTemplate,
    "portfolio": PortfolioReportTemplate,
    "analysis": AnalysisReportTemplate,
    "executive": ExecutiveReportTemplate
}


def get_template(template_name: str) -> Optional[ReportTemplate]:
    """Get a template by name"""
    template_class = TEMPLATE_REGISTRY.get(template_name)
    if template_class:
        return template_class()
    return None


def list_available_templates() -> List[str]:
    """List all available templates"""
    return list(TEMPLATE_REGISTRY.keys())


def register_custom_template(template_name: str, template_class):
    """Register a custom template"""
    TEMPLATE_REGISTRY[template_name] = template_class
    logger.info(f"Custom template registered: {template_name}")


def create_template_from_file(file_path: str) -> Optional[ReportTemplate]:
    """Create template from YAML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            template_data = yaml.safe_load(f)

        sections = []
        for section_data in template_data.get('sections', []):
            section = ReportSection(**section_data)
            sections.append(section)

        return ReportTemplate(
            name=template_data['name'],
            description=template_data.get('description', ''),
            sections=sections,
            template_file=file_path,
            style_config=template_data.get('style_config', {}),
            data_requirements=template_data.get('data_requirements', [])
        )

    except Exception as e:
        logger.error(f"Failed to load template from {file_path}: {e}")
        return None