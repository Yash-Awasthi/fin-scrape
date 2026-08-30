"""
Portfolio risk analysis from empyrical — risk metrics and performance.
"""
from dataclasses import dataclass
from typing import List
import math


@dataclass
class RiskMetrics:
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    tail_ratio: float = 0.0


def compute_returns(prices: List[float]) -> List[float]:
    return [(prices[i] - prices[i - 1]) / prices[i - 1] if prices[i - 1] != 0 else 0 for i in range(1, len(prices))]


def compute_volatility(returns: List[float], annualize: bool = True) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    vol = math.sqrt(variance)
    return vol * math.sqrt(252) if annualize else vol


def compute_sharpe(returns: List[float], risk_free: float = 0.02) -> float:
    if not returns:
        return 0.0
    mean_ret = sum(returns) / len(returns) * 252
    vol = compute_volatility(returns)
    return (mean_ret - risk_free) / vol if vol > 0 else 0.0


def compute_sortino(returns: List[float], risk_free: float = 0.02) -> float:
    if not returns:
        return 0.0
    mean_ret = sum(returns) / len(returns) * 252
    downside = [min(0, r) ** 2 for r in returns]
    downside_vol = math.sqrt(sum(downside) / len(downside)) * math.sqrt(252) if downside else 0
    return (mean_ret - risk_free) / downside_vol if downside_vol > 0 else 0.0


def compute_max_drawdown(prices: List[float]) -> float:
    peak = prices[0] if prices else 0
    max_dd = 0
    for p in prices:
        if p > peak:
            peak = p
        dd = (peak - p) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)
    return max_dd


def compute_var(returns: List[float], confidence: float = 0.95) -> float:
    sorted_rets = sorted(returns)
    idx = int((1 - confidence) * len(sorted_rets))
    return sorted_rets[max(0, idx)]


def compute_cvar(returns: List[float], confidence: float = 0.95) -> float:
    sorted_rets = sorted(returns)
    cutoff = int((1 - confidence) * len(sorted_rets))
    tail = sorted_rets[:max(1, cutoff)]
    return sum(tail) / len(tail) if tail else 0.0


def compute_skewness(returns: List[float]) -> float:
    if len(returns) < 3:
        return 0.0
    mean = sum(returns) / len(returns)
    std = math.sqrt(sum((r - mean) ** 2 for r in returns) / len(returns))
    if std == 0:
        return 0.0
    m3 = sum(((r - mean) / std) ** 3 for r in returns) / len(returns)
    return m3


def compute_kurtosis(returns: List[float]) -> float:
    if len(returns) < 4:
        return 0.0
    mean = sum(returns) / len(returns)
    std = math.sqrt(sum((r - mean) ** 2 for r in returns) / len(returns))
    if std == 0:
        return 0.0
    m4 = sum(((r - mean) / std) ** 4 for r in returns) / len(returns)
    return m4 - 3


def analyze_portfolio(prices: List[float], risk_free: float = 0.02) -> RiskMetrics:
    returns = compute_returns(prices)
    vol = compute_volatility(returns)
    sharpe = compute_sharpe(returns, risk_free)
    sortino = compute_sortino(returns, risk_free)
    max_dd = compute_max_drawdown(prices)
    calmar = (sum(returns) / len(returns) * 252) / max_dd if max_dd > 0 else 0
    var = compute_var(returns)
    cvar = compute_cvar(returns)
    skew = compute_skewness(returns)
    kurt = compute_kurtosis(returns)
    right = compute_var(returns, 0.95)
    left = abs(compute_var(returns, 0.05))
    tail = right / left if left > 0 else 1.0

    return RiskMetrics(
        volatility=round(vol, 4), sharpe_ratio=round(sharpe, 4), sortino_ratio=round(sortino, 4),
        max_drawdown=round(max_dd, 4), calmar_ratio=round(calmar, 4), var_95=round(var, 4),
        cvar_95=round(cvar, 4), skewness=round(skew, 4), kurtosis=round(kurt, 4), tail_ratio=round(tail, 4),
    )
