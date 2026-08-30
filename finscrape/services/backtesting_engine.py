"""
Backtesting Engine — Inspired by Freqtrade
Event-driven backtesting with broker simulation, order management, and performance analytics
"""

import math
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Signal(Enum):
    BUY = 1
    SELL = -1
    HOLD = 0


@dataclass
class Candle:
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Order:
    order_id: str
    side: OrderSide
    order_type: OrderType
    price: float
    amount: float
    status: OrderStatus = OrderStatus.PENDING
    filled_price: float = 0.0
    filled_amount: float = 0.0
    timestamp: float = 0.0
    fee: float = 0.0


@dataclass
class Position:
    symbol: str
    side: OrderSide
    entry_price: float
    amount: float
    entry_time: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0

    def update_pnl(self, current_price: float):
        if self.side == OrderSide.BUY:
            self.pnl = (current_price - self.entry_price) * self.amount
            self.pnl_pct = ((current_price - self.entry_price) / self.entry_price * 100
                           if self.entry_price > 0 else 0)
        else:
            self.pnl = (self.entry_price - current_price) * self.amount
            self.pnl_pct = ((self.entry_price - current_price) / self.entry_price * 100
                           if self.entry_price > 0 else 0)


@dataclass
class TradeResult:
    symbol: str
    side: OrderSide
    entry_price: float
    exit_price: float
    amount: float
    entry_time: float
    exit_time: float
    pnl: float
    pnl_pct: float
    fee: float
    duration_seconds: float


@dataclass
class BacktestResult:
    trades: List[TradeResult]
    total_pnl: float
    total_pnl_pct: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    avg_trade_duration: float
    starting_balance: float
    ending_balance: float
    return_pct: float
    calmar_ratio: float
    sortino_ratio: float


class BacktestBroker:
    """Simulates a broker for backtesting."""

    def __init__(self, initial_balance: float = 10000.0, fee_rate: float = 0.001,
                 slippage: float = 0.0005):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.positions: List[Position] = []
        self.orders: List[Order] = []
        self.trades: List[TradeResult] = []
        self.order_counter = 0

    def create_order(self, side: OrderSide, price: float, amount: float,
                     order_type: OrderType = OrderType.MARKET) -> Order:
        self.order_counter += 1
        order = Order(
            order_id=f"order_{self.order_counter}",
            side=side,
            order_type=order_type,
            price=price,
            amount=amount,
            timestamp=0.0
        )
        self.orders.append(order)
        return order

    def fill_order(self, order: Order, current_price: float, timestamp: float) -> bool:
        if order.status != OrderStatus.PENDING:
            return False
        if order.order_type == OrderType.MARKET:
            fill_price = current_price * (1 + self.slippage if order.side == OrderSide.BUY
                                          else 1 - self.slippage)
        elif order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY and current_price > order.price:
                return False
            if order.side == OrderSide.SELL and current_price < order.price:
                return False
            fill_price = order.price
        elif order.order_type == OrderType.STOP:
            if order.side == OrderSide.BUY and current_price < order.price:
                return False
            if order.side == OrderSide.SELL and current_price > order.price:
                return False
            fill_price = current_price
        else:
            fill_price = current_price
        fee = fill_price * order.amount * self.fee_rate
        cost = fill_price * order.amount + fee if order.side == OrderSide.BUY else 0
        if cost > self.balance:
            order.status = OrderStatus.REJECTED
            return False
        self.balance -= cost
        order.status = OrderStatus.FILLED
        order.filled_price = fill_price
        order.filled_amount = order.amount
        order.timestamp = timestamp
        order.fee = fee
        if order.side == OrderSide.BUY:
            position = Position(
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                entry_price=fill_price,
                amount=order.amount,
                entry_time=timestamp
            )
            self.positions.append(position)
        else:
            for pos in self.positions[:]:
                if pos.side == OrderSide.BUY:
                    pnl = (fill_price - pos.entry_price) * pos.amount
                    trade = TradeResult(
                        symbol=pos.symbol,
                        side=pos.side,
                        entry_price=pos.entry_price,
                        exit_price=fill_price,
                        amount=pos.amount,
                        entry_time=pos.entry_time,
                        exit_time=timestamp,
                        pnl=pnl - fee,
                        pnl_pct=((fill_price - pos.entry_price) / pos.entry_price * 100
                                if pos.entry_price > 0 else 0),
                        fee=fee + pos.amount * pos.entry_price * self.fee_rate,
                        duration_seconds=timestamp - pos.entry_time
                    )
                    self.trades.append(trade)
                    self.positions.remove(pos)
                    self.balance += fill_price * pos.amount - fee
                    break
        return True

    def get_balance(self) -> float:
        return self.balance

    def get_positions(self) -> List[Position]:
        return self.positions.copy()

    def get_portfolio_value(self, current_price: float) -> float:
        value = self.balance
        for pos in self.positions:
            pos.update_pnl(current_price)
            value += pos.entry_price * pos.amount + pos.pnl
        return value

    def cancel_all_orders(self):
        for order in self.orders:
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED


