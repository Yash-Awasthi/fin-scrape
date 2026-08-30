"""
Quantitative Factor Engine — Extracted from Microsoft Qlib patterns.

Provides alpha factor calculation, risk modeling, and portfolio optimization
using pure functions. Inspired by Qlib's Alpha158/Alpha360 factor sets and
its supervised learning pipeline for quantitative investment.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class OHLCVBar:
    """Single OHLCV bar."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class FactorSet:
    """Computed alpha factors for a single instrument."""
    # Price-based factors
    returns_1d: float = 0.0
    returns_5d: float = 0.0
    returns_20d: float = 0.0
    log_volume: float = 0.0
    high_low_range: float = 0.0
    close_open_range: float = 0.0
    # Moving average factors
    ma5_ratio: float = 0.0
    ma10_ratio: float = 0.0
    ma20_ratio: float = 0.0
    ma60_ratio: float = 0.0
    # Momentum factors
    momentum_5d: float = 0.0
    momentum_20d: float = 0.0
    # Volatility factors
    volatility_5d: float = 0.0
    volatility_20d: float = 0.0
    # Volume factors
    volume_ratio_5d: float = 0.0
    volume_ratio_20d: float = 0.0
    # VWAP
    vwap_ratio: float = 0.0
    # RSI
    rsi_14: float = 50.0


@dataclass
class RiskModel:
    """Portfolio risk metrics."""
    variance: float = 0.0
    volatility: float = 0.0
    var_95: float = 0.0  # Value at Risk 95%
    cvar_95: float = 0.0  # Conditional VaR 95%
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    beta: float = 1.0
    alpha: float = 0.0
    information_ratio: float = 0.0


@dataclass
class PortfolioWeight:
    """Weight allocation for a single instrument."""
    instrument: str
    weight: float
    expected_return: float = 0.0
    risk_contribution: float = 0.0


@dataclass
class FactorCorrelation:
    """Correlation between two factors."""
    factor_a: str
    factor_b: str
    correlation: float


# ---------------------------------------------------------------------------
# Factor calculation (Alpha158-inspired)
# ---------------------------------------------------------------------------

def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    """Safe division avoiding ZeroDivisionError."""
    return a / b if b != 0 else default


def calculate_price_factors(bars: List[OHLCVBar]) -> Dict[str, float]:
    """
    Calculate price-based alpha factors from OHLCV bars.
    
    Inspired by Qlib's Alpha158 handler which computes 158 factors
    from daily OHLCV data.
    
    Args:
        bars: List of OHLCVBar in chronological order (oldest first)
    
    Returns:
        Dict of factor_name -> factor_value
    """
    if len(bars) < 2:
        return {}
    
    latest = bars[-1]
    factors = {}
    
    # 1-day return
    prev_close = bars[-2].close
    factors["returns_1d"] = _safe_div(latest.close - prev_close, prev_close)
    
    # N-day returns
    for n in [5, 20]:
        if len(bars) >= n + 1:
            ref_close = bars[-(n + 1)].close
            factors[f"returns_{n}d"] = _safe_div(latest.close - ref_close, ref_close)
    
    # Log volume
    factors["log_volume"] = math.log(latest.volume + 1)
    
    # Intraday ranges
    factors["high_low_range"] = _safe_div(latest.high - latest.low, latest.close)
    factors["close_open_range"] = _safe_div(latest.close - latest.open, latest.open)
    
    return factors


def calculate_moving_average_factors(bars: List[OHLCVBar]) -> Dict[str, float]:
    """
    Calculate moving average ratio factors.
    
    MA ratio = current_close / MA(N) - 1
    Values > 0 indicate price above MA (bullish), < 0 below (bearish).
    """
    if not bars:
        return {}
    
    closes = [b.close for b in bars]
    latest_close = closes[-1]
    factors = {}
    
    for period in [5, 10, 20, 60]:
        if len(closes) >= period:
            ma = sum(closes[-period:]) / period
            factors[f"ma{period}_ratio"] = _safe_div(latest_close - ma, ma)
    
    return factors


