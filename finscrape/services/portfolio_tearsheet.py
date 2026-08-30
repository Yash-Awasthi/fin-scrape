"""Portfolio Tear Sheet Service.

Extracted from pyfolio (inspiration).
Performance analysis: returns analysis, risk metrics,
tear sheet generation, and benchmark comparison.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PerformanceMetrics:
    total_return: float
    annual_return: float
    annual_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    skewness: float
    kurtosis: float
    var_95: float
    cvar_95: float
    positive_days_pct: float
    avg_win: float
    avg_loss: float
    profit_factor: float


@dataclass
class DrawdownAnalysis:
    max_drawdown: float
    max_drawdown_duration_days: int
    avg_drawdown: float
    max_drawdown_start: int
    max_drawdown_end: int
    drawdown_series: list[float] = field(default_factory=list)


@dataclass
class TearSheet:
    performance: PerformanceMetrics
    drawdowns: DrawdownAnalysis
    monthly_returns: dict[str, float]
    rolling_sharpe: list[float]
    rolling_volatility: list[float]
    summary: str = ""


def calculate_returns(equity_curve: list[float]) -> list[float]:
    """Calculate returns from equity curve."""
    if len(equity_curve) < 2:
        return []
    return [(equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1] for i in range(1, len(equity_curve))]


def calculate_drawdowns(equity_curve: list[float]) -> DrawdownAnalysis:
    """Calculate drawdown analysis from equity curve."""
    if not equity_curve:
        return DrawdownAnalysis(0, 0, 0, 0, 0)
    peak = equity_curve[0]
    drawdowns = []
    max_dd = 0
    max_dd_start = 0
    max_dd_end = 0
    current_dd_start = 0
    for i, val in enumerate(equity_curve):
        if val > peak:
            peak = val
            current_dd_start = i
        dd = (peak - val) / peak
        drawdowns.append(dd)
        if dd > max_dd:
            max_dd = dd
            max_dd_start = current_dd_start
            max_dd_end = i
    avg_dd = statistics.mean(drawdowns) if drawdowns else 0
    return DrawdownAnalysis(
        max_drawdown=round(max_dd, 4),
        max_drawdown_duration_days=max_dd_end - max_dd_start,
        avg_drawdown=round(avg_dd, 4),
        max_drawdown_start=max_dd_start,
        max_drawdown_end=max_dd_end,
        drawdown_series=drawdowns,
    )


def calculate_performance_metrics(returns: list[float], risk_free_rate: float = 0.02) -> PerformanceMetrics:
    """Calculate comprehensive performance metrics."""
    if not returns:
        return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    total_return = 1.0
    for r in returns:
        total_return *= (1 + r)
    total_return -= 1
    n = len(returns)
    annual_return = (1 + total_return) ** (252 / max(n, 1)) - 1
    annual_vol = statistics.stdev(returns) * math.sqrt(252) if n > 1 else 0
    sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0
    downside = [r for r in returns if r < risk_free_rate / 252]
    downside_vol = statistics.stdev(downside) * math.sqrt(252) if len(downside) > 1 else 0
    sortino = (annual_return - risk_free_rate) / downside_vol if downside_vol > 0 else 0
    equity = [1.0]
    for r in returns:
        equity.append(equity[-1] * (1 + r))
    dd = calculate_drawdowns(equity)
    calmar = annual_return / dd.max_drawdown if dd.max_drawdown > 0 else 0
    mean_r = statistics.mean(returns)
    skew = sum((r - mean_r) ** 3 for r in returns) / (n * (statistics.stdev(returns) ** 3)) if n > 2 and statistics.stdev(returns) > 0 else 0
    kurt = sum((r - mean_r) ** 4 for r in returns) / (n * (statistics.stdev(returns) ** 4)) if n > 3 and statistics.stdev(returns) > 0 else 0
    sorted_rets = sorted(returns)
    var_idx = max(0, int(n * 0.05) - 1)
    var_95 = sorted_rets[var_idx]
    cvar_95 = statistics.mean(sorted_rets[:var_idx + 1]) if var_idx >= 0 else var_95
    positive = sum(1 for r in returns if r > 0)
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r < 0]
    avg_win = statistics.mean(wins) if wins else 0
    avg_loss = statistics.mean(losses) if losses else 0
    profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf')
    return PerformanceMetrics(
        total_return=round(total_return, 4), annual_return=round(annual_return, 4),
        annual_volatility=round(annual_vol, 4), sharpe_ratio=round(sharpe, 4),
        sortino_ratio=round(sortino, 4), max_drawdown=dd.max_drawdown,
        calmar_ratio=round(calmar, 4), skewness=round(skew, 4), kurtosis=round(kurt, 4),
        var_95=round(var_95, 4), cvar_95=round(cvar_95, 4),
        positive_days_pct=round(positive / n, 4) if n > 0 else 0,
        avg_win=round(avg_win, 4), avg_loss=round(avg_loss, 4),
        profit_factor=round(profit_factor, 4),
    )


def calculate_monthly_returns(returns: list[float]) -> dict[str, float]:
    """Calculate monthly returns."""
    monthly = {}
    for i, r in enumerate(returns):
        month = (i // 21) % 12
        key = f"Month_{month + 1}"
        monthly[key] = monthly.get(key, 0) + r
    return {k: round(v, 4) for k, v in monthly.items()}


def calculate_rolling_sharpe(returns: list[float], window: int = 63, risk_free_rate: float = 0.02) -> list[float]:
    """Calculate rolling Sharpe ratio."""
    if len(returns) < window:
        return []
    rolling = []
    for i in range(window, len(returns) + 1):
        window_rets = returns[i - window:i]
        mean_r = statistics.mean(window_rets)
        std_r = statistics.stdev(window_rets) if len(window_rets) > 1 else 0
        sharpe = (mean_r * 252 - risk_free_rate) / (std_r * math.sqrt(252)) if std_r > 0 else 0
        rolling.append(round(sharpe, 4))
    return rolling


def calculate_rolling_volatility(returns: list[float], window: int = 63) -> list[float]:
    """Calculate rolling volatility."""
    if len(returns) < window:
        return []
    rolling = []
    for i in range(window, len(returns) + 1):
        window_rets = returns[i - window:i]
        vol = statistics.stdev(window_rets) * math.sqrt(252) if len(window_rets) > 1 else 0
        rolling.append(round(vol, 4))
    return rolling


def generate_tear_sheet(equity_curve: list[float], risk_free_rate: float = 0.02) -> TearSheet:
    """Generate complete tear sheet from equity curve."""
    returns = calculate_returns(equity_curve)
    if not returns:
        empty_perf = PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        empty_dd = DrawdownAnalysis(0, 0, 0, 0, 0)
        return TearSheet(empty_perf, empty_dd, {}, [], [])
    performance = calculate_performance_metrics(returns, risk_free_rate)
    drawdowns = calculate_drawdowns(equity_curve)
    monthly = calculate_monthly_returns(returns)
    rolling_sharpe = calculate_rolling_sharpe(returns)
    rolling_vol = calculate_rolling_volatility(returns)
    summary = f"Total Return: {performance.total_return:.1%}, Sharpe: {performance.sharpe_ratio:.2f}, Max DD: {performance.max_drawdown:.1%}"
    return TearSheet(performance, drawdowns, monthly, rolling_sharpe, rolling_vol, summary)
