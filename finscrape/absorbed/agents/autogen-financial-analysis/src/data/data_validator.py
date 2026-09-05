"""
Data Validator
Validation and quality assessment for financial data
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np
from .data_models import FinancialData, MarketData, DataQuality, CollectionResult


@dataclass
class ValidationRule:
    """Individual validation rule"""
    name: str
    description: str
    severity: str  # "error", "warning", "info"
    condition: callable
    message_template: str

    def validate(self, data: Any) -> Optional[Dict[str, Any]]:
        """Validate data against this rule"""
        try:
            result = self.condition(data)
            if not result:
                return {
                    "rule": self.name,
                    "severity": self.severity,
                    "message": self.message_template,
                    "timestamp": datetime.now().isoformat()
                }
            return None
        except Exception as e:
            return {
                "rule": self.name,
                "severity": "error",
                "message": f"Validation error in {self.name}: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }


class DataValidator:
    """Comprehensive data validation for financial data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rules = self._initialize_validation_rules()

    def _initialize_validation_rules(self) -> Dict[str, List[ValidationRule]]:
        """Initialize all validation rules"""
        return {
            "market_data": self._get_market_data_rules(),
            "financial_statements": self._get_financial_statement_rules(),
            "completeness": self._get_completeness_rules(),
            "consistency": self._get_consistency_rules(),
            "timeliness": self._get_timeliness_rules()
        }

    def _get_market_data_rules(self) -> List[ValidationRule]:
        """Get market data validation rules"""
        return [
            ValidationRule(
                name="positive_price",
                description="Current price must be positive",
                severity="error",
                condition=lambda data: data.current_price > 0,
                message_template="Current price must be positive"
            ),
            ValidationRule(
                name="reasonable_price_range",
                description="Price should be within reasonable bounds",
                severity="warning",
                condition=lambda data: 0.01 <= data.current_price <= 1000000,
                message_template="Price {price} is outside reasonable range"
            ),
            ValidationRule(
                name="non_zero_volume",
                description="Average volume should not be zero",
                severity="warning",
                condition=lambda data: data.avg_volume is None or data.avg_volume > 0,
                message_template="Average volume should not be zero"
            ),
            ValidationRule(
                name="sufficient_price_history",
                description="Should have sufficient price history",
                severity="warning",
                condition=lambda data: len(data.price_history) >= 30,
                message_template="Insufficient price history ({count} data points)"
            ),
            ValidationRule(
                name="chronological_order",
                description="Price history should be in chronological order",
                severity="error",
                condition=lambda data: self._check_chronological_order(data.price_history),
                message_template="Price history is not in chronological order"
            )
        ]

    def _get_financial_statement_rules(self) -> List[ValidationRule]:
        """Get financial statement validation rules"""
        return [
            ValidationRule(
                name="positive_revenue",
                description="Revenue should be positive",
                severity="error",
                condition=lambda data: self._check_positive_revenue(data),
                message_template="Revenue should be positive"
            ),
            ValidationRule(
                name="balance_sheet_equation",
                description="Assets = Liabilities + Equity",
                severity="error",
                condition=lambda data: self._check_balance_sheet_equation(data),
                message_template="Balance sheet equation not satisfied"
            ),
            ValidationRule(
                name="cash_flow_consistency",
                description="Cash flow should be consistent with balance sheet changes",
                severity="warning",
                condition=lambda data: self._check_cash_flow_consistency(data),
                message_template="Cash flow inconsistency detected"
            ),
            ValidationRule(
                name="reasonable_growth_rates",
                description="Growth rates should be reasonable",
                severity="warning",
                condition=lambda data: self._check_reasonable_growth_rates(data),
                message_template="Unreasonable growth rates detected"
            )
        ]

    def _get_completeness_rules(self) -> List[ValidationRule]:
        """Get completeness validation rules"""
        return [
            ValidationRule(
                name="required_fields_present",
                description="Required fields should be present",
                severity="error",
                condition=lambda data: self._check_required_fields(data),
                message_template="Missing required fields"
            ),
            ValidationRule(
                name="minimum_data_points",
                description="Should have minimum required data points",
                severity="warning",
                condition=lambda data: self._check_minimum_data_points(data),
                message_template="Insufficient data points"
            )
        ]

    def _get_consistency_rules(self) -> List[ValidationRule]:
        """Get consistency validation rules"""
        return [
            ValidationRule(
                name="currency_consistency",
                description="Currency should be consistent across data",
                severity="warning",
                condition=lambda data: self._check_currency_consistency(data),
                message_template="Currency inconsistency detected"
            ),
            ValidationRule(
                name="date_consistency",
                description="Dates should be consistent across data sources",
                severity="warning",
                condition=lambda data: self._check_date_consistency(data),
                message_template="Date inconsistency detected"
            ),
            ValidationRule(
                name="value_ranges_consistency",
                description="Values should be within reasonable ranges",
                severity="warning",
                condition=lambda data: self._check_value_ranges(data),
                message_template="Values outside expected ranges"
            )
        ]

    def _get_timeliness_rules(self) -> List[ValidationRule]:
        """Get timeliness validation rules"""
        return [
            ValidationRule(
                name="recent_data",
                description="Data should be recent",
                severity="warning",
                condition=lambda data: self._check_data_recency(data),
                message_template="Data is stale (last updated: {date})"
            ),
            ValidationRule(
                name="frequent_updates",
                description="Price data should be updated frequently",
                severity="warning",
                condition=lambda data: self._check_update_frequency(data),
                message_template="Data update frequency is low"
            )
        ]

    def validate_financial_data(self, data: FinancialData) -> Dict[str, Any]:
        """Validate complete financial data"""
        validation_results = {
            "symbol": data.symbol,
            "validation_timestamp": datetime.now().isoformat(),
            "errors": [],
            "warnings": [],
            "info": [],
            "overall_valid": True,
            "quality_score": 1.0,
            "rule_results": {}
        }

        # Validate market data
        if data.market_data:
            market_results = self.validate_market_data(data.market_data)
            self._merge_validation_results(validation_results, market_results, "market_data")

        # Validate financial statements
        statement_results = self.validate_financial_statements(data)
        self._merge_validation_results(validation_results, statement_results, "financial_statements")

        # Validate completeness
        completeness_results = self.validate_completeness(data)
        self._merge_validation_results(validation_results, completeness_results, "completeness")

        # Validate consistency
        consistency_results = self.validate_consistency(data)
        self._merge_validation_results(validation_results, consistency_results, "consistency")

        # Validate timeliness
        timeliness_results = self.validate_timeliness(data)
        self._merge_validation_results(validation_results, timeliness_results, "timeliness")

        # Calculate overall quality score
        validation_results["quality_score"] = self._calculate_quality_score(validation_results)
        validation_results["overall_valid"] = len(validation_results["errors"]) == 0

        return validation_results

    def validate_market_data(self, market_data: MarketData) -> Dict[str, Any]:
        """Validate market data"""
        results = {
            "errors": [],
            "warnings": [],
            "info": [],
            "rule_results": {}
        }

        for rule in self.rules["market_data"]:
            rule_result = rule.validate(market_data)
            if rule_result:
                results["rule_results"][rule.name] = rule_result
                self._add_validation_result(results, rule_result)

        return results

    def validate_financial_statements(self, financial_data: FinancialData) -> Dict[str, Any]:
        """Validate financial statements"""
        results = {
            "errors": [],
            "warnings": [],
            "info": [],
            "rule_results": {}
        }

        for rule in self.rules["financial_statements"]:
            rule_result = rule.validate(financial_data)
            if rule_result:
                results["rule_results"][rule.name] = rule_result
                self._add_validation_result(results, rule_result)

        return results

    def validate_completeness(self, data: FinancialData) -> Dict[str, Any]:
        """Validate data completeness"""
        results = {
            "errors": [],
            "warnings": [],
            "info": [],
            "rule_results": {}
        }

        for rule in self.rules["completeness"]:
            rule_result = rule.validate(data)
            if rule_result:
                results["rule_results"][rule.name] = rule_result
                self._add_validation_result(results, rule_result)

        return results

    def validate_consistency(self, data: FinancialData) -> Dict[str, Any]:
        """Validate data consistency"""
        results = {
            "errors": [],
            "warnings": [],
            "info": [],
            "rule_results": {}
        }

        for rule in self.rules["consistency"]:
            rule_result = rule.validate(data)
            if rule_result:
                results["rule_results"][rule.name] = rule_result
                self._add_validation_result(results, rule_result)

        return results

    def validate_timeliness(self, data: FinancialData) -> Dict[str, Any]:
        """Validate data timeliness"""
        results = {
            "errors": [],
            "warnings": [],
            "info": [],
            "rule_results": {}
        }

        for rule in self.rules["timeliness"]:
            rule_result = rule.validate(data)
            if rule_result:
                results["rule_results"][rule.name] = rule_result
                self._add_validation_result(results, rule_result)

        return results

    def _merge_validation_results(self, target: Dict[str, Any], source: Dict[str, Any], category: str):
        """Merge validation results"""
        target["errors"].extend(source["errors"])
        target["warnings"].extend(source["warnings"])
        target["info"].extend(source["info"])
        target["rule_results"][category] = source["rule_results"]

    def _add_validation_result(self, results: Dict[str, Any], rule_result: Dict[str, Any]):
        """Add validation result to appropriate category"""
        severity = rule_result["severity"]
        if severity == "error":
            results["errors"].append(rule_result)
        elif severity == "warning":
            results["warnings"].append(rule_result)
        else:
            results["info"].append(rule_result)

    def _calculate_quality_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall data quality score"""
        total_rules = len(validation_results["rule_results"])
        if total_rules == 0:
            return 1.0

        passed_rules = total_rules - len(validation_results["errors"]) - len(validation_results["warnings"])
        return passed_rules / total_rules

    # Helper methods for validation rules
    def _check_chronological_order(self, price_history: List) -> bool:
        """Check if price history is in chronological order"""
        if len(price_history) < 2:
            return True
        return all(price_history[i].date <= price_history[i+1].date for i in range(len(price_history)-1))

    def _check_positive_revenue(self, data: FinancialData) -> bool:
        """Check if revenue is positive"""
        if not data.income_statement:
            return True
        latest_year = data.income_statement.get_latest_year()
        if not latest_year:
            return True
        revenue = data.income_statement.get_value("Total Revenue", latest_year)
        return revenue is None or revenue > 0

    def _check_balance_sheet_equation(self, data: FinancialData) -> bool:
        """Check balance sheet equation"""
        if not data.balance_sheet:
            return True
        latest_year = data.balance_sheet.get_latest_year()
        if not latest_year:
            return True

        assets = data.balance_sheet.get_value("Total Assets", latest_year)
        liabilities = data.balance_sheet.get_value("Total Liabilities", latest_year)
        equity = data.balance_sheet.get_value("Total Stockholder Equity", latest_year)

        if assets is None or liabilities is None or equity is None:
            return True

        return abs(assets - (liabilities + equity)) < max(assets * 0.01, 1000)

    def _check_cash_flow_consistency(self, data: FinancialData) -> bool:
        """Check cash flow consistency"""
        # Simplified check - in practice, this would be more complex
        return True

    def _check_reasonable_growth_rates(self, data: FinancialData) -> bool:
        """Check if growth rates are reasonable"""
        # Simplified check - in practice, this would analyze year-over-year changes
        return True

    def _check_required_fields(self, data: FinancialData) -> bool:
        """Check if required fields are present"""
        return (data.symbol is not None and
                data.market_data is not None and
                data.market_data.current_price is not None)

    def _check_minimum_data_points(self, data: FinancialData) -> bool:
        """Check minimum data points"""
        if data.market_data and data.market_data.price_history:
            return len(data.market_data.price_history) >= 10
        return True

    def _check_currency_consistency(self, data: FinancialData) -> bool:
        """Check currency consistency"""
        currencies = set()
        if data.market_data and data.market_data.currency:
            currencies.add(data.market_data.currency)
        if data.income_statement and data.income_statement.currency:
            currencies.add(data.income_statement.currency)
        if data.balance_sheet and data.balance_sheet.currency:
            currencies.add(data.balance_sheet.currency)
        return len(currencies) <= 1

    def _check_date_consistency(self, data: FinancialData) -> bool:
        """Check date consistency"""
        # Simplified check - in practice, this would compare dates across data sources
        return True

    def _check_value_ranges(self, data: FinancialData) -> bool:
        """Check if values are within reasonable ranges"""
        # Simplified check - in practice, this would validate financial ratios and metrics
        return True

    def _check_data_recency(self, data: FinancialData) -> bool:
        """Check if data is recent"""
        if not data.last_updated:
            return False

        # Data should be less than 7 days old
        age = datetime.now() - data.last_updated
        return age.days <= 7

    def _check_update_frequency(self, data: FinancialData) -> bool:
        """Check update frequency"""
        # Simplified check - in practice, this would analyze historical update patterns
        return True

    def validate_collection_result(self, result: CollectionResult) -> CollectionResult:
        """Validate collection result and enhance with validation info"""
        if result.data:
            validation_results = self.validate_financial_data(result.data)
            result.metadata["validation"] = validation_results

            # Add validation warnings/errors to result
            for error in validation_results["errors"]:
                result.add_error(error["message"])

            for warning in validation_results["warnings"]:
                result.add_warning(warning["message"])

            # Update data quality
            if result.data.data_quality:
                result.data.data_quality.overall_score = validation_results["quality_score"]

        return result

    def create_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """Create human-readable validation report"""
        report = f"Validation Report for {validation_results['symbol']}\n"
        report += "=" * 50 + "\n\n"

        report += f"Validation Timestamp: {validation_results['validation_timestamp']}\n"
        report += f"Overall Valid: {validation_results['overall_valid']}\n"
        report += f"Quality Score: {validation_results['quality_score']:.2%}\n\n"

        if validation_results["errors"]:
            report += "ERRORS:\n"
            for error in validation_results["errors"]:
                report += f"  - {error['message']} (Rule: {error['rule']})\n"
            report += "\n"

        if validation_results["warnings"]:
            report += "WARNINGS:\n"
            for warning in validation_results["warnings"]:
                report += f"  - {warning['message']} (Rule: {warning['rule']})\n"
            report += "\n"

        if validation_results["info"]:
            report += "INFO:\n"
            for info in validation_results["info"]:
                report += f"  - {info['message']} (Rule: {info['rule']})\n"
            report += "\n"

        return report