class BacktestEngine:
    """Event-driven backtesting engine."""

    def __init__(self, broker: Optional[BacktestBroker] = None):
        self.broker = broker or BacktestBroker()
        self.candles: List[Candle] = []
        self.strategy: Optional[Callable] = None
        self.results: Optional[BacktestResult] = None

    def load_candles(self, candles: List[Candle]):
        self.candles = sorted(candles, key=lambda c: c.timestamp)

    def set_strategy(self, strategy: Callable):
        self.strategy = strategy

    def run(self, initial_balance: float = 10000.0) -> BacktestResult:
        if not self.candles:
            raise ValueError("No candles loaded")
        if not self.strategy:
            raise ValueError("No strategy set")
        self.broker = BacktestBroker(initial_balance=initial_balance)
        portfolio_values = [initial_balance]
        for i, candle in enumerate(self.candles):
            context = {
                "candle": candle,
                "candles": self.candles[:i + 1],
                "index": i,
                "balance": self.broker.get_balance(),
                "positions": self.broker.get_positions()
            }
            signal = self.strategy(context)
            if signal == Signal.BUY and not self.broker.get_positions():
                amount = (self.broker.get_balance() * 0.95) / candle.close
                order = self.broker.create_order(OrderSide.BUY, candle.close, amount)
                self.broker.fill_order(order, candle.close, candle.timestamp)
            elif signal == Signal.SELL and self.broker.get_positions():
                for pos in self.broker.get_positions():
                    order = self.broker.create_order(OrderSide.SELL, candle.close, pos.amount)
                    self.broker.fill_order(order, candle.close, candle.timestamp)
            portfolio_values.append(self.broker.get_portfolio_value(candle.close))
        self.broker.cancel_all_orders()
        self.results = self._calculate_results(portfolio_values, initial_balance)
        return self.results

    def _calculate_results(self, portfolio_values: List[float],
                           initial_balance: float) -> BacktestResult:
        trades = self.broker.trades
        if not trades:
            return BacktestResult(
                trades=[], total_pnl=0, total_pnl_pct=0, win_rate=0,
                profit_factor=0, sharpe_ratio=0, max_drawdown=0,
                max_drawdown_pct=0, total_trades=0, winning_trades=0,
                losing_trades=0, avg_win=0, avg_loss=0, best_trade=0,
                worst_trade=0, avg_trade_duration=0, starting_balance=initial_balance,
                ending_balance=initial_balance, return_pct=0, calmar_ratio=0,
                sortino_ratio=0
            )
        total_pnl = sum(t.pnl for t in trades)
        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl <= 0]
        win_rate = len(winning) / len(trades) if trades else 0
        gross_profit = sum(t.pnl for t in winning)
        gross_loss = abs(sum(t.pnl for t in losing))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        returns = []
        for i in range(1, len(portfolio_values)):
            if portfolio_values[i - 1] > 0:
                returns.append((portfolio_values[i] - portfolio_values[i - 1]) / portfolio_values[i - 1])
        avg_return = sum(returns) / len(returns) if returns else 0
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if returns else 1
        sharpe = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0
        peak = portfolio_values[0]
        max_dd = 0
        max_dd_pct = 0
        for v in portfolio_values:
            if v > peak:
                peak = v
            dd = peak - v
            dd_pct = dd / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
        downside_returns = [r for r in returns if r < 0]
        downside_std = (sum(r ** 2 for r in downside_returns) / len(downside_returns)) ** 0.5 if downside_returns else 1
        sortino = (avg_return / downside_std * (252 ** 0.5)) if downside_std > 0 else 0
        calmar = (total_pnl / initial_balance * 252) / max_dd_pct if max_dd_pct > 0 else 0
        return BacktestResult(
            trades=trades,
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl / initial_balance * 100, 2),
            win_rate=round(win_rate, 3),
            profit_factor=round(profit_factor, 2),
            sharpe_ratio=round(sharpe, 2),
            max_drawdown=round(max_dd, 2),
            max_drawdown_pct=round(max_dd_pct * 100, 2),
            total_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            avg_win=round(sum(t.pnl for t in winning) / len(winning), 2) if winning else 0,
            avg_loss=round(sum(t.pnl for t in losing) / len(losing), 2) if losing else 0,
            best_trade=round(max(t.pnl for t in trades), 2),
            worst_trade=round(min(t.pnl for t in trades), 2),
            avg_trade_duration=round(sum(t.duration_seconds for t in trades) / len(trades), 0),
            starting_balance=initial_balance,
            ending_balance=round(self.broker.get_balance(), 2),
            return_pct=round(total_pnl / initial_balance * 100, 2),
            calmar_ratio=round(calmar, 2),
            sortino_ratio=round(sortino, 2)
        )

    @staticmethod
    def compare_results(results: List[BacktestResult], names: List[str]) -> Dict:
        if not results:
            return {"error": "No results to compare"}
        comparison = []
        for result, name in zip(results, names):
            comparison.append({
                "name": name,
                "return_pct": result.return_pct,
                "win_rate": result.win_rate,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown_pct": result.max_drawdown_pct,
                "profit_factor": result.profit_factor,
                "total_trades": result.total_trades
            })
        best_return = max(comparison, key=lambda x: x["return_pct"])
        best_sharpe = max(comparison, key=lambda x: x["sharpe_ratio"])
        lowest_dd = min(comparison, key=lambda x: x["max_drawdown_pct"])
        return {
            "strategies": comparison,
            "best_return": best_return["name"],
            "best_sharpe": best_sharpe["name"],
            "lowest_drawdown": lowest_dd["name"]
        }


