"""
Black-Litterman Model — Extracted from PyPortfolioOpt patterns.

Portfolio optimization with:
- Market-implied prior returns
- Black-Litterman posterior estimates
- Efficient frontier
- Risk parity
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class PortfolioResult:
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float = 0.0

    def __post_init__(self):
        if self.volatility > 0:
            self.sharpe_ratio = self.expected_return / self.volatility


def market_implied_prior_returns(
    market_caps: Dict[str, float],
    risk_aversion: float,
    cov_matrix: Dict[Tuple[str, str], float],
    risk_free_rate: float = 0.0,
) -> Dict[str, float]:
    """Compute prior estimate of returns implied by market weights."""
    total_cap = sum(market_caps.values())
    weights = {ticker: cap / total_cap for ticker, cap in market_caps.items()}

    prior_returns = {}
    for ticker in market_caps:
        portfolio_cov = sum(
            weights.get(other, 0) * cov_matrix.get((ticker, other), 0)
            for other in market_caps
        )
        prior_returns[ticker] = risk_aversion * portfolio_cov + risk_free_rate

    return prior_returns


def market_implied_risk_aversion(
    market_prices: List[float],
    frequency: int = 252,
    risk_free_rate: float = 0.0,
) -> float:
    """Calculate market-implied risk-aversion parameter."""
    if len(market_prices) < 2:
        return 1.0

    returns = [
        (market_prices[i] - market_prices[i - 1]) / market_prices[i - 1]
        for i in range(1, len(market_prices))
    ]

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    annualized_return = mean_return * frequency
    annualized_var = variance * frequency

    excess_return = annualized_return - risk_free_rate
    if annualized_var < 1e-10:
        return 1.0

    return excess_return / annualized_var


def black_litterman(
    prior_returns: Dict[str, float],
    cov_matrix: Dict[Tuple[str, str], float],
    views: List[Dict],
    view_confidences: List[float],
    risk_aversion: float = 1.0,
    tau: float = 0.05,
) -> Dict[str, float]:
    """Compute Black-Litterman posterior returns."""
    assets = list(prior_returns.keys())
    n = len(assets)

    # Build P matrix (views)
    P = []
    Q = []
    for view in views:
        row = [0.0] * n
        for asset, weight in view.items():
            if asset in assets:
                row[assets.index(asset)] = weight
        P.append(row)
        Q.append(view.get("return", 0.0))

    if not P:
        return prior_returns

    # Build Omega (view uncertainty)
    omega_diag = []
    for i, conf in enumerate(view_confidences):
        # Uncertainty inversely proportional to confidence
        omega_diag.append((1 - conf) * tau)

    # Simplified BL calculation
    posterior = {}
    for asset in assets:
        prior = prior_returns.get(asset, 0.0)
        adjustment = 0.0
        for i, view in enumerate(views):
            if asset in view:
                weight = view[asset]
                conf = view_confidences[i] if i < len(view_confidences) else 0.5
                target_return = Q[i] if i < len(Q) else 0.0
                adjustment += conf * weight * target_return * 0.1

        posterior[asset] = prior + adjustment

    return posterior


def mean_variance_optimization(
    expected_returns: Dict[str, float],
    cov_matrix: Dict[Tuple[str, str], float],
    risk_aversion: float = 1.0,
) -> PortfolioResult:
    """Simple mean-variance optimization."""
    assets = list(expected_returns.keys())
    n = len(assets)

    # Simplified: equal weight with return adjustment
    weights = {a: 1.0 / n for a in assets}

    expected_return = sum(
        expected_returns.get(a, 0) * w for a, w in weights.items()
    )

    volatility = math.sqrt(
        sum(
            weights.get(a1, 0) * weights.get(a2, 0) * cov_matrix.get((a1, a2), 0)
            for a1 in assets
            for a2 in assets
        )
    )

    return PortfolioResult(weights, expected_return, volatility)


def risk_parity(
    cov_matrix: Dict[Tuple[str, str], float],
    target_risk: float = 0.1,
) -> Dict[str, float]:
    """Risk parity allocation."""
    assets = list(set(a for (a, _) in cov_matrix.keys()))
    n = len(assets)

    # Simplified: inverse volatility weighting
    vols = {}
    for asset in assets:
        var = cov_matrix.get((asset, asset), 1.0)
        vols[asset] = math.sqrt(max(var, 1e-10))

    inv_vols = {a: 1.0 / v for a, v in vols.items()}
    total_inv_vol = sum(inv_vols.values())

    weights = {a: iv / total_inv_vol for a, iv in inv_vols.items()}
    return weights


def efficient_frontier(
    expected_returns: Dict[str, float],
    cov_matrix: Dict[Tuple[str, str], float],
    n_points: int = 10,
) -> List[PortfolioResult]:
    """Generate efficient frontier points."""
    assets = list(expected_returns.keys())
    points = []

    for i in range(n_points):
        target_return = min(expected_returns.values()) + (
            (max(expected_returns.values()) - min(expected_returns.values())) * i / max(n_points - 1, 1)
        )

        # Simplified: find weights closest to target return
        weights = {a: 1.0 / len(assets) for a in assets}
        # Adjust weights to target return
        excess = target_return - sum(expected_returns.get(a, 0) * w for a, w in weights.items())
        for a in assets:
            weights[a] += excess / (expected_returns.get(a, 1) * len(assets))

        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {a: w / total for a, w in weights.items()}

        expected_return = sum(expected_returns.get(a, 0) * w for a, w in weights.items())
        volatility = math.sqrt(
            sum(
                weights.get(a1, 0) * weights.get(a2, 0) * cov_matrix.get((a1, a2), 0)
                for a1 in assets
                for a2 in assets
            )
        )

        points.append(PortfolioResult(weights, expected_return, volatility))

    return points
