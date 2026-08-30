"""
Technical Analysis Indicators — Inspired by ta-lib, pandas-ta, and quantstats.

Provides classic technical analysis indicators computed from price/volume data.
All pure functions following the established pattern — no DB, no async, just math.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PriceBar:
    """Single price bar."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class IndicatorResult:
    """Single indicator value with metadata."""
    name: str
    value: float
    signal: str  # "buy", "sell", "neutral"
    strength: float  # 0.0 to 1.0


@dataclass
class TechnicalAnalysis:
    """Complete technical analysis snapshot."""
    trend: str  # "uptrend", "downtrend", "sideways"
    momentum: str  # "overbought", "oversold", "neutral"
    volatility: str  # "high", "medium", "low"
    support: float
    resistance: float
    indicators: List[IndicatorResult]
    overall_signal: str  # "buy", "sell", "hold"
    confidence: float  # 0.0 to 1.0


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _sma(data: List[float], period: int) -> List[float]:
    """Simple Moving Average."""
    result = []
    for i in range(len(data)):
        if i < period - 1:
            result.append(float('nan'))
        else:
            result.append(sum(data[i - period + 1:i + 1]) / period)
    return result


def _ema(data: List[float], period: int) -> List[float]:
    """Exponential Moving Average."""
    if not data or period <= 0:
        return []
    
    multiplier = 2 / (period + 1)
    result = [data[0]]
    
    for i in range(1, len(data)):
        val = data[i] * multiplier + result[-1] * (1 - multiplier)
        result.append(val)
    
    return result


def _true_range(bars: List[PriceBar]) -> List[float]:
    """True Range calculation."""
    if not bars:
        return []
    
    tr = [bars[0].high - bars[0].low]
    for i in range(1, len(bars)):
        prev_close = bars[i - 1].close
        tr.append(max(
            bars[i].high - bars[i].low,
            abs(bars[i].high - prev_close),
            abs(bars[i].low - prev_close),
        ))
    return tr


# ---------------------------------------------------------------------------
# Trend indicators
# ---------------------------------------------------------------------------

def moving_average_convergence(bars: List[PriceBar], fast: int = 12, slow: int = 26, signal: int = 9) -> List[IndicatorResult]:
    """MACD indicator."""
    closes = [b.close for b in bars]
    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)
    
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = _ema(macd_line, signal)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    
    if not histogram:
        return []
    
    hist = histogram[-1]
    macd_val = macd_line[-1]
    sig_val = signal_line[-1]
    
    if macd_val > sig_val and hist > 0:
        signal_str = "buy"
        strength = min(1.0, abs(hist) / (abs(sig_val) + 1e-10))
    elif macd_val < sig_val and hist < 0:
        signal_str = "sell"
        strength = min(1.0, abs(hist) / (abs(sig_val) + 1e-10))
    else:
        signal_str = "neutral"
        strength = 0.3
    
    return [IndicatorResult(name="MACD", value=round(macd_val, 4), signal=signal_str, strength=round(strength, 3))]


