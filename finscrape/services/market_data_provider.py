"""Market Data Provider Service.

Extracted from yfinance (inspiration).
Market data fetching, caching, and normalization for financial analysis.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class OHLCV:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: float = 0.0


@dataclass
class MarketQuote:
    symbol: str
    price: float
    change: float
    change_pct: float
    volume: int
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    dividend_yield: float = 0.0
    fifty_two_week_high: float = 0.0
    fifty_two_week_low: float = 0.0
    timestamp: str = ""


@dataclass
class MarketDataResult:
    symbol: str
    data: list[OHLCV]
    quote: MarketQuote | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


MOCK_DATA = {
    "AAPL": {"price": 178.50, "change": 2.30, "change_pct": 1.31, "volume": 52000000,
             "market_cap": 2800000000000, "pe_ratio": 28.5, "dividend_yield": 0.005,
             "fifty_two_week_high": 198.23, "fifty_two_week_low": 143.90},
    "GOOGL": {"price": 141.80, "change": -1.20, "change_pct": -0.84, "volume": 28000000,
              "market_cap": 1800000000000, "pe_ratio": 25.2, "dividend_yield": 0.0,
              "fifty_two_week_high": 153.78, "fifty_two_week_low": 115.83},
    "MSFT": {"price": 378.90, "change": 4.50, "change_pct": 1.20, "volume": 22000000,
             "market_cap": 2800000000000, "pe_ratio": 35.8, "dividend_yield": 0.007,
             "fifty_two_week_high": 384.30, "fifty_two_week_low": 309.45},
    "TSLA": {"price": 248.50, "change": 8.20, "change_pct": 3.41, "volume": 120000000,
             "market_cap": 790000000000, "pe_ratio": 62.5, "dividend_yield": 0.0,
             "fifty_two_week_high": 299.29, "fifty_two_week_low": 138.80},
    "BTC-USD": {"price": 67500, "change": 1200, "change_pct": 1.81, "volume": 35000000000,
                "market_cap": 1320000000000, "pe_ratio": 0, "dividend_yield": 0.0,
                "fifty_two_week_high": 73750, "fifty_two_week_low": 38505},
}


def generate_mock_ohlcv(symbol: str, days: int = 30) -> list[OHLCV]:
    """Generate mock OHLCV data for a symbol."""
    import random
    base_price = MOCK_DATA.get(symbol, {}).get("price", 100)
    data = []
    price = base_price * 0.9
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
        change = random.uniform(-0.03, 0.03) * price
        open_price = price
        close_price = price + change
        high = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
        low = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
        volume = int(random.uniform(10000000, 80000000))
        data.append(OHLCV(date=date, open=round(open_price, 2), high=round(high, 2),
                           low=round(low, 2), close=round(close_price, 2),
                           volume=volume, adj_close=round(close_price, 2)))
        price = close_price
    return data


def get_quote(symbol: str) -> MarketQuote | None:
    """Get current market quote for a symbol."""
    info = MOCK_DATA.get(symbol.upper())
    if not info:
        return None
    return MarketQuote(
        symbol=symbol.upper(), price=info["price"],
        change=info["change"], change_pct=info["change_pct"],
        volume=info["volume"], market_cap=info.get("market_cap", 0),
        pe_ratio=info.get("pe_ratio", 0), dividend_yield=info.get("dividend_yield", 0),
        fifty_two_week_high=info.get("fifty_two_week_high", 0),
        fifty_two_week_low=info.get("fifty_two_week_low", 0),
        timestamp=datetime.now().isoformat(),
    )


def fetch_market_data(symbol: str, period: str = "1mo") -> MarketDataResult:
    """Fetch market data for a symbol."""
    days = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}.get(period, 30)
    data = generate_mock_ohlcv(symbol, days)
    quote = get_quote(symbol)
    return MarketDataResult(
        symbol=symbol, data=data, quote=quote,
        metadata={"period": period, "data_points": len(data)},
    )


def calculate_technical_indicators(data: list[OHLCV]) -> dict[str, Any]:
    """Calculate technical indicators from OHLCV data."""
    if len(data) < 5:
        return {}
    closes = [d.close for d in data]
    volumes = [d.volume for d in data]
    sma_5 = statistics.mean(closes[-5:])
    sma_20 = statistics.mean(closes[-20:]) if len(closes) >= 20 else sma_5
    ema_12 = _calculate_ema(closes, 12)
    ema_26 = _calculate_ema(closes, 26)
    macd = ema_12 - ema_26 if ema_12 and ema_26 else 0
    rsi = _calculate_rsi(closes)
    avg_volume = statistics.mean(volumes)
    return {
        "sma_5": round(sma_5, 2), "sma_20": round(sma_20, 2),
        "ema_12": round(ema_12, 2) if ema_12 else 0,
        "ema_26": round(ema_26, 2) if ema_26 else 0,
        "macd": round(macd, 4), "rsi": round(rsi, 2),
        "avg_volume": int(avg_volume),
        "volume_ratio": round(volumes[-1] / avg_volume, 2) if avg_volume > 0 else 1.0,
    }


def _calculate_ema(prices: list[float], period: int) -> float:
    """Calculate Exponential Moving Average."""
    if len(prices) < period:
        return statistics.mean(prices) if prices else 0
    multiplier = 2 / (period + 1)
    ema = statistics.mean(prices[:period])
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema


def _calculate_rsi(prices: list[float], period: int = 14) -> float:
    """Calculate Relative Strength Index."""
    if len(prices) < period + 1:
        return 50.0
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = statistics.mean(gains[:period])
    avg_loss = statistics.mean(losses[:period])
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def batch_fetch(symbols: list[str], period: str = "1mo") -> dict[str, MarketDataResult]:
    """Fetch market data for multiple symbols."""
    return {symbol: fetch_market_data(symbol, period) for symbol in symbols}
