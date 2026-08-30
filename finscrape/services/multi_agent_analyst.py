"""Multi-Agent Financial Analyst Service.

Extracted from TradingAgents (inspiration).
Multi-agent system with specialized analyst roles:
market, social, news, and fundamentals analysts that
collaborate to generate trading decisions.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AnalystRole(Enum):
    MARKET = "market"
    SOCIAL = "social"
    NEWS = "news"
    FUNDAMENTALS = "fundamentals"
    RISK = "risk"
    PORTFOLIO = "portfolio"


class SignalStrength(Enum):
    STRONG_SELL = -2
    SELL = -1
    NEUTRAL = 0
    BUY = 1
    STRONG_BUY = 2


class Decision(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class MarketData:
    ticker: str
    price: float
    volume: int
    market_cap: float
    pe_ratio: float | None = None
    eps: float | None = None
    dividend_yield: float | None = None
    sector: str = ""
    industry: str = ""
    fifty_two_week_high: float = 0.0
    fifty_two_week_low: float = 0.0


@dataclass
class AnalystSignal:
    analyst: AnalystRole
    signal: SignalStrength
    confidence: float  # 0-1
    reasoning: str
    evidence: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TradingDecision:
    ticker: str
    decision: Decision
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    signals: list[AnalystSignal] = field(default_factory=list)
    reasoning: str = ""
    risk_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


def analyze_market_technicals(data: MarketData, price_history: list[float]) -> AnalystSignal:
    """Analyze market technicals: trends, support/resistance, momentum."""
    if len(price_history) < 2:
        return AnalystSignal(analyst=AnalystRole.MARKET, signal=SignalStrength.NEUTRAL,
                             confidence=0.3, reasoning="Insufficient price history")
    sma_20 = statistics.mean(price_history[-20:]) if len(price_history) >= 20 else statistics.mean(price_history)
    sma_50 = statistics.mean(price_history[-50:]) if len(price_history) >= 50 else sma_20
    current_price = price_history[-1]
    momentum = (current_price - price_history[-min(10, len(price_history))]) / price_history[-min(10, len(price_history))]
    if current_price > sma_20 > sma_50 and momentum > 0.02:
        signal = SignalStrength.BUY
        confidence = min(0.8, 0.5 + momentum)
    elif current_price < sma_20 < sma_50 and momentum < -0.02:
        signal = SignalStrength.SELL
        confidence = min(0.8, 0.5 + abs(momentum))
    else:
        signal = SignalStrength.NEUTRAL
        confidence = 0.4
    reasons = []
    if current_price > sma_20:
        reasons.append("Price above SMA20")
    if current_price > sma_50:
        reasons.append("Price above SMA50")
    if momentum > 0:
        reasons.append(f"Positive momentum ({momentum:.1%})")
    else:
        reasons.append(f"Negative momentum ({momentum:.1%})")
    return AnalystSignal(analyst=AnalystRole.MARKET, signal=signal, confidence=confidence,
                         reasoning="; ".join(reasons), evidence=[f"SMA20={sma_20:.2f}", f"SMA50={sma_50:.2f}"])


def analyze_sentiment(texts: list[str]) -> AnalystSignal:
    """Analyze social/news sentiment from text data."""
    if not texts:
        return AnalystSignal(analyst=AnalystRole.SOCIAL, signal=SignalStrength.NEUTRAL,
                             confidence=0.2, reasoning="No sentiment data")
    positive_words = {"bullish", "buy", "upgrade", "growth", "profit", "surge", "rally", "strong", "beat"}
    negative_words = {"bearish", "sell", "downgrade", "loss", "decline", "crash", "weak", "miss", "risk"}
    pos_count = 0
    neg_count = 0
    for text in texts:
        words = set(text.lower().split())
        pos_count += len(words & positive_words)
        neg_count += len(words & negative_words)
    total = pos_count + neg_count
    if total == 0:
        return AnalystSignal(analyst=AnalystRole.SOCIAL, signal=SignalStrength.NEUTRAL,
                             confidence=0.3, reasoning="No strong sentiment detected")
    sentiment_ratio = (pos_count - neg_count) / total
    if sentiment_ratio > 0.3:
        signal = SignalStrength.BUY
    elif sentiment_ratio < -0.3:
        signal = SignalStrength.SELL
    else:
        signal = SignalStrength.NEUTRAL
    confidence = min(0.8, abs(sentiment_ratio) + 0.2)
    return AnalystSignal(analyst=AnalystRole.SOCIAL, signal=signal, confidence=confidence,
                         reasoning=f"Sentiment ratio: {sentiment_ratio:.2f} ({pos_count} positive, {neg_count} negative)",
                         evidence=[f"positive={pos_count}", f"negative={neg_count}"])


def analyze_fundamentals(data: MarketData) -> AnalystSignal:
    """Analyze fundamental valuation metrics."""
    reasons = []
    score = 0
    if data.pe_ratio:
        if data.pe_ratio < 15:
            score += 1
            reasons.append(f"Low P/E ({data.pe_ratio:.1f})")
        elif data.pe_ratio > 30:
            score -= 1
            reasons.append(f"High P/E ({data.pe_ratio:.1f})")
    if data.eps and data.eps > 0:
        score += 1
        reasons.append(f"Positive EPS ({data.eps:.2f})")
    elif data.eps and data.eps < 0:
        score -= 1
        reasons.append(f"Negative EPS ({data.eps:.2f})")
    if data.dividend_yield and data.dividend_yield > 0.03:
        score += 1
        reasons.append(f"High dividend ({data.dividend_yield:.1%})")
    if data.fifty_two_week_high > 0:
        range_position = (data.price - data.fifty_two_week_low) / (data.fifty_two_week_high - data.fifty_two_week_low)
        if range_position < 0.3:
            score += 1
            reasons.append("Near 52-week low")
        elif range_position > 0.9:
            score -= 1
            reasons.append("Near 52-week high")
    if score >= 2:
        signal = SignalStrength.BUY
    elif score <= -2:
        signal = SignalStrength.SELL
    else:
        signal = SignalStrength.NEUTRAL
    confidence = min(0.8, abs(score) * 0.2 + 0.3)
    return AnalystSignal(analyst=AnalystRole.FUNDAMENTALS, signal=signal, confidence=confidence,
                         reasoning="; ".join(reasons) if reasons else "Neutral fundamentals",
                         evidence=[f"pe={data.pe_ratio}", f"eps={data.eps}"])


def calculate_position_size(account_balance: float, risk_tolerance: float, entry_price: float, stop_loss: float) -> float:
    """Calculate position size based on risk management."""
    risk_per_share = abs(entry_price - stop_loss)
    if risk_per_share <= 0:
        return 0.0
    max_risk_amount = account_balance * risk_tolerance
    shares = max_risk_amount / risk_per_share
    return round(shares, 0)


def calculate_target_price(entry_price: float, risk_reward_ratio: float = 2.0) -> float:
    """Calculate target price based on risk-reward ratio."""
    return round(entry_price * (1 + risk_reward_ratio * 0.1), 2)


def calculate_stop_loss(entry_price: float, atr: float = None, percent: float = 0.05) -> float:
    """Calculate stop loss price."""
    if atr:
        return round(entry_price - 2 * atr, 2)
    return round(entry_price * (1 - percent), 2)


def aggregate_signals(signals: list[AnalystSignal]) -> tuple[Decision, float]:
    """Aggregate multiple analyst signals into a final decision."""
    if not signals:
        return Decision.HOLD, 0.0
    weighted_sum = 0.0
    total_weight = 0.0
    role_weights = {
        AnalystRole.MARKET: 1.0,
        AnalystRole.FUNDAMENTALS: 1.2,
        AnalystRole.SOCIAL: 0.6,
        AnalystRole.NEWS: 0.8,
        AnalystRole.RISK: 1.5,
    }
    for signal in signals:
        weight = role_weights.get(signal.analyst, 1.0) * signal.confidence
        weighted_sum += signal.signal.value * weight
        total_weight += weight
    if total_weight == 0:
        return Decision.HOLD, 0.0
    avg_score = weighted_sum / total_weight
    confidence = min(1.0, total_weight / (len(signals) * 2))
    if avg_score > 1.2:
        decision = Decision.STRONG_BUY
    elif avg_score > 0.4:
        decision = Decision.BUY
    elif avg_score < -1.2:
        decision = Decision.STRONG_SELL
    elif avg_score < -0.4:
        decision = Decision.SELL
    else:
        decision = Decision.HOLD
    return decision, confidence


def generate_trading_decision(
    ticker: str, data: MarketData, price_history: list[float],
    news_texts: list[str], account_balance: float = 10000.0,
    risk_tolerance: float = 0.02,
) -> TradingDecision:
    """Generate a complete trading decision using multi-agent analysis."""
    signals = []
    market_signal = analyze_market_technicals(data, price_history)
    signals.append(market_signal)
    sentiment_signal = analyze_sentiment(news_texts)
    signals.append(sentiment_signal)
    fundamental_signal = analyze_fundamentals(data)
    signals.append(fundamental_signal)
    decision, confidence = aggregate_signals(signals)
    entry_price = data.price
    atr = (data.fifty_two_week_high - data.fifty_two_week_low) / 20 if data.fifty_two_week_high > data.fifty_two_week_low else entry_price * 0.03
    stop_loss = calculate_stop_loss(entry_price, atr=atr)
    target_price = calculate_target_price(entry_price)
    reasoning_parts = [f"{s.analyst.value}: {s.signal.name} ({s.confidence:.0%})" for s in signals]
    return TradingDecision(
        ticker=ticker, decision=decision, confidence=confidence,
        entry_price=entry_price, target_price=target_price, stop_loss=stop_loss,
        signals=signals, reasoning=" | ".join(reasoning_parts),
        risk_score=1 - confidence,
    )
