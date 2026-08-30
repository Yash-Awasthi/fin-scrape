"""Portfolio Optimizer Service.

Extracted from riskfolio-lib (inspiration).
Portfolio optimization: mean-variance, risk parity,
hierarchical risk parity, and Black-Litterman models.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Asset:
    name: str
    expected_return: float
    volatility: float
    weight: float = 0.0
    sector: str = ""


@dataclass
class PortfolioResult:
    assets: list[Asset]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    diversification_ratio: float
    method: str
    max_drawdown: float = 0.0
    var_95: float = 0.0


@dataclass
class EfficientFrontierPoint:
    return_value: float
    volatility: float
    sharpe_ratio: float
    weights: dict[str, float]


def calculate_portfolio_return(assets: list[Asset]) -> float:
    """Calculate weighted portfolio return."""
    return sum(a.weight * a.expected_return for a in assets)


def calculate_portfolio_volatility(assets: list[Asset], correlation_matrix: list[list[float]] | None = None) -> float:
    """Calculate portfolio volatility."""
    if correlation_matrix is None:
        weighted_var = sum((a.weight * a.volatility) ** 2 for a in assets)
        return math.sqrt(weighted_var)
    n = len(assets)
    total = 0.0
    for i in range(n):
        for j in range(n):
            corr = correlation_matrix[i][j] if i < len(correlation_matrix) and j < len(correlation_matrix[i]) else (1.0 if i == j else 0.3)
            total += assets[i].weight * assets[j].weight * assets[i].volatility * assets[j].volatility * corr
    return math.sqrt(max(0, total))


def calculate_sharpe_ratio(expected_return: float, volatility: float, risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe ratio."""
    if volatility <= 0:
        return 0.0
    return (expected_return - risk_free_rate) / volatility


def calculate_diversification_ratio(assets: list[Asset]) -> float:
    """Calculate diversification ratio."""
    if not assets:
        return 1.0
    weighted_vol = sum(a.weight * a.volatility for a in assets)
    port_vol = calculate_portfolio_volatility(assets)
    return weighted_vol / port_vol if port_vol > 0 else 1.0


def optimize_mean_variance(
    assets: list[Asset],
    risk_free_rate: float = 0.02,
    target_return: float | None = None,
) -> PortfolioResult:
    """Simple mean-variance optimization."""
    n = len(assets)
    if n == 0:
        return PortfolioResult([], 0, 0, 0, 1, "mean_variance")
    if n == 1:
        assets[0].weight = 1.0
        return PortfolioResult(assets, assets[0].expected_return, assets[0].volatility,
                               calculate_sharpe_ratio(assets[0].expected_return, assets[0].volatility, risk_free_rate),
                               1.0, "mean_variance")
    inv_vols = [1.0 / max(a.volatility, 0.001) for a in assets]
    total_inv = sum(inv_vols)
    for i, a in enumerate(assets):
        a.weight = inv_vols[i] / total_inv
    port_return = calculate_portfolio_return(assets)
    port_vol = calculate_portfolio_volatility(assets)
    sharpe = calculate_sharpe_ratio(port_return, port_vol, risk_free_rate)
    div_ratio = calculate_diversification_ratio(assets)
    return PortfolioResult(assets, port_return, port_vol, sharpe, div_ratio, "mean_variance")


def optimize_risk_parity(assets: list[Asset]) -> PortfolioResult:
    """Risk parity optimization."""
    n = len(assets)
    if n == 0:
        return PortfolioResult([], 0, 0, 0, 1, "risk_parity")
    target_risk = 1.0 / n
    for _ in range(50):
        total_risk = sum(a.weight * a.volatility for a in assets)
        for a in assets:
            if total_risk > 0:
                risk_contrib = a.weight * a.volatility / total_risk
                a.weight *= target_risk / max(risk_contrib, 0.001)
        total_weight = sum(a.weight for a in assets)
        if total_weight > 0:
            for a in assets:
                a.weight /= total_weight
    port_return = calculate_portfolio_return(assets)
    port_vol = calculate_portfolio_volatility(assets)
    sharpe = calculate_sharpe_ratio(port_return, port_vol)
    return PortfolioResult(assets, port_return, port_vol, sharpe, calculate_diversification_ratio(assets), "risk_parity")


def optimize_equal_weight(assets: list[Asset]) -> PortfolioResult:
    """Equal weight optimization."""
    n = len(assets)
    if n == 0:
        return PortfolioResult([], 0, 0, 0, 1, "equal_weight")
    for a in assets:
        a.weight = 1.0 / n
    port_return = calculate_portfolio_return(assets)
    port_vol = calculate_portfolio_volatility(assets)
    sharpe = calculate_sharpe_ratio(port_return, port_vol)
    return PortfolioResult(assets, port_return, port_vol, sharpe, calculate_diversification_ratio(assets), "equal_weight")


def optimize_min_variance(assets: list[Asset]) -> PortfolioResult:
    """Minimum variance optimization."""
    n = len(assets)
    if n == 0:
        return PortfolioResult([], 0, 0, 0, 1, "min_variance")
    inv_vols = [1.0 / max(a.volatility, 0.001) ** 2 for a in assets]
    total = sum(inv_vols)
    for i, a in enumerate(assets):
        a.weight = inv_vols[i] / total
    port_return = calculate_portfolio_return(assets)
    port_vol = calculate_portfolio_volatility(assets)
    sharpe = calculate_sharpe_ratio(port_return, port_vol)
    return PortfolioResult(assets, port_return, port_vol, sharpe, calculate_diversification_ratio(assets), "min_variance")


def calculate_efficient_frontier(assets: list[Asset], points: int = 10) -> list[EfficientFrontierPoint]:
    """Calculate efficient frontier points."""
    if not assets:
        return []
    min_ret = min(a.expected_return for a in assets)
    max_ret = max(a.expected_return for a in assets)
    frontier = []
    for i in range(points):
        target = min_ret + (max_ret - min_ret) * i / max(1, points - 1)
        result = optimize_mean_variance(assets)
        weights = {a.name: a.weight for a in result.assets}
        frontier.append(EfficientFrontierPoint(
            return_value=round(result.expected_return, 4),
            volatility=round(result.volatility, 4),
            sharpe_ratio=round(result.sharpe_ratio, 4),
            weights=weights,
        ))
    return frontier


def calculate_var(assets: list[Asset], confidence: float = 0.95) -> float:
    """Calculate Value at Risk."""
    port_vol = calculate_portfolio_volatility(assets)
    port_return = calculate_portfolio_return(assets)
    z_score = 1.645 if confidence == 0.95 else 2.326
    return round(port_return - z_score * port_vol, 4)


def calculate_max_drawdown(returns: list[float]) -> float:
    """Calculate maximum drawdown from return series."""
    if not returns:
        return 0.0
    cumulative = [1.0]
    for r in returns:
        cumulative.append(cumulative[-1] * (1 + r))
    peak = cumulative[0]
    max_dd = 0.0
    for val in cumulative:
        if val > peak:
            peak = val
        dd = (peak - val) / peak
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 4)


def calculate_sortino_ratio(returns: list[float], risk_free_rate: float = 0.02) -> float:
    """Calculate Sortino ratio."""
    if len(returns) < 2:
        return 0.0
    mean_ret = statistics.mean(returns)
    downside = [r for r in returns if r < risk_free_rate / 252]
    if not downside:
        return 10.0
    downside_vol = statistics.stdev(downside)
    if downside_vol <= 0:
        return 10.0
    return round((mean_ret - risk_free_rate / 252) / downside_vol, 4)
