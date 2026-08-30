"""
Technical Indicators — RSI, MACD, Bollinger Bands, ATR, Stochastic, OBV, VWAP
Inspired by ta-lib, pandas-ta
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class OHLCV:
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class IndicatorResult:
    name: str
    values: List[float]
    signal: str
    description: str


class TechnicalIndicators:
    """Pure function technical indicator calculations."""

    @staticmethod
    def sma(prices: List[float], period: int) -> List[float]:
        if len(prices) < period:
            return [0.0] * len(prices)
        result = [0.0] * (period - 1)
        for i in range(period - 1, len(prices)):
            avg = sum(prices[i - period + 1:i + 1]) / period
            result.append(round(avg, 4))
        return result

    @staticmethod
    def ema(prices: List[float], period: int) -> List[float]:
        if not prices:
            return []
        if len(prices) < period:
            return [0.0] * len(prices)
        multiplier = 2 / (period + 1)
        result = [0.0] * (period - 1)
        ema_val = sum(prices[:period]) / period
        result.append(round(ema_val, 4))
        for i in range(period, len(prices)):
            ema_val = (prices[i] - ema_val) * multiplier + ema_val
            result.append(round(ema_val, 4))
        return result

    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        if len(prices) < period + 1:
            return [50.0] * len(prices)
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [max(0, d) for d in deltas]
        losses = [max(0, -d) for d in deltas]
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        result = [50.0] * period
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(round(100 - 100 / (1 + rs), 2))
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                result.append(round(100 - 100 / (1 + rs), 2))
        return result

    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26,
             signal: int = 9) -> Dict[str, List[float]]:
        ema_fast = TechnicalIndicators.ema(prices, fast)
        ema_slow = TechnicalIndicators.ema(prices, slow)
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = [m - s for m, s in zip(macd_line, signal_line)]
        return {
            "macd": [round(v, 4) for v in macd_line],
            "signal": [round(v, 4) for v in signal_line],
            "histogram": [round(v, 4) for v in histogram],
        }

    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20,
                        std_dev: float = 2.0) -> Dict[str, List[float]]:
        sma = TechnicalIndicators.sma(prices, period)
        upper = []
        lower = []
        for i in range(len(prices)):
            if i < period - 1:
                upper.append(0.0)
                lower.append(0.0)
            else:
                window = prices[i - period + 1:i + 1]
                mean = sma[i]
                variance = sum((p - mean) ** 2 for p in window) / period
                std = math.sqrt(variance)
                upper.append(round(mean + std_dev * std, 4))
                lower.append(round(mean - std_dev * std, 4))
        return {
            "upper": upper,
            "middle": sma,
            "lower": lower,
        }

    @staticmethod
    def atr(candles: List[OHLCV], period: int = 14) -> List[float]:
        if len(candles) < 2:
            return [0.0] * len(candles)
        trs = [candles[0].high - candles[0].low]
        for i in range(1, len(candles)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i - 1].close
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
        result = [0.0] * (period - 1)
        atr_val = sum(trs[:period]) / period
        result.append(round(atr_val, 4))
        for i in range(period, len(trs)):
            atr_val = (atr_val * (period - 1) + trs[i]) / period
            result.append(round(atr_val, 4))
        return result

    @staticmethod
    def stochastic(candles: List[OHLCV], k_period: int = 14,
                   d_period: int = 3) -> Dict[str, List[float]]:
        k_values = []
        for i in range(len(candles)):
            if i < k_period - 1:
                k_values.append(50.0)
            else:
                window = candles[i - k_period + 1:i + 1]
                highest = max(c.high for c in window)
                lowest = min(c.low for c in window)
                if highest == lowest:
                    k_values.append(50.0)
                else:
                    k = (candles[i].close - lowest) / (highest - lowest) * 100
                    k_values.append(round(k, 2))
        d_values = TechnicalIndicators.sma(k_values, d_period)
        return {"k": k_values, "d": d_values}

    @staticmethod
    def obv(candles: List[OHLCV]) -> List[float]:
        if not candles:
            return []
        obv_values = [0.0]
        for i in range(1, len(candles)):
            if candles[i].close > candles[i - 1].close:
                obv_values.append(obv_values[-1] + candles[i].volume)
            elif candles[i].close < candles[i - 1].close:
                obv_values.append(obv_values[-1] - candles[i].volume)
            else:
                obv_values.append(obv_values[-1])
        return [round(v, 2) for v in obv_values]

    @staticmethod
    def vwap(candles: List[OHLCV]) -> List[float]:
        if not candles:
            return []
        cumulative_volume = 0.0
        cumulative_tpv = 0.0
        vwap_values = []
        for candle in candles:
            typical_price = (candle.high + candle.low + candle.close) / 3
            cumulative_volume += candle.volume
            cumulative_tpv += typical_price * candle.volume
            if cumulative_volume > 0:
                vwap_values.append(round(cumulative_tpv / cumulative_volume, 4))
            else:
                vwap_values.append(round(typical_price, 4))
        return vwap_values

    @staticmethod
    def support_resistance(candles: List[OHLCV],
                          lookback: int = 20) -> Dict[str, List[float]]:
        if len(candles) < lookback:
            return {"support": [], "resistance": []}
        supports = []
        resistances = []
        for i in range(lookback, len(candles)):
            window = candles[i - lookback:i + 1]
            lows = [c.low for c in window]
            highs = [c.high for c in window]
            supports.append(min(lows))
            resistances.append(max(highs))
        return {
            "support": [round(s, 4) for s in supports],
            "resistance": [round(r, 4) for r in resistances],
        }

    @classmethod
    def analyze_trend(cls, prices: List[float]) -> Dict:
        if len(prices) < 20:
            return {"trend": "insufficient_data"}
        sma_short = cls.sma(prices, 10)
        sma_long = cls.sma(prices, 20)
        rsi_values = cls.rsi(prices)
        current_rsi = rsi_values[-1] if rsi_values else 50
        current_sma_short = sma_short[-1]
        current_sma_long = sma_long[-1]
        if current_sma_short > current_sma_long and current_rsi > 50:
            trend = "bullish"
        elif current_sma_short < current_sma_long and current_rsi < 50:
            trend = "bearish"
        else:
            trend = "neutral"
        return {
            "trend": trend,
            "rsi": current_rsi,
            "sma_short": current_sma_short,
            "sma_long": current_sma_long,
            "sma_crossover": current_sma_short > current_sma_long,
        }
