"""
Data Models
Structured data models for financial information
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from decimal import Decimal
import pandas as pd


@dataclass
class DataQuality:
    """Data quality metrics"""
    completeness: float = 0.0  # 0-1 scale
    accuracy: float = 0.0      # 0-1 scale
    timeliness: float = 0.0    # 0-1 scale
    consistency: float = 0.0   # 0-1 scale
    overall_score: float = 0.0  # 0-1 scale

    def __post_init__(self):
        # Validate ranges
        for metric in [self.completeness, self.accuracy, self.timeliness, self.consistency, self.overall_score]:
            if not 0 <= metric <= 1:
                raise ValueError(f"Data quality metrics must be between 0 and 1, got {metric}")

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "completeness": self.completeness,
            "accuracy": self.accuracy,
            "timeliness": self.timeliness,
            "consistency": self.consistency,
            "overall_score": self.overall_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'DataQuality':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class PriceData:
    """Price data point"""
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "date": self.date.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "adjusted_close": self.adjusted_close
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceData':
        """Create from dictionary"""
        return cls(
            date=datetime.fromisoformat(data["date"]),
            open=float(data["open"]),
            high=float(data["high"]),
            low=float(data["low"]),
            close=float(data["close"]),
            volume=int(data["volume"]),
            adjusted_close=float(data["adjusted_close"]) if data.get("adjusted_close") else None
        )


@dataclass
class MarketData:
    """Market data container"""
    symbol: str
    current_price: float
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    price_history: List[PriceData] = field(default_factory=list)
    _52_week_high: Optional[float] = None
    _52_week_low: Optional[float] = None
    avg_volume: Optional[int] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    data_quality: Optional[DataQuality] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "current_price": self.current_price,
            "market_cap": self.market_cap,
            "enterprise_value": self.enterprise_value,
            "trailing_pe": self.trailing_pe,
            "forward_pe": self.forward_pe,
            "dividend_yield": self.dividend_yield,
            "beta": self.beta,
            "price_history": [p.to_dict() for p in self.price_history],
            "52_week_high": self._52_week_high,
            "52_week_low": self._52_week_low,
            "avg_volume": self.avg_volume,
            "currency": self.currency,
            "exchange": self.exchange,
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        """Create from dictionary"""
        return cls(
            symbol=data["symbol"],
            current_price=float(data["current_price"]),
            market_cap=float(data["market_cap"]) if data.get("market_cap") else None,
            enterprise_value=float(data["enterprise_value"]) if data.get("enterprise_value") else None,
            trailing_pe=float(data["trailing_pe"]) if data.get("trailing_pe") else None,
            forward_pe=float(data["forward_pe"]) if data.get("forward_pe") else None,
            dividend_yield=float(data["dividend_yield"]) if data.get("dividend_yield") else None,
            beta=float(data["beta"]) if data.get("beta") else None,
            price_history=[PriceData.from_dict(p) for p in data.get("price_history", [])],
            _52_week_high=float(data["52_week_high"]) if data.get("52_week_high") else None,
            _52_week_low=float(data["52_week_low"]) if data.get("52_week_low") else None,
            avg_volume=int(data["avg_volume"]) if data.get("avg_volume") else None,
            currency=data.get("currency"),
            exchange=data.get("exchange"),
            data_quality=DataQuality.from_dict(data["data_quality"]) if data.get("data_quality") else None,
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else None
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Convert price history to pandas DataFrame"""
        if not self.price_history:
            return pd.DataFrame()

        data = [p.to_dict() for p in self.price_history]
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df

    def calculate_returns(self, period: str = 'daily') -> pd.Series:
        """Calculate returns"""
        df = self.to_dataframe()
        if df.empty:
            return pd.Series()

        if period == 'daily':
            return df['close'].pct_change().dropna()
        elif period == 'weekly':
            return df['close'].resample('W').last().pct_change().dropna()
        elif period == 'monthly':
            return df['close'].resample('M').last().pct_change().dropna()
        else:
            raise ValueError(f"Unsupported period: {period}")