def calculate_momentum_factors(bars: List[OHLCVBar]) -> Dict[str, float]:
    """Calculate momentum factors (rate of change)."""
    if not bars:
        return {}
    
    closes = [b.close for b in bars]
    factors = {}
    
    for n in [5, 20]:
        if len(closes) > n:
            factors[f"momentum_{n}d"] = _safe_div(
                closes[-1] - closes[-n - 1], closes[-n - 1]
            )
    
    return factors


def calculate_volatility_factors(bars: List[OHLCVBar]) -> Dict[str, float]:
    """
    Calculate realized volatility factors.
    
    Volatility = std(daily_returns) * sqrt(252) for annualized.
    """
    if len(bars) < 3:
        return {}
    
    closes = [b.close for b in bars]
    returns = [
        _safe_div(closes[i] - closes[i - 1], closes[i - 1])
        for i in range(1, len(closes))
    ]
    
    factors = {}
    for n in [5, 20]:
        if len(returns) >= n:
            window = returns[-n:]
            mean = sum(window) / len(window)
            var = sum((r - mean) ** 2 for r in window) / len(window)
            factors[f"volatility_{n}d"] = math.sqrt(var) * math.sqrt(252)
    
    return factors


def calculate_volume_factors(bars: List[OHLCVBar]) -> Dict[str, float]:
    """Calculate volume relative factors."""
    if not bars:
        return {}
    
    volumes = [b.volume for b in bars]
    latest_vol = volumes[-1]
    factors = {}
    
    for n in [5, 20]:
        if len(volumes) >= n:
            avg_vol = sum(volumes[-n:]) / n
            factors[f"volume_ratio_{n}d"] = _safe_div(latest_vol, avg_vol)
    
    return factors


def calculate_vwap(bars: List[OHLCVBar]) -> float:
    """
    Calculate Volume Weighted Average Price.
    
    VWAP = sum(typical_price * volume) / sum(volume)
    typical_price = (high + low + close) / 3
    """
    if not bars:
        return 0.0
    
    total_pv = sum(
        ((b.high + b.low + b.close) / 3) * b.volume for b in bars
    )
    total_vol = sum(b.volume for b in bars)
    
    return _safe_div(total_pv, total_vol)


