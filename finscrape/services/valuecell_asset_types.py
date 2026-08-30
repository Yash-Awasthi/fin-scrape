"""
ValueCell Asset Types — Extracted from ValueCell patterns.

Multi-source asset data structures with:
- Asset type enumeration (stock, crypto, ETF, index)
- Exchange support (NASDAQ, NYSE, SSE, HKEX, etc.)
- Market status tracking
- Data source adapters (yfinance, akshare, baostock)
- Interval-based historical data
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class AssetType(Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    ETF = "etf"
    INDEX = "index"


class Exchange(Enum):
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    AMEX = "AMEX"
    SSE = "SSE"
    SZSE = "SZSE"
    BSE = "BSE"
    HKEX = "HKEX"
    CRYPTO = "CRYPTO"


class MarketStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"
    HALTED = "halted"
    UNKNOWN = "unknown"


class DataSource(Enum):
    YFINANCE = "yfinance"
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"


class Interval(Enum):
    MINUTE = "m"
    HOUR = "h"
    DAY = "d"
    WEEK = "w"
    MONTH = "mo"
    YEAR = "y"


@dataclass
class Asset:
    symbol: str
    name: str
    asset_type: AssetType
    exchange: Exchange
    currency: str = "USD"
    market_status: MarketStatus = MarketStatus.UNKNOWN
    last_price: Optional[float] = None
    last_updated: str = ""

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


@dataclass
class OHLCVBar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str = ""
    source: DataSource = DataSource.YFINANCE


@dataclass
class AssetQuote:
    symbol: str
    price: float
    change: float
    change_pct: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class AssetSnapshot:
    asset: Asset
    quote: Optional[AssetQuote] = None
    historical_bars: List[OHLCVBar] = field(default_factory=list)
    news: List[Dict[str, Any]] = field(default_factory=list)
    fundamentals: Dict[str, Any] = field(default_factory=dict)


class AssetAdapter:
    """Base class for data source adapters."""

    def __init__(self, source: DataSource) -> None:
        self.source = source

    def fetch_quote(self, symbol: str) -> Optional[AssetQuote]:
        raise NotImplementedError

    def fetch_historical(
        self,
        symbol: str,
        interval: Interval = Interval.DAY,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[OHLCVBar]:
        raise NotImplementedError

    def search(self, query: str) -> List[Asset]:
        raise NotImplementedError

    def get_market_status(self, exchange: Exchange) -> MarketStatus:
        raise NotImplementedError


class YFinanceAdapter(AssetAdapter):
    """Adapter for yfinance data source."""

    def __init__(self) -> None:
        super().__init__(DataSource.YFINANCE)

    def fetch_quote(self, symbol: str) -> Optional[AssetQuote]:
        # Pattern extraction — actual yfinance calls would go here
        return AssetQuote(
            symbol=symbol,
            price=0.0,
            change=0.0,
            change_pct=0.0,
            volume=0,
        )

    def fetch_historical(
        self,
        symbol: str,
        interval: Interval = Interval.DAY,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[OHLCVBar]:
        return []

    def search(self, query: str) -> List[Asset]:
        return []

    def get_market_status(self, exchange: Exchange) -> MarketStatus:
        return MarketStatus.UNKNOWN


class AkShareAdapter(AssetAdapter):
    """Adapter for akshare data source (Chinese markets)."""

    def __init__(self) -> None:
        super().__init__(DataSource.AKSHARE)

    def fetch_quote(self, symbol: str) -> Optional[AssetQuote]:
        return AssetQuote(symbol=symbol, price=0.0, change=0.0, change_pct=0.0, volume=0)

    def fetch_historical(
        self,
        symbol: str,
        interval: Interval = Interval.DAY,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[OHLCVBar]:
        return []

    def search(self, query: str) -> List[Asset]:
        return []

    def get_market_status(self, exchange: Exchange) -> MarketStatus:
        if exchange in (Exchange.SSE, Exchange.SZSE, Exchange.BSE):
            return MarketStatus.OPEN
        return MarketStatus.UNKNOWN


class BaoStockAdapter(AssetAdapter):
    """Adapter for baostock data source (Chinese markets)."""

    def __init__(self) -> None:
        super().__init__(DataSource.BAOSTOCK)

    def fetch_quote(self, symbol: str) -> Optional[AssetQuote]:
        return AssetQuote(symbol=symbol, price=0.0, change=0.0, change_pct=0.0, volume=0)

    def fetch_historical(
        self,
        symbol: str,
        interval: Interval = Interval.DAY,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> List[OHLCVBar]:
        return []

    def search(self, query: str) -> List[Asset]:
        return []

    def get_market_status(self, exchange: Exchange) -> MarketStatus:
        return MarketStatus.UNKNOWN


class AssetManager:
    """Manage multiple data source adapters with fallback."""

    def __init__(self) -> None:
        self.adapters: Dict[DataSource, AssetAdapter] = {
            DataSource.YFINANCE: YFinanceAdapter(),
            DataSource.AKSHARE: AkShareAdapter(),
            DataSource.BAOSTOCK: BaoStockAdapter(),
        }
        self.primary_source = DataSource.YFINANCE

    def get_quote(self, symbol: str, source: Optional[DataSource] = None) -> Optional[AssetQuote]:
        adapter = self.adapters.get(source or self.primary_source)
        if adapter:
            return adapter.fetch_quote(symbol)
        return None

    def get_historical(
        self,
        symbol: str,
        interval: Interval = Interval.DAY,
        source: Optional[DataSource] = None,
    ) -> List[OHLCVBar]:
        adapter = self.adapters.get(source or self.primary_source)
        if adapter:
            return adapter.fetch_historical(symbol, interval)
        return []

    def search(self, query: str, source: Optional[DataSource] = None) -> List[Asset]:
        adapter = self.adapters.get(source or self.primary_source)
        if adapter:
            return adapter.search(query)
        return []

    def get_market_status(self, exchange: Exchange) -> MarketStatus:
        for adapter in self.adapters.values():
            status = adapter.get_market_status(exchange)
            if status != MarketStatus.UNKNOWN:
                return status
        return MarketStatus.UNKNOWN
