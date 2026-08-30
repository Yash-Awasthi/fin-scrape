"""
AShare Backtest — Extracted from TradingAgents-AShare patterns.

Provides:
- Historical backtest job management
- Trading date utilities
- Price fetching and performance evaluation
- Multi-agent debate visualization
- Portfolio tracking and watchlist management
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisPeriod(Enum):
    SHORT_TERM = "short_term"  # 1-5 days
    MEDIUM_TERM = "medium_term"  # 5-20 days
    LONG_TERM = "long_term"  # 20+ days


@dataclass
class BacktestJob:
    job_id: str
    symbol: str
    start_date: str
    end_date: str
    interval_days: int = 5
    hold_days: int = 5
    status: JobStatus = JobStatus.PENDING
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class DebateRound:
    round_num: int
    agent_name: str
    stance: str  # "bullish", "bearish", "neutral"
    arguments: List[str]
    confidence: float
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class AgentDebate:
    symbol: str
    rounds: List[DebateRound] = field(default_factory=list)
    final_verdict: Optional[str] = None
    consensus_score: float = 0.0

    def add_round(self, agent_name: str, stance: str, arguments: List[str], confidence: float) -> DebateRound:
        round_num = len(self.rounds) + 1
        r = DebateRound(round_num, agent_name, stance, arguments, confidence)
        self.rounds.append(r)
        return r

    def get_consensus(self) -> Tuple[str, float]:
        if not self.rounds:
            return "neutral", 0.0

        stance_scores = {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0}
        for r in self.rounds:
            stance_scores[r.stance] = stance_scores.get(r.stance, 0) + r.confidence

        verdict = max(stance_scores, key=stance_scores.get)
        total = sum(stance_scores.values())
        score = stance_scores[verdict] / total if total > 0 else 0.0
        self.final_verdict = verdict
        self.consensus_score = score
        return verdict, score


@dataclass
class WatchlistItem:
    symbol: str
    name: str
    period: AnalysisPeriod = AnalysisPeriod.SHORT_TERM
    interval_days: int = 5
    enabled: bool = True
    last_analyzed: Optional[str] = None
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class Position:
    symbol: str
    name: str
    quantity: int
    cost_price: float
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def pnl(self) -> float:
        return (self.current_price - self.cost_price) * self.quantity

    @property
    def pnl_percent(self) -> float:
        if self.cost_price <= 0:
            return 0.0
        return (self.current_price - self.cost_price) / self.cost_price * 100


class BacktestService:
    """Manage backtest jobs and historical analysis."""

    def __init__(self) -> None:
        self._jobs: Dict[str, BacktestJob] = {}
        self._lock = threading.Lock()

    def create_job(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval_days: int = 5,
        hold_days: int = 5,
    ) -> BacktestJob:
        job = BacktestJob(
            job_id=str(uuid4())[:8],
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval_days=interval_days,
            hold_days=hold_days,
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[BacktestJob]:
        return self._jobs.get(job_id)

    def list_jobs(self) -> List[BacktestJob]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def complete_job(self, job_id: str, results: Dict[str, Any]) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            job.status = JobStatus.COMPLETED
            job.results = results
            job.completed_at = datetime.now(timezone.utc).isoformat()
            return True

    def fail_job(self, job_id: str, error: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            job.status = JobStatus.FAILED
            job.error = error
            return True

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False


def get_trading_dates(start: str, end: str, interval_days: int = 5) -> List[str]:
    """Get weekday dates between start and end, sampled every interval_days."""
    fmt = "%Y-%m-%d"
    cur = datetime.strptime(start, fmt)
    end_dt = datetime.strptime(end, fmt)
    dates: List[str] = []
    while cur <= end_dt:
        if cur.weekday() < 5:
            dates.append(cur.strftime(fmt))
        cur += timedelta(days=interval_days)
    return dates


def calculate_performance(
    buy_price: float,
    sell_price: float,
    quantity: int = 1,
    commission_rate: float = 0.001,
) -> Dict[str, float]:
    """Calculate trading performance metrics."""
    gross_profit = (sell_price - buy_price) * quantity
    commission = (buy_price + sell_price) * quantity * commission_rate
    net_profit = gross_profit - commission
    return_pct = (sell_price - buy_price) / buy_price * 100 if buy_price > 0 else 0.0

    return {
        "gross_profit": gross_profit,
        "commission": commission,
        "net_profit": net_profit,
        "return_pct": return_pct,
        "quantity": quantity,
    }


def evaluate_signal_accuracy(
    signals: List[Dict[str, Any]],
    prices: Dict[str, float],
    hold_days: int = 5,
) -> Dict[str, float]:
    """Evaluate signal accuracy against actual price movements."""
    correct = 0
    total = 0
    returns: List[float] = []

    for signal in signals:
        symbol = signal.get("symbol", "")
        direction = signal.get("direction", "neutral")
        entry_price = signal.get("price", 0.0)

        if symbol not in prices or entry_price <= 0:
            continue

        exit_price = prices[symbol]
        actual_return = (exit_price - entry_price) / entry_price
        returns.append(actual_return)

        if direction == "bullish" and actual_return > 0:
            correct += 1
        elif direction == "bearish" and actual_return < 0:
            correct += 1
        elif direction == "neutral" and abs(actual_return) < 0.02:
            correct += 1

        total += 1

    accuracy = correct / total if total > 0 else 0.0
    avg_return = sum(returns) / len(returns) if returns else 0.0

    return {
        "accuracy": accuracy,
        "total_signals": total,
        "avg_return": avg_return,
    }
