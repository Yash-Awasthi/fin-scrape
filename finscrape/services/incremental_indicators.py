"""
Incremental Indicators — Extracted from talipp patterns.

O(1) incremental computation for technical indicators:
- SMA, EMA, WMA
- RSI, MACD
- Bollinger Bands
- ATR, Stochastic
- Support for appending, updating, removing values
"""
from __future__ import annotations

from collections import deque
from typing import Deque, List, Optional


class IncrementalSMA:
    """Simple Moving Average with O(1) incremental updates."""

    def __init__(self, period: int) -> None:
        self.period = period
        self._values: Deque[float] = deque(maxlen=period)
        self._sum = 0.0

    def add(self, value: float) -> Optional[float]:
        if len(self._values) == self.period:
            self._sum -= self._values[0]
        self._values.append(value)
        self._sum += value
        if len(self._values) == self.period:
            return self._sum / self.period
        return None

    def update(self, value: float) -> Optional[float]:
        if not self._values:
            return self.add(value)
        self._sum -= self._values[-1]
        self._values[-1] = value
        self._sum += value
        if len(self._values) == self.period:
            return self._sum / self.period
        return None

    def remove(self) -> Optional[float]:
        if not self._values:
            return None
        old = self._values.popleft()
        self._sum -= old
        if len(self._values) == self.period:
            return self._sum / self.period
        return None

    @property
    def value(self) -> Optional[float]:
        if len(self._values) == self.period:
            return self._sum / self.period
        return None

    @property
    def values(self) -> List[float]:
        return list(self._values)


class IncrementalEMA:
    """Exponential Moving Average with O(1) incremental updates."""

    def __init__(self, period: int) -> None:
        self.period = period
        self._multiplier = 2.0 / (period + 1)
        self._value: Optional[float] = None
        self._count = 0
        self._sum = 0.0

    def add(self, value: float) -> Optional[float]:
        self._count += 1
        if self._count == 1:
            self._value = value
            self._sum = value
        else:
            self._value = (value - self._value) * self._multiplier + self._value
        return self._value

    def update(self, value: float) -> Optional[float]:
        if self._value is None:
            return self.add(value)
        self._value = (value - self._value) * self._multiplier + self._value
        return self._value

    @property
    def value(self) -> Optional[float]:
        return self._value


class IncrementalRSI:
    """Relative Strength Index with O(1) incremental updates."""

    def __init__(self, period: int = 14) -> None:
        self.period = period
        self._gains: Deque[float] = deque(maxlen=period)
        self._losses: Deque[float] = deque(maxlen=period)
        self._prev_value: Optional[float] = None
        self._avg_gain = 0.0
        self._avg_loss = 0.0

    def add(self, value: float) -> Optional[float]:
        if self._prev_value is None:
            self._prev_value = value
            return None

        change = value - self._prev_value
        self._prev_value = value

        gain = max(change, 0.0)
        loss = max(-change, 0.0)

        if len(self._gains) == self.period:
            self._avg_gain = (self._avg_gain * (self.period - 1) + gain) / self.period
            self._avg_loss = (self._avg_loss * (self.period - 1) + loss) / self.period
        else:
            self._gains.append(gain)
            self._losses.append(loss)
            self._avg_gain = sum(self._gains) / len(self._gains)
            self._avg_loss = sum(self._losses) / len(self._losses)

        if len(self._gains) < self.period:
            return None

        if self._avg_loss < 1e-10:
            return 100.0
        rs = self._avg_gain / self._avg_loss
        return 100.0 - (100.0 / (1.0 + rs))


class IncrementalMACD:
    """MACD with incremental EMA components."""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        self._fast_ema = IncrementalEMA(fast)
        self._slow_ema = IncrementalEMA(slow)
        self._signal_ema = IncrementalEMA(signal)
        self._macd_values: Deque[float] = deque(maxlen=100)

    def add(self, value: float) -> Optional[dict]:
        fast = self._fast_ema.add(value)
        slow = self._slow_ema.add(value)

        if fast is None or slow is None:
            return None

        macd_line = fast - slow
        self._macd_values.append(macd_line)
        signal_line = self._signal_ema.add(macd_line)

        if signal_line is None:
            return {"macd": macd_line, "signal": None, "histogram": None}

        histogram = macd_line - signal_line
        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


class IncrementalBollingerBands:
    """Bollinger Bands with incremental SMA and variance."""

    def __init__(self, period: int = 20, std_dev: float = 2.0) -> None:
        self.period = period
        self.std_dev = std_dev
        self._sma = IncrementalSMA(period)
        self._values: Deque[float] = deque(maxlen=period)
        self._sum_sq = 0.0

    def add(self, value: float) -> Optional[dict]:
        if len(self._values) == self.period:
            old = self._values[0]
            self._sum_sq -= old * old

        self._values.append(value)
        self._sum_sq += value * value

        sma = self._sma.add(value)
        if sma is None:
            return None

        variance = self._sum_sq / len(self._values) - sma * sma
        std = max(variance, 0.0) ** 0.5

        return {
            "upper": sma + self.std_dev * std,
            "middle": sma,
            "lower": sma - self.std_dev * std,
            "std": std,
        }


class IncrementalATR:
    """Average True Range with incremental computation."""

    def __init__(self, period: int = 14) -> None:
        self.period = period
        self._tr_values: Deque[float] = deque(maxlen=period)
        self._prev_close: Optional[float] = None
        self._atr: Optional[float] = None

    def add(self, high: float, low: float, close: float) -> Optional[float]:
        if self._prev_close is None:
            self._prev_close = close
            return None

        tr = max(high - low, abs(high - self._prev_close), abs(low - self._prev_close))
        self._prev_close = close

        if len(self._tr_values) == self.period:
            self._atr = (self._atr * (self.period - 1) + tr) / self.period
        else:
            self._tr_values.append(tr)
            self._atr = sum(self._tr_values) / len(self._tr_values)

        return self._atr if len(self._tr_values) >= self.period else None


class IncrementalStochastic:
    """Stochastic Oscillator with incremental computation."""

    def __init__(self, k_period: int = 14, d_period: int = 3) -> None:
        self.k_period = k_period
        self.d_period = d_period
        self._highs: Deque[float] = deque(maxlen=k_period)
        self._lows: Deque[float] = deque(maxlen=k_period)
        self._k_values: Deque[float] = deque(maxlen=d_period)

    def add(self, high: float, low: float, close: float) -> Optional[dict]:
        self._highs.append(high)
        self._lows.append(low)

        if len(self._highs) < self.k_period:
            return None

        highest = max(self._highs)
        lowest = min(self._lows)

        if highest - lowest < 1e-10:
            k = 50.0
        else:
            k = (close - lowest) / (highest - lowest) * 100.0

        self._k_values.append(k)

        d = sum(self._k_values) / len(self._k_values) if self._k_values else k
        return {"k": k, "d": d}
