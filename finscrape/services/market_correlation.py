"""Market Correlation Service.

Extracted from anteroom-oracle (inspiration).
Calculates correlations between markets, lead-lag relationships,
and historical crash pattern detection.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CorrelationResult:
    """Correlation between two markets."""
    market_a: str
    market_b: str
    correlation: float
    lag_weeks: int = 0
    direction: str = "same"  # "same" or "opposite"


@dataclass
class LeadLagRelationship:
    """Lead-lag relationship between markets."""
    leader: str
    follower: str
    lag_weeks: int
    correlation: float
    direction: str  # "same" or "opposite"


@dataclass
class CrashPattern:
    """Historical crash pattern."""
    name: str
    start_date: str
    end_date: str
    conditions: dict = field(default_factory=dict)


# --- Known Crash Patterns ---

KNOWN_CRASHES = [
    CrashPattern("Great Depression 1929", "1928-01-01", "1933-01-01"),
    CrashPattern("Oil Crisis 1973", "1972-01-01", "1975-01-01"),
    CrashPattern("Black Monday 1987", "1987-06-01", "1988-06-01"),
    CrashPattern("Dot-com Crash 2000", "1999-01-01", "2002-12-01"),
    CrashPattern("Financial Crisis 2008", "2007-01-01", "2009-12-01"),
    CrashPattern("COVID Crash 2020", "2020-01-01", "2020-12-01"),
    CrashPattern("Crypto Crash 2022", "2021-11-01", "2022-12-01"),
]


# --- Core Calculations ---

def calculate_correlation(x: list[float], y: list[float]) -> float:
    """Calculate Pearson correlation coefficient between two series.

    Args:
        x: First series
        y: Second series

    Returns:
        Correlation coefficient (-1 to 1)
    """
    n = len(x)
    if n < 2 or n != len(y):
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if denom_x == 0 or denom_y == 0:
        return 0.0

    return numerator / (denom_x * denom_y)


def calculate_returns(prices: list[float], period: int = 1) -> list[float]:
    """Calculate percentage returns over a period.

    Args:
        prices: List of prices
        period: Return period

    Returns:
        List of returns
    """
    if len(prices) < period + 1:
        return []

    returns = []
    for i in range(period, len(prices)):
        if prices[i - period] != 0:
            returns.append((prices[i] - prices[i - period]) / prices[i - period])
        else:
            returns.append(0.0)

    return returns


def calculate_rolling_correlation(
    x: list[float],
    y: list[float],
    window: int = 20,
) -> list[float]:
    """Calculate rolling correlation between two series.

    Args:
        x: First series
        y: Second series
        window: Rolling window size

    Returns:
        List of rolling correlation values
    """
    if len(x) < window or len(y) < window:
        return []

    returns_x = calculate_returns(x)
    returns_y = calculate_returns(y)

    if len(returns_x) < window or len(returns_y) < window:
        return []

    rolling = []
    for i in range(window, len(returns_x)):
        window_x = returns_x[i - window:i]
        window_y = returns_y[i - window:i]
        corr = calculate_correlation(window_x, window_y)
        rolling.append(corr)

    return rolling


# --- Correlation Matrix ---

def calculate_correlation_matrix(
    market_data: dict[str, list[float]],
) -> dict[str, dict[str, float]]:
    """Calculate correlation matrix for multiple markets.

    Args:
        market_data: Dictionary of market name -> price series

    Returns:
        Correlation matrix
    """
    markets = list(market_data.keys())
    matrix = {}

    for m1 in markets:
        matrix[m1] = {}
        returns1 = calculate_returns(market_data[m1])
        for m2 in markets:
            returns2 = calculate_returns(market_data[m2])
            corr = calculate_correlation(returns1, returns2)
            matrix[m1][m2] = round(corr, 4)

    return matrix


def find_strongest_correlations(
    market_data: dict[str, list[float]],
    min_correlation: float = 0.5,
    top_n: int = 10,
) -> list[CorrelationResult]:
    """Find strongest correlations between market pairs.

    Args:
        market_data: Dictionary of market name -> price series
        min_correlation: Minimum absolute correlation
        top_n: Number of results to return

    Returns:
        List of correlation results sorted by strength
    """
    correlations = []
    markets = list(market_data.keys())

    for i, m1 in enumerate(markets):
        returns1 = calculate_returns(market_data[m1])
        for m2 in markets[i + 1:]:
            returns2 = calculate_returns(market_data[m2])
            corr = calculate_correlation(returns1, returns2)

            if abs(corr) >= min_correlation:
                correlations.append(CorrelationResult(
                    market_a=m1,
                    market_b=m2,
                    correlation=round(corr, 4),
                    direction="same" if corr > 0 else "opposite",
                ))

    correlations.sort(key=lambda c: abs(c.correlation), reverse=True)
    return correlations[:top_n]


# --- Lead-Lag Analysis ---

def find_lead_lag_relationships(
    market_data: dict[str, list[float]],
    max_lag_weeks: int = 12,
    min_correlation: float = 0.4,
    top_n: int = 20,
) -> list[LeadLagRelationship]:
    """Find lead-lag relationships between markets.

    Args:
        market_data: Dictionary of market name -> price series
        max_lag_weeks: Maximum lag to test
        min_correlation: Minimum absolute correlation
        top_n: Number of results to return

    Returns:
        List of lead-lag relationships
    """
    relationships = []
    markets = list(market_data.keys())

    for leader in markets:
        returns_leader = calculate_returns(market_data[leader])
        for follower in markets:
            if leader == follower:
                continue

            returns_follower = calculate_returns(market_data[follower])

            best_corr = 0.0
            best_lag = 0

            for lag in range(1, max_lag_weeks + 1):
                if lag >= len(returns_follower):
                    break

                shifted = returns_follower[lag:]
                truncated_leader = returns_leader[:len(shifted)]

                corr = calculate_correlation(truncated_leader, shifted)

                if abs(corr) > abs(best_corr):
                    best_corr = corr
                    best_lag = lag

            if abs(best_corr) >= min_correlation:
                relationships.append(LeadLagRelationship(
                    leader=leader,
                    follower=follower,
                    lag_weeks=best_lag,
                    correlation=round(best_corr, 4),
                    direction="same" if best_corr > 0 else "opposite",
                ))

    relationships.sort(key=lambda r: abs(r.correlation), reverse=True)
    return relationships[:top_n]


# --- Crash Pattern Matching ---

def match_crash_pattern(
    current_conditions: dict[str, float],
    historical_patterns: list[dict[str, float]],
    threshold: float = 0.7,
) -> list[dict]:
    """Match current market conditions against historical crash patterns.

    Args:
        current_conditions: Current market metrics
        historical_patterns: Historical pattern data
        threshold: Minimum similarity score

    Returns:
        List of matching patterns with scores
    """
    matches = []

    for pattern in historical_patterns:
        # Calculate similarity (cosine similarity)
        common_keys = set(current_conditions.keys()) & set(pattern.keys())
        if not common_keys:
            continue

        dot_product = sum(current_conditions[k] * pattern[k] for k in common_keys)
        norm_current = math.sqrt(sum(current_conditions[k] ** 2 for k in common_keys))
        norm_pattern = math.sqrt(sum(pattern[k] ** 2 for k in common_keys))

        if norm_current == 0 or norm_pattern == 0:
            continue

        similarity = dot_product / (norm_current * norm_pattern)

        if similarity >= threshold:
            matches.append({
                "pattern_name": pattern.get("name", "unknown"),
                "similarity": round(similarity, 4),
                "matching_factors": list(common_keys),
            })

    matches.sort(key=lambda m: m["similarity"], reverse=True)
    return matches


def detect_anomaly(
    values: list[float],
    window: int = 20,
    std_threshold: float = 2.0,
) -> list[dict]:
    """Detect anomalies in a time series using z-score.

    Args:
        values: Time series values
        window: Rolling window size
        std_threshold: Standard deviation threshold

    Returns:
        List of anomaly points
    """
    if len(values) < window:
        return []

    anomalies = []
    for i in range(window, len(values)):
        window_data = values[i - window:i]
        mean = sum(window_data) / len(window_data)
        std = math.sqrt(sum((x - mean) ** 2 for x in window_data) / len(window_data))

        if std == 0:
            continue

        z_score = (values[i] - mean) / std
        if abs(z_score) > std_threshold:
            anomalies.append({
                "index": i,
                "value": values[i],
                "z_score": round(z_score, 4),
                "direction": "high" if z_score > 0 else "low",
            })

    return anomalies
