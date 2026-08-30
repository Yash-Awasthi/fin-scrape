"""Market Data Simulator.

Extracted from Real-Time-Financial-Analysis-Trading-System (inspiration).
Generates realistic stock price data using geometric Brownian motion,
order book simulation, and news sentiment generation.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OHLCV:
    """Open-High-Low-Close-Volume bar."""
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class OrderBookLevel:
    """Single order book level."""
    price: float
    quantity: int
    order_type: str  # "buy" or "sell"


@dataclass
class OrderBook:
    """Order book snapshot."""
    timestamp: float
    symbol: str
    bids: list[OrderBookLevel]
    asks: list[OrderBookLevel]


@dataclass
class NewsSentiment:
    """News sentiment data."""
    timestamp: float
    symbol: str
    headline: str
    sentiment_score: float  # -1 to 1
    magnitude: float  # 0 to 1


@dataclass
class MarketDataConfig:
    """Configuration for market data generation."""
    initial_price: float = 100.0
    drift: float = 0.0002  # mu: average daily return
    volatility: float = 0.01  # sigma: daily volatility
    tick_size: float = 0.01
    base_volume: int = 5000
    volume_volatility: float = 0.1


# --- Price Generation ---

def generate_ohlcv(
    symbol: str,
    prev_price: float,
    config: MarketDataConfig = MarketDataConfig(),
    dt: float = 1.0,
) -> OHLCV:
    """Generate a single OHLCV bar using geometric Brownian motion.

    Args:
        symbol: Stock symbol
        prev_price: Previous closing price
        config: Market data configuration
        dt: Time step (1 = daily)

    Returns:
        Generated OHLCV bar
    """
    # Geometric Brownian motion for price change
    price_change = math.exp(
        (config.drift - 0.5 * config.volatility ** 2) * dt +
        config.volatility * math.sqrt(dt) * random.gauss(0, 1)
    )

    opening_price = max(config.tick_size, prev_price * price_change)
    closing_price = max(config.tick_size, opening_price + round(random.gauss(0, 10), 2))
    high = max(opening_price, closing_price) + round(abs(random.gauss(0, 5)), 2)
    low = min(opening_price, closing_price) - round(abs(random.gauss(0, 5)), 2)
    low = max(config.tick_size, low)

    # Volume with Poisson distribution
    volume = max(0, int(random.expovariate(1.0 / config.base_volume) *
                        (1 + config.volume_volatility * random.gauss(0, 1))))

    return OHLCV(
        timestamp=time.time(),
        open=round(opening_price, 2),
        high=round(high, 2),
        low=round(low, 2),
        close=round(closing_price, 2),
        volume=volume,
    )


def generate_price_series(
    symbol: str,
    num_bars: int,
    config: MarketDataConfig = MarketDataConfig(),
) -> list[OHLCV]:
    """Generate a series of OHLCV bars.

    Args:
        symbol: Stock symbol
        num_bars: Number of bars to generate
        config: Market data configuration

    Returns:
        List of OHLCV bars
    """
    bars = []
    prev_price = config.initial_price

    for _ in range(num_bars):
        bar = generate_ohlcv(symbol, prev_price, config)
        bars.append(bar)
        prev_price = bar.close

    return bars


def calculate_returns(prices: list[float]) -> list[float]:
    """Calculate returns from price series.

    Args:
        prices: List of prices

    Returns:
        List of returns (price changes as percentages)
    """
    if len(prices) < 2:
        return []

    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] != 0:
            returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
        else:
            returns.append(0.0)

    return returns


def calculate_volatility(returns: list[float], window: int = 20) -> float:
    """Calculate rolling volatility from returns.

    Args:
        returns: List of returns
        window: Rolling window size

    Returns:
        Annualized volatility
    """
    if len(returns) < 2:
        return 0.0

    recent = returns[-window:] if len(returns) >= window else returns
    mean = sum(recent) / len(recent)
    variance = sum((r - mean) ** 2 for r in recent) / len(recent)
    return math.sqrt(variance) * math.sqrt(252)  # Annualize


# --- Order Book Generation ---

def generate_order_book(
    symbol: str,
    mid_price: float,
    num_levels: int = 5,
    spread_pct: float = 0.001,
) -> OrderBook:
    """Generate a simulated order book.

    Args:
        symbol: Stock symbol
        mid_price: Current mid price
        num_levels: Number of price levels
        spread_pct: Spread as percentage of mid price

    Returns:
        Generated order book
    """
    spread = mid_price * spread_pct
    bid_base = mid_price - spread / 2
    ask_base = mid_price + spread / 2

    bids = []
    asks = []

    for i in range(num_levels):
        # Decreasing quantity further from mid
        qty_factor = 1.0 / (1 + i * 0.5)

        bids.append(OrderBookLevel(
            price=round(bid_base - i * mid_price * 0.001, 2),
            quantity=max(1, int(random.expovariate(1.0 / (100 * qty_factor)))),
            order_type="buy",
        ))

        asks.append(OrderBookLevel(
            price=round(ask_base + i * mid_price * 0.001, 2),
            quantity=max(1, int(random.expovariate(1.0 / (100 * qty_factor)))),
            order_type="sell",
        ))

    return OrderBook(
        timestamp=time.time(),
        symbol=symbol,
        bids=bids,
        asks=asks,
    )


def calculate_order_book_metrics(book: OrderBook) -> dict:
    """Calculate metrics from order book.

    Args:
        book: Order book snapshot

    Returns:
        Order book metrics
    """
    if not book.bids or not book.asks:
        return {"spread": 0, "mid_price": 0, "bid_depth": 0, "ask_depth": 0}

    best_bid = book.bids[0].price
    best_ask = book.asks[0].price
    spread = best_ask - best_bid
    mid_price = (best_bid + best_ask) / 2

    bid_depth = sum(level.quantity for level in book.bids)
    ask_depth = sum(level.quantity for level in book.asks)

    return {
        "spread": round(spread, 4),
        "spread_pct": round(spread / mid_price * 100, 4) if mid_price > 0 else 0,
        "mid_price": round(mid_price, 2),
        "bid_depth": bid_depth,
        "ask_depth": ask_depth,
        "imbalance": round((bid_depth - ask_depth) / (bid_depth + ask_depth), 3) if (bid_depth + ask_depth) > 0 else 0,
    }


# --- News Sentiment ---

SENTIMENT_TEMPLATES = {
    "positive": [
        "{symbol} reports strong quarterly earnings",
        "Analysts upgrade {symbol} to buy rating",
        "{symbol} announces new product launch",
        "Market momentum favors {symbol}",
    ],
    "negative": [
        "{symbol} misses earnings expectations",
        "Regulatory concerns around {symbol}",
        "{symbol} faces increased competition",
        "Downgrade for {symbol} amid market uncertainty",
    ],
    "neutral": [
        "{symbol} maintains steady performance",
        "Market watches {symbol} for direction",
        "{symbol} quarterly report in line with expectations",
    ],
}


def generate_news_sentiment(
    symbol: str,
    sentiment_bias: float = 0.0,
) -> NewsSentiment:
    """Generate simulated news sentiment.

    Args:
        symbol: Stock symbol
        sentiment_bias: Bias towards positive (-1) or negative (1)

    Returns:
        News sentiment data
    """
    # Determine sentiment category
    rand = random.random() + sentiment_bias * 0.3
    if rand < 0.33:
        category = "negative"
        score = random.uniform(-1, -0.1)
    elif rand > 0.66:
        category = "positive"
        score = random.uniform(0.1, 1)
    else:
        category = "neutral"
        score = random.uniform(-0.1, 0.1)

    template = random.choice(SENTIMENT_TEMPLATES[category])
    headline = template.format(symbol=symbol)

    return NewsSentiment(
        timestamp=time.time(),
        symbol=symbol,
        headline=headline,
        sentiment_score=round(score, 3),
        magnitude=round(abs(score), 3),
    )


def aggregate_sentiment(sentiments: list[NewsSentiment]) -> dict:
    """Aggregate multiple sentiment scores.

    Args:
        sentiments: List of news sentiments

    Returns:
        Aggregated sentiment metrics
    """
    if not sentiments:
        return {"average": 0, "momentum": 0, "count": 0}

    scores = [s.sentiment_score for s in sentiments]
    average = sum(scores) / len(scores)

    # Momentum: recent vs older sentiment
    if len(scores) >= 2:
        mid = len(scores) // 2
        recent_avg = sum(scores[mid:]) / len(scores[mid:])
        older_avg = sum(scores[:mid]) / max(1, mid)
        momentum = recent_avg - older_avg
    else:
        momentum = 0.0

    return {
        "average": round(average, 3),
        "momentum": round(momentum, 3),
        "count": len(sentiments),
        "positive_count": sum(1 for s in scores if s > 0.1),
        "negative_count": sum(1 for s in scores if s < -0.1),
        "neutral_count": sum(1 for s in scores if -0.1 <= s <= 0.1),
    }


# --- Market Statistics ---

def calculate_market_stats(bars: list[OHLCV]) -> dict:
    """Calculate market statistics from OHLCV bars.

    Args:
        bars: List of OHLCV bars

    Returns:
        Market statistics
    """
    if not bars:
        return {}

    closes = [bar.close for bar in bars]
    volumes = [bar.volume for bar in bars]
    returns = calculate_returns(closes)

    return {
        "symbol": bars[0].open if bars else "",
        "period_bars": len(bars),
        "start_price": closes[0] if closes else 0,
        "end_price": closes[-1] if closes else 0,
        "total_return_pct": round((closes[-1] / closes[0] - 1) * 100, 2) if closes and closes[0] > 0 else 0,
        "volatility": round(calculate_volatility(returns), 4) if returns else 0,
        "avg_volume": round(sum(volumes) / len(volumes)) if volumes else 0,
        "max_volume": max(volumes) if volumes else 0,
        "min_volume": min(volumes) if volumes else 0,
        "sharpe_ratio": round(
            (sum(returns) / len(returns)) / calculate_volatility(returns) if returns and calculate_volatility(returns) > 0 else 0,
            3,
        ),
    }
