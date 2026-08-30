"""
Multi-agent investment analysis using legendary investor mental models.

Extracted from ai-investment-goatlens — Buffett, Lynch, Graham, Munger, Dalio agents.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import math


class InvestmentSignal(Enum):
    STRONG_BUY = 2
    BUY = 1
    HOLD = 0
    SELL = -1
    STRONG_SELL = -2


@dataclass
class InvestorMetrics:
    roe: float = 0.0
    profit_margin: float = 0.0
    debt_to_equity: float = 0.0
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    peg_ratio: float = 0.0
    free_cash_flow: float = 0.0
    revenue_growth: float = 0.0
    earnings_growth: float = 0.0
    dividend_yield: float = 0.0
    current_ratio: float = 0.0
    market_cap: float = 0.0


@dataclass
class AgentVerdict:
    agent_name: str
    signal: InvestmentSignal
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    reasoning: List[str] = field(default_factory=list)
    key_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ConsensusResult:
    ticker: str
    consensus_signal: InvestmentSignal
    consensus_score: float
    verdicts: List[AgentVerdict]
    agreement_ratio: float  # How much agents agree
    divergence_points: List[str] = field(default_factory=list)


class BuffettAgent:
    """Warren Buffett — Value + Quality Focus."""
    MIN_ROE = 0.15
    MAX_DEBT_TO_EQUITY = 0.5
    MIN_PROFIT_MARGIN = 0.10

    def analyze(self, metrics: InvestorMetrics) -> AgentVerdict:
        score = 0.0
        reasoning = []

        if metrics.roe >= self.MIN_ROE:
            score += 0.25
            reasoning.append(f"ROE {metrics.roe:.1%} meets threshold {self.MIN_ROE:.0%}")
        else:
            score -= 0.2
            reasoning.append(f"ROE {metrics.roe:.1%} below threshold")

        if metrics.profit_margin >= self.MIN_PROFIT_MARGIN:
            score += 0.2
            reasoning.append(f"Profit margin {metrics.profit_margin:.1%} is healthy")

        if metrics.debt_to_equity <= self.MAX_DEBT_TO_EQUITY:
            score += 0.2
            reasoning.append(f"Conservative debt (D/E {metrics.debt_to_equity:.2f})")
        else:
            score -= 0.15
            reasoning.append(f"High debt (D/E {metrics.debt_to_equity:.2f})")

        if metrics.free_cash_flow > 0:
            score += 0.15
            reasoning.append("Positive owner earnings")

        if metrics.dividend_yield > 0:
            score += 0.1
            reasoning.append(f"Dividend yield {metrics.dividend_yield:.1%}")

        signal = self._score_to_signal(score)
        confidence = min(1.0, abs(score) + 0.3)

        return AgentVerdict(
            agent_name="Warren Buffett",
            signal=signal,
            score=max(-1.0, min(1.0, score)),
            confidence=confidence,
            reasoning=reasoning,
            key_metrics={"roe": metrics.roe, "debt_to_equity": metrics.debt_to_equity},
        )

    def _score_to_signal(self, score: float) -> InvestmentSignal:
        if score > 0.5:
            return InvestmentSignal.STRONG_BUY
        elif score > 0.2:
            return InvestmentSignal.BUY
        elif score > -0.2:
            return InvestmentSignal.HOLD
        elif score > -0.5:
            return InvestmentSignal.SELL
        return InvestmentSignal.STRONG_SELL


class LynchAgent:
    """Peter Lynch — GARP (Growth at Reasonable Price)."""
    MAX_PEG = 1.0
    MIN_GROWTH = 0.10

    def analyze(self, metrics: InvestorMetrics) -> AgentVerdict:
        score = 0.0
        reasoning = []

        if metrics.peg_ratio > 0 and metrics.peg_ratio < self.MAX_PEG:
            score += 0.3
            reasoning.append(f"PEG {metrics.peg_ratio:.2f} is attractive (<1.0)")
        elif metrics.peg_ratio >= 1.0 and metrics.peg_ratio < 1.5:
            score += 0.1
            reasoning.append(f"PEG {metrics.peg_ratio:.2f} is fair")
        elif metrics.peg_ratio >= 1.5:
            score -= 0.2
            reasoning.append(f"PEG {metrics.peg_ratio:.2f} is expensive")

        if metrics.revenue_growth >= self.MIN_GROWTH:
            score += 0.25
            reasoning.append(f"Revenue growth {metrics.revenue_growth:.1%} is strong")
        elif metrics.revenue_growth > 0:
            score += 0.1
            reasoning.append(f"Revenue growth {metrics.revenue_growth:.1%} is moderate")

        if metrics.earnings_growth > metrics.revenue_growth and metrics.earnings_growth > 0:
            score += 0.15
            reasoning.append("Earnings growing faster than revenue — margin expansion")

        if metrics.debt_to_equity < 1.0:
            score += 0.1
            reasoning.append("Manageable debt levels")

        if metrics.current_ratio > 1.5:
            score += 0.1
            reasoning.append("Strong liquidity")

        signal = self._score_to_signal(score)
        confidence = min(1.0, abs(score) + 0.25)

        return AgentVerdict(
            agent_name="Peter Lynch",
            signal=signal,
            score=max(-1.0, min(1.0, score)),
            confidence=confidence,
            reasoning=reasoning,
            key_metrics={"peg_ratio": metrics.peg_ratio, "revenue_growth": metrics.revenue_growth},
        )

    def _score_to_signal(self, score: float) -> InvestmentSignal:
        if score > 0.4:
            return InvestmentSignal.STRONG_BUY
        elif score > 0.15:
            return InvestmentSignal.BUY
        elif score > -0.15:
            return InvestmentSignal.HOLD
        elif score > -0.4:
            return InvestmentSignal.SELL
        return InvestmentSignal.STRONG_SELL


class GrahamAgent:
    """Benjamin Graham — Deep Value + Margin of Safety."""
    MAX_PE = 15
    MAX_PB = 1.5
    MIN_CURRENT_RATIO = 2.0

    def analyze(self, metrics: InvestorMetrics) -> AgentVerdict:
        score = 0.0
        reasoning = []

        if 0 < metrics.pe_ratio < self.MAX_PE:
            score += 0.3
            reasoning.append(f"P/E {metrics.pe_ratio:.1f} is undervalued (<{self.MAX_PE})")
        elif metrics.pe_ratio >= self.MAX_PE and metrics.pe_ratio < 25:
            score += 0.05
            reasoning.append(f"P/E {metrics.pe_ratio:.1f} is fairly valued")
        elif metrics.pe_ratio >= 25:
            score -= 0.2
            reasoning.append(f"P/E {metrics.pe_ratio:.1f} is overvalued")

        if 0 < metrics.pb_ratio < self.MAX_PB:
            score += 0.25
            reasoning.append(f"P/B {metrics.pb_ratio:.2f} suggests margin of safety")
        elif metrics.pb_ratio >= self.MAX_PB:
            score -= 0.15
            reasoning.append(f"P/B {metrics.pb_ratio:.2f} is high")

        if metrics.current_ratio >= self.MIN_CURRENT_RATIO:
            score += 0.15
            reasoning.append(f"Current ratio {metrics.current_ratio:.1f} shows liquidity")

        if metrics.dividend_yield > 0.03:
            score += 0.15
            reasoning.append(f"Dividend yield {metrics.dividend_yield:.1%} provides income floor")

        if metrics.debt_to_equity < 0.5:
            score += 0.1
            reasoning.append("Conservative balance sheet")

        signal = self._score_to_signal(score)
        confidence = min(1.0, abs(score) + 0.3)

        return AgentVerdict(
            agent_name="Benjamin Graham",
            signal=signal,
            score=max(-1.0, min(1.0, score)),
            confidence=confidence,
            reasoning=reasoning,
            key_metrics={"pe_ratio": metrics.pe_ratio, "pb_ratio": metrics.pb_ratio},
        )

    def _score_to_signal(self, score: float) -> InvestmentSignal:
        if score > 0.5:
            return InvestmentSignal.STRONG_BUY
        elif score > 0.2:
            return InvestmentSignal.BUY
        elif score > -0.2:
            return InvestmentSignal.HOLD
        elif score > -0.5:
            return InvestmentSignal.SELL
        return InvestmentSignal.STRONG_SELL


class MungerAgent:
    """Charlie Munger — Quality First, Avoid Mistakes."""
    MIN_ROE = 0.20
    MIN_PROFIT_MARGIN = 0.15
    MAX_DEBT_TO_EQUITY = 0.3

    def analyze(self, metrics: InvestorMetrics) -> AgentVerdict:
        score = 0.0
        reasoning = []

        quality_score = 0
        if metrics.roe >= self.MIN_ROE:
            quality_score += 1
            reasoning.append(f"ROE {metrics.roe:.1%} indicates quality")
        if metrics.profit_margin >= self.MIN_PROFIT_MARGIN:
            quality_score += 1
            reasoning.append(f"Margin {metrics.profit_margin:.1%} shows pricing power")
        if metrics.debt_to_equity <= self.MAX_DEBT_TO_EQUITY:
            quality_score += 1
            reasoning.append("Conservative leverage")

        score = (quality_score / 3.0) * 0.6

        if metrics.revenue_growth > 0.10 and metrics.profit_margin > 0.10:
            score += 0.2
            reasoning.append("Growing with maintained margins — competitive advantage")

        if metrics.debt_to_equity > 1.0:
            score -= 0.3
            reasoning.append("Excessive leverage — avoid")

        signal = self._score_to_signal(score)
        confidence = min(1.0, abs(score) + 0.35)

        return AgentVerdict(
            agent_name="Charlie Munger",
            signal=signal,
            score=max(-1.0, min(1.0, score)),
            confidence=confidence,
            reasoning=reasoning,
            key_metrics={"roe": metrics.roe, "quality_score": quality_score / 3.0},
        )

    def _score_to_signal(self, score: float) -> InvestmentSignal:
        if score > 0.45:
            return InvestmentSignal.STRONG_BUY
        elif score > 0.15:
            return InvestmentSignal.BUY
        elif score > -0.15:
            return InvestmentSignal.HOLD
        elif score > -0.45:
            return InvestmentSignal.SELL
        return InvestmentSignal.STRONG_SELL


class DalioAgent:
    """Ray Dalio — Macro/Risk, Debt Cycles, Diversification."""
    MAX_DEBT_TO_EQUITY = 2.0

    def analyze(self, metrics: InvestorMetrics) -> AgentVerdict:
        score = 0.0
        reasoning = []

        if metrics.debt_to_equity > self.MAX_DEBT_TO_EQUITY:
            score -= 0.3
            reasoning.append(f"High leverage (D/E {metrics.debt_to_equity:.2f}) — cycle risk")
        elif metrics.debt_to_equity < 0.5:
            score += 0.15
            reasoning.append("Low leverage — resilient to downturns")

        if metrics.current_ratio < 1.0:
            score -= 0.25
            reasoning.append("Liquidity stress — vulnerable to credit tightening")
        elif metrics.current_ratio > 2.0:
            score += 0.1
            reasoning.append("Strong liquidity buffer")

        if metrics.dividend_yield > 0.02:
            score += 0.1
            reasoning.append(f"Dividend provides income in downturns")

        if metrics.revenue_growth < 0:
            score -= 0.2
            reasoning.append("Negative growth — contraction risk")
        elif metrics.revenue_growth > 0.15:
            score += 0.15
            reasoning.append("Strong growth despite macro risks")

        if metrics.pe_ratio > 30:
            score -= 0.15
            reasoning.append("Elevated valuation — limited margin of safety")

        signal = self._score_to_signal(score)
        confidence = min(1.0, abs(score) + 0.2)

        return AgentVerdict(
            agent_name="Ray Dalio",
            signal=signal,
            score=max(-1.0, min(1.0, score)),
            confidence=confidence,
            reasoning=reasoning,
            key_metrics={"debt_to_equity": metrics.debt_to_equity, "current_ratio": metrics.current_ratio},
        )

    def _score_to_signal(self, score: float) -> InvestmentSignal:
        if score > 0.35:
            return InvestmentSignal.STRONG_BUY
        elif score > 0.1:
            return InvestmentSignal.BUY
        elif score > -0.1:
            return InvestmentSignal.HOLD
        elif score > -0.35:
            return InvestmentSignal.SELL
        return InvestmentSignal.STRONG_SELL


def run_consensus(ticker: str, metrics: InvestorMetrics) -> ConsensusResult:
    agents = [BuffettAgent(), LynchAgent(), GrahamAgent(), MungerAgent(), DalioAgent()]
    verdicts = [agent.analyze(metrics) for agent in agents]

    scores = [v.score for v in verdicts]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    if avg_score > 0.4:
        consensus = InvestmentSignal.STRONG_BUY
    elif avg_score > 0.15:
        consensus = InvestmentSignal.BUY
    elif avg_score > -0.15:
        consensus = InvestmentSignal.HOLD
    elif avg_score > -0.4:
        consensus = InvestmentSignal.SELL
    else:
        consensus = InvestmentSignal.STRONG_SELL

    agreement = 1.0 - (max(scores) - min(scores)) / 4.0

    divergences = []
    for i, v1 in enumerate(verdicts):
        for j, v2 in enumerate(verdicts):
            if i < j and v1.signal != v2.signal:
                divergences.append(f"{v1.agent_name} vs {v2.agent_name}: {v1.signal.name} vs {v2.signal.name}")

    return ConsensusResult(
        ticker=ticker,
        consensus_signal=consensus,
        consensus_score=avg_score,
        verdicts=verdicts,
        agreement_ratio=agreement,
        divergence_points=divergences,
    )
