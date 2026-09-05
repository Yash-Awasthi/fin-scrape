"""
Graph state — TypedDict shared across all agent nodes.

Modeled after TradingAgents' AgentState but without langchain messages.
Each agent reads from state and writes its report back.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TradeState:
    """Mutable state passed through the pipeline."""

    ticker: str
    trade_date: str

    # Analyst reports (populated by analyst nodes)
    market_report: str = ""
    sentiment_report: str = ""
    news_report: str = ""
    fundamentals_report: str = ""

    # Debate state
    investment_debate_history: list[str] = field(default_factory=list)
    bull_history: list[str] = field(default_factory=list)
    bear_history: list[str] = field(default_factory=list)
    debate_round: int = 0

    # Research manager output
    investment_plan: str = ""

    # Trader output
    trader_proposal: str = ""

    # Risk debate state
    risk_debate_history: list[str] = field(default_factory=list)
    aggressive_history: list[str] = field(default_factory=list)
    conservative_history: list[str] = field(default_factory=list)
    neutral_history: list[str] = field(default_factory=list)
    risk_round: int = 0

    # Risk manager output
    risk_assessment: str = ""

    # Final output
    final_decision: str = ""
    signal: str = ""  # Buy / Hold / Sell

    # Metadata
    errors: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    def add_error(self, agent: str, msg: str) -> None:
        self.errors.append(f"[{agent}] {msg}")

    def add_debate_entry(self, speaker: str, content: str) -> None:
        entry = f"{speaker}: {content}"
        self.investment_debate_history.append(entry)
        if "Bull" in speaker:
            self.bull_history.append(entry)
        elif "Bear" in speaker:
            self.bear_history.append(entry)

    def add_risk_entry(self, speaker: str, content: str) -> None:
        entry = f"{speaker}: {content}"
        self.risk_debate_history.append(entry)
        if "Aggressive" in speaker:
            self.aggressive_history.append(entry)
        elif "Conservative" in speaker:
            self.conservative_history.append(entry)
        elif "Neutral" in speaker:
            self.neutral_history.append(entry)