def calculate_rsi(bars: List[OHLCVBar], period: int = 14) -> float:
    """
    Calculate Relative Strength Index.
    
    RSI = 100 - (100 / (1 + RS))
    RS = average_gain / average_loss over period
    """
    if len(bars) < period + 1:
        return 50.0
    
    closes = [b.close for b in bars]
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    
    gains = [max(c, 0) for c in changes[-period:]]
    losses = [abs(min(c, 0)) for c in changes[-period:]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_all_factors(bars: List[OHLCVBar]) -> FactorSet:
    """
    Compute the full Alpha158-inspired factor set for an instrument.
    
    This is the main entry point for factor calculation. It combines
    all individual factor calculations into a single FactorSet.
    """
    price = calculate_price_factors(bars)
    ma = calculate_moving_average_factors(bars)
    momentum = calculate_momentum_factors(bars)
    volatility = calculate_volatility_factors(bars)
    volume = calculate_volume_factors(bars)
    
    closes = [b.close for b in bars]
    
    return FactorSet(
        returns_1d=price.get("returns_1d", 0),
        returns_5d=price.get("returns_5d", 0),
        returns_20d=price.get("returns_20d", 0),
        log_volume=price.get("log_volume", 0),
        high_low_range=price.get("high_low_range", 0),
        close_open_range=price.get("close_open_range", 0),
        ma5_ratio=ma.get("ma5_ratio", 0),
        ma10_ratio=ma.get("ma10_ratio", 0),
        ma20_ratio=ma.get("ma20_ratio", 0),
        ma60_ratio=ma.get("ma60_ratio", 0),
        momentum_5d=momentum.get("momentum_5d", 0),
        momentum_20d=momentum.get("momentum_20d", 0),
        volatility_5d=volatility.get("volatility_5d", 0),
        volatility_20d=volatility.get("volatility_20d", 0),
        volume_ratio_5d=volume.get("volume_ratio_5d", 0),
        volume_ratio_20d=volume.get("volume_ratio_20d", 0),
        vwap_ratio=_safe_div(closes[-1] - calculate_vwap(bars), calculate_vwap(bars)) if bars else 0,
        rsi_14=calculate_rsi(bars),
    )


# ---------------------------------------------------------------------------
# Risk modeling
# ---------------------------------------------------------------------------

def calculate_risk_metrics(
    returns: List[float],
    risk_free_rate: float = 0.02,
    benchmark_returns: Optional[List[float]] = None,
) -> RiskModel:
    """
    Calculate comprehensive risk metrics from a return series.
    
    Inspired by Qlib's risk analysis framework which provides
    variance, VaR, Sharpe, Sortino, and drawdown metrics.
    
    Args:
        returns: List of periodic returns (e.g., daily)
        risk_free_rate: Annual risk-free rate (default 2%)
        benchmark_returns: Optional benchmark returns for beta/alpha/IR
    
    Returns:
        RiskModel with all computed metrics
    """
    if len(returns) < 2:
        return RiskModel()
    
    n = len(returns)
    rf_period = risk_free_rate / 252  # Daily risk-free rate
    
    # Mean and variance
    mean_return = sum(returns) / n
    variance = sum((r - mean_return) ** 2 for r in returns) / (n - 1)
    volatility = math.sqrt(variance)
    
    # Annualized metrics
    annual_return = mean_return * 252
    annual_vol = volatility * math.sqrt(252)
    
    # Value at Risk (historical, 95%)
    sorted_returns = sorted(returns)
    var_index = int(0.05 * n)
    var_95 = sorted_returns[max(0, var_index)]
    
    # Conditional VaR (expected shortfall)
    tail_returns = sorted_returns[:max(1, var_index)]
    cvar_95 = sum(tail_returns) / len(tail_returns)
    
    # Sharpe ratio
    excess_return = mean_return - rf_period
    sharpe = _safe_div(excess_return, volatility) * math.sqrt(252)
    
    # Sortino ratio (downside deviation only)
    downside_returns = [min(r - rf_period, 0) for r in returns]
    downside_var = sum(d ** 2 for d in downside_returns) / n
    downside_dev = math.sqrt(downside_var)
    sortino = _safe_div(excess_return, downside_dev) * math.sqrt(252)
    
    # Maximum drawdown
    cumulative = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cumulative *= (1 + r)
        peak = max(peak, cumulative)
        dd = (cumulative - peak) / peak
        max_dd = min(max_dd, dd)
    
    # Beta, Alpha, Information Ratio (if benchmark provided)
    beta = 1.0
    alpha = 0.0
    ir = 0.0
    
    if benchmark_returns and len(benchmark_returns) == n:
        bench_mean = sum(benchmark_returns) / n
        bench_var = sum((r - bench_mean) ** 2 for r in benchmark_returns) / (n - 1)
        
        covariance = sum(
            (returns[i] - mean_return) * (benchmark_returns[i] - bench_mean)
            for i in range(n)
        ) / (n - 1)
        
        beta = _safe_div(covariance, bench_var)
        alpha = (mean_return - rf_period) - beta * (bench_mean - rf_period)
        alpha_annual = alpha * 252
        
        # Information ratio
        active_returns = [returns[i] - benchmark_returns[i] for i in range(n)]
        active_mean = sum(active_returns) / n
        tracking_error = math.sqrt(
            sum((r - active_mean) ** 2 for r in active_returns) / (n - 1)
        )
        ir = _safe_div(active_mean, tracking_error) * math.sqrt(252)
    else:
        alpha_annual = annual_return - risk_free_rate
    
    return RiskModel(
        variance=variance,
        volatility=annual_vol,
        var_95=var_95,
        cvar_95=cvar_95,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        max_drawdown=max_dd,
        beta=beta,
        alpha=alpha_annual if not benchmark_returns else alpha * 252,
        information_ratio=ir,
    )


# ---------------------------------------------------------------------------
# Portfolio optimization
# ---------------------------------------------------------------------------

def equal_weight_portfolio(instruments: List[str]) -> List[PortfolioWeight]:
    """Create an equal-weight portfolio."""
    n = len(instruments)
    if n == 0:
        return []
    weight = 1.0 / n
    return [PortfolioWeight(instrument=inst, weight=weight) for inst in instruments]


def min_variance_portfolio(
    returns_matrix: Dict[str, List[float]],
) -> List[PortfolioWeight]:
    """
    Approximate minimum variance portfolio using iterative optimization.
    
    For a simplified analytical solution with 2 assets:
    w1 = (σ2² - ρσ1σ2) / (σ1² + σ2² - 2ρσ1σ2)
    
    For N assets, uses a greedy approach as approximation.
    """
    instruments = list(returns_matrix.keys())
    n = len(instruments)
    
    if n == 0:
        return []
    if n == 1:
        return [PortfolioWeight(instrument=instruments[0], weight=1.0)]
    
    # Calculate individual volatilities
    vols = {}
    for inst in instruments:
        rets = returns_matrix[inst]
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / len(rets)
        vols[inst] = math.sqrt(var)
    
    # Inverse-volatility weighting (simple approximation)
    inv_vols = {inst: _safe_div(1.0, v) for inst, v in vols.items()}
    total_inv_vol = sum(inv_vols.values())
    
    weights = []
    for inst in instruments:
        w = _safe_div(inv_vols[inst], total_inv_vol)
        weights.append(PortfolioWeight(instrument=inst, weight=w))
    
    return weights


def risk_parity_portfolio(
    returns_matrix: Dict[str, List[float]],
) -> List[PortfolioWeight]:
    """
    Risk parity portfolio — equal risk contribution from each asset.
    
    Each asset contributes equally to total portfolio risk.
    Uses iterative approximation.
    """
    instruments = list(returns_matrix.keys())
    n = len(instruments)
    
    if n == 0:
        return []
    if n == 1:
        return [PortfolioWeight(instrument=instruments[0], weight=1.0)]
    
    # Calculate volatilities
    vols = {}
    for inst in instruments:
        rets = returns_matrix[inst]
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / len(rets)
        vols[inst] = math.sqrt(var) if var > 0 else 1e-8
    
    # Risk parity: weight inversely proportional to volatility
    total_inv_vol = sum(_safe_div(1.0, v) for v in vols.values())
    
    weights = []
    for inst in instruments:
        w = _safe_div(_safe_div(1.0, vols[inst]), total_inv_vol)
        weights.append(PortfolioWeight(instrument=inst, weight=w))
    
    return weights


# ---------------------------------------------------------------------------
# Factor correlation analysis
# ---------------------------------------------------------------------------

def calculate_factor_correlation(
    factor_a: List[float], factor_b: List[float]
) -> float:
    """Calculate Pearson correlation between two factor series."""
    n = min(len(factor_a), len(factor_b))
    if n < 2:
        return 0.0
    
    a = factor_a[:n]
    b = factor_b[:n]
    
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / (n - 1)
    std_a = math.sqrt(sum((x - mean_a) ** 2 for x in a) / (n - 1))
    std_b = math.sqrt(sum((x - mean_b) ** 2 for x in b) / (n - 1))
    
    return _safe_div(cov, std_a * std_b)


def rank_factors_by_ic(
    factor_values: Dict[str, List[float]],
    forward_returns: List[float],
) -> List[Tuple[str, float]]:
    """
    Rank alpha factors by Information Coefficient (IC).
    
    IC = correlation(factor, forward_returns)
    Higher |IC| indicates stronger predictive power.
    
    Returns:
        List of (factor_name, ic_value) sorted by |IC| descending
    """
    ics = []
    for name, values in factor_values.items():
        ic = calculate_factor_correlation(values, forward_returns)
        ics.append((name, ic))
    
    return sorted(ics, key=lambda x: abs(x[1]), reverse=True)