def relative_strength_index(bars: List[PriceBar], period: int = 14) -> List[IndicatorResult]:
    """RSI indicator."""
    closes = [b.close for b in bars]
    if len(closes) < period + 1:
        return [IndicatorResult(name="RSI", value=50.0, signal="neutral", strength=0.3)]
    
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(c, 0) for c in changes[-period:]]
    losses = [abs(min(c, 0)) for c in changes[-period:]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
    if rsi > 70:
        signal = "sell"
        strength = (rsi - 70) / 30
    elif rsi < 30:
        signal = "buy"
        strength = (30 - rsi) / 30
    else:
        signal = "neutral"
        strength = 0.3
    
    return [IndicatorResult(name="RSI", value=round(rsi, 2), signal=signal, strength=round(min(1.0, strength), 3))]


def bollinger_bands(bars: List[PriceBar], period: int = 20, std_dev: float = 2.0) -> List[IndicatorResult]:
    """Bollinger Bands indicator."""
    closes = [b.close for b in bars]
    if len(closes) < period:
        return []
    
    middle = sum(closes[-period:]) / period
    variance = sum((c - middle) ** 2 for c in closes[-period:]) / period
    std = math.sqrt(variance)
    
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    current = closes[-1]
    
    # %B position
    bandwidth = upper - lower
    pct_b = (current - lower) / bandwidth if bandwidth > 0 else 0.5
    
    if current >= upper:
        signal = "sell"
        strength = min(1.0, (current - upper) / std if std > 0 else 0.5)
    elif current <= lower:
        signal = "buy"
        strength = min(1.0, (lower - current) / std if std > 0 else 0.5)
    else:
        signal = "neutral"
        strength = 0.3
    
    return [
        IndicatorResult(name="BB_Upper", value=round(upper, 4), signal="resistance", strength=0.5),
        IndicatorResult(name="BB_Middle", value=round(middle, 4), signal="neutral", strength=0.3),
        IndicatorResult(name="BB_Lower", value=round(lower, 4), signal="support", strength=0.5),
        IndicatorResult(name="BB_%B", value=round(pct_b, 4), signal=signal, strength=round(strength, 3)),
    ]


def average_true_range(bars: List[PriceBar], period: int = 14) -> List[IndicatorResult]:
    """ATR — volatility measure."""
    tr = _true_range(bars)
    if len(tr) < period:
        return [IndicatorResult(name="ATR", value=0, signal="neutral", strength=0)]
    
    atr = sum(tr[-period:]) / period
    atr_pct = atr / bars[-1].close * 100 if bars[-1].close > 0 else 0
    
    if atr_pct > 3:
        signal = "high_volatility"
        strength = min(1.0, atr_pct / 5)
    elif atr_pct < 1:
        signal = "low_volatility"
        strength = min(1.0, (1 - atr_pct) / 1)
    else:
        signal = "medium_volatility"
        strength = 0.5
    
    return [IndicatorResult(name="ATR", value=round(atr, 4), signal=signal, strength=round(strength, 3))]


# ---------------------------------------------------------------------------
# Momentum indicators
# ---------------------------------------------------------------------------

def stochastic_oscillator(bars: List[PriceBar], k_period: int = 14, d_period: int = 3) -> List[IndicatorResult]:
    """Stochastic Oscillator (%K and %D)."""
    if len(bars) < k_period:
        return []
    
    # Calculate %K for each period
    k_values = []
    for i in range(k_period - 1, len(bars)):
        window = bars[i - k_period + 1:i + 1]
        highest = max(b.high for b in window)
        lowest = min(b.low for b in window)
        
        if highest == lowest:
            k = 50.0
        else:
            k = (bars[i].close - lowest) / (highest - lowest) * 100
        k_values.append(k)
    
    # %D is SMA of %K
    d_values = _sma(k_values, d_period)
    
    if not k_values:
        return []
    
    k = k_values[-1]
    d = d_values[-1] if d_values and not math.isnan(d_values[-1]) else k
    
    if k > 80 and d > 80:
        signal = "sell"
        strength = (k - 80) / 20
    elif k < 20 and d < 20:
        signal = "buy"
        strength = (20 - k) / 20
    elif k > d and k_values[-2] <= d_values[-2] if len(k_values) > 1 and len(d_values) > 1 else False:
        signal = "buy"
        strength = 0.6
    elif k < d and k_values[-2] >= d_values[-2] if len(k_values) > 1 and len(d_values) > 1 else False:
        signal = "sell"
        strength = 0.6
    else:
        signal = "neutral"
        strength = 0.3
    
    return [
        IndicatorResult(name="Stoch_%K", value=round(k, 2), signal=signal, strength=round(min(1.0, strength), 3)),
        IndicatorResult(name="Stoch_%D", value=round(d, 2), signal=signal, strength=round(min(1.0, strength * 0.8), 3)),
    ]


def williams_r(bars: List[PriceBar], period: int = 14) -> List[IndicatorResult]:
    """Williams %R indicator."""
    if len(bars) < period:
        return [IndicatorResult(name="Williams_%R", value=-50, signal="neutral", strength=0.3)]
    
    window = bars[-period:]
    highest = max(b.high for b in window)
    lowest = min(b.low for b in window)
    
    if highest == lowest:
        wr = -50.0
    else:
        wr = (highest - bars[-1].close) / (highest - lowest) * -100
    
    if wr > -20:
        signal = "sell"
        strength = (wr + 20) / 20
    elif wr < -80:
        signal = "buy"
        strength = (-80 - wr) / 20
    else:
        signal = "neutral"
        strength = 0.3
    
    return [IndicatorResult(name="Williams_%R", value=round(wr, 2), signal=signal, strength=round(min(1.0, strength), 3))]


# ---------------------------------------------------------------------------
# Volume indicators
# ---------------------------------------------------------------------------

def on_balance_volume(bars: List[PriceBar]) -> List[IndicatorResult]:
    """On-Balance Volume indicator."""
    if len(bars) < 2:
        return [IndicatorResult(name="OBV", value=0, signal="neutral", strength=0)]
    
    obv = 0
    for i in range(1, len(bars)):
        if bars[i].close > bars[i - 1].close:
            obv += bars[i].volume
        elif bars[i].close < bars[i - 1].close:
            obv -= bars[i].volume
    
    # Trend from OBV
    obv_sma = _ema([float(obv)], 20)[-1] if bars else 0
    if obv > 0:
        signal = "buy"
        strength = min(1.0, obv / (bars[-1].volume + 1))
    elif obv < 0:
        signal = "sell"
        strength = min(1.0, abs(obv) / (bars[-1].volume + 1))
    else:
        signal = "neutral"
        strength = 0.3
    
    return [IndicatorResult(name="OBV", value=round(obv, 0), signal=signal, strength=round(strength, 3))]


def volume_weighted_average_price(bars: List[PriceBar]) -> List[IndicatorResult]:
    """VWAP indicator."""
    if not bars:
        return []
    
    total_pv = sum(((b.high + b.low + b.close) / 3) * b.volume for b in bars)
    total_vol = sum(b.volume for b in bars)
    
    vwap = total_pv / total_vol if total_vol > 0 else 0
    current = bars[-1].close
    
    if current > vwap * 1.02:
        signal = "sell"  # Price above VWAP
        strength = min(1.0, (current - vwap) / vwap)
    elif current < vwap * 0.98:
        signal = "buy"  # Price below VWAP
        strength = min(1.0, (vwap - current) / vwap)
    else:
        signal = "neutral"
        strength = 0.3
    
    return [IndicatorResult(name="VWAP", value=round(vwap, 4), signal=signal, strength=round(strength, 3))]


# ---------------------------------------------------------------------------
# Support / Resistance
# ---------------------------------------------------------------------------

def find_support_resistance(bars: List[PriceBar], lookback: int = 20) -> Tuple[float, float]:
    """Find support and resistance levels using pivot points."""
    if len(bars) < lookback:
        lookback = len(bars)
    
    if lookback < 3:
        return (0, 0)
    
    recent = bars[-lookback:]
    highs = [b.high for b in recent]
    lows = [b.low for b in recent]
    
    # Simple: resistance = recent high, support = recent low
    # More sophisticated: use pivot point clustering
    resistance = max(highs)
    support = min(lows)
    
    # Refine using local extrema
    pivot_highs = []
    pivot_lows = []
    for i in range(1, len(recent) - 1):
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
            pivot_highs.append(highs[i])
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
            pivot_lows.append(lows[i])
    
    if pivot_highs:
        resistance = sum(pivot_highs) / len(pivot_highs)
    if pivot_lows:
        support = sum(pivot_lows) / len(pivot_lows)
    
    return (round(support, 4), round(resistance, 4))


# ---------------------------------------------------------------------------
# Complete analysis
# ---------------------------------------------------------------------------

def analyze(bars: List[PriceBar]) -> TechnicalAnalysis:
    """
    Run complete technical analysis on price data.
    
    Combines all indicators into a comprehensive analysis with
    overall signal and confidence.
    """
    if len(bars) < 5:
        return TechnicalAnalysis(
            trend="sideways", momentum="neutral", volatility="low",
            support=0, resistance=0, indicators=[],
            overall_signal="hold", confidence=0.1,
        )
    
    # Collect all indicators
    indicators = []
    indicators.extend(moving_average_convergence(bars))
    indicators.extend(relative_strength_index(bars))
    indicators.extend(bollinger_bands(bars))
    indicators.extend(average_true_range(bars))
    indicators.extend(stochastic_oscillator(bars))
    indicators.extend(williams_r(bars))
    indicators.extend(on_balance_volume(bars))
    indicators.extend(volume_weighted_average_price(bars))
    
    # Support / Resistance
    support, resistance = find_support_resistance(bars)
    
    # Trend determination
    closes = [b.close for b in bars]
    ma20 = _sma(closes, 20)
    ma50 = _sma(closes, min(50, len(closes)))
    
    if not ma20[-1] or math.isnan(ma20[-1]):
        trend = "sideways"
    elif ma50 and not math.isnan(ma50[-1]) and ma20[-1] > ma50[-1]:
        trend = "uptrend"
    elif ma50 and not math.isnan(ma50[-1]) and ma20[-1] < ma50[-1]:
        trend = "downtrend"
    else:
        trend = "sideways"
    
    # Momentum
    rsi_vals = [i for i in indicators if i.name == "RSI"]
    if rsi_vals:
        rsi = rsi_vals[0].value
        if rsi > 70:
            momentum = "overbought"
        elif rsi < 30:
            momentum = "oversold"
        else:
            momentum = "neutral"
    else:
        momentum = "neutral"
    
    # Volatility
    atr_vals = [i for i in indicators if i.name == "ATR"]
    if atr_vals:
        vol_signal = atr_vals[0].signal
        if "high" in vol_signal:
            volatility = "high"
        elif "low" in vol_signal:
            volatility = "low"
        else:
            volatility = "medium"
    else:
        volatility = "medium"
    
    # Overall signal (majority vote)
    buy_signals = sum(1 for i in indicators if i.signal == "buy")
    sell_signals = sum(1 for i in indicators if i.signal == "sell")
    total_signals = buy_signals + sell_signals
    
    if buy_signals > sell_signals and buy_signals >= 3:
        overall = "buy"
        confidence = buy_signals / max(1, len(indicators))
    elif sell_signals > buy_signals and sell_signals >= 3:
        overall = "sell"
        confidence = sell_signals / max(1, len(indicators))
    else:
        overall = "hold"
        confidence = 0.4
    
    return TechnicalAnalysis(
        trend=trend,
        momentum=momentum,
        volatility=volatility,
        support=support,
        resistance=resistance,
        indicators=indicators,
        overall_signal=overall,
        confidence=round(min(1.0, confidence), 3),
    )
