"""
Contest trading simulation from contesttrade.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time


@dataclass
class Trade:
    symbol: str
    side: str  # buy, sell
    quantity: float
    price: float
    timestamp: float = 0.0


@dataclass
class Portfolio:
    cash: float = 100000.0
    positions: Dict[str, float] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    pnl: float = 0.0


@dataclass
class Contest:
    id: str
    name: str
    start_capital: float
    start_time: float
    end_time: float
    participants: Dict[str, Portfolio]
    rankings: List[Dict]


def create_contest(contest_id: str, name: str, start_capital: float = 100000, duration_hours: float = 24) -> Contest:
    return Contest(
        id=contest_id, name=name, start_capital=start_capital,
        start_time=time.time(), end_time=time.time() + duration_hours * 3600,
        participants={}, rankings=[],
    )


def join_contest(contest: Contest, user_id: str) -> Portfolio:
    portfolio = Portfolio(cash=contest.start_capital)
    contest.participants[user_id] = portfolio
    return portfolio


def execute_trade(portfolio: Portfolio, symbol: str, side: str, quantity: float, price: float) -> Optional[Trade]:
    if side == "buy":
        cost = quantity * price
        if cost > portfolio.cash:
            return None
        portfolio.cash -= cost
        portfolio.positions[symbol] = portfolio.positions.get(symbol, 0) + quantity
    elif side == "sell":
        held = portfolio.positions.get(symbol, 0)
        if quantity > held:
            return None
        portfolio.cash += quantity * price
        portfolio.positions[symbol] = held - quantity
        if portfolio.positions[symbol] <= 0:
            del portfolio.positions[symbol]
    trade = Trade(symbol=symbol, side=side, quantity=quantity, price=price, timestamp=time.time())
    portfolio.trades.append(trade)
    return trade


def compute_portfolio_value(portfolio: Portfolio, prices: Dict[str, float]) -> float:
    value = portfolio.cash
    for symbol, qty in portfolio.positions.items():
        value += qty * prices.get(symbol, 0)
    return value


def rank_participants(contest: Contest, prices: Dict[str, float]) -> List[Dict]:
    rankings = []
    for user_id, portfolio in contest.participants.items():
        value = compute_portfolio_value(portfolio, prices)
        rankings.append({"user_id": user_id, "value": value, "pnl": value - contest.start_capital, "pnl_pct": (value - contest.start_capital) / contest.start_capital * 100})
    rankings.sort(key=lambda x: x["value"], reverse=True)
    for i, r in enumerate(rankings):
        r["rank"] = i + 1
    contest.rankings = rankings
    return rankings
