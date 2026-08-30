"""Tests for trade_executor.py — order management and execution."""

import pytest
from finscrape.services.trade_executor import (
    OrderSide, OrderType, OrderStatus, PositionSide,
    create_market_order, create_limit_order, create_stop_order,
    simulate_fill, check_stop_orders,
    update_position_pnl, calculate_position_size,
    check_stop_loss, check_take_profit,
    calculate_portfolio_value, calculate_risk_metrics,
    Order, Position,
)


class TestOrderCreation:
    def test_market_order(self):
        order = create_market_order("AAPL", OrderSide.BUY, 10)
        assert order.symbol == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 10
        assert order.price is None
        assert order.status == OrderStatus.PENDING

    def test_limit_order(self):
        order = create_limit_order("AAPL", OrderSide.SELL, 5, 150.0)
        assert order.order_type == OrderType.LIMIT
        assert order.price == 150.0

    def test_stop_order(self):
        order = create_stop_order("AAPL", OrderSide.SELL, 5, 140.0)
        assert order.order_type == OrderType.STOP

    def test_stop_limit_order(self):
        order = create_stop_order("AAPL", OrderSide.SELL, 5, 140.0, limit_price=139.0)
        assert order.order_type == OrderType.STOP_LIMIT
        assert order.price == 139.0


class TestFillSimulation:
    def test_market_buy_fill(self):
        order = create_market_order("AAPL", OrderSide.BUY, 10)
        fill = simulate_fill(order, 150.0)
        assert fill.quantity == 10
        assert fill.price >= 150.0  # Slippage added
        assert fill.commission > 0

    def test_market_sell_fill(self):
        order = create_market_order("AAPL", OrderSide.SELL, 10)
        fill = simulate_fill(order, 150.0)
        assert fill.price <= 150.0  # Slippage subtracted

    def test_limit_order_not_fillable(self):
        order = create_limit_order("AAPL", OrderSide.BUY, 10, 140.0)
        fill = simulate_fill(order, 150.0)  # Market above limit
        assert fill.quantity == 0

    def test_commission_calculation(self):
        order = create_market_order("AAPL", OrderSide.BUY, 10)
        fill = simulate_fill(order, 100.0, commission_rate=0.001)
        assert fill.commission == pytest.approx(1.0, abs=0.1)  # 10 * 100 * 0.001


class TestStopOrders:
    def test_trigger_stop_loss(self):
        order = create_stop_order("AAPL", OrderSide.SELL, 10, 140.0)
        triggered = check_stop_orders([order], {"AAPL": 135.0})
        assert len(triggered) == 1

    def test_no_trigger_above_stop(self):
        order = create_stop_order("AAPL", OrderSide.SELL, 10, 140.0)
        triggered = check_stop_orders([order], {"AAPL": 145.0})
        assert len(triggered) == 0


class TestPositionManagement:
    def test_long_pnl(self):
        pos = Position(symbol="AAPL", side=PositionSide.LONG, entry_price=100, quantity=10)
        pos = update_position_pnl(pos, 110)
        assert pos.unrealized_pnl == 100  # (110-100) * 10

    def test_short_pnl(self):
        pos = Position(symbol="AAPL", side=PositionSide.SHORT, entry_price=100, quantity=10)
        pos = update_position_pnl(pos, 90)
        assert pos.unrealized_pnl == 100  # (100-90) * 10

    def test_position_size_calculation(self):
        size = calculate_position_size(risk_per_trade=100, stop_loss_distance=5, entry_price=100)
        assert size > 0  # 100/5=20, but capped by max_value=1000
        assert size <= 10  # Max 10x risk = 1000/100 = 10

    def test_stop_loss_check(self):
        pos = Position(symbol="AAPL", side=PositionSide.LONG, entry_price=100, quantity=10, stop_loss=95)
        assert check_stop_loss(pos, 94) is True
        assert check_stop_loss(pos, 96) is False

    def test_take_profit_check(self):
        pos = Position(symbol="AAPL", side=PositionSide.LONG, entry_price=100, quantity=10, take_profit=110)
        assert check_take_profit(pos, 111) is True
        assert check_take_profit(pos, 109) is False


class TestPortfolio:
    def test_portfolio_value(self):
        positions = {
            "AAPL": Position(symbol="AAPL", side=PositionSide.LONG, entry_price=100, quantity=10),
        }
        snapshot = calculate_portfolio_value(cash=5000, positions=positions, current_prices={"AAPL": 110})
        assert snapshot.total_value == 6100  # 5000 + 10*110
        assert snapshot.unrealized_pnl == 100

    def test_risk_metrics(self):
        positions = {
            "AAPL": Position(symbol="AAPL", side=PositionSide.LONG, entry_price=100, quantity=10),
            "MSFT": Position(symbol="MSFT", side=PositionSide.LONG, entry_price=200, quantity=5),
        }
        metrics = calculate_risk_metrics(positions, {"AAPL": 100, "MSFT": 200}, 3000)
        assert metrics["position_count"] == 2
        assert metrics["exposure"] > 0
