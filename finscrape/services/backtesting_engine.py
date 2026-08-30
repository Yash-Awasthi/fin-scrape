"""Backtesting Engine — Alpha Model Simulation and Performance Analysis.

Extracted from ai-hedge-fund (inspiration).
Simulates trading alpha model signals with equal-dollar sizing,
computes performance metrics (Sharpe, drawdown, win rate).

All pure functions — no DB, no async.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Trade:
    """A single completed trade."""
    ticker: str
    direction: str  # "long" or "short"
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    shares: float
    pnl: float
    return_pct: float
    holding_days: int
    reasoning: str = ""


@dataclass
class PerformanceMetrics:
    """Summary statistics for a set of trades."""
    total_return_pct: float = 0.0
    annualized_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    n_trades: int = 0
    n_long: int = 0
    n_short: int = 0
    avg_return_pct: float = 0.0
    avg_holding_days: float = 0.0
    profit_factor: float = 0.0
    calmar_ratio: float = 0.0


@dataclass
class BacktestResult:
    """Complete backtest result."""
    trades: list[Trade] = field(default_factory=list)
    metrics: Optional[PerformanceMetrics] = None
    equity_curve: list[float] = field(default_factory=list)


def simulate_trade(
    ticker: str,
    direction: str,
    entry_date: str,
    exit_date: str,
    entry_price: float,
    exit_price: float,
    capital: float,
    reasoning: str = "",
) -> Trade:
    """Simulate a single trade with equal-dollar sizing.

    Args:
        ticker: Stock ticker
        direction: "long" or "short"
        entry_date: Entry date (YYYY-MM-DD)
        exit_date: Exit date (YYYY-MM-DD)
        entry_price: Entry price per share
        exit_price: Exit price per share
        capital: Dollar amount to allocate
        reasoning: Why the trade was made

    Returns:
        Completed Trade
    """
    if entry_price <= 0:
        return Trade(
            ticker=ticker, direction=direction,
            entry_date=entry_date, exit_date=exit_date,
            entry_price=entry_price, exit_price=exit_price,
            shares=0, pnl=0, return_pct=0, holding_days=0,
        )

    shares = capital / entry_price

    if direction == "long":
        pnl = (exit_price - entry_price) * shares
        return_pct = ((exit_price - entry_price) / entry_price) * 100.0
    else:  # short
        pnl = (entry_price - exit_price) * shares
        return_pct = ((entry_price - exit_price) / entry_price) * 100.0

    # Estimate holding days from dates
    try:
        from datetime import datetime
        d1 = datetime.strptime(entry_date, "%Y-%m-%d")
        d2 = datetime.strptime(exit_date, "%Y-%m-%d")
        holding_days = (d2 - d1).days
    except (ValueError, TypeError):
        holding_days = 0

    return Trade(
        ticker=ticker,
        direction=direction,
        entry_date=entry_date,
        exit_date=exit_date,
        entry_price=entry_price,
        exit_price=exit_price,
        shares=round(shares, 4),
        pnl=round(pnl, 2),
        return_pct=round(return_pct, 4),
        holding_days=holding_days,
        reasoning=reasoning,
    )


def compute_performance_metrics(trades: list[Trade]) -> PerformanceMetrics:
    """Compute comprehensive performance metrics from trades.

    Args:
        trades: List of completed trades

    Returns:
        PerformanceMetrics with all computed statistics
    """
    if not trades:
        return PerformanceMetrics()

    n = len(trades)
    returns = [t.return_pct for t in trades]
    pnls = [t.pnl for t in trades]

    total_return = sum(returns)
    avg_return = total_return / n
    avg_holding = sum(t.holding_days for t in trades) / n

    # Win rate
    wins = sum(1 for r in returns if r > 0)
    win_rate = (wins / n) * 100.0

    # Long/short counts
    n_long = sum(1 for t in trades if t.direction == "long")
    n_short = n - n_long

    # Sharpe ratio (simplified: mean return / std return)
    if n > 1:
        mean_ret = avg_return
        variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
        std_ret = math.sqrt(variance)
        sharpe = (mean_ret / std_ret) if std_ret > 0 else 0.0
    else:
        sharpe = 0.0

    # Max drawdown from equity curve
    equity = [0.0]
    for pnl in pnls:
        equity.append(equity[-1] + pnl)

    peak = equity[0]
    max_dd = 0.0
    for val in equity:
        peak = max(peak, val)
        dd = (peak - val) / abs(peak) if peak != 0 else 0
        max_dd = max(max_dd, dd)

    # Profit factor
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Annualized return (assuming 252 trading days)
    total_days = sum(t.holding_days for t in trades) or 1
    annualized = (total_return / total_days) * 252.0 if total_days > 0 else 0.0

    # Calmar ratio
    calmar = annualized / (max_dd * 100) if max_dd > 0 else 0.0

    return PerformanceMetrics(
        total_return_pct=round(total_return, 2),
        annualized_return_pct=round(annualized, 2),
        sharpe_ratio=round(sharpe, 3),
        max_drawdown_pct=round(max_dd * 100, 2),
        win_rate=round(win_rate, 1),
        n_trades=n,
        n_long=n_long,
        n_short=n_short,
        avg_return_pct=round(avg_return, 4),
        avg_holding_days=round(avg_holding, 1),
        profit_factor=round(profit_factor, 2),
        calmar_ratio=round(calmar, 3),
    )


def build_equity_curve(trades: list[Trade], initial_capital: float = 100000.0) -> list[float]:
    """Build equity curve from trades.

    Args:
        trades: Chronologically sorted trades
        initial_capital: Starting capital

    Returns:
        List of equity values over time
    """
    equity = [initial_capital]
    for trade in sorted(trades, key=lambda t: t.entry_date):
        equity.append(equity[-1] + trade.pnl)
    return equity


def backtest_simple(
    signals: list[dict],
    prices: dict[str, list[tuple[str, float]]],
    capital: float = 100000.0,
    per_trade: float = 10000.0,
    holding_days: int = 5,
    threshold: float = 0.0,
) -> BacktestResult:
    """Run a simple backtest with threshold-based entry.

    Args:
        signals: List of {ticker, date, conviction} (conviction in [-1, +1])
        prices: Dict mapping ticker to list of (date, close_price)
        capital: Total capital
        per_trade: Capital per trade
        holding_days: Days to hold each position
        threshold: Minimum |conviction| to trigger trade

    Returns:
        BacktestResult with trades and metrics
    """
    trades = []

    # Group signals by ticker
    signals_by_ticker: dict[str, list] = {}
    for sig in signals:
        ticker = sig["ticker"]
        if ticker not in signals_by_ticker:
            signals_by_ticker[ticker] = []
        signals_by_ticker[ticker].append(sig)

    for ticker, ticker_signals in signals_by_ticker.items():
        if ticker not in prices:
            continue

        price_dict = {d: p for d, p in prices[ticker]}

        for sig in sorted(ticker_signals, key=lambda s: s["date"]):
            conviction = sig["conviction"]
            if abs(conviction) <= threshold:
                continue

            entry_date = sig["date"]
            entry_price = price_dict.get(entry_date)
            if entry_price is None:
                continue

            # Find exit date
            sorted_dates = sorted(price_dict.keys())
            try:
                entry_idx = sorted_dates.index(entry_date)
                exit_idx = min(entry_idx + holding_days, len(sorted_dates) - 1)
                exit_date = sorted_dates[exit_idx]
                exit_price = price_dict[exit_date]
            except (ValueError, IndexError):
                continue

            direction = "long" if conviction > 0 else "short"
            trade = simulate_trade(
                ticker=ticker,
                direction=direction,
                entry_date=entry_date,
                exit_date=exit_date,
                entry_price=entry_price,
                exit_price=exit_price,
                capital=per_trade,
                reasoning=f"conviction={conviction:.2f}",
            )
            trades.append(trade)

    if not trades:
        return BacktestResult()

    trades.sort(key=lambda t: t.entry_date)
    equity = build_equity_curve(trades, capital)
    metrics = compute_performance_metrics(trades)

    return BacktestResult(trades=trades, metrics=metrics, equity_curve=equity)


def walk_forward_test(
    signals: list[dict],
    prices: dict[str, list[tuple[str, float]]],
    train_pct: float = 0.7,
    capital: float = 100000.0,
    per_trade: float = 10000.0,
    holding_days: int = 5,
) -> dict:
    """Walk-forward optimization test.

    Splits data into train/test, optimizes on train, evaluates on test.

    Args:
        signals: All signals
        prices: All prices
        train_pct: Fraction for training
        capital: Starting capital
        per_trade: Per-trade allocation
        holding_days: Holding period

    Returns:
        Dictionary with train and test results
    """
    n = len(signals)
    split = int(n * train_pct)

    train_signals = signals[:split]
    test_signals = signals[split:]

    # Test with default threshold
    train_result = backtest_simple(
        train_signals, prices, capital, per_trade, holding_days, threshold=0.0
    )
    test_result = backtest_simple(
        test_signals, prices, capital, per_trade, holding_days, threshold=0.0
    )

    return {
        "train": train_result,
        "test": test_result,
        "train_trades": train_result.metrics.n_trades if train_result.metrics else 0,
        "test_trades": test_result.metrics.n_trades if test_result.metrics else 0,
    }
