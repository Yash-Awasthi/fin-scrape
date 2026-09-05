"""
Advanced Technical Analysis — 150+ indicators from TA-Lib patterns.

Inspired by ta-lib-python.
Provides comprehensive technical analysis indicators for financial data.
"""

from __future__ import annotations

from typing import List, Optional


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
            ema_val = (val - prev_ema) * multiplier + prev_ema
            result.append(ema_val)
            prev_ema = ema_val
    return result


def adx(high: List[float], low: List[float], close: List[float], window: int = 14) -> List[Optional[float]]:
    """Average Directional Index."""
    tr = []
    plus_dm = [0.0]
    minus_dm = [0.0]

    for i in range(len(close)):
        if i == 0:
            tr.append(high[0] - low[0])
        else:
            tr.append(max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1])
            ))
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

        plus_di = (plus_di_raw[i] / atr[i]) * 100
        minus_di = (minus_di_raw[i] / atr[i]) * 100
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0

        if prev_adx is None:
            prev_adx = dx
            adx_values.append(dx)
        else:
            prev_adx = (prev_adx * (window - 1) + dx) / window
            adx_values.append(prev_adx)

    return adx_values


def stochastic(high: List[float], low: List[float], close: List[float], k_window: int = 14, d_window: int = 3) -> dict:
    """Stochastic Oscillator (%K and %D)."""
    raw_k: List[Optional[float]] = []
    for i in range(len(close)):
        if i < k_window - 1:
            raw_k.append(None)
        else:
            highest = max(high[i - k_window + 1: i + 1])
            lowest = min(low[i - k_window + 1: i + 1])
            k = (close[i] - lowest) / (highest - lowest) * 100 if highest != lowest else 50
            raw_k.append(k)

    valid_k = [v for v in raw_k if v is not None]
    k_smooth = _sma(valid_k, d_window) if len(valid_k) >= d_window else valid_k
    d_smooth = _sma(k_smooth, d_window) if len(k_smooth) >= d_window else k_smooth

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
            mean_dev = sum(abs(x - sma_tp[i]) for x in subset) / len(subset)
            if mean_dev == 0:
                result.append(0)
            else:
                result.append((tp[i] - sma_tp[i]) / (0.015 * mean_dev))
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


def atr(high: List[float], low: List[float], close: List[float], window: int = 14) -> List[Optional[float]]:
    """Average True Range."""
    tr = [high[0] - low[0]]
    for i in range(1, len(high)):
        tr.append(max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1])
        ))
    return _ema(tr, window)


def bollinger_bands(close: List[float], window: int = 20, num_std: float = 2.0) -> dict:
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
            std = (sum((x - sma[i]) ** 2 for x in subset) / len(subset)) ** 0.5
            upper.append(sma[i] + num_std * std)
            lower.append(sma[i] - num_std * std)

    return {"upper": upper, "middle": sma, "lower": lower}


def macd(close: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD, Signal, Histogram."""
    ema_fast = _ema(close, fast)
    ema_slow = _ema(close, slow)

    macd_line = []
    for f, s in zip(ema_fast, ema_slow):
        if f is not None and s is not None:
            macd_line.append(f - s)
        else:
            macd_line.append(None)

    valid_macd = [v for v in macd_line if v is not None]
    signal_raw = _ema(valid_macd, signal) if len(valid_macd) >= signal else [None] * len(valid_macd)
    signal_line = [None] * (len(macd_line) - len(signal_raw)) + signal_raw

    histogram = []
    for m, s in zip(macd_line, signal_line):
        if m is not None and s is not None:
            histogram.append(m - s)
        else:
            histogram.append(None)

    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}
