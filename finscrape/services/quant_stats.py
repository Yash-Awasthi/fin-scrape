"""
Quant Stats — Extracted from QuantStats patterns.

Portfolio analytics with:
- Return metrics
- Risk ratios
- Drawdown analysis
- Benchmark comparison
"""
from __future__ import annotations

import math
from typing import List, Optional


def cagr(returns: List[float], periods: int = 252) -> float:
    """Compound Annual Growth Rate."""
    if len(returns) < 2:
        return 0.0
    total = 1.0
    for r in returns:
        total *= (1 + r)
    years = len(returns) / periods
    if years <= 0 or total <= 0:
        return 0.0
    return total ** (1 / years) - 1


def sharpe_ratio(returns: List[float], risk_free: float = 0.0, periods: int = 252) -> float:
    """Annualized Sharpe ratio."""
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(var) if var > 0 else 0
    if std < 1e-10:
        return 0.0
    return (mean - risk_free) / std * math.sqrt(periods)


def sortino_ratio(returns: List[float], risk_free: float = 0.0, periods: int = 252) -> float:
    """Sortino ratio (downside deviation only)."""
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    downside = [min(r - risk_free, 0) ** 2 for r in returns]
    downside_dev = math.sqrt(sum(downside) / len(downside)) if downside else 0
    if downside_dev < 1e-10:
        return 0.0
    return (mean - risk_free) / downside_dev * math.sqrt(periods)


def calmar_ratio(returns: List[float], periods: int = 252) -> float:
    """Calmar ratio (return / max drawdown)."""
    if len(returns) < 2:
        return 0.0
    total_cagr = cagr(returns, periods)
    max_dd = max_drawdown(returns)
    if max_dd < 1e-10:
        return 0.0
    return total_cagr / max_dd


def max_drawdown(returns: List[float]) -> float:
    """Maximum drawdown from returns."""
    if not returns:
        return 0.0
    cumulative = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cumulative *= (1 + r)
        if cumulative > peak:
            peak = cumulative
        dd = (peak - cumulative) / peak
        max_dd = max(max_dd, dd)
    return max_dd


def max_drawdown_duration(returns: List[float]) -> int:
    """Duration of maximum drawdown in periods."""
    if not returns:
        return 0
    cumulative = 1.0
    peak = 1.0
    current_duration = 0
    max_duration = 0
    for r in returns:
        cumulative *= (1 + r)
        if cumulative >= peak:
            peak = cumulative
            current_duration = 0
        else:
            current_duration += 1
            max_duration = max(max_duration, current_duration)
    return max_duration


def volatility(returns: List[float], periods: int = 252) -> float:
    """Annualized volatility."""
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(var * periods) if var > 0 else 0.0


def downside_deviation(returns: List[float], risk_free: float = 0.0, periods: int = 252) -> float:
    """Annualized downside deviation."""
    if len(returns) < 2:
        return 0.0
    downside = [min(r - risk_free, 0) ** 2 for r in returns]
    var = sum(downside) / len(returns)
    return math.sqrt(var * periods) if var > 0 else 0.0


def win_rate(returns: List[float]) -> float:
    """Percentage of positive return periods."""
    if not returns:
        return 0.0
    wins = sum(1 for r in returns if r > 0)
    return wins / len(returns)


def profit_factor(returns: List[float]) -> float:
    """Gross profit / gross loss."""
    gross_profit = sum(r for r in returns if r > 0)
    gross_loss = abs(sum(r for r in returns if r < 0))
    if gross_loss < 1e-10:
        return float('inf') if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def alpha_beta(returns: List[float], benchmark: List[float], periods: int = 252) -> tuple:
    """Jensen's alpha and beta."""
    if len(returns) < 2 or len(benchmark) < 2:
        return 0.0, 0.0
    n = min(len(returns), len(benchmark))
    r = returns[:n]
    b = benchmark[:n]
    mean_r = sum(r) / n
    mean_b = sum(b) / n
    cov = sum((ri - mean_r) * (bi - mean_b) for ri, bi in zip(r, b)) / n
    var_b = sum((bi - mean_b) ** 2 for bi in b) / n
    beta = cov / var_b if var_b > 1e-10 else 0.0
    alpha = (mean_r - mean_b * beta) * periods
    return alpha, beta


def information_ratio(returns: List[float], benchmark: List[float], periods: int = 252) -> float:
    """Information ratio."""
    if len(returns) < 2 or len(benchmark) < 2:
        return 0.0
    n = min(len(returns), len(benchmark))
    active = [returns[i] - benchmark[i] for i in range(n)]
    mean_active = sum(active) / n
    te = math.sqrt(sum((a - mean_active) ** 2 for a in active) / n)
    if te < 1e-10:
        return 0.0
    return mean_active / te * math.sqrt(periods)


def tail_ratio(returns: List[float]) -> float:
    """Ratio of 95th percentile to 5th percentile returns."""
    if len(returns) < 20:
        return 1.0
    sorted_returns = sorted(returns)
    p95 = sorted_returns[int(0.95 * len(sorted_returns))]
    p5 = sorted_returns[int(0.05 * len(sorted_returns))]
    if abs(p5) < 1e-10:
        return float('inf') if p95 > 0 else 0.0
    return abs(p95 / p5)


def var(returns: List[float], confidence: float = 0.95) -> float:
    """Value at Risk."""
    if not returns:
        return 0.0
    sorted_returns = sorted(returns)
    idx = int((1 - confidence) * len(sorted_returns))
    return sorted_returns[max(0, idx)]


def cvar(returns: List[float], confidence: float = 0.95) -> float:
    """Conditional Value at Risk (Expected Shortfall)."""
    if not returns:
        return 0.0
    threshold = var(returns, confidence)
    tail = [r for r in returns if r <= threshold]
    return sum(tail) / len(tail) if tail else 0.0


def pct_rank(prices: List[float], window: int = 60) -> List[float]:
    """Percentile rank over rolling window."""
    ranks = []
    for i in range(len(prices)):
        start = max(0, i - window + 1)
        window_prices = prices[start:i + 1]
        current = prices[i]
        rank = sum(1 for p in window_prices if p <= current) / len(window_prices) * 100
        ranks.append(rank)
    return ranks
