"""
Trade Execution — Order management, position tracking, and execution simulation.

Inspired by freqtrade and backtrader's order/position management.
Provides order lifecycle, position tracking, and fill simulation.
All pure functions — no broker API calls.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums and data structures
# ---------------------------------------------------------------------------

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class Order:
    """Trade order."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]  # None for market orders
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0
    filled_price: float = 0
    commission: float = 0
    timestamp: str = ""
    ttl_seconds: int = 0  # time to live, 0 = GTC
    parent_order_id: Optional[str] = None  # for OCO orders


@dataclass
class Position:
    """Open position."""
    symbol: str
    side: PositionSide
    entry_price: float
    quantity: float
    leverage: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0
    realized_pnl: float = 0
    fees_paid: float = 0
    opened_at: str = ""


@dataclass
class Fill:
    """Order fill record."""
    fill_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float
    timestamp: str


@dataclass
class PortfolioSnapshot:
    """Portfolio state at a point in time."""
    cash: float
    positions: Dict[str, Position]
    total_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_fees: float


# ---------------------------------------------------------------------------
# Order creation
# ---------------------------------------------------------------------------

def create_market_order(
    symbol: str,
    side: OrderSide,
    quantity: float,
    timestamp: str = "",
) -> Order:
    """Create a market order (executes at best available price)."""
    return Order(
        order_id=f"ord_{uuid.uuid4().hex[:12]}",
        symbol=symbol,
        side=side,
        order_type=OrderType.MARKET,
        quantity=quantity,
        price=None,
        timestamp=timestamp,
    )


def create_limit_order(
    symbol: str,
    side: OrderSide,
    quantity: float,
    price: float,
    ttl_seconds: int = 86400,
    timestamp: str = "",
) -> Order:
    """Create a limit order (executes at specified price or better)."""
    return Order(
        order_id=f"ord_{uuid.uuid4().hex[:12]}",
        symbol=symbol,
        side=side,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        timestamp=timestamp,
        ttl_seconds=ttl_seconds,
    )


def create_stop_order(
    symbol: str,
    side: OrderSide,
    quantity: float,
    stop_price: float,
    limit_price: Optional[float] = None,
    timestamp: str = "",
) -> Order:
    """Create a stop order (triggers at stop price)."""
    order_type = OrderType.STOP_LIMIT if limit_price else OrderType.STOP
    return Order(
        order_id=f"ord_{uuid.uuid4().hex[:12]}",
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=limit_price or stop_price,
        timestamp=timestamp,
    )


# ---------------------------------------------------------------------------
# Order matching / fill simulation
# ---------------------------------------------------------------------------

def simulate_fill(
    order: Order,
    current_price: float,
    commission_rate: float = 0.001,
    slippage_bps: float = 5,  # basis points
) -> Fill:
    """
    Simulate order fill with slippage and commission.
    
    Args:
        order: Order to fill
        current_price: Current market price
        commission_rate: Commission as fraction (default 0.1%)
        slippage_bps: Slippage in basis points (default 5 bps = 0.05%)
    
    Returns:
        Fill record
    """
    # Apply slippage
    slippage = current_price * slippage_bps / 10000
    if order.side == OrderSide.BUY:
        fill_price = current_price + slippage
    else:
        fill_price = current_price - slippage
    
    # For limit orders, check if price is achievable
    if order.order_type == OrderType.LIMIT:
        if order.side == OrderSide.BUY and order.price is not None:
            if current_price > order.price:
                return Fill(
                    fill_id="", order_id=order.order_id, symbol=order.symbol,
                    side=order.side, quantity=0, price=0, commission=0,
                    timestamp=order.timestamp,
                )
        elif order.side == OrderSide.SELL and order.price is not None:
            if current_price < order.price:
                return Fill(
                    fill_id="", order_id=order.order_id, symbol=order.symbol,
                    side=order.side, quantity=0, price=0, commission=0,
                    timestamp=order.timestamp,
                )
    
    # Calculate commission
    commission = fill_price * order.quantity * commission_rate
    
    return Fill(
        fill_id=f"fill_{uuid.uuid4().hex[:12]}",
        order_id=order.order_id,
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        price=round(fill_price, 4),
        commission=round(commission, 4),
        timestamp=order.timestamp,
    )


