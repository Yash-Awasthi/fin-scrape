"""
K-line candlestick analysis and technical indicators.

Extracted from ai-kline — stock data fetching and technical indicator calculation.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple
import math


@dataclass
class Candlestick:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0.0
    amplitude: float = 0.0
    pct_change: float = 0.0
    change: float = 0.0
    turnover: float = 0.0


class TrendDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class TechnicalIndicators:
    sma_5: float = 0.0
    sma_10: float = 0.0
    sma_20: float = 0.0
    sma_60: float = 0.0
    ema_12: float = 0.0
    ema_26: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_histogram: float = 0.0
    rsi_14: float = 50.0
    rsi_6: float = 50.0
    kdj_k: float = 50.0
    kdj_d: float = 50.0
    kdj_j: float = 50.0
    boll_upper: float = 0.0
    boll_middle: float = 0.0
    boll_lower: float = 0.0
    atr_14: float = 0.0
    obv: float = 0.0
    vwap: float = 0.0


@dataclass
class Signal:
    indicator: str
    direction: TrendDirection
    strength: float  # 0-1
    description: str


@dataclass
class AnalysisResult:
    ticker: str
    trend: TrendDirection
    signals: List[Signal]
    indicators: TechnicalIndicators
    support_levels: List[float]
    resistance_levels: List[float]
    recommendation: str


def compute_sma(prices: List[float], period: int) -> List[float]:
    """Simple Moving Average."""
    result = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(prices[i])
        else:
            avg = sum(prices[i - period + 1: i + 1]) / period
            result.append(avg)
    return result


def compute_ema(prices: List[float], period: int) -> List[float]:
    """Exponential Moving Average."""
    if not prices:
        return []
    multiplier = 2 / (period + 1)
    ema = [prices[0]]
    for i in range(1, len(prices)):
        val = prices[i] * multiplier + ema[-1] * (1 - multiplier)
        ema.append(val)
    return ema


def compute_rsi(prices: List[float], period: int = 14) -> float:
    """Relative Strength Index."""
    if len(prices) < period + 1:
        return 50.0

    gains = []
    losses = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(max(0, change))
        losses.append(max(0, -change))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_macd(prices: List[float]) -> Tuple[float, float, float]:
    """MACD: line, signal, histogram."""
    ema12 = compute_ema(prices, 12)
    ema26 = compute_ema(prices, 26)
    macd_line = [e12 - e26 for e12, e26 in zip(ema12, ema26)]
    signal = compute_ema(macd_line, 9)
    macd_val = macd_line[-1] if macd_line else 0.0
    signal_val = signal[-1] if signal else 0.0
    return macd_val, signal_val, macd_val - signal_val


def compute_kdj(
    highs: List[float], lows: List[float], closes: List[float], period: int = 9
) -> Tuple[float, float, float]:
    """KDJ indicator."""
    if len(closes) < period:
        return 50.0, 50.0, 50.0

    k_values = [50.0]
    d_values = [50.0]

    for i in range(period - 1, len(closes)):
        period_highs = highs[i - period + 1: i + 1]
        period_lows = lows[i - period + 1: i + 1]
        highest = max(period_highs)
        lowest = min(period_lows)

        if highest == lowest:
            rsv = 50.0
        else:
            rsv = (closes[i] - lowest) / (highest - lowest) * 100

        k = 2 / 3 * k_values[-1] + 1 / 3 * rsv
        d = 2 / 3 * d_values[-1] + 1 / 3 * k
        k_values.append(k)
        d_values.append(d)

    k = k_values[-1]
    d = d_values[-1]
    j = 3 * k - 2 * d
    return k, d, j


def compute_bollinger(
    prices: List[float], period: int = 20, num_std: float = 2.0
) -> Tuple[float, float, float]:
    """Bollinger Bands: upper, middle, lower."""
    if len(prices) < period:
        avg = sum(prices) / len(prices) if prices else 0
        return avg, avg, avg

    middle = sum(prices[-period:]) / period
    variance = sum((p - middle) ** 2 for p in prices[-period:]) / period
    std = math.sqrt(variance)

    return middle + num_std * std, middle, middle - num_std * std


def compute_atr(
    highs: List[float], lows: List[float], closes: List[float], period: int = 14
) -> float:
    """Average True Range."""
    if len(closes) < 2:
        return 0.0

    tr_values = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        tr_values.append(tr)

    if len(tr_values) < period:
        return sum(tr_values) / len(tr_values) if tr_values else 0.0

    return sum(tr_values[-period:]) / period


def compute_obv(closes: List[float], volumes: List[float]) -> List[float]:
    """On-Balance Volume."""
    if not closes:
        return []
    obv = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv.append(obv[-1] + volumes[i])
        elif closes[i] < closes[i - 1]:
            obv.append(obv[-1] - volumes[i])
        else:
            obv.append(obv[-1])
    return obv


def compute_vwap(candles: List[Candlestick]) -> float:
    """Volume Weighted Average Price."""
    total_volume = sum(c.volume for c in candles)
    if total_volume == 0:
        return 0.0
    vwap = sum(
        ((c.high + c.low + c.close) / 3) * c.volume for c in candles
    ) / total_volume
    return vwap


def compute_indicators(candles: List[Candlestick]) -> TechnicalIndicators:
    """Compute all technical indicators from candlestick data."""
    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    volumes = [c.volume for c in candles]

    sma5 = compute_sma(closes, 5)
    sma10 = compute_sma(closes, 10)
    sma20 = compute_sma(closes, 20)
    sma60 = compute_sma(closes, 60)
    ema12 = compute_ema(closes, 12)
    ema26 = compute_ema(closes, 26)
    macd_val, signal_val, histogram = compute_macd(closes)
    rsi14 = compute_rsi(closes, 14)
    rsi6 = compute_rsi(closes, 6)
    k, d, j = compute_kdj(highs, lows, closes)
    boll_upper, boll_middle, boll_lower = compute_bollinger(closes)
    atr = compute_atr(highs, lows, closes)
    obv_vals = compute_obv(closes, volumes)
    vwap = compute_vwap(candles)

    return TechnicalIndicators(
        sma_5=sma5[-1] if sma5 else 0.0,
        sma_10=sma10[-1] if sma10 else 0.0,
        sma_20=sma20[-1] if sma20 else 0.0,
        sma_60=sma60[-1] if sma60 else 0.0,
        ema_12=ema12[-1] if ema12 else 0.0,
        ema_26=ema26[-1] if ema26 else 0.0,
        macd=macd_val,
        macd_signal=signal_val,
        macd_histogram=histogram,
        rsi_14=rsi14,
        rsi_6=rsi6,
        kdj_k=k,
        kdj_d=d,
        kdj_j=j,
        boll_upper=boll_upper,
        boll_middle=boll_middle,
        boll_lower=boll_lower,
        atr_14=atr,
        obv=obv_vals[-1] if obv_vals else 0.0,
        vwap=vwap,
    )


def generate_signals(indicators: TechnicalIndicators, price: float) -> List[Signal]:
    """Generate trading signals from technical indicators."""
    signals = []

    # MACD signals
    if indicators.macd_histogram > 0 and indicators.macd > 0:
        signals.append(Signal("MACD", TrendDirection.BULLISH, 0.7, "MACD histogram positive and above zero"))
    elif indicators.macd_histogram < 0:
        signals.append(Signal("MACD", TrendDirection.BEARISH, 0.6, "MACD histogram negative"))

    # RSI signals
    if indicators.rsi_14 < 30:
        signals.append(Signal("RSI", TrendDirection.BULLISH, 0.8, f"RSI {indicators.rsi_14:.1f} — oversold"))
    elif indicators.rsi_14 > 70:
        signals.append(Signal("RSI", TrendDirection.BEARISH, 0.8, f"RSI {indicators.rsi_14:.1f} — overbought"))

    # KDJ signals
    if indicators.kdj_j < 20:
        signals.append(Signal("KDJ", TrendDirection.BULLISH, 0.6, "KDJ J-value oversold"))
    elif indicators.kdj_j > 80:
        signals.append(Signal("KDJ", TrendDirection.BEARISH, 0.6, "KDJ J-value overbought"))

    # Bollinger signals
    if price < indicators.boll_lower:
        signals.append(Signal("BOLL", TrendDirection.BULLISH, 0.7, "Price below lower Bollinger Band"))
    elif price > indicators.boll_upper:
        signals.append(Signal("BOLL", TrendDirection.BEARISH, 0.7, "Price above upper Bollinger Band"))

    # SMA crossover
    if indicators.sma_5 > indicators.sma_20:
        signals.append(Signal("SMA_CROSS", TrendDirection.BULLISH, 0.5, "SMA5 above SMA20 — golden cross"))
    elif indicators.sma_5 < indicators.sma_20:
        signals.append(Signal("SMA_CROSS", TrendDirection.BEARISH, 0.5, "SMA5 below SMA20 — death cross"))

    return signals


def analyze_stock(
    ticker: str, candles: List[Candlestick]
) -> AnalysisResult:
    """Full technical analysis of a stock."""
    indicators = compute_indicators(candles)
    price = candles[-1].close if candles else 0.0
    signals = generate_signals(indicators, price)

    bullish_count = sum(1 for s in signals if s.direction == TrendDirection.BULLISH)
    bearish_count = sum(1 for s in signals if s.direction == TrendDirection.BEARISH)

    if bullish_count > bearish_count:
        trend = TrendDirection.BULLISH
        rec = "Consider buying — majority of signals bullish"
    elif bearish_count > bullish_count:
        trend = TrendDirection.BEARISH
        rec = "Consider selling — majority of signals bearish"
    else:
        trend = TrendDirection.NEUTRAL
        rec = "Hold — mixed signals"

    closes = [c.close for c in candles]
    support_levels = sorted(set([min(closes[-20:]), min(closes[-60:])]))
    resistance_levels = sorted(set([max(closes[-20:]), max(closes[-60:])]))

    return AnalysisResult(
        ticker=ticker,
        trend=trend,
        signals=signals,
        indicators=indicators,
        support_levels=support_levels,
        resistance_levels=resistance_levels,
        recommendation=rec,
    )
