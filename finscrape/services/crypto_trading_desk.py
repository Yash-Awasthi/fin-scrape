"""Crypto Trading Desk Service.

Extracted from cryptoagents (inspiration).
Multi-agent crypto trading desk with specialized analyst roles:
market, social, news, and fundamentals analysts.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CryptoAnalystRole(Enum):
    MARKET = "market"
    SOCIAL = "social"
    NEWS = "news"
    FUNDAMENTALS = "fundamentals"
    RISK_AGGRESSIVE = "risk_aggressive"
    RISK_CONSERVATIVE = "risk_conservative"
    RISK_NEUTRAL = "risk_neutral"
    PORTFOLIO = "portfolio"


class CryptoSignal(Enum):
    STRONG_BUY = 2
    BUY = 1
    HOLD = 0
    SELL = -1
    STRONG_SELL = -2


class RiskProfile(Enum):
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    NEUTRAL = "neutral"


@dataclass
class CryptoMarketData:
    symbol: str
    price: float
    volume_24h: float
    market_cap: float
    price_change_24h: float
    price_change_7d: float
    ath: float
    circulating_supply: float
    total_supply: float
    btc_correlation: float = 0.0
    dominance: float = 0.0


@dataclass
class CryptoAnalystSignal:
    analyst: CryptoAnalystRole
    signal: CryptoSignal
    confidence: float
    reasoning: str
    evidence: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CryptoTradingDecision:
    symbol: str
    signal: CryptoSignal
    confidence: float
    allocation_percent: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_profile: RiskProfile
    signals: list[CryptoAnalystSignal] = field(default_factory=list)
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


def analyze_crypto_market(data: CryptoMarketData, price_history: list[float]) -> CryptoAnalystSignal:
    """Analyze crypto market technicals."""
    if len(price_history) < 2:
        return CryptoAnalystSignal(analyst=CryptoAnalystRole.MARKET, signal=CryptoSignal.HOLD,
                                   confidence=0.3, reasoning="Insufficient data")
    sma_20 = statistics.mean(price_history[-20:]) if len(price_history) >= 20 else statistics.mean(price_history)
    current = price_history[-1]
    momentum = (current - price_history[-min(10, len(price_history))]) / price_history[-min(10, len(price_history))]
    volatility = statistics.pstdev(price_history[-20:]) / sma_20 if len(price_history) >= 20 else 0.1
    if current > sma_20 and momentum > 0.05:
        signal = CryptoSignal.BUY
        confidence = min(0.8, 0.5 + abs(momentum))
    elif current < sma_20 and momentum < -0.05:
        signal = CryptoSignal.SELL
        confidence = min(0.8, 0.5 + abs(momentum))
    else:
        signal = CryptoSignal.HOLD
        confidence = 0.4
    reasons = [f"Price: ${current:.2f}", f"SMA20: ${sma_20:.2f}", f"Momentum: {momentum:.1%}", f"Volatility: {volatility:.1%}"]
    return CryptoAnalystSignal(analyst=CryptoAnalystRole.MARKET, signal=signal, confidence=confidence,
                               reasoning="; ".join(reasons), evidence=[f"sma20={sma_20:.2f}", f"vol={volatility:.3f}"])


def analyze_crypto_sentiment(texts: list[str]) -> CryptoAnalystSignal:
    """Analyze crypto social/news sentiment."""
    if not texts:
        return CryptoAnalystSignal(analyst=CryptoAnalystRole.SOCIAL, signal=CryptoSignal.HOLD,
                                   confidence=0.2, reasoning="No data")
    bullish_words = {"bullish", "moon", "pump", "buy", "hodl", "accumulate", "breakout", "ath"}
    bearish_words = {"bearish", "dump", "sell", "crash", "rug", "scam", "bear", "breakdown"}
    pos = sum(1 for t in texts for w in t.lower().split() if w in bullish_words)
    neg = sum(1 for t in texts for w in t.lower().split() if w in bearish_words)
    total = pos + neg
    if total == 0:
        return CryptoAnalystSignal(analyst=CryptoAnalystRole.SOCIAL, signal=CryptoSignal.HOLD,
                                   confidence=0.3, reasoning="Neutral sentiment")
    ratio = (pos - neg) / total
    if ratio > 0.3:
        signal = CryptoSignal.BUY
    elif ratio < -0.3:
        signal = CryptoSignal.SELL
    else:
        signal = CryptoSignal.HOLD
    return CryptoAnalystSignal(analyst=CryptoAnalystRole.SOCIAL, signal=signal,
                               confidence=min(0.8, abs(ratio) + 0.2),
                               reasoning=f"Sentiment ratio: {ratio:.2f} ({pos}B/{neg}S)")


def analyze_crypto_fundamentals(data: CryptoMarketData) -> CryptoAnalystSignal:
    """Analyze crypto fundamental metrics."""
    score = 0
    reasons = []
    if data.ath > 0:
        ath_ratio = data.price / data.ath
        if ath_ratio < 0.3:
            score += 2
            reasons.append(f"Well below ATH ({ath_ratio:.0%})")
        elif ath_ratio > 0.9:
            score -= 1
            reasons.append(f"Near ATH ({ath_ratio:.0%})")
    if data.total_supply > 0:
        supply_ratio = data.circulating_supply / data.total_supply
        if supply_ratio > 0.8:
            score += 1
            reasons.append(f"High circulating supply ({supply_ratio:.0%})")
    if data.btc_correlation > 0.8:
        reasons.append(f"High BTC correlation ({data.btc_correlation:.2f})")
    if data.price_change_7d > 20:
        score -= 1
        reasons.append(f"Large 7d gain ({data.price_change_7d:.1f}%)")
    signal = CryptoSignal.BUY if score >= 2 else (CryptoSignal.SELL if score <= -2 else CryptoSignal.HOLD)
    return CryptoAnalystSignal(analyst=CryptoAnalystRole.FUNDAMENTALS, signal=signal,
                               confidence=min(0.8, abs(score) * 0.2 + 0.3),
                               reasoning="; ".join(reasons) if reasons else "Neutral fundamentals")


def calculate_risk_adjusted_allocation(
    signal: CryptoSignal, confidence: float, risk_profile: RiskProfile,
    volatility: float = 0.5,
) -> float:
    """Calculate position allocation based on risk profile."""
    base_alloc = {CryptoSignal.STRONG_BUY: 0.25, CryptoSignal.BUY: 0.15,
                  CryptoSignal.HOLD: 0.0, CryptoSignal.SELL: -0.10, CryptoSignal.STRONG_SELL: -0.20}
    risk_mult = {RiskProfile.AGGRESSIVE: 1.5, RiskProfile.NEUTRAL: 1.0, RiskProfile.CONSERVATIVE: 0.5}
    vol_adjust = max(0.5, 1 - volatility)
    alloc = base_alloc.get(signal, 0) * confidence * risk_mult.get(risk_profile, 1.0) * vol_adjust
    return round(min(0.3, max(-0.2, alloc)), 3)


def aggregate_crypto_signals(signals: list[CryptoAnalystSignal]) -> tuple[CryptoSignal, float]:
    """Aggregate crypto analyst signals."""
    if not signals:
        return CryptoSignal.HOLD, 0.0
    weights = {CryptoAnalystRole.MARKET: 1.0, CryptoAnalystRole.FUNDAMENTALS: 1.2,
               CryptoAnalystRole.SOCIAL: 0.6, CryptoAnalystRole.NEWS: 0.8}
    weighted_sum = 0.0
    total_weight = 0.0
    for s in signals:
        w = weights.get(s.analyst, 1.0) * s.confidence
        weighted_sum += s.signal.value * w
        total_weight += w
    if total_weight == 0:
        return CryptoSignal.HOLD, 0.0
    avg = weighted_sum / total_weight
    conf = min(1.0, total_weight / (len(signals) * 2))
    if avg > 1.2:
        sig = CryptoSignal.STRONG_BUY
    elif avg > 0.4:
        sig = CryptoSignal.BUY
    elif avg < -1.2:
        sig = CryptoSignal.STRONG_SELL
    elif avg < -0.4:
        sig = CryptoSignal.SELL
    else:
        sig = CryptoSignal.HOLD
    return sig, conf


def generate_crypto_decision(
    data: CryptoMarketData, price_history: list[float],
    news_texts: list[str], risk_profile: RiskProfile = RiskProfile.NEUTRAL,
) -> CryptoTradingDecision:
    """Generate complete crypto trading decision."""
    signals = [
        analyze_crypto_market(data, price_history),
        analyze_crypto_sentiment(news_texts),
        analyze_crypto_fundamentals(data),
    ]
    signal, confidence = aggregate_crypto_signals(signals)
    vol = statistics.pstdev(price_history[-20:]) / statistics.mean(price_history[-20:]) if len(price_history) >= 20 else 0.5
    allocation = calculate_risk_adjusted_allocation(signal, confidence, risk_profile, vol)
    sl_pct = 0.10 if risk_profile == RiskProfile.AGGRESSIVE else (0.05 if risk_profile == RiskProfile.CONSERVATIVE else 0.07)
    tp_pct = sl_pct * 2.5
    return CryptoTradingDecision(
        symbol=data.symbol, signal=signal, confidence=confidence,
        allocation_percent=allocation, entry_price=data.price,
        stop_loss=round(data.price * (1 - sl_pct), 4),
        take_profit=round(data.price * (1 + tp_pct), 4),
        risk_profile=risk_profile, signals=signals,
        reasoning=f"Signal: {signal.name} ({confidence:.0%}), Alloc: {allocation:.1%}",
    )