def check_stop_orders(
    orders: List[Order],
    current_prices: Dict[str, float],
) -> List[Order]:
    """
    Check if any stop orders should be triggered.
    
    Returns list of orders that should be converted to market orders.
    """
    triggered = []
    
    for order in orders:
        if order.status != OrderStatus.PENDING:
            continue
        if order.order_type not in (OrderType.STOP, OrderType.STOP_LIMIT):
            continue
        
        price = current_prices.get(order.symbol)
        if price is None:
            continue
        
        # Stop triggered
        if order.side == OrderSide.BUY and price >= (order.price or 0):
            triggered.append(order)
        elif order.side == OrderSide.SELL and price <= (order.price or float('inf')):
            triggered.append(order)
    
    return triggered


# ---------------------------------------------------------------------------
# Position management
# ---------------------------------------------------------------------------

def update_position_pnl(
    position: Position,
    current_price: float,
) -> Position:
    """Update unrealized PnL for a position."""
    if position.side == PositionSide.LONG:
        unrealized = (current_price - position.entry_price) * position.quantity
    else:
        unrealized = (position.entry_price - current_price) * position.quantity
    
    position.unrealized_pnl = round(unrealized, 4)
    return position


def calculate_position_size(
    risk_per_trade: float,  # $ amount willing to risk
    stop_loss_distance: float,  # price difference to stop loss
    entry_price: float,
    leverage: float = 1.0,
) -> float:
    """
    Calculate position size based on risk management.
    
    Kelly-inspired: risk a fixed dollar amount per trade.
    """
    if stop_loss_distance <= 0 or entry_price <= 0:
        return 0
    
    quantity = risk_per_trade / stop_loss_distance
    max_value = risk_per_trade * 10  # Max 10x risk
    
    value = quantity * entry_price
    if value > max_value:
        quantity = max_value / entry_price
    
    return round(quantity, 4)


def check_stop_loss(position: Position, current_price: float) -> bool:
    """Check if position should be stopped out."""
    if position.stop_loss is None:
        return False
    
    if position.side == PositionSide.LONG:
        return current_price <= position.stop_loss
    else:
        return current_price >= position.stop_loss


def check_take_profit(position: Position, current_price: float) -> bool:
    """Check if position should take profit."""
    if position.take_profit is None:
        return False
    
    if position.side == PositionSide.LONG:
        return current_price >= position.take_profit
    else:
        return current_price <= position.take_profit


# ---------------------------------------------------------------------------
# Portfolio management
# ---------------------------------------------------------------------------

def calculate_portfolio_value(
    cash: float,
    positions: Dict[str, Position],
    current_prices: Dict[str, float],
) -> PortfolioSnapshot:
    """Calculate total portfolio value with unrealized PnL."""
    total_unrealized = 0
    total_realized = 0
    total_fees = 0
    
    for symbol, pos in positions.items():
        price = current_prices.get(symbol, pos.entry_price)
        pos = update_position_pnl(pos, price)
        total_unrealized += pos.unrealized_pnl
        total_realized += pos.realized_pnl
        total_fees += pos.fees_paid
    
    position_value = sum(
        pos.quantity * current_prices.get(sym, pos.entry_price)
        for sym, pos in positions.items()
    )
    
    return PortfolioSnapshot(
        cash=cash,
        positions=positions,
        total_value=round(cash + position_value, 2),
        unrealized_pnl=round(total_unrealized, 2),
        realized_pnl=round(total_realized, 2),
        total_fees=round(total_fees, 2),
    )


def calculate_risk_metrics(
    positions: Dict[str, Position],
    current_prices: Dict[str, float],
    portfolio_value: float,
) -> Dict[str, float]:
    """Calculate portfolio risk metrics."""
    if portfolio_value <= 0:
        return {"exposure": 0, "concentration": 0, "max_drawdown": 0}
    
    # Total exposure
    exposure = sum(
        pos.quantity * current_prices.get(sym, pos.entry_price)
        for sym, pos in positions.items()
    )
    
    # Concentration (Herfindahl index)
    weights = {}
    for sym, pos in positions.items():
        value = pos.quantity * current_prices.get(sym, pos.entry_price)
        weights[sym] = value / portfolio_value if portfolio_value > 0 else 0
    
    hhi = sum(w ** 2 for w in weights.values())
    
    # Max position concentration
    max_concentration = max(weights.values()) if weights else 0
    
    return {
        "exposure": round(exposure, 2),
        "exposure_pct": round(exposure / portfolio_value * 100, 2),
        "concentration_hhi": round(hhi, 4),
        "max_position_pct": round(max_concentration * 100, 2),
        "position_count": len(positions),
    }
