"""
Nautilus trader patterns from nautilus_trader — order management.
"""
from dataclasses import dataclass
from typing import List, Optional
import time


@dataclass
class Order:
    id: str
    symbol: str
    side: str  # buy, sell
    order_type: str  # market, limit, stop
    quantity: float
    price: float = 0.0
    status: str = "pending"
    created_at: float = 0.0
    filled_at: float = 0.0
    filled_price: float = 0.0


class OrderManager:
    def __init__(self):
        self.orders: List[Order] = []
        self.order_id_counter = 0

    def create_market_order(self, symbol: str, side: str, quantity: float) -> Order:
        self.order_id_counter += 1
        order = Order(id=f"ord_{self.order_id_counter}", symbol=symbol, side=side, order_type="market", quantity=quantity, created_at=time.time(), status="submitted")
        self.orders.append(order)
        return order

    def create_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Order:
        self.order_id_counter += 1
        order = Order(id=f"ord_{self.order_id_counter}", symbol=symbol, side=side, order_type="limit", quantity=quantity, price=price, created_at=time.time(), status="submitted")
        self.orders.append(order)
        return order

    def cancel_order(self, order_id: str) -> bool:
        for order in self.orders:
            if order.id == order_id and order.status in ("submitted", "pending"):
                order.status = "cancelled"
                return True
        return False

    def get_open_orders(self) -> List[Order]:
        return [o for o in self.orders if o.status in ("submitted", "pending")]

    def get_filled_orders(self) -> List[Order]:
        return [o for o in self.orders if o.status == "filled"]
