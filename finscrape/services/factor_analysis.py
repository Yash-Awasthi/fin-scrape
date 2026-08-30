"""Factor Analysis Service.

Extracted from alphalens (inspiration).
Calculates information coefficient, factor returns, turnover metrics,
and factor weighting for quantitative analysis.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FactorData:
    """Factor data point."""
    timestamp: float
    asset: str
    factor_value: float
    forward_return: float
    group: str = "default"


@dataclass
class ICResult:
    """Information Coefficient result."""
    mean_ic: float
    std_ic: float
    ic_series: list[float]
    ic_ir: float  # Information Ratio (mean/std)
    positive_pct: float  # % of periods with positive IC


@dataclass
class FactorReturnResult:
    """Factor return analysis result."""
    long_short_return: float
    long_return: float
    short_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    turnover: float


# --- Information Coefficient ---

def rank_correlation(x: list[float], y: list[float]) -> float:
    """Calculate Spearman rank correlation between two lists.

    Args:
        x: First list
        y: Second list

    Returns:
        Spearman rank correlation (-1 to 1)
    """
    n = len(x)
    if n < 2:
        return 0.0

    # Rank the data
    def rank(values):
        sorted_vals = sorted(enumerate(values), key=lambda pair: pair[1])
        ranks = [0.0] * len(values)
        for rank_idx, (orig_idx, _) in enumerate(sorted_vals):
            ranks[orig_idx] = rank_idx + 1
        return ranks

    rx = rank(x)
    ry = rank(y)

    # Calculate Spearman correlation
    d_sq_sum = sum((rx[i] - ry[i]) ** 2 for i in range(n))
    return 1.0 - (6.0 * d_sq_sum) / (n * (n * n - 1))


def calculate_ic(factor_data: list[FactorData]) -> ICResult:
    """Calculate Information Coefficient for factor data.

    IC = Spearman rank correlation between factor values and forward returns.

    Args:
        factor_data: List of factor data points

    Returns:
        IC analysis result
    """
    if not factor_data:
        return ICResult(0.0, 0.0, [], 0.0, 0.0)

    # Group by timestamp
    timestamps = sorted(set(d.timestamp for d in factor_data))
    ic_series = []

    for ts in timestamps:
        period_data = [d for d in factor_data if d.timestamp == ts]
        if len(period_data) < 2:
            continue

        factors = [d.factor_value for d in period_data]
        returns = [d.forward_return for d in period_data]

        ic = rank_correlation(factors, returns)
        ic_series.append(ic)

    if not ic_series:
        return ICResult(0.0, 0.0, [], 0.0, 0.0)

    mean_ic = sum(ic_series) / len(ic_series)
    variance = sum((ic - mean_ic) ** 2 for ic in ic_series) / len(ic_series)
    std_ic = math.sqrt(variance)
    ic_ir = mean_ic / std_ic if std_ic > 0 else 0.0
    positive_pct = sum(1 for ic in ic_series if ic > 0) / len(ic_series)

    return ICResult(
        mean_ic=round(mean_ic, 4),
        std_ic=round(std_ic, 4),
        ic_series=ic_series,
        ic_ir=round(ic_ir, 4),
        positive_pct=round(positive_pct, 4),
    )


# --- Factor Returns ---

def calculate_factor_returns(
    factor_data: list[FactorData],
    num_quantiles: int = 5,
) -> FactorReturnResult:
    """Calculate factor-weighted portfolio returns.

    Args:
        factor_data: List of factor data points
        num_quantiles: Number of quantile buckets

    Returns:
        Factor return analysis
    """
    if not factor_data:
        return FactorReturnResult(0, 0, 0, 0, 0, 0, 0)

    # Group by timestamp
    timestamps = sorted(set(d.timestamp for d in factor_data))
    period_returns = []

    for ts in timestamps:
        period_data = sorted(
            [d for d in factor_data if d.timestamp == ts],
            key=lambda d: d.factor_value,
        )
        if len(period_data) < num_quantiles:
            continue

        # Split into quantiles
        q_size = len(period_data) // num_quantiles
        long_quantile = period_data[-q_size:]  # Top quantile
        short_quantile = period_data[:q_size]  # Bottom quantile

        long_return = sum(d.forward_return for d in long_quantile) / len(long_quantile)
        short_return = sum(d.forward_return for d in short_quantile) / len(short_quantile)
        ls_return = long_return - short_return

        period_returns.append(ls_return)

    if not period_returns:
        return FactorReturnResult(0, 0, 0, 0, 0, 0, 0)

    avg_return = sum(period_returns) / len(period_returns)
    annualized = avg_return * 252

    # Sharpe ratio
    variance = sum((r - avg_return) ** 2 for r in period_returns) / len(period_returns)
    std = math.sqrt(variance)
    sharpe = (annualized / (std * math.sqrt(252))) if std > 0 else 0.0

    # Max drawdown
    cumulative = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in period_returns:
        cumulative *= (1 + r)
        peak = max(peak, cumulative)
        dd = (peak - cumulative) / peak
        max_dd = max(max_dd, dd)

    # Turnover (average factor change)
    turnover = 0.0
    if len(timestamps) > 1:
        for i in range(1, len(timestamps)):
            prev_data = sorted(
                [d for d in factor_data if d.timestamp == timestamps[i - 1]],
                key=lambda d: d.factor_value,
            )
            curr_data = sorted(
                [d for d in factor_data if d.timestamp == timestamps[i]],
                key=lambda d: d.factor_value,
            )
            if prev_data and curr_data:
                q = min(len(prev_data), len(curr_data)) // num_quantiles or 1
                prev_top = set(d.asset for d in prev_data[-q:])
                curr_top = set(d.asset for d in curr_data[-q:])
                if prev_top:
                    turnover += len(prev_top - curr_top) / len(prev_top)
        turnover /= max(1, len(timestamps) - 1)

    return FactorReturnResult(
        long_short_return=round(avg_return, 6),
        long_return=round(sum(d.forward_return for d in factor_data if d.factor_value > 0) / max(1, sum(1 for d in factor_data if d.factor_value > 0)), 6),
        short_return=round(sum(d.forward_return for d in factor_data if d.factor_value < 0) / max(1, sum(1 for d in factor_data if d.factor_value < 0)), 6),
        annualized_return=round(annualized, 4),
        sharpe_ratio=round(sharpe, 4),
        max_drawdown=round(max_dd, 4),
        turnover=round(turnover, 4),
    )


# --- Factor Weights ---

def calculate_factor_weights(
    factor_data: list[FactorData],
    demeaned: bool = True,
) -> dict[str, float]:
    """Calculate factor-weighted portfolio weights.

    Args:
        factor_data: List of factor data points
        demeaned: Whether to demean factor values

    Returns:
        Dictionary of asset -> weight
    """
    if not factor_data:
        return {}

    # Get latest period
    latest_ts = max(d.timestamp for d in factor_data)
    latest = [d for d in factor_data if d.timestamp == latest_ts]

    # Demean if requested
    values = [d.factor_value for d in latest]
    if demeaned and values:
        mean_val = sum(values) / len(values)
        values = [v - mean_val for v in values]

    # Calculate weights (sum of absolute values = 1)
    total_abs = sum(abs(v) for v in values)
    if total_abs == 0:
        return {d.asset: 0.0 for d in latest}

    weights = {}
    for d, v in zip(latest, values):
        weights[d.asset] = round(v / total_abs, 6)

    return weights


# --- Factor Decay ---

def calculate_ic_decay(
    factor_data: list[FactorData],
    max_lag: int = 5,
) -> list[float]:
    """Calculate IC decay at different forward periods.

    Args:
        factor_data: List of factor data points
        max_lag: Maximum lag periods

    Returns:
        List of IC values at each lag
    """
    if not factor_data:
        return []

    # Group by asset
    assets = sorted(set(d.asset for d in factor_data))
    timestamps = sorted(set(d.timestamp for d in factor_data))

    decay = []
    for lag in range(1, max_lag + 1):
        ic_values = []
        for i, ts in enumerate(timestamps):
            if i + lag >= len(timestamps):
                continue

            future_ts = timestamps[i + lag]
            current = {d.asset: d.factor_value for d in factor_data if d.timestamp == ts}
            future = {d.asset: d.forward_return for d in factor_data if d.timestamp == future_ts}

            common = set(current.keys()) & set(future.keys())
            if len(common) < 2:
                continue

            factors = [current[a] for a in sorted(common)]
            returns = [future[a] for a in sorted(common)]

            ic = rank_correlation(factors, returns)
            ic_values.append(ic)

        if ic_values:
            decay.append(round(sum(ic_values) / len(ic_values), 4))
        else:
            decay.append(0.0)

    return decay
