"""
Technical Analysis Indicators Library — 43+ indicators extracted from ta.

Inspired by bukosabino/ta — Technical Analysis Library in Python.
Pure functions for computing financial technical indicators on price/volume data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ============================================================================
# Helper Functions
# ============================================================================

def _sma(data: List[float], window: int) -> List[Optional[float]]:
    """Simple Moving Average."""
    result: List[Optional[float]] = []
    for i in range(len(data)):
        if i < window - 1:
            result.append(None)
        else:
            result.append(sum(data[i - window + 1: i + 1]) / window)
    return result


def _ema(data: List[float], window: int) -> List[Optional[float]]:
    """Exponential Moving Average."""
    result: List[Optional[float]] = []
    multiplier = 2 / (window + 1)
    prev_ema: Optional[float] = None
    for i, val in enumerate(data):
        if i < window - 1:
            result.append(None)
        elif i == window - 1:
            sma_val = sum(data[:window]) / window
            result.append(sma_val)
            prev_ema = sma_val
        else:
            ema_val = (val - prev_ema!) * multiplier + prev_ema!
            result.append(ema_val)
            prev_ema = ema_val
    return result


def _true_range(high: List[float], low: List[float], close: List[float]) -> List[float]:
    """True Range calculation."""
    tr: List[float] = [high[0] - low[0]]
    for i in range(1, len(high)):
        tr.append(max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1])
        ))
    return tr


# ============================================================================
# Trend Indicators
# ============================================================================

def macd(
    close: List[float],
    window_fast: int = 12,
    window_slow: int = 26,
    window_signal: int = 9,
) -> dict:
    """Moving Average Convergence Divergence (MACD)."""
    ema_fast = _ema(close, window_fast)
    ema_slow = _ema(close, window_slow)

    macd_line = []
    for f, s in zip(ema_fast, ema_slow):
        if f is not None and s is not None:
            macd_line.append(f - s)
        else:
            macd_line.append(None)

    # Signal line
    valid_macd = [v for v in macd_line if v is not None]
    signal_raw = _ema(valid_macd, window_signal) if len(valid_macd) >= window_signal else [None] * len(valid_macd)

    # Pad signal to match macd_line length
    signal_line = [None] * (len(macd_line) - len(signal_raw)) + signal_raw

    histogram = []
    for m, s in zip(macd_line, signal_line):
        if m is not None and s is not None:
            histogram.append(m - s)
        else:
            histogram.append(None)

    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def rsi(close: List[float], window: int = 14) -> List[Optional[float]]:
    """Relative Strength Index."""
    if len(close) < window + 1:
        return [None] * len(close)

    gains = []
    losses = []
    for i in range(1, len(close)):
        diff = close[i] - close[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))

    avg_gain = sum(gains[:window]) / window
    avg_loss = sum(losses[:window]) / window

    result: List[Optional[float]] = [None] * window
    rs = avg_gain / avg_loss if avg_loss != 0 else 100
    result.append(100 - (100 / (1 + rs)))

    for i in range(window, len(gains)):
        avg_gain = (avg_gain * (window - 1) + gains[i]) / window
        avg_loss = (avg_loss * (window - 1) + losses[i]) / window
        rs = avg_gain / avg_loss if avg_loss != 0 else 100
        result.append(100 - (100 / (1 + rs)))

    return result


def bollinger_bands(
    close: List[float],
    window: int = 20,
    window_dev: int = 2,
) -> dict:
    """Bollinger Bands."""
    sma = _sma(close, window)
    upper = []
    lower = []

    for i in range(len(close)):
        if sma[i] is None:
            upper.append(None)
            lower.append(None)
        else:
            subset = close[i - window + 1: i + 1]
            std = (sum((x - sma[i]!) ** 2 for x in subset) / len(subset)) ** 0.5
            upper.append(sma[i]! + window_dev * std)
            lower.append(sma[i]! - window_dev * std)

    return {"upper": upper, "middle": sma, "lower": lower}


def aroon(high: List[float], low: List[float], window: int = 25) -> dict:
    """Aroon Up/Down/Indicator."""
    aroon_up = []
    aroon_down = []

    for i in range(len(high)):
        if i < window:
            aroon_up.append(None)
            aroon_down.append(None)
        else:
            subset_high = high[i - window: i + 1]
            subset_low = low[i - window: i + 1]
            days_since_high = window - subset_high.index(max(subset_high))
            days_since_low = window - subset_low.index(min(subset_low))
            aroon_up.append(days_since_high / window * 100)
            aroon_down.append(days_since_low / window * 100)

    indicator = []
    for u, d in zip(aroon_up, aroon_down):
        if u is not None and d is not None:
            indicator.append(u - d)
        else:
            indicator.append(None)

    return {"aroon_up": aroon_up, "aroon_down": aroon_down, "aroon_indicator": indicator}


def adx(high: List[float], low: List[float], close: List[float], window: int = 14) -> List[Optional[float]]:
    """Average Directional Index."""
    tr = _true_range(high, low, close)

    plus_dm = [0.0]
    minus_dm = [0.0]
    for i in range(1, len(high)):
        up = high[i] - high[i - 1]
        down = low[i - 1] - low[i]
        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)

    atr = _ema(tr, window)
    plus_di_raw = _ema(plus_dm, window)
    minus_di_raw = _ema(minus_dm, window)

    adx_values: List[Optional[float]] = []
    prev_adx: Optional[float] = None

    for i in range(len(close)):
        if atr[i] is None or plus_di_raw[i] is None or minus_di_raw[i] is None or atr[i] == 0:
            adx_values.append(None)
            continue

        plus_di = (plus_di_raw[i]! / atr[i]!) * 100
        minus_di = (minus_di_raw[i]! / atr[i]!) * 100
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0

        if prev_adx is None:
            prev_adx = dx
            adx_values.append(dx)
        else:
            prev_adx = (prev_adx * (window - 1) + dx) / window
            adx_values.append(prev_adx)

    return adx_values


# ============================================================================
# Momentum Indicators
# ============================================================================

def stochastic_oscillator(
    high: List[float],
    low: List[float],
    close: List[float],
    window: int = 14,
    smooth_window: int = 3,
) -> dict:
    """Stochastic Oscillator (%K and %D)."""
    raw_k: List[Optional[float]] = []

    for i in range(len(close)):
        if i < window - 1:
            raw_k.append(None)
        else:
            highest = max(high[i - window + 1: i + 1])
            lowest = min(low[i - window + 1: i + 1])
            k = (close[i] - lowest) / (highest - lowest) * 100 if highest != lowest else 50
            raw_k.append(k)

    valid_k = [v for v in raw_k if v is not None]
    k_smooth = _sma(valid_k, smooth_window) if len(valid_k) >= smooth_window else valid_k
    d_smooth = _sma(k_smooth, smooth_window) if len(k_smooth) >= smooth_window else k_smooth

    return {"k": raw_k, "d": d_smooth}


def williams_r(high: List[float], low: List[float], close: List[float], window: int = 14) -> List[Optional[float]]:
    """Williams %R."""
    result: List[Optional[float]] = []
    for i in range(len(close)):
        if i < window - 1:
            result.append(None)
        else:
            highest = max(high[i - window + 1: i + 1])
            lowest = min(low[i - window + 1: i + 1])
            wr = (highest - close[i]) / (highest - lowest) * -100 if highest != lowest else -50
            result.append(wr)
    return result


def cci(high: List[float], low: List[float], close: List[float], window: int = 20) -> List[Optional[float]]:
    """Commodity Channel Index."""
    tp = [(h + l + c) / 3 for h, l, c in zip(high, low, close)]
    sma_tp = _sma(tp, window)
    result: List[Optional[float]] = []

    for i in range(len(tp)):
        if sma_tp[i] is None:
            result.append(None)
        else:
            subset = tp[i - window + 1: i + 1]
            mean_dev = sum(abs(x - sma_tp[i]!) for x in subset) / len(subset)
            if mean_dev == 0:
                result.append(0)
            else:
                result.append((tp[i] - sma_tp[i]!) / (0.015 * mean_dev))
    return result


def roc(close: List[float], window: int = 12) -> List[Optional[float]]:
    """Rate of Change."""
    result: List[Optional[float]] = []
    for i in range(len(close)):
        if i < window:
            result.append(None)
        else:
            result.append((close[i] - close[i - window]) / close[i - window] * 100 if close[i - window] != 0 else 0)
    return result


defawesomeIndicator(high: List[float], low: List[float], close: List[float]) -> List[float]:
    """Awesome Oscillator."""
    mid = [(h + l) / 2 for h, l in zip(high, low)]
    sma5 = _sma(mid, 5)
    sma34 = _sma(mid, 34)
    result = []
    for m5, m34 in zip(sma5, sma34):
        if m5 is not None and m34 is not None:
            result.append(m5 - m34)
        else:
            result.append(0)
    return result


# ============================================================================
# Volatility Indicators
# ============================================================================

def atr(high: List[float], low: List[float], close: List[float], window: int = 14) -> List[Optional[float]]:
    """Average True Range."""
    tr = _true_range(high, low, close)
    return _ema(tr, window)


def kc(high: List[float], low: List[float], close: List[float], window: int = 20, atr_window: int = 10, multiplier: float = 2.0) -> dict:
    """Keltner Channel."""
    mid = _ema(close, window)
    atr_values = atr(high, low, close, atr_window)

    upper = []
    lower = []
    for m, a in zip(mid, atr_values):
        if m is not None and a is not None:
            upper.append(m + multiplier * a)
            lower.append(m - multiplier * a)
        else:
            upper.append(None)
            lower.append(None)

    return {"upper": upper, "middle": mid, "lower": lower}


def donchian_channel(high: List[float], low: List[float], window: int = 20) -> dict:
    """Donchian Channel."""
    upper: List[Optional[float]] = []
    lower: List[Optional[float]] = []

    for i in range(len(high)):
        if i < window - 1:
            upper.append(None)
            lower.append(None)
        else:
            upper.append(max(high[i - window + 1: i + 1]))
            lower.append(min(low[i - window + 1: i + 1]))

    middle = [(u + l) / 2 if u is not None and l is not None else None for u, l in zip(upper, lower)]
    return {"upper": upper, "middle": middle, "lower": lower}


# ============================================================================
# Volume Indicators
# ============================================================================

def obv(close: List[float], volume: List[float]) -> List[float]:
    """On-Balance Volume."""
    result = [0.0]
    for i in range(1, len(close)):
        if close[i] > close[i - 1]:
            result.append(result[-1] + volume[i])
        elif close[i] < close[i - 1]:
            result.append(result[-1] - volume[i])
        else:
            result.append(result[-1])
    return result


def vwap(high: List[float], low: List[float], close: List[float], volume: List[float]) -> List[float]:
    """Volume Weighted Average Price."""
    result = []
    cum_vol = 0.0
    cum_tp_vol = 0.0
    for h, l, c, v in zip(high, low, close, volume):
        tp = (h + l + c) / 3
        cum_vol += v
        cum_tp_vol += tp * v
        result.append(cum_tp_vol / cum_vol if cum_vol > 0 else 0)
    return result


def mfi(high: List[float], low: List[float], close: List[float], volume: List[float], window: int = 14) -> List[Optional[float]]:
    """Money Flow Index."""
    tp = [(h + l + c) / 3 for h, l, c in zip(high, low, close)]
    mf = [t * v for t, v in zip(tp, volume)]

    result: List[Optional[float]] = []
    for i in range(len(close)):
        if i < window:
            result.append(None)
        else:
            pos_flow = sum(mf[j] for j in range(i - window + 1, i + 1) if tp[j] > tp[j - 1])
            neg_flow = sum(mf[j] for j in range(i - window + 1, i + 1) if tp[j] < tp[j - 1])
            ratio = pos_flow / neg_flow if neg_flow > 0 else 100
            mfi_val = 100 - (100 / (1 + ratio))
            result.append(mfi_val)
    return result


def ad(high: List[float], low: List[float], close: List[float], volume: List[float]) -> List[float]:
    """Accumulation/Distribution Index."""
    result = [0.0]
    for i in range(len(close)):
        h, l, c, v = high[i], low[i], close[i], volume[i]
        clv = ((c - l) - (h - c)) / (h - l) if h != l else 0
        result.append(result[-1] + clv * v)
    return result


# ============================================================================
# Other Indicators
# ============================================================================

def daily_return(close: List[float]) -> List[float]:
    """Daily Log Return."""
    return [0.0] + [math.log(close[i] / close[i - 1]) if close[i - 1] != 0 else 0 for i in range(1, len(close))]


def cumulative_return(close: List[float]) -> List[float]:
    """Cumulative Return."""
    base = close[0] if close[0] != 0 else 1
    return [(c / base - 1) for c in close]
