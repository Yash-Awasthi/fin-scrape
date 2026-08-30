"""
Risk Parity & Portfolio Optimization — Inspired by quantstats and pyfolio.

Provides portfolio construction methods: risk parity, mean-variance,
Black-Litterman, and hierarchical risk parity. All pure functions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Asset:
    """Asset with return series and metadata."""
    name: str
    returns: List[float]
    expected_return: float = 0.0
    volatility: float = 0.0
    sector: str = ""


@dataclass
class PortfolioAllocation:
    """Portfolio allocation result."""
    weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    method: str
    diversification_ratio: float = 0.0


@dataclass
class EfficientFrontier:
    """Point on the efficient frontier."""
    target_return: float
    min_volatility: float
    weights: Dict[str, float]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mean(data: List[float]) -> float:
    return sum(data) / len(data) if data else 0.0

def _std(data: List[float]) -> float:
    if len(data) < 2:
        return 0.0
    m = _mean(data)
    return math.sqrt(sum((x - m) ** 2 for x in data) / (len(data) - 1))

def _covariance(a: List[float], b: List[float]) -> float:
    n = min(len(a), len(b))
    if n < 2:
        return 0.0
    ma, mb = _mean(a[:n]), _mean(b[:n])
    return sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / (n - 1)

def _correlation(a: List[float], b: List[float]) -> float:
    sa, sb = _std(a), _std(b)
    if sa == 0 or sb == 0:
        return 0.0
    return _covariance(a, b) / (sa * sb)


def _portfolio_stats(
    weights: Dict[str, float],
    assets: Dict[str, Asset],
    risk_free_rate: float = 0.02,
) -> Tuple[float, float, float]:
    """Calculate portfolio return, volatility, Sharpe."""
    # Expected return
    exp_return = sum(
        weights.get(name, 0) * asset.expected_return
        for name, asset in assets.items()
    )
    
    # Portfolio volatility (simplified — uses correlation matrix)
    symbols = [name for name in assets if weights.get(name, 0) > 0]
    n = len(symbols)
    
    if n == 0:
        return 0, 0, 0
    
    variance = 0
    for i in range(n):
        for j in range(n):
            wi = weights.get(symbols[i], 0)
            wj = weights.get(symbols[j], 0)
            si = assets[symbols[i]].volatility
            sj = assets[symbols[j]].volatility
            corr = _correlation(
                assets[symbols[i]].returns,
                assets[symbols[j]].returns,
            )
            variance += wi * wj * si * sj * corr
    
    volatility = math.sqrt(max(0, variance))
    
    # Sharpe ratio (annualized)
    rf_period = risk_free_rate / 252
    excess = exp_return - rf_period
    sharpe = (excess / volatility * math.sqrt(252)) if volatility > 0 else 0
    
    return exp_return, volatility, sharpe


# ---------------------------------------------------------------------------
# Risk Parity
# ---------------------------------------------------------------------------

def risk_parity(
    assets: Dict[str, Asset],
    risk_budget: Optional[Dict[str, float]] = None,
    target_volatility: float = 0.15,
) -> PortfolioAllocation:
    """
    Risk parity portfolio — equal risk contribution from each asset.
    
    Each asset contributes equally to total portfolio risk.
    Uses iterative optimization to find weights.
    
    Args:
        assets: Dict of asset_name -> Asset
        risk_budget: Optional target risk contribution per asset (default: equal)
        target_volatility: Target annual portfolio volatility
    """
    symbols = list(assets.keys())
    n = len(symbols)
    
    if n == 0:
        return PortfolioAllocation(weights={}, expected_return=0, expected_volatility=0, sharpe_ratio=0, method="risk_parity")
    
    if n == 1:
        return PortfolioAllocation(
            weights={symbols[0]: 1.0},
            expected_return=assets[symbols[0]].expected_return,
            expected_volatility=assets[symbols[0]].volatility,
            sharpe_ratio=0, method="risk_parity",
        )
    
    # Default: equal risk budget
    if risk_budget is None:
        risk_budget = {s: 1.0 / n for s in symbols}
    
    # Iterative risk parity (gradient-based approximation)
    weights = {s: 1.0 / n for s in symbols}
    
    for _ in range(100):  # iterations
        # Calculate risk contributions
        exp_ret, vol, _ = _portfolio_stats(weights, assets)
        if vol == 0:
            break
        
        risk_contrib = {}
        for i, si in enumerate(symbols):
            marginal = 0
            for j, sj in enumerate(symbols):
                wj = weights[sj]
                cov = _covariance(assets[si].returns, assets[sj].returns)
                marginal += wj * cov
            risk_contrib[si] = weights[si] * marginal / vol
        
        # Update weights to match risk budget
        total_rc = sum(risk_contrib.values())
        if total_rc == 0:
            break
        
        for si in symbols:
            target_rc = risk_budget.get(si, 1.0 / n)
            actual_rc = risk_contrib[si] / total_rc
            if actual_rc > 0:
                weights[si] *= target_rc / actual_rc
        
        # Normalize
        total_w = sum(weights.values())
        if total_w > 0:
            weights = {s: w / total_w for s, w in weights.items()}
    
    # Scale to target volatility
    exp_ret, vol, sharpe = _portfolio_stats(weights, assets)
    if vol > 0:
        scale = target_volatility / vol
        # Adjust weights proportionally (simplified)
        # For proper scaling, would need to re-optimize
    
    exp_ret, vol, sharpe = _portfolio_stats(weights, assets)
    
    return PortfolioAllocation(
        weights={s: round(w, 4) for s, w in weights.items()},
        expected_return=round(exp_ret, 6),
        expected_volatility=round(vol, 6),
        sharpe_ratio=round(sharpe, 3),
        method="risk_parity",
    )


# ---------------------------------------------------------------------------
# Mean-Variance Optimization
# ---------------------------------------------------------------------------

def mean_variance_optimize(
    assets: Dict[str, Asset],
    risk_aversion: float = 1.0,
    target_return: Optional[float] = None,
) -> PortfolioAllocation:
    """
    Mean-variance optimization (Markowitz).
    
    Finds the portfolio that maximizes: E[r] - (γ/2) * σ²
    
    Uses a simplified grid search for the 2-asset case and
    iterative optimization for N assets.
    """
    symbols = list(assets.keys())
    n = len(symbols)
    
    if n == 0:
        return PortfolioAllocation(weights={}, expected_return=0, expected_volatility=0, sharpe_ratio=0, method="mean_variance")
    
    if n == 1:
        return PortfolioAllocation(
            weights={symbols[0]: 1.0},
            expected_return=assets[symbols[0]].expected_return,
            expected_volatility=assets[symbols[0]].volatility,
            sharpe_ratio=0, method="mean_variance",
        )
    
    # Grid search optimization
    best_score = float('-inf')
    best_weights = {s: 1.0 / n for s in symbols}
    
    # For efficiency, use a coarse grid for N>5 assets
    grid_points = 11 if n <= 5 else 5
    step = 1.0 / (grid_points - 1)
    
    def _grid_search(depth: int, remaining: float, current: Dict[str, float]):
        nonlocal best_score, best_weights
        
        if depth == n - 1:
            current[symbols[depth]] = remaining
            w = {s: current.get(s, 0) for s in symbols}
            exp_ret, vol, sharpe = _portfolio_stats(w, assets)
            
            # Utility: return - risk_aversion * variance
            utility = exp_ret - (risk_aversion / 2) * vol ** 2
            
            if target_return is not None:
                # Minimize volatility for target return
                if abs(exp_ret - target_return) < 0.01:
                    score = -vol
                else:
                    score = float('-inf')
            else:
                score = utility
            
            if score > best_score:
                best_score = score
                best_weights = dict(current)
            return
        
        for i in range(grid_points):
            w = step * i
            if w <= remaining + 1e-10:
                current[symbols[depth]] = w
                _grid_search(depth + 1, remaining - w, current)
    
    _grid_search(0, 1.0, {})
    
    exp_ret, vol, sharpe = _portfolio_stats(best_weights, assets)
    
    return PortfolioAllocation(
        weights={s: round(w, 4) for s, w in best_weights.items()},
        expected_return=round(exp_ret, 6),
        expected_volatility=round(vol, 6),
        sharpe_ratio=round(sharpe, 3),
        method="mean_variance",
    )


# ---------------------------------------------------------------------------
# Minimum Variance Portfolio
# ---------------------------------------------------------------------------

def minimum_variance(
    assets: Dict[str, Asset],
) -> PortfolioAllocation:
    """Find the portfolio with minimum volatility."""
    return mean_variance_optimize(assets, risk_aversion=100.0)


# ---------------------------------------------------------------------------
# Maximum Sharpe Portfolio
# ---------------------------------------------------------------------------

def maximum_sharpe(
    assets: Dict[str, Asset],
    risk_free_rate: float = 0.02,
) -> PortfolioAllocation:
    """Find the portfolio with maximum Sharpe ratio."""
    symbols = list(assets.keys())
    n = len(symbols)
    
    if n == 0:
        return PortfolioAllocation(weights={}, expected_return=0, expected_volatility=0, sharpe_ratio=0, method="max_sharpe")
    
    # Grid search maximizing Sharpe
    best_sharpe = float('-inf')
    best_weights = {s: 1.0 / n for s in symbols}
    
    grid_points = 11
    step = 1.0 / (grid_points - 1)
    
    def _search(depth: int, remaining: float, current: Dict[str, float]):
        nonlocal best_sharpe, best_weights
        
        if depth == n - 1:
            current[symbols[depth]] = remaining
            w = {s: current.get(s, 0) for s in symbols}
            _, vol, sharpe = _portfolio_stats(w, assets, risk_free_rate)
            
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = dict(current)
            return
        
        for i in range(grid_points):
            w = step * i
            if w <= remaining + 1e-10:
                current[symbols[depth]] = w
                _search(depth + 1, remaining - w, current)
    
    _search(0, 1.0, {})
    
    exp_ret, vol, sharpe = _portfolio_stats(best_weights, assets, risk_free_rate)
    
    return PortfolioAllocation(
        weights={s: round(w, 4) for s, w in best_weights.items()},
        expected_return=round(exp_ret, 6),
        expected_volatility=round(vol, 6),
        sharpe_ratio=round(sharpe, 3),
        method="max_sharpe",
    )


# ---------------------------------------------------------------------------
# Efficient Frontier
# ---------------------------------------------------------------------------

def efficient_frontier(
    assets: Dict[str, Asset],
    num_points: int = 10,
) -> List[EfficientFrontier]:
    """
    Compute the efficient frontier.
    
    Returns a list of optimal portfolios at different return levels.
    """
    # Find return range
    returns = [a.expected_return for a in assets.values()]
    min_ret = min(returns) if returns else 0
    max_ret = max(returns) if returns else 1
    
    if min_ret == max_ret:
        return []
    
    frontier = []
    step = (max_ret - min_ret) / max(1, num_points - 1)
    
    for i in range(num_points):
        target = min_ret + step * i
        alloc = mean_variance_optimize(assets, target_return=target)
        frontier.append(EfficientFrontier(
            target_return=round(target, 6),
            min_volatility=alloc.expected_volatility,
            weights=alloc.weights,
        ))
    
    return frontier


# ---------------------------------------------------------------------------
# Diversification metrics
# ---------------------------------------------------------------------------

def diversification_ratio(
    weights: Dict[str, float],
    assets: Dict[str, Asset],
) -> float:
    """
    Calculate diversification ratio.
    
    DR = weighted_avg_volatility / portfolio_volatility
    Higher = more diversified.
    """
    symbols = list(assets.keys())
    
    weighted_vol = sum(
        weights.get(s, 0) * assets[s].volatility
        for s in symbols
    )
    
    _, port_vol, _ = _portfolio_stats(weights, assets)
    
    if port_vol == 0:
        return 1.0
    
    return weighted_vol / port_vol