class StrategyBase:
    """Base class for backtesting strategies."""

    def __init__(self):
        self.position = None
        self.entry_price = 0.0
        self.trade_count = 0

    def on_candle(self, candle: Candle, candles: List[Candle], index: int) -> Signal:
        raise NotImplementedError

    def sma(self, candles: List[Candle], period: int, index: int) -> float:
        if index < period - 1:
            return 0.0
        return sum(c.close for c in candles[index - period + 1:index + 1]) / period

    def ema(self, candles: List[Candle], period: int, index: int) -> float:
        if index < period - 1:
            return self.sma(candles, period, index)
        multiplier = 2 / (period + 1)
        ema_val = self.sma(candles, period, period - 1)
        for i in range(period, index + 1):
            ema_val = (candles[i].close - ema_val) * multiplier + ema_val
        return ema_val

    def rsi(self, candles: List[Candle], period: int, index: int) -> float:
        if index < period:
            return 50.0
        gains = []
        losses = []
        for i in range(index - period + 1, index + 1):
            change = candles[i].close - candles[i - 1].close
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def bollinger_bands(self, candles: List[Candle], period: int,
                        index: int, std_dev: float = 2.0) -> Tuple[float, float, float]:
        if index < period - 1:
            mid = candles[index].close
            return mid, mid, mid
        closes = [candles[i].close for i in range(index - period + 1, index + 1)]
        mid = sum(closes) / period
        variance = sum((c - mid) ** 2 for c in closes) / period
        std = variance ** 0.5
        return mid - std_dev * std, mid, mid + std_dev * std

    def atr(self, candles: List[Candle], period: int, index: int) -> float:
        if index < period:
            return 0.0
        trs = []
        for i in range(index - period + 1, index + 1):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i - 1].close
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
        return sum(trs) / period
