"""
Advanced Financial Analyzer
Comprehensive financial analysis engine with ratio calculations
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats

from .financial_models import FinancialMetrics, FinancialRatio
from .ratio_calculator import RatioCalculator
from .dupont_analyzer import DuPontAnalyzer
from .trend_analyzer import TrendAnalyzer
from ..data.data_models import FinancialData


class AdvancedFinancialAnalyzer:
    """Advanced financial analysis engine"""

    def __init__(self, industry_benchmarks: Optional[Dict[str, Dict[str, float]]] = None):
        self.logger = logging.getLogger(__name__)
        self.ratio_calculator = RatioCalculator()
        self.dupont_analyzer = DuPontAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.industry_benchmarks = industry_benchmarks or self._load_default_benchmarks()

    def _load_default_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Load default industry benchmarks"""
        return {
            "technology": {
                "roe": 15.2,
                "roa": 8.5,
                "debt_to_equity": 0.5,
                "gross_margin": 65.2,
                "net_margin": 18.7,
                "current_ratio": 1.8,
                "asset_turnover": 0.9
            },
            "financial": {
                "roe": 12.8,
                "roa": 1.2,
                "debt_to_equity": 2.5,
                "gross_margin": 45.3,
                "net_margin": 22.1,
                "current_ratio": 1.2,
                "asset_turnover": 0.1
            },
            "healthcare": {
                "roe": 18.5,
                "roa": 6.8,
                "debt_to_equity": 0.8,
                "gross_margin": 72.4,
                "net_margin": 14.2,
                "current_ratio": 2.1,
                "asset_turnover": 0.6
            },
            "consumer_goods": {
                "roe": 14.2,
                "roa": 5.9,
                "debt_to_equity": 1.2,
                "gross_margin": 38.7,
                "net_margin": 8.4,
                "current_ratio": 1.6,
                "asset_turnover": 1.4
            },
            "energy": {
                "roe": 8.9,
                "roa": 3.2,
                "debt_to_equity": 1.8,
                "gross_margin": 32.1,
                "net_margin": 6.8,
                "current_ratio": 1.3,
                "asset_turnover": 0.8
            }
        }

    def analyze_financial_data(self, financial_data: FinancialData,
                             analysis_period: str = "annual",
                             calculate_trends: bool = True) -> FinancialMetrics:
        """Perform comprehensive financial analysis"""
        try:
            self.logger.info(f"Starting financial analysis for {financial_data.symbol}")

            # Initialize metrics container
            metrics = FinancialMetrics(
                symbol=financial_data.symbol,
                company_name=financial_data.company_name,
                sector=financial_data.sector,
                industry=financial_data.industry,
                analysis_date=datetime.now(),
                data_period=analysis_period,
                data_sources=financial_data.data_sources,
                data_quality_score=financial_data.data_quality.overall_score if financial_data.data_quality else 1.0
            )

            # Extract financial data
            financial_data_extracted = self._extract_financial_data(financial_data)

            # Calculate ratios by category
            metrics = self._calculate_profitability_ratios(metrics, financial_data_extracted)
            metrics = self._calculate_liquidity_ratios(metrics, financial_data_extracted)
            metrics = self._calculate_efficiency_ratios(metrics, financial_data_extracted)
            metrics = self._calculate_leverage_ratios(metrics, financial_data_extracted)
            metrics = self._calculate_growth_ratios(metrics, financial_data_extracted)
            metrics = self._calculate_market_ratios(metrics, financial_data_extracted)
            metrics = self._calculate_cash_flow_ratios(metrics, financial_data_extracted)

            # Perform advanced analysis
            metrics = self._perform_advanced_analysis(metrics, financial_data_extracted)

            # Calculate quality scores
            metrics = self._calculate_quality_scores(metrics)

            # Add trend analysis if requested
            if calculate_trends and financial_data_extracted.get("has_historical_data", False):
                metrics = self._add_trend_analysis(metrics, financial_data)

            # Calculate industry comparisons
            metrics = self._add_industry_comparisons(metrics)

            self.logger.info(f"Financial analysis completed for {financial_data.symbol}")
            return metrics

        except Exception as e:
            self.logger.error(f"Financial analysis failed for {financial_data.symbol}: {str(e)}")
            raise

    def _extract_financial_data(self, financial_data: FinancialData) -> Dict[str, Any]:
        """Extract and normalize financial data"""
        extracted_data = {
            "symbol": financial_data.symbol,
            "has_historical_data": False
        }

        def safe_get_df_value(df_dict: Dict, key: str, default: float = 0.0) -> float:
            """Safely get value from pandas DataFrame dictionary"""
            try:
                if isinstance(df_dict, dict) and key in df_dict:
                    value = df_dict[key]
                    return float(value) if pd.notna(value) else default
                return default
            except:
                return default

        # Get latest year data
        latest_year = None
        if financial_data.income_statement and financial_data.income_statement.data:
            latest_year = financial_data.income_statement.get_latest_year()

        if latest_year:
            # Income statement data
            if financial_data.income_statement:
                income_data = financial_data.income_statement.data.get(latest_year, {})
                extracted_data.update({
                    "revenue": safe_get_df_value(income_data, "Total Revenue"),
                    "net_income": safe_get_df_value(income_data, "Net Income"),
                    "gross_profit": safe_get_df_value(income_data, "Gross Profit"),
                    "ebit": safe_get_df_value(income_data, "EBIT"),
                    "ebitda": safe_get_df_value(income_data, "EBITDA"),
                    "operating_income": safe_get_df_value(income_data, "Operating Income"),
                    "interest_expense": safe_get_df_value(income_data, "Interest Expense"),
                    "tax_expense": safe_get_df_value(income_data, "Income Tax Expense")
                })

            # Balance sheet data
            if financial_data.balance_sheet:
                balance_data = financial_data.balance_sheet.data.get(latest_year, {})
                extracted_data.update({
                    "total_assets": safe_get_df_value(balance_data, "Total Assets"),
                    "total_equity": safe_get_df_value(balance_data, "Total Stockholder Equity"),
                    "total_liabilities": safe_get_df_value(balance_data, "Total Liabilities"),
                    "total_debt": safe_get_df_value(balance_data, "Total Debt"),
                    "current_assets": safe_get_df_value(balance_data, "Total Current Assets"),
                    "current_liabilities": safe_get_df_value(balance_data, "Total Current Liabilities"),
                    "inventory": safe_get_df_value(balance_data, "Inventory"),
                    "accounts_receivable": safe_get_df_value(balance_data, "Net Receivables"),
                    "accounts_payable": safe_get_df_value(balance_data, "Accounts Payable"),
                    "cash_and_equivalents": safe_get_df_value(balance_data, "Cash And Cash Equivalents"),
                    "retained_earnings": safe_get_df_value(balance_data, "Retained Earnings"),
                    "working_capital": (safe_get_df_value(balance_data, "Total Current Assets") -
                                     safe_get_df_value(balance_data, "Total Current Liabilities"))
                })

            # Cash flow data
            if financial_data.cash_flow:
                cash_data = financial_data.cash_flow.data.get(latest_year, {})
                extracted_data.update({
                    "operating_cash_flow": safe_get_df_value(cash_data, "Operating Cash Flow"),
                    "investing_cash_flow": safe_get_df_value(cash_data, "Investing Cash Flow"),
                    "financing_cash_flow": safe_get_df_value(cash_data, "Financing Cash Flow"),
                    "capital_expenditures": abs(safe_get_df_value(cash_data, "Capital Expenditure")),
                    "free_cash_flow": (safe_get_df_value(cash_data, "Operating Cash Flow") +
                                     safe_get_df_value(cash_data, "Investing Cash Flow"))
                })

            # Market data
            if financial_data.market_data:
                market_data = financial_data.market_data
                extracted_data.update({
                    "market_cap": market_data.market_cap,
                    "current_price": market_data.current_price,
                    "shares_outstanding": (market_data.market_cap / market_data.current_price
                                          if market_data.current_price > 0 else 0),
                    "beta": market_data.beta
                })

            # Historical data for trend analysis
            if financial_data.income_statement and len(financial_data.income_statement.data) > 1:
                extracted_data["has_historical_data"] = True
                historical_data = {}
                for year, data in financial_data.income_statement.data.items():
                    historical_data[year] = {
                        "revenue": safe_get_df_value(data, "Total Revenue"),
                        "net_income": safe_get_df_value(data, "Net Income")
                    }
                extracted_data["historical_income"] = historical_data

        return extracted_data

    def _calculate_profitability_ratios(self, metrics: FinancialMetrics, data: Dict) -> FinancialMetrics:
        """Calculate profitability ratios"""
        revenue = data.get("revenue", 0)
        net_income = data.get("net_income", 0)
        gross_profit = data.get("gross_profit", 0)
        ebit = data.get("ebit", 0)
        operating_income = data.get("operating_income", 0)
        total_assets = data.get("total_assets", 0)
        total_equity = data.get("total_equity", 0)

        # Return on Equity (ROE)
        if total_equity > 0:
            metrics.roe = FinancialRatio(
                name="Return on Equity",
                value=(net_income / total_equity) * 100,
                category="profitability",
                description="Measures return generated on shareholders' equity",
                benchmark=self._get_benchmark(metrics.industry, "roe"),
                calculation_method="Net Income / Total Shareholder Equity"
            )

        # Return on Assets (ROA)
        if total_assets > 0:
            metrics.roa = FinancialRatio(
                name="Return on Assets",
                value=(net_income / total_assets) * 100,
                category="profitability",
                description="Measures efficiency in using assets to generate earnings",
                benchmark=self._get_benchmark(metrics.industry, "roa"),
                calculation_method="Net Income / Total Assets"
            )

        # Gross Margin
        if revenue > 0:
            metrics.gross_margin = FinancialRatio(
                name="Gross Margin",
                value=(gross_profit / revenue) * 100,
                category="profitability",
                description="Percentage of revenue remaining after cost of goods sold",
                benchmark=self._get_benchmark(metrics.industry, "gross_margin"),
                calculation_method="Gross Profit / Revenue"
            )

        # Net Margin
        if revenue > 0:
            metrics.net_margin = FinancialRatio(
                name="Net Margin",
                value=(net_income / revenue) * 100,
                category="profitability",
                description="Percentage of revenue remaining after all expenses",
                calculation_method="Net Income / Revenue"
            )

        # EBIT Margin
        if revenue > 0:
            metrics.ebit_margin = FinancialRatio(
                name="EBIT Margin",
                value=(ebit / revenue) * 100,
                category="profitability",
                description="Operating profitability as percentage of revenue",
                calculation_method="EBIT / Revenue"
            )

        # Operating Margin
        if revenue > 0:
            metrics.operating_margin = FinancialRatio(
                name="Operating Margin",
                value=(operating_income / revenue) * 100,
                category="profitability",
                description="Operating profitability as percentage of revenue",
                calculation_method="Operating Income / Revenue"
            )

        return metrics

    def _calculate_liquidity_ratios(self, metrics: FinancialMetrics, data: Dict) -> FinancialMetrics:
        """Calculate liquidity ratios"""
        current_assets = data.get("current_assets", 0)
        current_liabilities = data.get("current_liabilities", 0)
        inventory = data.get("inventory", 0)
        cash_and_equivalents = data.get("cash_and_equivalents", 0)

        # Current Ratio
        if current_liabilities > 0:
            metrics.current_ratio = FinancialRatio(
                name="Current Ratio",
                value=current_assets / current_liabilities,
                unit="",
                category="liquidity",
                description="Ability to pay short-term obligations",
                benchmark=self._get_benchmark(metrics.industry, "current_ratio"),
                calculation_method="Current Assets / Current Liabilities"
            )

        # Quick Ratio (Acid Test)
        if current_liabilities > 0:
            metrics.quick_ratio = FinancialRatio(
                name="Quick Ratio",
                value=(current_assets - inventory) / current_liabilities,
                unit="",
                category="liquidity",
                description="Ability to pay short-term obligations without inventory",
                benchmark=1.0,
                calculation_method="(Current Assets - Inventory) / Current Liabilities"
            )

        # Cash Ratio
        if current_liabilities > 0:
            metrics.cash_ratio = FinancialRatio(
                name="Cash Ratio",
                value=cash_and_equivalents / current_liabilities,
                unit="",
                category="liquidity",
                description="Ability to pay short-term obligations with cash",
                benchmark=0.2,
                calculation_method="Cash and Equivalents / Current Liabilities"
            )

        return metrics

    def _calculate_efficiency_ratios(self, metrics: FinancialMetrics, data: Dict) -> FinancialMetrics:
        """Calculate efficiency ratios"""
        revenue = data.get("revenue", 0)
        total_assets = data.get("total_assets", 0)
        inventory = data.get("inventory", 0)
        accounts_receivable = data.get("accounts_receivable", 0)
        accounts_payable = data.get("accounts_payable", 0)
        working_capital = data.get("working_capital", 0)

        # Asset Turnover
        if total_assets > 0:
            metrics.asset_turnover = FinancialRatio(
                name="Asset Turnover",
                value=revenue / total_assets,
                unit="",
                category="efficiency",
                description="Efficiency in using assets to generate sales",
                benchmark=self._get_benchmark(metrics.industry, "asset_turnover"),
                calculation_method="Revenue / Total Assets"
            )

        # Inventory Turnover
        if inventory > 0:
            metrics.inventory_turnover = FinancialRatio(
                name="Inventory Turnover",
                value=revenue / inventory,
                unit="",
                category="efficiency",
                description="Efficiency in managing inventory",
                benchmark=6.0,
                calculation_method="Revenue / Inventory"
            )

        # Receivables Turnover
        if accounts_receivable > 0:
            metrics.receivables_turnover = FinancialRatio(
                name="Receivables Turnover",
                value=revenue / accounts_receivable,
                unit="",
                category="efficiency",
                description="Efficiency in collecting receivables",
                benchmark=8.0,
                calculation_method="Revenue / Accounts Receivable"
            )

        # Working Capital Turnover
        if working_capital > 0:
            metrics.working_capital_turnover = FinancialRatio(
                name="Working Capital Turnover",
                value=revenue / working_capital,
                unit="",
                category="efficiency",
                description="Efficiency in using working capital",
                benchmark=3.0,
                calculation_method="Revenue / Working Capital"
            )

        return metrics

    def _calculate_leverage_ratios(self, metrics: FinancialMetrics, data: Dict) -> FinancialMetrics:
        """Calculate leverage ratios"""
        total_debt = data.get("total_debt", 0)
        total_assets = data.get("total_assets", 0)
        total_equity = data.get("total_equity", 0)
        total_liabilities = data.get("total_liabilities", 0)
        ebit = data.get("ebit", 0)
        interest_expense = data.get("interest_expense", 0)

        # Debt to Equity
        if total_equity > 0:
            metrics.debt_to_equity = FinancialRatio(
                name="Debt to Equity",
                value=total_debt / total_equity,
                unit="",
                category="leverage",
                description="Financial leverage ratio",
                benchmark=self._get_benchmark(metrics.industry, "debt_to_equity"),
                calculation_method="Total Debt / Total Shareholder Equity"
            )

        # Debt to Assets
        if total_assets > 0:
            metrics.debt_to_assets = FinancialRatio(
                name="Debt to Assets",
                value=(total_debt / total_assets) * 100,
                category="leverage",
                description="Percentage of assets financed by debt",
                benchmark=40.0,
                calculation_method="Total Debt / Total Assets"
            )

        # Equity Multiplier
        if total_equity > 0:
            metrics.equity_multiplier = FinancialRatio(
                name="Equity Multiplier",
                value=total_assets / total_equity,
                unit="",
                category="leverage",
                description="Financial leverage multiplier",
                benchmark=2.0,
                calculation_method="Total Assets / Total Shareholder Equity"
            )

        # Interest Coverage
        if interest_expense > 0:
            metrics.interest_coverage = FinancialRatio(
                name="Interest Coverage",
                value=ebit / interest_expense,
                unit="",
                category="leverage",
                description="Ability to pay interest on debt",
                benchmark=3.0,
                calculation_method="EBIT / Interest Expense"
            )

        return metrics

    def _calculate_growth_ratios(self, metrics: FinancialMetrics, data: Dict) -> FinancialMetrics:
        """Calculate growth ratios"""
        historical_data = data.get("historical_income", {})

        if len(historical_data) >= 2:
            years = sorted(historical_data.keys())
            current_year = years[0]
            previous_year = years[1]

            current_revenue = historical_data[current_year].get("revenue", 0)
            previous_revenue = historical_data[previous_year].get("revenue", 0)
            current_net_income = historical_data[current_year].get("net_income", 0)
            previous_net_income = historical_data[previous_year].get("net_income", 0)

            # Revenue Growth
            if previous_revenue > 0:
                metrics.revenue_growth = FinancialRatio(
                    name="Revenue Growth",
                    value=((current_revenue - previous_revenue) / previous_revenue) * 100,
                    category="growth",
                    description="Year-over-year revenue growth rate",
                    benchmark=10.0,
                    calculation_method="(Current Revenue - Previous Revenue) / Previous Revenue"
                )

            # Earnings Growth
            if previous_net_income > 0:
                metrics.earnings_growth = FinancialRatio(
                    name="Earnings Growth",
                    value=((current_net_income - previous_net_income) / previous_net_income) * 100,
                    category="growth",
                    description="Year-over-year earnings growth rate",
                    benchmark=15.0,
                    calculation_method="(Current Net Income - Previous Net Income) / Previous Net Income"
                )

        return metrics

    def _calculate_market_ratios(self, metrics: FinancialMetrics, data: Dict) -> FinancialMetrics:
        """Calculate market ratios"""
        market_cap = data.get("market_cap", 0)
        current_price = data.get("current_price", 0)
        net_income = data.get("net_income", 0)
        total_equity = data.get("total_equity", 0)
        revenue = data.get("revenue", 0)
        shares_outstanding = data.get("shares_outstanding", 0)
        operating_cash_flow = data.get("operating_cash_flow", 0)

        # P/E Ratio
        if net_income > 0 and market_cap > 0:
            metrics.price_to_earnings = FinancialRatio(
                name="Price to Earnings",
                value=market_cap / net_income,
                unit="",
                category="market",
                description="Market value per dollar of earnings",
                benchmark=20.0,
                calculation_method="Market Cap / Net Income"
            )

        # P/B Ratio
        if total_equity > 0 and market_cap > 0:
            metrics.price_to_book = FinancialRatio(
                name="Price to Book",
                value=market_cap / total_equity,
                unit="",
                category="market",
                description="Market value per dollar of book value",
                benchmark=3.0,
                calculation_method="Market Cap / Total Shareholder Equity"
            )

        # P/S Ratio
        if revenue > 0 and market_cap > 0:
            metrics.price_to_sales = FinancialRatio(
                name="Price to Sales",
                value=market_cap / revenue,
                unit="",
                category="market",
                description="Market value per dollar of sales",
                benchmark=2.0,
                calculation_method="Market Cap / Revenue"
            )

        # Dividend Yield (would need dividend data)
        # This is a placeholder - in practice you'd get dividend data
        metrics.dividend_yield = FinancialRatio(
            name="Dividend Yield",
            value=0.0,
            category="market",
            description="Annual dividend per share divided by share price",
            benchmark=2.0,
            calculation_method="Annual Dividend per Share / Share Price"
        )

        return metrics

    def _calculate_cash_flow_ratios(self, metrics: FinancialMetrics, data: Dict) -> FinancialMetrics:
        """Calculate cash flow ratios"""
        revenue = data.get("revenue", 0)
        operating_cash_flow = data.get("operating_cash_flow", 0)
        capital_expenditures = data.get("capital_expenditures", 0)
        total_debt = data.get("total_debt", 0)

        # Operating Cash Flow to Sales
        if revenue > 0:
            metrics.operating_cash_flow_to_sales = FinancialRatio(
                name="Operating Cash Flow to Sales",
                value=(operating_cash_flow / revenue) * 100,
                category="cash_flow",
                description="Cash generated from operations as percentage of sales",
                benchmark=15.0,
                calculation_method="Operating Cash Flow / Revenue"
            )

        # Free Cash Flow to Sales
        if revenue > 0:
            free_cash_flow = operating_cash_flow - capital_expenditures
            metrics.free_cash_flow_to_sales = FinancialRatio(
                name="Free Cash Flow to Sales",
                value=(free_cash_flow / revenue) * 100,
                category="cash_flow",
                description="Free cash flow as percentage of sales",
                benchmark=8.0,
                calculation_method="Free Cash Flow / Revenue"
            )

        # Capital Expenditure Ratio
        if revenue > 0:
            metrics.capital_expenditure_ratio = FinancialRatio(
                name="Capital Expenditure Ratio",
                value=(capital_expenditures / revenue) * 100,
                category="cash_flow",
                description="Capital expenditures as percentage of sales",
                benchmark=6.0,
                calculation_method="Capital Expenditures / Revenue"
            )

        return metrics

    def _perform_advanced_analysis(self, metrics: FinancialMetrics, data: Dict) -> FinancialMetrics:
        """Perform advanced financial analysis"""
        # DuPont Analysis
        dupont_result = self.dupont_analyzer.analyze_dupont(metrics, data)
        if dupont_result:
            metrics.calculation_methods.update({"dupont_analysis": dupont_result})

        # Altman Z-Score (simplified version)
        z_score = self._calculate_altman_z_score(data)
        if z_score is not None:
            metrics.altman_z_score = FinancialRatio(
                name="Altman Z-Score",
                value=z_score,
                unit="",
                category="distress",
                description="Bankruptcy prediction score",
                benchmark=2.99,
                calculation_method="1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 1.0X5"
            )

        return metrics

    def _calculate_altman_z_score(self, data: Dict) -> Optional[float]:
        """Calculate Altman Z-Score for bankruptcy prediction"""
        try:
            working_capital = data.get("working_capital", 0)
            total_assets = data.get("total_assets", 0)
            retained_earnings = data.get("retained_earnings", 0)
            ebit = data.get("ebit", 0)
            market_cap = data.get("market_cap", 0)
            total_liabilities = data.get("total_liabilities", 0)
            revenue = data.get("revenue", 0)

            if total_assets == 0 or total_liabilities == 0:
                return None

            # Z-Score formula
            X1 = working_capital / total_assets  # Working Capital / Total Assets
            X2 = retained_earnings / total_assets  # Retained Earnings / Total Assets
            X3 = ebit / total_assets  # EBIT / Total Assets
            X4 = market_cap / total_liabilities  # Market Value of Equity / Total Liabilities
            X5 = revenue / total_assets  # Sales / Total Assets

            Z = 1.2 * X1 + 1.4 * X2 + 3.3 * X3 + 0.6 * X4 + 1.0 * X5
            return Z

        except Exception as e:
            self.logger.warning(f"Could not calculate Altman Z-Score: {str(e)}")
            return None

    def _calculate_quality_scores(self, metrics: FinancialMetrics) -> FinancialMetrics:
        """Calculate overall quality scores"""
        scores = {
            "profitability": 0.0,
            "liquidity": 0.0,
            "efficiency": 0.0,
            "leverage": 0.0,
            "growth": 0.0
        }

        weights = {
            "profitability": 0.3,
            "liquidity": 0.2,
            "efficiency": 0.2,
            "leverage": 0.15,
            "growth": 0.15
        }

        # Calculate category scores
        profitability_ratios = [metrics.roe, metrics.roa, metrics.gross_margin, metrics.net_margin]
        scores["profitability"] = self._calculate_category_score(profitability_ratios)

        liquidity_ratios = [metrics.current_ratio, metrics.quick_ratio, metrics.cash_ratio]
        scores["liquidity"] = self._calculate_category_score(liquidity_ratios)

        efficiency_ratios = [metrics.asset_turnover, metrics.inventory_turnover, metrics.receivables_turnover]
        scores["efficiency"] = self._calculate_category_score(efficiency_ratios)

        leverage_ratios = [metrics.debt_to_equity, metrics.debt_to_assets]
        scores["leverage"] = self._calculate_category_score(leverage_ratios, inverse=True)

        growth_ratios = [metrics.revenue_growth, metrics.earnings_growth]
        scores["growth"] = self._calculate_category_score(growth_ratios)

        # Calculate weighted overall score
        overall_score = sum(scores[category] * weights[category] for category in scores)

        # Update metrics
        metrics.profitability_score = scores["profitability"]
        metrics.liquidity_score = scores["liquidity"]
        metrics.efficiency_score = scores["efficiency"]
        metrics.leverage_score = scores["leverage"]
        metrics.growth_score = scores["growth"]
        metrics.overall_quality_score = overall_score

        return metrics

    def _calculate_category_score(self, ratios: List[Optional[FinancialRatio]], inverse: bool = False) -> float:
        """Calculate score for a category of ratios"""
        valid_ratios = [r for r in ratios if r is not None and r.value is not None]
        if not valid_ratios:
            return 0.5  # Neutral score

        scores = []
        for ratio in valid_ratios:
            score = 0.5  # Base score

            # Compare to benchmark
            if ratio.benchmark is not None:
                ratio_score = ratio.value / ratio.benchmark
                if inverse:
                    ratio_score = ratio.benchmark / ratio.value if ratio.value > 0 else 0

                # Normalize score between 0 and 1
                score = min(1.0, max(0.0, ratio_score / 2))  # Cap at 2x benchmark

            scores.append(score)

        return sum(scores) / len(scores)

    def _add_trend_analysis(self, metrics: FinancialMetrics, financial_data: FinancialData) -> FinancialMetrics:
        """Add trend analysis to metrics"""
        try:
            trend_results = self.trend_analyzer.analyze_trends(financial_data)
            metrics.calculation_methods.update({"trend_analysis": trend_results})
        except Exception as e:
            self.logger.warning(f"Trend analysis failed: {str(e)}")

        return metrics

    def _add_industry_comparisons(self, metrics: FinancialMetrics) -> FinancialMetrics:
        """Add industry benchmark comparisons"""
        industry = metrics.industry or "general"

        for ratio in metrics.get_all_ratios():
            benchmark = self._get_benchmark(industry, ratio.name.lower().replace(" ", "_"))
            if benchmark is not None:
                ratio.benchmark = benchmark

                # Calculate percentile (simplified)
                if ratio.value is not None:
                    percentile = min(100, max(0, (ratio.value / benchmark) * 50))
                    ratio.percentile = percentile

        return metrics

    def _get_benchmark(self, industry: str, ratio_name: str) -> Optional[float]:
        """Get industry benchmark for a ratio"""
        if not industry:
            return None

        industry_data = self.industry_benchmarks.get(industry.lower(), {})
        return industry_data.get(ratio_name)

    def generate_analysis_report(self, metrics: FinancialMetrics) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        return {
            "summary": metrics.generate_summary(),
            "key_metrics": metrics.get_key_metrics(),
            "financial_strengths": metrics.get_strengths(),
            "areas_of_concern": metrics.get_distress_signals(),
            "quality_scores": {
                "overall": metrics.overall_quality_score,
                "profitability": metrics.profitability_score,
                "liquidity": metrics.liquidity_score,
                "efficiency": metrics.efficiency_score,
                "leverage": metrics.leverage_score,
                "growth": metrics.growth_score
            },
            "ratios_by_category": {
                "profitability": [r.to_dict() for r in metrics.get_ratios_by_category("profitability")],
                "liquidity": [r.to_dict() for r in metrics.get_ratios_by_category("liquidity")],
                "efficiency": [r.to_dict() for r in metrics.get_ratios_by_category("efficiency")],
                "leverage": [r.to_dict() for r in metrics.get_ratios_by_category("leverage")],
                "growth": [r.to_dict() for r in metrics.get_ratios_by_category("growth")],
                "market": [r.to_dict() for r in metrics.get_ratios_by_category("market")]
            },
            "investment_recommendation": self._generate_investment_recommendation(metrics)
        }

    def _generate_investment_recommendation(self, metrics: FinancialMetrics) -> str:
        """Generate investment recommendation based on analysis"""
        score = metrics.overall_quality_score

        if score > 0.8:
            return "Strong Buy - Excellent financial health with strong fundamentals"
        elif score > 0.65:
            return "Buy - Good financial position with solid growth prospects"
        elif score > 0.5:
            return "Hold - Adequate financial position but monitor key metrics"
        elif score > 0.35:
            return "Underperform - Some financial concerns requiring attention"
        else:
            return "Sell - Significant financial distress signals detected"