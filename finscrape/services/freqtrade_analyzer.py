"""
Freqtrade patterns — backtesting and strategy analysis from freqtrade.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import math


@dataclass
class TradeResult:
    pair: str
    open_date: str
    close_date: str
    open_rate: float
    close_rate: float
    profit_pct: float
    profit_abs: float
    duration_minutes: float
    is_short: bool = False
    exit_reason: str = ""


@dataclass
class BacktestResult:
    trades: List[TradeResult]
    total_profit: float = 0.0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_winning: float = 0.0
    avg_losing: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0


def compute_backtest_metrics(trades: List[TradeResult]) -> BacktestResult:
    if not trades:
        return BacktestResult(trades=[])

    total_profit = sum(t.profit_pct for t in trades)
    winners = [t for t in trades if t.profit_pct > 0]
    losers = [t for t in trades if t.profit_pct <= 0]

    win_rate = len(winners) / len(trades) if trades else 0
    avg_profit = total_profit / len(trades) if trades else 0
    avg_winning = sum(t.profit_pct for t in winners) / len(winners) if winners else 0
    avg_losing = sum(t.profit_pct for t in losers) / len(losers) if losers else 0

    gross_profit = sum(t.profit_pct for t in winners)
    gross_loss = abs(sum(t.profit_pct for t in losers))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    expectancy = (win_rate * avg_winning) - ((1 - win_rate) * abs(avg_losing))

    cumulative = []
    running = 0
    for t in trades:
        running += t.profit_pct
        cumulative.append(running)
    peak = cumulative[0] if cumulative else 0
    max_dd = 0
    for val in cumulative:
        if val > peak:
            peak = val
        dd = peak - val
        if dd > max_dd:
            max_dd = dd

    returns = [t.profit_pct for t in trades]
    mean_ret = sum(returns) / len(returns)
    std = math.sqrt(sum((r - mean_ret) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 1
    sharpe = mean_ret / std if std > 0 else 0

    return BacktestResult(
        trades=trades, total_profit=total_profit, win_rate=win_rate, avg_profit=avg_profit,
        max_drawdown=max_dd, sharpe_ratio=sharpe, total_trades=len(trades),
        winning_trades=len(winners), losing_trades=len(losers),
        avg_winning=avg_winning, avg_losing=avg_losing, profit_factor=profit_factor, expectancy=expectancy,
    )


def analyze_pairs(trades: List[TradeResult]) -> Dict[str, Dict]:
    pairs = {}
    for t in trades:
        if t.pair not in pairs:
            pairs[t.pair] = {"trades": 0, "wins": 0, "total_profit": 0}
        pairs[t.pair]["trades"] += 1
        pairs[t.pair]["total_profit"] += t.profit_pct
        if t.profit_pct > 0:
            pairs[t.pair]["wins"] += 1
    for pair, data in pairs.items():
        data["win_rate"] = data["wins"] / data["trades"] if data["trades"] > 0 else 0
        data["avg_profit"] = data["total_profit"] / data["trades"] if data["trades"] > 0 else 0
    return pairs


def optimize_parameters(trades: List[TradeResult], param_grid: Dict[str, List]) -> Dict:
    best = {"params": {}, "sharpe": -999}
    for key, values in param_grid.items():
        for val in values:
            filtered = [t for t in trades if True]
            result = compute_backtest_metrics(filtered)
            if result.sharpe_ratio > best["sharpe"]:
                best = {"params": {key: val}, "sharpe": result.sharpe_ratio}
    return best
