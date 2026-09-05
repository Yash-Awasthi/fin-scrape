"""
Ratio Calculator
Comprehensive financial ratio calculations with validation and benchmarking
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

from .financial_models import FinancialRatio, FinancialMetrics


class RatioCategory(Enum):
    """Financial ratio categories"""
    PROFITABILITY = "profitability"
    LIQUIDITY = "liquidity"
    EFFICIENCY = "efficiency"
    LEVERAGE = "leverage"
    GROWTH = "growth"
    MARKET = "market"
    CASH_FLOW = "cash_flow"


@dataclass
class RatioBenchmark:
    """Industry benchmark data for ratios"""
    ratio_name: str
    industry: str
    sector: str
    median: float
    percentile_25: float
    percentile_75: float
    data_points: int
    last_updated: datetime


class RatioCalculator:
    """Comprehensive financial ratio calculator with validation and benchmarking"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.benchmarks: Dict[str, List[RatioBenchmark]] = {}
        self._load_industry_benchmarks()

    def _load_industry_benchmarks(self):
        """Load industry benchmark data"""
        # Default industry benchmarks (in practice, this would come from a database)
        default_benchmarks = {
            "ROE": [
                RatioBenchmark("ROE", "Technology", "Software", 15.2, 8.5, 22.1, 1500, datetime.now()),
                RatioBenchmark("ROE", "Healthcare", "Pharmaceuticals", 18.7, 12.3, 25.4, 800, datetime.now()),
                RatioBenchmark("ROE", "Finance", "Banking", 12.8, 7.2, 18.5, 2000, datetime.now())
            ],
            "Current Ratio": [
                RatioBenchmark("Current Ratio", "Technology", "Software", 2.5, 1.8, 3.2, 1500, datetime.now()),
                RatioBenchmark("Current Ratio", "Manufacturing", "Industrial", 1.8, 1.2, 2.5, 1200, datetime.now()),
                RatioBenchmark("Current Ratio", "Retail", "Consumer", 1.5, 1.0, 2.0, 1800, datetime.now())
            ],
            "Debt to Equity": [
                RatioBenchmark("Debt to Equity", "Technology", "Software", 0.3, 0.1, 0.6, 1500, datetime.now()),
                RatioBenchmark("Debt to Equity", "Manufacturing", "Industrial", 0.8, 0.4, 1.2, 1200, datetime.now()),
                RatioBenchmark("Debt to Equity", "Finance", "Banking", 2.1, 1.5, 2.8, 2000, datetime.now())
            ]
        }

        self.benchmarks = default_benchmarks

    def calculate_profitability_ratios(self, financial_data: Dict) -> Dict[str, FinancialRatio]:
        """Calculate profitability ratios"""
        ratios = {}

        # Return on Equity (ROE)
        if financial_data.get('net_income') and financial_data.get('shareholders_equity'):
            roe = (financial_data['net_income'] / financial_data['shareholders_equity']) * 100
            ratios['roe'] = FinancialRatio(
                name="ROE",
                value=roe,
                unit="%",
                description="Return on Equity measures profitability relative to shareholders' equity",
                calculation_method="Net Income / Shareholders' Equity",
                category="profitability"
            )

        # Return on Assets (ROA)
        if financial_data.get('net_income') and financial_data.get('total_assets'):
            roa = (financial_data['net_income'] / financial_data['total_assets']) * 100
            ratios['roa'] = FinancialRatio(
                name="ROA",
                value=roa,
                unit="%",
                description="Return on Assets measures profitability relative to total assets",
                calculation_method="Net Income / Total Assets",
                category="profitability"
            )

        # Gross Margin
        if financial_data.get('gross_profit') and financial_data.get('revenue'):
            gross_margin = (financial_data['gross_profit'] / financial_data['revenue']) * 100
            ratios['gross_margin'] = FinancialRatio(
                name="Gross Margin",
                value=gross_margin,
                unit="%",
                description="Gross Margin shows the percentage of revenue that exceeds the cost of goods sold",
                calculation_method="Gross Profit / Revenue",
                category="profitability"
            )

        # Net Margin
        if financial_data.get('net_income') and financial_data.get('revenue'):
            net_margin = (financial_data['net_income'] / financial_data['revenue']) * 100
            ratios['net_margin'] = FinancialRatio(
                name="Net Margin",
                value=net_margin,
                unit="%",
                description="Net Margin shows the percentage of revenue remaining after all expenses",
                calculation_method="Net Income / Revenue",
                category="profitability"
            )

        # EBIT Margin
        if financial_data.get('ebit') and financial_data.get('revenue'):
            ebit_margin = (financial_data['ebit'] / financial_data['revenue']) * 100
            ratios['ebit_margin'] = FinancialRatio(
                name="EBIT Margin",
                value=ebit_margin,
                unit="%",
                description="EBIT Margin shows operating profitability as a percentage of revenue",
                calculation_method="EBIT / Revenue",
                category="profitability"
            )

        # Operating Margin
        if financial_data.get('operating_income') and financial_data.get('revenue'):
            operating_margin = (financial_data['operating_income'] / financial_data['revenue']) * 100
            ratios['operating_margin'] = FinancialRatio(
                name="Operating Margin",
                value=operating_margin,
                unit="%",
                description="Operating Margin shows profitability from core operations",
                calculation_method="Operating Income / Revenue",
                category="profitability"
            )

        return ratios

    def calculate_liquidity_ratios(self, financial_data: Dict) -> Dict[str, FinancialRatio]:
        """Calculate liquidity ratios"""
        ratios = {}

        # Current Ratio
        if financial_data.get('current_assets') and financial_data.get('current_liabilities'):
            current_ratio = financial_data['current_assets'] / financial_data['current_liabilities']
            ratios['current_ratio'] = FinancialRatio(
                name="Current Ratio",
                value=current_ratio,
                unit="",
                description="Current Ratio measures ability to pay short-term obligations",
                calculation_method="Current Assets / Current Liabilities",
                category="liquidity"
            )

        # Quick Ratio (Acid Test)
        if all(k in financial_data for k in ['current_assets', 'inventory', 'current_liabilities']):
            quick_ratio = (financial_data['current_assets'] - financial_data['inventory']) / financial_data['current_liabilities']
            ratios['quick_ratio'] = FinancialRatio(
                name="Quick Ratio",
                value=quick_ratio,
                unit="",
                description="Quick Ratio measures ability to pay short-term obligations without selling inventory",
                calculation_method="(Current Assets - Inventory) / Current Liabilities",
                category="liquidity"
            )

        # Cash Ratio
        if financial_data.get('cash_equivalents') and financial_data.get('current_liabilities'):
            cash_ratio = financial_data['cash_equivalents'] / financial_data['current_liabilities']
            ratios['cash_ratio'] = FinancialRatio(
                name="Cash Ratio",
                value=cash_ratio,
                unit="",
                description="Cash Ratio measures ability to pay short-term obligations with cash and equivalents",
                calculation_method="Cash and Equivalents / Current Liabilities",
                category="liquidity"
            )

        # Working Capital Ratio
        if all(k in financial_data for k in ['current_assets', 'current_liabilities', 'total_assets']):
            working_capital = financial_data['current_assets'] - financial_data['current_liabilities']
            working_capital_ratio = working_capital / financial_data['total_assets']
            ratios['working_capital_ratio'] = FinancialRatio(
                name="Working Capital Ratio",
                value=working_capital_ratio,
                unit="",
                description="Working Capital Ratio shows the proportion of working capital to total assets",
                calculation_method="Working Capital / Total Assets",
                category="liquidity"
            )

        return ratios

    def calculate_efficiency_ratios(self, financial_data: Dict) -> Dict[str, FinancialRatio]:
        """Calculate efficiency ratios"""
        ratios = {}

        # Asset Turnover
        if financial_data.get('revenue') and financial_data.get('total_assets'):
            asset_turnover = financial_data['revenue'] / financial_data['total_assets']
            ratios['asset_turnover'] = FinancialRatio(
                name="Asset Turnover",
                value=asset_turnover,
                unit="",
                description="Asset Turnover measures how efficiently assets generate revenue",
                calculation_method="Revenue / Total Assets",
                category="efficiency"
            )

        # Inventory Turnover
        if financial_data.get('cost_of_goods_sold') and financial_data.get('inventory'):
            inventory_turnover = financial_data['cost_of_goods_sold'] / financial_data['inventory']
            ratios['inventory_turnover'] = FinancialRatio(
                name="Inventory Turnover",
                value=inventory_turnover,
                unit="",
                description="Inventory Turnover measures how many times inventory is sold and replaced",
                calculation_method="Cost of Goods Sold / Inventory",
                category="efficiency"
            )

        # Receivables Turnover
        if financial_data.get('revenue') and financial_data.get('accounts_receivable'):
            receivables_turnover = financial_data['revenue'] / financial_data['accounts_receivable']
            ratios['receivables_turnover'] = FinancialRatio(
                name="Receivables Turnover",
                value=receivables_turnover,
                unit="",
                description="Receivables Turnover measures how efficiently receivables are collected",
                calculation_method="Revenue / Accounts Receivable",
                category="efficiency"
            )

        # Payables Turnover
        if financial_data.get('cost_of_goods_sold') and financial_data.get('accounts_payable'):
            payables_turnover = financial_data['cost_of_goods_sold'] / financial_data['accounts_payable']
            ratios['payables_turnover'] = FinancialRatio(
                name="Payables Turnover",
                value=payables_turnover,
                unit="",
                description="Payables Turnover measures how quickly payables are paid",
                calculation_method="Cost of Goods Sold / Accounts Payable",
                category="efficiency"
            )

        return ratios

    def calculate_leverage_ratios(self, financial_data: Dict) -> Dict[str, FinancialRatio]:
        """Calculate leverage ratios"""
        ratios = {}

        # Debt to Equity
        if financial_data.get('total_debt') and financial_data.get('shareholders_equity'):
            debt_to_equity = financial_data['total_debt'] / financial_data['shareholders_equity']
            ratios['debt_to_equity'] = FinancialRatio(
                name="Debt to Equity",
                value=debt_to_equity,
                unit="",
                description="Debt to Equity measures the proportion of debt to equity financing",
                calculation_method="Total Debt / Shareholders' Equity",
                category="leverage"
            )

        # Debt to Assets
        if financial_data.get('total_debt') and financial_data.get('total_assets'):
            debt_to_assets = (financial_data['total_debt'] / financial_data['total_assets']) * 100
            ratios['debt_to_assets'] = FinancialRatio(
                name="Debt to Assets",
                value=debt_to_assets,
                unit="%",
                description="Debt to Assets shows the percentage of assets financed by debt",
                calculation_method="Total Debt / Total Assets",
                category="leverage"
            )

        # Equity Multiplier
        if financial_data.get('total_assets') and financial_data.get('shareholders_equity'):
            equity_multiplier = financial_data['total_assets'] / financial_data['shareholders_equity']
            ratios['equity_multiplier'] = FinancialRatio(
                name="Equity Multiplier",
                value=equity_multiplier,
                unit="",
                description="Equity Multiplier measures financial leverage",
                calculation_method="Total Assets / Shareholders' Equity",
                category="leverage"
            )

        # Interest Coverage
        if financial_data.get('ebit') and financial_data.get('interest_expense'):
            interest_coverage = financial_data['ebit'] / financial_data['interest_expense']
            ratios['interest_coverage'] = FinancialRatio(
                name="Interest Coverage",
                value=interest_coverage,
                unit="",
                description="Interest Coverage measures ability to pay interest on debt",
                calculation_method="EBIT / Interest Expense",
                category="leverage"
            )

        return ratios

    def calculate_growth_ratios(self, financial_data: Dict, historical_data: List[Dict]) -> Dict[str, FinancialRatio]:
        """Calculate growth ratios using historical data"""
        ratios = {}

        if len(historical_data) < 2:
            return ratios

        current_period = financial_data
        previous_period = historical_data[-2]

        # Revenue Growth
        if current_period.get('revenue') and previous_period.get('revenue'):
            revenue_growth = ((current_period['revenue'] - previous_period['revenue']) / previous_period['revenue']) * 100
            ratios['revenue_growth'] = FinancialRatio(
                name="Revenue Growth",
                value=revenue_growth,
                unit="%",
                description="Revenue Growth shows the percentage change in revenue",
                calculation_method="(Current Revenue - Previous Revenue) / Previous Revenue",
                category="growth"
            )

        # Earnings Growth
        if current_period.get('net_income') and previous_period.get('net_income'):
            earnings_growth = ((current_period['net_income'] - previous_period['net_income']) / previous_period['net_income']) * 100
            ratios['earnings_growth'] = FinancialRatio(
                name="Earnings Growth",
                value=earnings_growth,
                unit="%",
                description="Earnings Growth shows the percentage change in net income",
                calculation_method="(Current Net Income - Previous Net Income) / Previous Net Income",
                category="growth"
            )

        # Book Value Growth
        if current_period.get('shareholders_equity') and previous_period.get('shareholders_equity'):
            book_value_growth = ((current_period['shareholders_equity'] - previous_period['shareholders_equity']) / previous_period['shareholders_equity']) * 100
            ratios['book_value_growth'] = FinancialRatio(
                name="Book Value Growth",
                value=book_value_growth,
                unit="%",
                description="Book Value Growth shows the percentage change in shareholders' equity",
                calculation_method="(Current Equity - Previous Equity) / Previous Equity",
                category="growth"
            )

        return ratios

    def calculate_market_ratios(self, financial_data: Dict, market_data: Dict) -> Dict[str, FinancialRatio]:
        """Calculate market ratios using market data"""
        ratios = {}

        # Price to Earnings (P/E)
        if market_data.get('current_price') and financial_data.get('eps'):
            pe_ratio = market_data['current_price'] / financial_data['eps']
            ratios['price_to_earnings'] = FinancialRatio(
                name="P/E Ratio",
                value=pe_ratio,
                unit="",
                description="Price to Earnings ratio shows market valuation relative to earnings",
                calculation_method="Market Price per Share / Earnings per Share",
                category="market"
            )

        # Price to Book (P/B)
        if market_data.get('current_price') and financial_data.get('book_value_per_share'):
            pb_ratio = market_data['current_price'] / financial_data['book_value_per_share']
            ratios['price_to_book'] = FinancialRatio(
                name="P/B Ratio",
                value=pb_ratio,
                unit="",
                description="Price to Book ratio shows market valuation relative to book value",
                calculation_method="Market Price per Share / Book Value per Share",
                category="market"
            )

        # Price to Sales (P/S)
        if market_data.get('market_cap') and financial_data.get('revenue'):
            ps_ratio = market_data['market_cap'] / financial_data['revenue']
            ratios['price_to_sales'] = FinancialRatio(
                name="P/S Ratio",
                value=ps_ratio,
                unit="",
                description="Price to Sales ratio shows market valuation relative to revenue",
                calculation_method="Market Capitalization / Revenue",
                category="market"
            )

        # Dividend Yield
        if market_data.get('dividend_per_share') and market_data.get('current_price'):
            dividend_yield = (market_data['dividend_per_share'] / market_data['current_price']) * 100
            ratios['dividend_yield'] = FinancialRatio(
                name="Dividend Yield",
                value=dividend_yield,
                unit="%",
                description="Dividend Yield shows the return from dividends relative to price",
                calculation_method="Annual Dividend per Share / Market Price per Share",
                category="market"
            )

        return ratios

    def calculate_cash_flow_ratios(self, financial_data: Dict) -> Dict[str, FinancialRatio]:
        """Calculate cash flow ratios"""
        ratios = {}

        # Operating Cash Flow to Sales
        if financial_data.get('operating_cash_flow') and financial_data.get('revenue'):
            ocf_to_sales = (financial_data['operating_cash_flow'] / financial_data['revenue']) * 100
            ratios['operating_cash_flow_to_sales'] = FinancialRatio(
                name="Operating Cash Flow to Sales",
                value=ocf_to_sales,
                unit="%",
                description="Operating Cash Flow to Sales shows cash generation efficiency",
                calculation_method="Operating Cash Flow / Revenue",
                category="cash_flow"
            )

        # Free Cash Flow to Sales
        if financial_data.get('free_cash_flow') and financial_data.get('revenue'):
            fcf_to_sales = (financial_data['free_cash_flow'] / financial_data['revenue']) * 100
            ratios['free_cash_flow_to_sales'] = FinancialRatio(
                name="Free Cash Flow to Sales",
                value=fcf_to_sales,
                unit="%",
                description="Free Cash Flow to Sales shows free cash flow generation efficiency",
                calculation_method="Free Cash Flow / Revenue",
                category="cash_flow"
            )

        # Cash Flow to Debt
        if financial_data.get('operating_cash_flow') and financial_data.get('total_debt'):
            cash_flow_to_debt = financial_data['operating_cash_flow'] / financial_data['total_debt']
            ratios['cash_flow_to_debt'] = FinancialRatio(
                name="Cash Flow to Debt",
                value=cash_flow_to_debt,
                unit="",
                description="Cash Flow to Debt measures ability to service debt with cash flow",
                calculation_method="Operating Cash Flow / Total Debt",
                category="cash_flow"
            )

        return ratios

    def calculate_all_ratios(self, financial_data: Dict, historical_data: List[Dict] = None,
                          market_data: Dict = None, industry: str = None, sector: str = None) -> Dict[str, FinancialRatio]:
        """Calculate all financial ratios"""
        all_ratios = {}

        # Calculate all ratio categories
        all_ratios.update(self.calculate_profitability_ratios(financial_data))
        all_ratios.update(self.calculate_liquidity_ratios(financial_data))
        all_ratios.update(self.calculate_efficiency_ratios(financial_data))
        all_ratios.update(self.calculate_leverage_ratios(financial_data))
        all_ratios.update(self.calculate_cash_flow_ratios(financial_data))

        # Calculate growth ratios if historical data is available
        if historical_data:
            all_ratios.update(self.calculate_growth_ratios(financial_data, historical_data))

        # Calculate market ratios if market data is available
        if market_data:
            all_ratios.update(self.calculate_market_ratios(financial_data, market_data))

        # Add benchmarks and percentiles
        for ratio_name, ratio in all_ratios.items():
            self._add_benchmark_and_percentile(ratio, industry, sector)

        return all_ratios

    def _add_benchmark_and_percentile(self, ratio: FinancialRatio, industry: str = None, sector: str = None):
        """Add benchmark and percentile information to a ratio"""
        if ratio.name in self.benchmarks:
            benchmarks = self.benchmarks[ratio.name]

            # Find matching benchmarks
            matching_benchmarks = []
            for benchmark in benchmarks:
                if (industry is None or benchmark.industry == industry) and \
                   (sector is None or benchmark.sector == sector):
                    matching_benchmarks.append(benchmark)

            if matching_benchmarks:
                # Use the most specific match
                selected_benchmark = matching_benchmarks[0]
                ratio.benchmark = selected_benchmark.median

                # Calculate percentile (simplified approach)
                if ratio.value <= selected_benchmark.percentile_25:
                    ratio.percentile = 25
                elif ratio.value <= selected_benchmark.median:
                    ratio.percentile = 50
                elif ratio.value <= selected_benchmark.percentile_75:
                    ratio.percentile = 75
                else:
                    ratio.percentile = 90

    def calculate_altman_z_score(self, financial_data: Dict, market_data: Dict) -> Optional[float]:
        """Calculate Altman Z-Score for bankruptcy prediction"""
        try:
            # Altman Z-Score formula: Z = 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 1.0X5
            # X1 = Working Capital / Total Assets
            # X2 = Retained Earnings / Total Assets
            # X3 = EBIT / Total Assets
            # X4 = Market Value of Equity / Total Liabilities
            # X5 = Sales / Total Assets

            working_capital = financial_data.get('current_assets', 0) - financial_data.get('current_liabilities', 0)
            total_assets = financial_data.get('total_assets', 1)

            x1 = working_capital / total_assets
            x2 = financial_data.get('retained_earnings', 0) / total_assets
            x3 = financial_data.get('ebit', 0) / total_assets

            market_value_equity = market_data.get('market_cap', 0)
            total_liabilities = financial_data.get('total_liabilities', 1)
            x4 = market_value_equity / total_liabilities

            x5 = financial_data.get('revenue', 0) / total_assets

            z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

            return z_score

        except Exception as e:
            self.logger.error(f"Error calculating Altman Z-Score: {str(e)}")
            return None

    def calculate_quality_score(self, ratios: Dict[str, FinancialRatio]) -> float:
        """Calculate overall financial quality score"""
        if not ratios:
            return 0.0

        # Weight different categories
        category_weights = {
            "profitability": 0.25,
            "liquidity": 0.20,
            "efficiency": 0.15,
            "leverage": 0.20,
            "growth": 0.10,
            "cash_flow": 0.10
        }

        category_scores = {}

        for ratio in ratios.values():
            category = ratio.category
            if category not in category_scores:
                category_scores[category] = []

            # Score based on percentile or absolute value
            if ratio.percentile:
                score = ratio.percentile / 100
            else:
                # Fallback scoring based on ratio type
                score = self._score_ratio_by_type(ratio)

            category_scores[category].append(score)

        # Calculate weighted average
        total_score = 0.0
        for category, scores in category_scores.items():
            if scores and category in category_weights:
                avg_category_score = sum(scores) / len(scores)
                total_score += avg_category_score * category_weights[category]

        return min(max(total_score, 0.0), 1.0)

    def _score_ratio_by_type(self, ratio: FinancialRatio) -> float:
        """Score a ratio based on its type and absolute value"""
        value = ratio.value

        # Scoring logic for different ratio types
        if ratio.name in ["ROE", "ROA", "Gross Margin", "Net Margin", "Operating Margin"]:
            # Higher is better
            if value > 20:
                return 0.9
            elif value > 15:
                return 0.8
            elif value > 10:
                return 0.7
            elif value > 5:
                return 0.6
            elif value > 0:
                return 0.5
            else:
                return 0.1

        elif ratio.name in ["Current Ratio", "Quick Ratio"]:
            # Optimal range 1.5-2.5
            if 1.5 <= value <= 2.5:
                return 0.9
            elif 1.0 <= value <= 3.0:
                return 0.8
            elif 0.5 <= value <= 4.0:
                return 0.6
            else:
                return 0.3

        elif ratio.name in ["Debt to Equity", "Debt to Assets"]:
            # Lower is better
            if value < 0.2:
                return 0.9
            elif value < 0.5:
                return 0.8
            elif value < 1.0:
                return 0.6
            elif value < 2.0:
                return 0.4
            else:
                return 0.2

        elif ratio.name in ["Asset Turnover", "Inventory Turnover"]:
            # Higher is better
            if value > 2.0:
                return 0.9
            elif value > 1.5:
                return 0.8
            elif value > 1.0:
                return 0.7
            elif value > 0.5:
                return 0.6
            else:
                return 0.4

        # Default score
        return 0.5

    def get_ratio_trends(self, historical_ratios: List[Dict[str, FinancialRatio]], ratio_name: str) -> Optional[str]:
        """Calculate trend for a specific ratio over time"""
        if len(historical_ratios) < 2:
            return None

        values = []
        for period_ratios in historical_ratios:
            if ratio_name in period_ratios and period_ratios[ratio_name].value is not None:
                values.append(period_ratios[ratio_name].value)

        if len(values) < 2:
            return None

        # Simple trend calculation
        if values[-1] > values[-2] * 1.05:
            return "Increasing"
        elif values[-1] < values[-2] * 0.95:
            return "Decreasing"
        else:
            return "Stable"

    def export_ratios_to_csv(self, ratios: Dict[str, FinancialRatio], filepath: str):
        """Export ratios to CSV file"""
        import csv

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'value', 'unit', 'category', 'description', 'benchmark', 'percentile', 'trend']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for ratio in ratios.values():
                writer.writerow({
                    'name': ratio.name,
                    'value': ratio.value,
                    'unit': ratio.unit,
                    'category': ratio.category,
                    'description': ratio.description,
                    'benchmark': ratio.benchmark,
                    'percentile': ratio.percentile,
                    'trend': ratio.trend
                })

        self.logger.info(f"Ratios exported to {filepath}")

    def import_ratios_from_csv(self, filepath: str) -> Dict[str, FinancialRatio]:
        """Import ratios from CSV file"""
        ratios = {}

        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    ratio = FinancialRatio(
                        name=row['name'],
                        value=float(row['value']),
                        unit=row['unit'],
                        category=row['category'],
                        description=row['description'],
                        benchmark=float(row['benchmark']) if row['benchmark'] else None,
                        percentile=float(row['percentile']) if row['percentile'] else None,
                        trend=row['trend'] if row['trend'] else None
                    )
                    ratios[ratio.name] = ratio

            self.logger.info(f"Ratios imported from {filepath}")
            return ratios

        except Exception as e:
            self.logger.error(f"Error importing ratios from {filepath}: {str(e)}")
            return {}

    def validate_ratios(self, ratios: Dict[str, FinancialRatio]) -> Dict[str, List[str]]:
        """Validate calculated ratios for reasonableness"""
        validation_results = {
            "warnings": [],
            "errors": []
        }

        for ratio_name, ratio in ratios.items():
            # Check for extreme values
            if ratio.value is not None:
                if ratio.unit == "%" and (ratio.value > 1000 or ratio.value < -1000):
                    validation_results["warnings"].append(f"Extreme percentage value for {ratio_name}: {ratio.value}%")

                if ratio_name in ["Current Ratio", "Quick Ratio"] and ratio.value > 10:
                    validation_results["warnings"].append(f"Unusually high liquidity ratio for {ratio_name}: {ratio.value}")

                if ratio_name in ["Debt to Equity"] and ratio.value > 10:
                    validation_results["warnings"].append(f"Extremely high leverage for {ratio_name}: {ratio.value}")

                if ratio_name in ["ROE", "ROA"] and ratio.value > 100:
                    validation_results["warnings"].append(f"Unusually high return ratio for {ratio_name}: {ratio.value}%")

        return validation_results