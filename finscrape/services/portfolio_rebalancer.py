"""
Portfolio Rebalancer — Extracted from qlib's SoftTopkStrategy.

Budget-constrained portfolio rebalancing with:
- Proportional budget allocation
- Trade impact limits
- Deterministic sell-first, then buy phase
- Cold start vs rebalancing paths
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Position:
    ticker: str
    weight: float  # 0.0 to 1.0


@dataclass
class RebalanceResult:
    target_weights: Dict[str, float]
    sells: Dict[str, float]
    buys: Dict[str, float]
    released_cash: float
    total_turnover: float


@dataclass
class PortfolioState:
    positions: Dict[str, float] = field(default_factory=dict)
    cash: float = 0.0

    @property
    def total_weight(self) -> float:
        return sum(self.positions.values())


def apply_impact_limit(weight: float, limit: Optional[float]) -> float:
    """Cap weight change by trade impact limit."""
    if limit is None:
        return weight
    return min(abs(weight), limit)


def compute_target_weights(
    scores: Dict[str, float],
    topk: int,
    risk_degree: float = 0.95,
    trade_impact_limit: Optional[float] = None,
) -> List[str]:
    """Select top-k tickers by score."""
    sorted_tickers = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)
    return sorted_tickers[:topk]


def rebalance_portfolio(
    scores: Dict[str, float],
    current: PortfolioState,
    topk: int,
    risk_degree: float = 0.95,
    trade_impact_limit: Optional[float] = None,
) -> RebalanceResult:
    """
    Generate target position using Proportional Budget Allocation.
    
    Mirrors qlib SoftTopkStrategy logic:
    1. Cold start: fill equally up to risk_degree / topk
    2. Rebalancing: sell excess first, then allocate proportionally
    """
    if topk <= 0:
        return RebalanceResult({}, {}, {}, 0.0, 0.0)

    ideal_per_stock = risk_degree / topk
    ideal_list = compute_target_weights(scores, topk, risk_degree, trade_impact_limit)
    cur_weights = dict(current.positions)
    initial_total_weight = current.total_weight

    # --- Cold Start ---
    if not cur_weights:
        fill = apply_impact_limit(ideal_per_stock, trade_impact_limit)
        target = {t: fill for t in ideal_list}
        buys = {t: fill for t in ideal_list}
        return RebalanceResult(target, {}, buys, 0.0, fill * len(ideal_list))

    # --- Rebalancing ---
    all_tickers = set(cur_weights.keys()) | set(ideal_list)
    next_weights = {t: cur_weights.get(t, 0.0) for t in all_tickers}
    sells: Dict[str, float] = {}

    # Phase 1: Deterministic Sell
    released_cash = 0.0
    for t in list(next_weights.keys()):
        cur = next_weights[t]
        if cur <= 1e-8:
            continue
        if t not in ideal_list:
            sell = apply_impact_limit(cur, trade_impact_limit)
            next_weights[t] -= sell
            sells[t] = sell
            released_cash += sell
        elif cur > ideal_per_stock + 1e-8:
            excess = cur - ideal_per_stock
            sell = apply_impact_limit(excess, trade_impact_limit)
            next_weights[t] -= sell
            sells[t] = sell
            released_cash += sell

    # Phase 2: Budget
    total_budget = released_cash + max(0.0, risk_degree - initial_total_weight)

    # Phase 3: Proportional Buy
    buys: Dict[str, float] = {}
    if total_budget > 1e-8:
        shortfalls = {
            t: max(0.0, ideal_per_stock - next_weights.get(t, 0.0))
            for t in ideal_list
            if next_weights.get(t, 0.0) < ideal_per_stock - 1e-8
        }
        total_shortfall = sum(shortfalls.values())
        if total_shortfall > 1e-8:
            for t, shortfall in shortfalls.items():
                alloc = (shortfall / total_shortfall) * total_budget
                alloc = apply_impact_limit(alloc, trade_impact_limit)
                alloc = min(alloc, ideal_per_stock - next_weights.get(t, 0.0))
                if alloc > 1e-8:
                    next_weights[t] = next_weights.get(t, 0.0) + alloc
                    buys[t] = alloc

    # Clean up near-zero positions
    target = {t: w for t, w in next_weights.items() if w > 1e-8}
    total_turnover = sum(sells.values()) + sum(buys.values())

    return RebalanceResult(target, sells, buys, released_cash, total_turnover)


def compute_sharpe_ratio(returns: List[float], risk_free: float = 0.0) -> float:
    """Annualized Sharpe ratio from daily returns."""
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    var = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std = var ** 0.5
    if std < 1e-10:
        return 0.0
    return (mean_r - risk_free) / std * (252 ** 0.5)


def compute_max_drawdown(equity_curve: List[float]) -> float:
    """Maximum drawdown from equity curve."""
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def compute_information_ratio(
    portfolio_returns: List[float],
    benchmark_returns: List[float],
) -> float:
    """Information ratio vs benchmark."""
    if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
        return 0.0
    active = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
    mean_active = sum(active) / len(active)
    var = sum((a - mean_active) ** 2 for a in active) / (len(active) - 1)
    te = var ** 0.5
    if te < 1e-10:
        return 0.0
    return mean_active / te * (252 ** 0.5)


def portfolio_attribution(
    weights: Dict[str, float],
    returns: Dict[str, float],
) -> Dict[str, float]:
    """Per-position contribution to portfolio return."""
    total = sum(weights.get(t, 0.0) * returns.get(t, 0.0) for t in set(weights) | set(returns))
    return {t: weights.get(t, 0.0) * returns.get(t, 0.0) / total if total > 0 else 0.0
            for t in set(weights) | set(returns)}
