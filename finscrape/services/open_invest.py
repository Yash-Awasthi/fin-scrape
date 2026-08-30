"""
Open invest from openinvest — portfolio analysis.
"""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Holding:
    symbol: str
    shares: float
    avg_cost: float
    current_price: float = 0.0
    weight: float = 0.0

    @property
    def market_value(self) -> float:
        return self.shares * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.avg_cost) * self.shares

    @property
    def unrealized_pnl_pct(self) -> float:
        return (self.current_price / self.avg_cost - 1) * 100 if self.avg_cost > 0 else 0


@dataclass
class PortfolioAnalysis:
    holdings: List[Holding]
    total_value: float = 0.0
    total_cost: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    sector_breakdown: Dict[str, float] = field(default_factory=dict)
    top_gainers: List[str] = field(default_factory=list)
    top_losers: List[str] = field(default_factory=list)


def analyze_portfolio(holdings: List[Holding]) -> PortfolioAnalysis:
    total_value = sum(h.market_value for h in holdings)
    total_cost = sum(h.avg_cost * h.shares for h in holdings)
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_value / total_cost - 1) * 100 if total_cost > 0 else 0

    for h in holdings:
        h.weight = h.market_value / total_value if total_value > 0 else 0

    sorted_by_pnl = sorted(holdings, key=lambda h: h.unrealized_pnl_pct, reverse=True)
    top_gainers = [h.symbol for h in sorted_by_pnl[:3] if h.unrealized_pnl_pct > 0]
    top_losers = [h.symbol for h in sorted_by_pnl[-3:] if h.unrealized_pnl_pct < 0]

    return PortfolioAnalysis(
        holdings=holdings, total_value=total_value, total_cost=total_cost,
        total_pnl=total_pnl, total_pnl_pct=total_pnl_pct,
        top_gainers=top_gainers, top_losers=top_losers
    )


def compute_rebalance_suggestions(holdings: List[Holding], target_weights: Dict[str, float]) -> List[Dict]:
    total_value = sum(h.market_value for h in holdings)
    suggestions = []
    for h in holdings:
        target = target_weights.get(h.symbol, 0)
        diff = h.weight - target
        if abs(diff) > 0.02:
            action = "sell" if diff > 0 else "buy"
            amount = abs(diff) * total_value
            suggestions.append({"symbol": h.symbol, "action": action, "amount": round(amount, 2), "current_weight": round(h.weight * 100, 1), "target_weight": round(target * 100, 1)})
    return suggestions
