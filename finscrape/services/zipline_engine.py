"""
Zipline Engine — Extracted from Zipline's algorithmic trading patterns.

Provides:
- Event-driven backtesting engine
- Order management system
- Position tracking
- Performance analytics
- Risk metrics
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: float = 0.0
    created_at: str = ""
    filled_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    market_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.market_price

    @property
    def unrealized_pnl(self) -> float:
        if self.quantity == 0:
            return 0.0
        return (self.market_price - self.avg_cost) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.avg_cost <= 0 or self.quantity == 0:
            return 0.0
        return (self.market_price - self.avg_cost) / self.avg_cost * 100


@dataclass
class Bar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str = ""


@dataclass
class PortfolioState:
    cash: float
    positions: Dict[str, Position]
    equity_curve: List[float]
    timestamp: str = ""

    @property
    def total_equity(self) -> float:
        position_value = sum(p.market_value for p in self.positions.values())
        return self.cash + position_value

    @property
    def returns(self) -> List[float]:
        if len(self.equity_curve) < 2:
            return []
        return [
            (self.equity_curve[i] - self.equity_curve[i - 1]) / self.equity_curve[i - 1]
            for i in range(1, len(self.equity_curve))
        ]


class ZiplineEngine:
    """Event-driven backtesting engine."""

    def __init__(self, initial_cash: float = 100000.0) -> None:
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.equity_curve: List[float] = [initial_cash]
        self.bars: List[Bar] = []
        self._order_id_counter = 0
        self._commission_rate = 0.001

    def order(
        self,
        symbol: str,
        quantity: int,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Order:
        """Place an order."""
        self._order_id_counter += 1
        order = Order(
            order_id=f"order-{self._order_id_counter}",
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            stop_price=stop_price,
        )
        self.orders.append(order)
        return order

    def execute_order(self, order: Order, fill_price: float) -> bool:
        """Execute an order at the given price."""
        if order.status != OrderStatus.PENDING:
            return False

        commission = fill_price * order.quantity * self._commission_rate
        total_cost = fill_price * order.quantity + commission

        if order.side == OrderSide.BUY:
            if self.cash < total_cost:
                order.status = OrderStatus.REJECTED
                return False

            self.cash -= total_cost
            pos = self.positions.get(order.symbol)
            if pos:
                total_qty = pos.quantity + order.quantity
                pos.avg_cost = (pos.avg_cost * pos.quantity + fill_price * order.quantity) / total_qty
                pos.quantity = total_qty
            else:
                self.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    avg_cost=fill_price,
                    market_price=fill_price,
                )
        else:  # SELL
            pos = self.positions.get(order.symbol)
            if not pos or pos.quantity < order.quantity:
                order.status = OrderStatus.REJECTED
                return False

            self.cash += fill_price * order.quantity - commission
            pos.quantity -= order.quantity
            if pos.quantity == 0:
                del self.positions[order.symbol]

        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = fill_price
        order.filled_at = datetime.now().isoformat()

        return True

    def update_market_price(self, symbol: str, price: float) -> None:
        """Update market price for a symbol."""
        if symbol in self.positions:
            self.positions[symbol].market_price = price

    def record_bar(self, bar: Bar) -> None:
        """Record a new bar and update equity curve."""
        self.bars.append(bar)
        self.update_market_price(bar.symbol, bar.close)
        self.equity_curve.append(self.portfolio.total_equity)

    @property
    def portfolio(self) -> PortfolioState:
        return PortfolioState(
            cash=self.cash,
            positions=dict(self.positions),
            equity_curve=list(self.equity_curve),
            timestamp=datetime.now().isoformat(),
        )

    def get_performance(self) -> Dict[str, float]:
        """Calculate performance metrics."""
        total_return = (self.equity_curve[-1] - self.initial_cash) / self.initial_cash if self.equity_curve else 0.0
        returns = self.portfolio.returns

        sharpe = 0.0
        if returns:
            mean_r = sum(returns) / len(returns)
            var = sum((r - mean_r) ** 2 for r in returns) / max(len(returns) - 1, 1)
            std = var ** 0.5
            sharpe = mean_r / std * (252 ** 0.5) if std > 1e-10 else 0.0

        max_dd = 0.0
        if self.equity_curve:
            peak = self.equity_curve[0]
            for val in self.equity_curve:
                if val > peak:
                    peak = val
                dd = (peak - val) / peak if peak > 0 else 0.0
                max_dd = max(max_dd, dd)

        return {
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "final_equity": self.equity_curve[-1] if self.equity_curve else self.initial_cash,
            "total_trades": len([o for o in self.orders if o.status == OrderStatus.FILLED]),
        }