@dataclass
class FinancialStatement:
    """Financial statement data"""
    statement_type: str  # "income", "balance", "cash_flow"
    period: str  # "annual", "quarterly"
    data: Dict[str, Dict[str, float]]  # {year: {account: value}}
    currency: Optional[str] = None
    data_quality: Optional[DataQuality] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "statement_type": self.statement_type,
            "period": self.period,
            "data": self.data,
            "currency": self.currency,
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinancialStatement':
        """Create from dictionary"""
        return cls(
            statement_type=data["statement_type"],
            period=data["period"],
            data=data["data"],
            currency=data.get("currency"),
            data_quality=DataQuality.from_dict(data["data_quality"]) if data.get("data_quality") else None,
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else None
        )

    def get_latest_year(self) -> Optional[str]:
        """Get the latest year available"""
        if not self.data:
            return None
        return max(self.data.keys())

    def get_value(self, account: str, year: Optional[str] = None) -> Optional[float]:
        """Get value for a specific account and year"""
        if year is None:
            year = self.get_latest_year()
        if not year or year not in self.data:
            return None
        return self.data[year].get(account)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame"""
        if not self.data:
            return pd.DataFrame()

        df = pd.DataFrame(self.data).T
        df.index.name = 'year'
        return df


@dataclass
class FinancialData:
    """Comprehensive financial data container"""
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

    # Financial statements
    income_statement: Optional[FinancialStatement] = None
    balance_sheet: Optional[FinancialStatement] = None
    cash_flow: Optional[FinancialStatement] = None

    # Quarterly statements
    quarterly_income: Optional[FinancialStatement] = None
    quarterly_balance: Optional[FinancialStatement] = None
    quarterly_cash_flow: Optional[FinancialStatement] = None

    # Market data
    market_data: Optional[MarketData] = None

    # Analyst data
    analyst_ratings: Optional[Dict[str, Any]] = None
    earnings_estimates: Optional[Dict[str, Any]] = None
    price_targets: Optional[Dict[str, Any]] = None

    # Ownership data
    institutional_holders: Optional[List[Dict[str, Any]]] = None
    insider_ownership: Optional[Dict[str, Any]] = None
    major_holders: Optional[List[Dict[str, Any]]] = None

    # Options data
    options_expirations: Optional[List[str]] = None
    options_chain: Optional[Dict[str, Any]] = None

    # Metadata
    data_sources: List[str] = field(default_factory=list)
    data_quality: Optional[DataQuality] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "sector": self.sector,
            "industry": self.industry,
            "description": self.description,
            "income_statement": self.income_statement.to_dict() if self.income_statement else None,
            "balance_sheet": self.balance_sheet.to_dict() if self.balance_sheet else None,
            "cash_flow": self.cash_flow.to_dict() if self.cash_flow else None,
            "quarterly_income": self.quarterly_income.to_dict() if self.quarterly_income else None,
            "quarterly_balance": self.quarterly_balance.to_dict() if self.quarterly_balance else None,
            "quarterly_cash_flow": self.quarterly_cash_flow.to_dict() if self.quarterly_cash_flow else None,
            "market_data": self.market_data.to_dict() if self.market_data else None,
            "analyst_ratings": self.analyst_ratings,
            "earnings_estimates": self.earnings_estimates,
            "price_targets": self.price_targets,
            "institutional_holders": self.institutional_holders,
            "insider_ownership": self.insider_ownership,
            "major_holders": self.major_holders,
            "options_expirations": self.options_expirations,
            "options_chain": self.options_chain,
            "data_sources": self.data_sources,
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinancialData':
        """Create from dictionary"""
        return cls(
            symbol=data["symbol"],
            company_name=data.get("company_name"),
            sector=data.get("sector"),
            industry=data.get("industry"),
            description=data.get("description"),
            income_statement=FinancialStatement.from_dict(data["income_statement"]) if data.get("income_statement") else None,
            balance_sheet=FinancialStatement.from_dict(data["balance_sheet"]) if data.get("balance_sheet") else None,
            cash_flow=FinancialStatement.from_dict(data["cash_flow"]) if data.get("cash_flow") else None,
            quarterly_income=FinancialStatement.from_dict(data["quarterly_income"]) if data.get("quarterly_income") else None,
            quarterly_balance=FinancialStatement.from_dict(data["quarterly_balance"]) if data.get("quarterly_balance") else None,
            quarterly_cash_flow=FinancialStatement.from_dict(data["quarterly_cash_flow"]) if data.get("quarterly_cash_flow") else None,
            market_data=MarketData.from_dict(data["market_data"]) if data.get("market_data") else None,
            analyst_ratings=data.get("analyst_ratings"),
            earnings_estimates=data.get("earnings_estimates"),
            price_targets=data.get("price_targets"),
            institutional_holders=data.get("institutional_holders"),
            insider_ownership=data.get("insider_ownership"),
            major_holders=data.get("major_holders"),
            options_expirations=data.get("options_expirations"),
            options_chain=data.get("options_chain"),
            data_sources=data.get("data_sources", []),
            data_quality=DataQuality.from_dict(data["data_quality"]) if data.get("data_quality") else None,
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else None
        )

    def get_financial_ratios(self, year: Optional[str] = None) -> Dict[str, float]:
        """Calculate key financial ratios"""
        ratios = {}

        if not self.income_statement or not self.balance_sheet:
            return ratios

        if year is None:
            year = self.income_statement.get_latest_year()

        if not year:
            return ratios

        # Get financial statement data
        income_data = self.income_statement.data.get(year, {})
        balance_data = self.balance_sheet.data.get(year, {})
        cash_data = self.cash_flow.data.get(year, {}) if self.cash_flow else {}

        # Extract values
        revenue = income_data.get('Total Revenue', 0)
        net_income = income_data.get('Net Income', 0)
        gross_profit = income_data.get('Gross Profit', 0)
        ebit = income_data.get('EBIT', 0)

        total_assets = balance_data.get('Total Assets', 0)
        total_equity = balance_data.get('Total Stockholder Equity', 0)
        total_debt = balance_data.get('Total Debt', 0)
        current_assets = balance_data.get('Total Current Assets', 0)
        current_liabilities = balance_data.get('Total Current Liabilities', 0)
        inventory = balance_data.get('Inventory', 0)

        operating_cf = cash_data.get('Operating Cash Flow', 0)

        # Calculate ratios
        if revenue > 0:
            ratios['gross_margin'] = (gross_profit / revenue) * 100
            ratios['net_margin'] = (net_income / revenue) * 100
            ratios['ebit_margin'] = (ebit / revenue) * 100

        if total_equity > 0:
            ratios['roe'] = (net_income / total_equity) * 100

        if total_assets > 0:
            ratios['roa'] = (net_income / total_assets) * 100
            ratios['asset_turnover'] = revenue / total_assets

        if total_assets > 0:
            ratios['debt_ratio'] = (total_debt / total_assets) * 100

        if current_liabilities > 0:
            ratios['current_ratio'] = current_assets / current_liabilities
            ratios['quick_ratio'] = (current_assets - inventory) / current_liabilities

        if revenue > 0:
            ratios['ocf_ratio'] = (operating_cf / revenue) * 100

        return ratios

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary financial metrics"""
        return {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "sector": self.sector,
            "industry": self.industry,
            "current_price": self.market_data.current_price if self.market_data else None,
            "market_cap": self.market_data.market_cap if self.market_data else None,
            "pe_ratio": self.market_data.trailing_pe if self.market_data else None,
            "dividend_yield": self.market_data.dividend_yield if self.market_data else None,
            "beta": self.market_data.beta if self.market_data else None,
            "52_week_high": self.market_data._52_week_high if self.market_data else None,
            "52_week_low": self.market_data._52_week_low if self.market_data else None,
            "data_quality": self.data_quality.overall_score if self.data_quality else 0.0,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


@dataclass
class CollectionResult:
    """Result of data collection operation"""
    success: bool
    symbol: str
    data: Optional[FinancialData] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    data_sources_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str):
        """Add error message"""
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str):
        """Add warning message"""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "symbol": self.symbol,
            "data": self.data.to_dict() if self.data else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "execution_time": self.execution_time,
            "data_sources_used": self.data_sources_used,
            "metadata": self.metadata
        }