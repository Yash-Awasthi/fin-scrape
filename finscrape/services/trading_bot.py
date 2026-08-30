"""
Trading bot from intelligent-trading-bot — automated trading logic.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import math


@dataclass
class Signal:
    pair: str
    side: str  # buy, sell, hold
    strength: float  # 0-1
    price: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    timestamp: float = 0.0
    reasoning: str = ""


@dataclass
class Position:
    pair: str
    side: str
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    opened_at: float = 0.0


class TradingBot:
    def __init__(self, initial_capital: float = 10000):
        self.capital = initial_capital
        self.positions: List[Position] = []
        self.trade_history: List[Dict] = []

    def generate_signal(self, prices: List[float], short_period: int = 5, long_period: int = 20) -> Signal:
        if len(prices) < long_period:
            return Signal(pair="BTC/USDT", side="hold", strength=0, price=prices[-1] if prices else 0)
        sma_short = sum(prices[-short_period:]) / short_period
        sma_long = sum(prices[-long_period:]) / long_period
        price = prices[-1]
        if sma_short > sma_long * 1.01:
            strength = min(1.0, (sma_short / sma_long - 1) * 10)
            return Signal(pair="BTC/USDT", side="buy", strength=strength, price=price,
                         stop_loss=price * 0.97, take_profit=price * 1.05,
                         reasoning=f"SMA{short_period} > SMA{long_period}")
        elif sma_short < sma_long * 0.99:
            strength = min(1.0, (1 - sma_short / sma_long) * 10)
            return Signal(pair="BTC/USDT", side="sell", strength=strength, price=price,
                         stop_loss=price * 1.03, take_profit=price * 0.95,
                         reasoning=f"SMA{short_period} < SMA{long_period}")
        return Signal(pair="BTC/USDT", side="hold", strength=0, price=price, reasoning="No clear signal")

    def execute_signal(self, signal: Signal) -> Optional[Position]:
        if signal.side == "hold" or signal.strength < 0.5:
            return None
        qty = self.capital * signal.strength * 0.1 / signal.price
        if signal.side == "buy":
            cost = qty * signal.price
            if cost > self.capital:
                return None
            self.capital -= cost
        elif signal.side == "sell":
            self.capital += qty * signal.price
        pos = Position(pair=signal.pair, side=signal.side, entry_price=signal.price,
                      quantity=qty, stop_loss=signal.stop_loss, take_profit=signal.take_profit)
        self.positions.append(pos)
        self.trade_history.append({"pair": signal.pair, "side": signal.side, "price": signal.price, "qty": qty})
        return pos

    def check_exits(self, current_prices: Dict[str, float]) -> List[Position]:
        closed = []
        remaining = []
        for pos in self.positions:
            price = current_prices.get(pos.pair, pos.entry_price)
            should_close = False
            if pos.side == "buy" and (price <= pos.stop_loss or price >= pos.take_profit):
                should_close = True
            elif pos.side == "sell" and (price >= pos.stop_loss or price <= pos.take_profit):
                should_close = True
            if should_close:
                pnl = (price - pos.entry_price) * pos.quantity if pos.side == "buy" else (pos.entry_price - price) * pos.quantity
                self.capital += pos.quantity * price + pnl
                closed.append(pos)
            else:
                remaining.append(pos)
        self.positions = remaining
        return closed
