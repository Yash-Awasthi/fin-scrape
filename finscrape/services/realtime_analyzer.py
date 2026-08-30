"""
Real-Time Market Analyzer — Live technical analysis, sentiment, and correlation.

Provides real-time calculation of technical indicators, live sentiment analysis,
price-news correlation, and volatility detection from streaming data.
All pure functions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LiveIndicator:
    """Real-time technical indicator value."""
    name: str
    value: float
    signal: str  # buy, sell, hold
    strength: float  # 0-1
    timestamp: float


@dataclass
class SentimentSnapshot:
    """Live sentiment analysis snapshot."""
    ticker: str
    score: float  # -1 to 1
    label: str  # bearish, neutral, bullish
    confidence: float  # 0-1
    source_count: int
    timestamp: float


@dataclass
class CorrelationResult:
    """Price-news correlation result."""
    ticker: str
    correlation: float  # -1 to 1
    price_change: float
    sentiment_change: float
    significance: str  # high, medium, low
    timestamp: float


@dataclass
class VolatilityAlert:
    """Volatility detection result."""
    ticker: str
    current_volatility: float
    historical_avg: float
    ratio: float  # current/historical
    is_elevated: bool
    timestamp: float


# ---------------------------------------------------------------------------
# Real-time technical indicators
# ---------------------------------------------------------------------------

def realtime_rsi(
    prices: List[float],
    period: int = 14,
) -> LiveIndicator:
    """Calculate RSI from a live price stream."""
    if len(prices) < period + 1:
        return LiveIndicator(name="RSI", value=50, signal="hold", strength=0, timestamp=0)
    
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [max(c, 0) for c in changes[-period:]]
    losses = [abs(min(c, 0)) for c in changes[-period:]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
    if rsi > 70:
        signal, strength = "sell", (rsi - 70) / 30
    elif rsi < 30:
        signal, strength = "buy", (30 - rsi) / 30
    else:
        signal, strength = "hold", 0.3
    
    return LiveIndicator(name="RSI", value=round(rsi, 2), signal=signal, strength=round(min(1, strength), 3), timestamp=0)


def realtime_macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> LiveIndicator:
    """Calculate MACD from live price stream."""
    if len(prices) < slow:
        return LiveIndicator(name="MACD", value=0, signal="hold", strength=0, timestamp=0)
    
    # EMA calculation
    def ema(data, period):
        alpha = 2 / (period + 1)
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(data[i] * alpha + result[-1] * (1 - alpha))
        return result
    
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema(macd_line, signal_period)
    
    if not macd_line:
        return LiveIndicator(name="MACD", value=0, signal="hold", strength=0, timestamp=0)
    
    macd_val = macd_line[-1]
    sig_val = signal_line[-1]
    hist = macd_val - sig_val
    
    if macd_val > sig_val and hist > 0:
        signal, strength = "buy", min(1, abs(hist) / (abs(sig_val) + 1e-10))
    elif macd_val < sig_val and hist < 0:
        signal, strength = "sell", min(1, abs(hist) / (abs(sig_val) + 1e-10))
    else:
        signal, strength = "hold", 0.3
    
    return LiveIndicator(name="MACD", value=round(macd_val, 4), signal=signal, strength=round(strength, 3), timestamp=0)


def realtime_vwap(
    prices: List[float],
    volumes: List[int],
) -> LiveIndicator:
    """Calculate VWAP from live price/volume stream."""
    if not prices or not volumes:
        return LiveIndicator(name="VWAP", value=0, signal="hold", strength=0, timestamp=0)
    
    total_pv = sum(p * v for p, v in zip(prices, volumes))
    total_vol = sum(volumes)
    vwap = total_pv / total_vol if total_vol > 0 else prices[-1]
    
    current = prices[-1]
    if current > vwap * 1.01:
        signal, strength = "sell", min(1, (current - vwap) / vwap)
    elif current < vwap * 0.99:
        signal, strength = "buy", min(1, (vwap - current) / vwap)
    else:
        signal, strength = "hold", 0.3
    
    return LiveIndicator(name="VWAP", value=round(vwap, 4), signal=signal, strength=round(strength, 3), timestamp=0)


# ---------------------------------------------------------------------------
# Live sentiment
# ---------------------------------------------------------------------------

_STRONG_POS = {"beat", "exceeded", "surge", "rally", "upgrade", "buy", "outperform", "bullish", "record", "growth"}
_STRONG_NEG = {"miss", "crash", "plunge", "downgrade", "sell", "underperform", "bearish", "bankruptcy", "fraud", "crisis"}
_MODERATE_POS = {"rise", "gain", "increase", "positive", "strong", "improve", "up"}
_MODERATE_NEG = {"fall", "drop", "decline", "negative", "weak", "risk", "concern", "down"}


def analyze_sentiment_live(text: str) -> SentimentSnapshot:
    """Real-time sentiment analysis on a text."""
    words = text.lower().split()
    
    pos_score = 0
    neg_score = 0
    
    for w in words:
        if w in _STRONG_POS:
            pos_score += 0.8
        elif w in _MODERATE_POS:
            pos_score += 0.4
        elif w in _STRONG_NEG:
            neg_score += 0.8
        elif w in _MODERATE_NEG:
            neg_score += 0.4
    
    total = pos_score + neg_score
    if total == 0:
        score = 0
        confidence = 0.3
    else:
        score = (pos_score - neg_score) / total
        confidence = min(1, total / (len(words) * 0.1 + 1e-10))
    
    if score > 0.2:
        label = "bullish"
    elif score < -0.2:
        label = "bearish"
    else:
        label = "neutral"
    
    return SentimentSnapshot(
        ticker="",
        score=round(score, 3),
        label=label,
        confidence=round(confidence, 3),
        source_count=1,
        timestamp=0,
    )


def aggregate_sentiment(
    items: List[str],
    ticker: str = "",
) -> SentimentSnapshot:
    """Aggregate sentiment from multiple text sources."""
    if not items:
        return SentimentSnapshot(ticker=ticker, score=0, label="neutral", confidence=0, source_count=0, timestamp=0)
    
    sentiments = [analyze_sentiment_live(item) for item in items]
    avg_score = sum(s.score for s in sentiments) / len(sentiments)
    avg_confidence = sum(s.confidence for s in sentiments) / len(sentiments)
    
    if avg_score > 0.2:
        label = "bullish"
    elif avg_score < -0.2:
        label = "bearish"
    else:
        label = "neutral"
    
    return SentimentSnapshot(
        ticker=ticker,
        score=round(avg_score, 3),
        label=label,
        confidence=round(avg_confidence, 3),
        source_count=len(items),
        timestamp=0,
    )


# ---------------------------------------------------------------------------
# Price-news correlation
# ---------------------------------------------------------------------------

def calculate_correlation(
    series_a: List[float],
    series_b: List[float],
) -> float:
    """Pearson correlation between two series."""
    n = min(len(series_a), len(series_b))
    if n < 3:
        return 0
    
    a, b = series_a[:n], series_b[:n]
    ma, mb = sum(a) / n, sum(b) / n
    
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / (n - 1)
    sa = math.sqrt(sum((x - ma) ** 2 for x in a) / (n - 1))
    sb = math.sqrt(sum((x - mb) ** 2 for x in b) / (n - 1))
    
    if sa == 0 or sb == 0:
        return 0
    return cov / (sa * sb)


def correlate_price_sentiment(
    price_changes: List[float],
    sentiment_scores: List[float],
    ticker: str = "",
) -> CorrelationResult:
    """Correlate price movements with sentiment changes."""
    corr = calculate_correlation(price_changes, sentiment_scores)
    
    n = min(len(price_changes), len(sentiment_scores))
    avg_price_change = sum(price_changes[:n]) / n if n > 0 else 0
    avg_sentiment_change = sum(sentiment_scores[:n]) / n if n > 0 else 0
    
    abs_corr = abs(corr)
    if abs_corr > 0.7:
        significance = "high"
    elif abs_corr > 0.4:
        significance = "medium"
    else:
        significance = "low"
    
    return CorrelationResult(
        ticker=ticker,
        correlation=round(corr, 3),
        price_change=round(avg_price_change, 4),
        sentiment_change=round(avg_sentiment_change, 4),
        significance=significance,
        timestamp=0,
    )


# ---------------------------------------------------------------------------
# Volatility detection
# ---------------------------------------------------------------------------

def detect_volatility_spike(
    recent_prices: List[float],
    historical_volatility: float,
    window: int = 20,
    spike_threshold: float = 2.0,
) -> VolatilityAlert:
    """
    Detect if current volatility exceeds historical average.
    
    Args:
        recent_prices: Recent price series
        historical_volatility: Historical average volatility
        window: Window for current volatility calculation
        spike_threshold: Ratio threshold for spike detection
    """
    if len(recent_prices) < window:
        return VolatilityAlert(
            ticker="", current_volatility=0, historical_avg=historical_volatility,
            ratio=0, is_elevated=False, timestamp=0,
        )
    
    # Calculate current volatility (annualized)
    returns = [
        (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
        for i in range(max(1, len(recent_prices) - window), len(recent_prices))
        if recent_prices[i-1] != 0
    ]
    
    if len(returns) < 2:
        return VolatilityAlert(
            ticker="", current_volatility=0, historical_avg=historical_volatility,
            ratio=0, is_elevated=False, timestamp=0,
        )
    
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    current_vol = math.sqrt(variance) * math.sqrt(252)
    
    ratio = current_vol / historical_volatility if historical_volatility > 0 else 0
    is_elevated = ratio >= spike_threshold
    
    return VolatilityAlert(
        ticker="",
        current_volatility=round(current_vol, 4),
        historical_avg=round(historical_volatility, 4),
        ratio=round(ratio, 2),
        is_elevated=is_elevated,
        timestamp=0,
    )
