"""Tests for Backtesting Engine."""
import pytest
from finscrape.services.backtesting_engine import (
    simulate_trade,
    compute_performance_metrics,
    build_equity_curve,
    backtest_simple,
    walk_forward_test,
    Trade,
)


class TestSimulateTrade:
    def test_long_trade_profit(self):
        trade = simulate_trade("AAPL", "long", "2024-01-01", "2024-01-06", 100, 110, 10000)
        assert trade.pnl > 0
        assert trade.return_pct == pytest.approx(10.0)
        assert trade.shares == 100

    def test_long_trade_loss(self):
        trade = simulate_trade("AAPL", "long", "2024-01-01", "2024-01-06", 100, 90, 10000)
        assert trade.pnl < 0
        assert trade.return_pct == pytest.approx(-10.0)

    def test_short_trade_profit(self):
        trade = simulate_trade("AAPL", "short", "2024-01-01", "2024-01-06", 100, 90, 10000)
        assert trade.pnl > 0
        assert trade.return_pct == pytest.approx(10.0)

    def test_zero_price(self):
        trade = simulate_trade("AAPL", "long", "2024-01-01", "2024-01-06", 0, 100, 10000)
        assert trade.pnl == 0
        assert trade.shares == 0


class TestPerformanceMetrics:
    def test_basic(self):
        trades = [
            Trade("A", "long", "2024-01-01", "2024-01-06", 100, 110, 100, 1000, 10.0, 5),
            Trade("B", "long", "2024-01-02", "2024-01-07", 100, 95, 100, -500, -5.0, 5),
            Trade("C", "long", "2024-01-03", "2024-01-08", 100, 120, 100, 2000, 20.0, 5),
        ]
        metrics = compute_performance_metrics(trades)
        assert metrics.n_trades == 3
        assert metrics.win_rate == pytest.approx(66.7, abs=1)
        assert metrics.n_long == 3
        assert metrics.avg_return_pct == pytest.approx(8.33, abs=0.1)

    def test_empty(self):
        metrics = compute_performance_metrics([])
        assert metrics.n_trades == 0

    def test_all_wins(self):
        trades = [
            Trade("A", "long", "2024-01-01", "2024-01-06", 100, 110, 100, 1000, 10.0, 5),
            Trade("B", "long", "2024-01-02", "2024-01-07", 100, 120, 100, 2000, 20.0, 5),
        ]
        metrics = compute_performance_metrics(trades)
        assert metrics.win_rate == 100.0
        assert metrics.max_drawdown_pct == 0.0


class TestEquityCurve:
    def test_basic(self):
        trades = [
            Trade("A", "long", "2024-01-01", "2024-01-06", 100, 110, 100, 1000, 10.0, 5),
            Trade("B", "long", "2024-01-02", "2024-01-07", 100, 95, 100, -500, -5.0, 5),
        ]
        equity = build_equity_curve(trades, 100000)
        assert equity[0] == 100000
        assert equity[-1] == 100500


class TestBacktestSimple:
    def test_basic(self):
        signals = [
            {"ticker": "AAPL", "date": "2024-01-02", "conviction": 0.8},
            {"ticker": "AAPL", "date": "2024-01-05", "conviction": -0.5},
        ]
        prices = {
            "AAPL": [
                ("2024-01-01", 100), ("2024-01-02", 102), ("2024-01-03", 104),
                ("2024-01-04", 106), ("2024-01-05", 108), ("2024-01-06", 110),
                ("2024-01-07", 112), ("2024-01-08", 114), ("2024-01-09", 116),
                ("2024-01-10", 118),
            ],
        }
        result = backtest_simple(signals, prices)
        assert result.trades is not None
        if result.metrics:
            assert result.metrics.n_trades >= 1

    def test_empty(self):
        result = backtest_simple([], {})
        assert result.trades == []


class TestWalkForward:
    def test_basic(self):
        signals = [
            {"ticker": "AAPL", "date": f"2024-01-{i:02d}", "conviction": 0.5 * (1 if i % 2 == 0 else -1)}
            for i in range(1, 20)
        ]
        prices = {
            "AAPL": [(f"2024-01-{i:02d}", 100 + i) for i in range(1, 25)],
        }
        result = walk_forward_test(signals, prices, train_pct=0.7)
        assert "train" in result
        assert "test" in result
