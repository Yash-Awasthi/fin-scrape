"""
Trading strategies from pixiu — strategy backtesting framework.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class StrategySignal:
    timestamp: float
    direction: str  # long, short, flat
    strength: float
    reason: str


class Strategy:
    def __init__(self, name: str):
        self.name = name
        self.signals: List[StrategySignal] = []

    def generate_signals(self, prices: List[float]) -> List[StrategySignal]:
        raise NotImplementedError


class MovingAverageCross(Strategy):
    def __init__(self, short_period: int = 10, long_period: int = 50):
        super().__init__("MA_Cross")
        self.short = short_period
        self.long = long_period

    def generate_signals(self, prices: List[float]) -> List[StrategySignal]:
        signals = []
        for i in range(self.long, len(prices)):
            sma_short = sum(prices[i-self.short:i]) / self.short
            sma_long = sum(prices[i-self.long:i]) / self.long
            prev_short = sum(prices[i-self.short-1:i-1]) / self.short
            prev_long = sum(prices[i-self.long-1:i-1]) / self.long
            if prev_short <= prev_long and sma_short > sma_long:
                signals.append(StrategySignal(timestamp=i, direction="long", strength=0.7, reason="Golden cross"))
            elif prev_short >= prev_long and sma_short < sma_long:
                signals.append(StrategySignal(timestamp=i, direction="short", strength=0.7, reason="Death cross"))
        return signals


class RSIStrategy(Strategy):
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def compute_rsi(self, prices: List[float]) -> float:
        if len(prices) < self.period + 1: return 50
        gains = [(prices[i] - prices[i-1]) for i in range(1, len(prices))]
        recent = gains[-self.period:]
        up = sum(max(0, g) for g in recent) / self.period
        down = sum(max(0, -g) for g in recent) / self.period
        return 100 - 100 / (1 + up / down) if down > 0 else 100

    def generate_signals(self, prices: List[float]) -> List[StrategySignal]:
        signals = []
        for i in range(self.period + 1, len(prices)):
            rsi = self.compute_rsi(prices[:i+1])
            if rsi < self.oversold:
                signals.append(StrategySignal(timestamp=i, direction="long", strength=(self.oversold - rsi) / self.oversold, reason=f"RSI oversold {rsi:.1f}"))
            elif rsi > self.overbought:
                signals.append(StrategySignal(timestamp=i, direction="short", strength=(rsi - self.overbought) / (100 - self.overbought), reason=f"RSI overbought {rsi:.1f}"))
        return signals
