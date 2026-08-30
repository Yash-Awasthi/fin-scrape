"""
Multi-agent council with debate and voting.

Extracted from berkshire-agent-council — multi-agent analysis patterns.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import math


class AgentRole(Enum):
    SENTIMENT = "sentiment"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    MACRO = "macro"


class VoteDirection(Enum):
    STRONG_BUY = 2
    BUY = 1
    HOLD = 0
    SELL = -1
    STRONG_SELL = -2


@dataclass
class AgentVerdict:
    agent: AgentRole
    direction: VoteDirection
    confidence: float  # 0-1
    reasoning: str
    key_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class DebateRound:
    agent: AgentRole
    statement: str
    responding_to: Optional[AgentRole] = None


@dataclass
class CouncilResult:
    ticker: str
    verdicts: List[AgentVerdict]
    debate: List[DebateRound]
    final_direction: VoteDirection
    final_confidence: float
    consensus_score: float  # -1 to 1


class MultiAgentCouncil:
    """Multi-agent investment council with debate mechanism."""

    def __init__(self):
        self.agents = {
            AgentRole.SENTIMENT: self._analyze_sentiment,
            AgentRole.TECHNICAL: self._analyze_technical,
            AgentRole.FUNDAMENTAL: self._analyze_fundamental,
            AgentRole.MACRO: self._analyze_macro,
        }

    def analyze(self, ticker: str, data: Dict[str, Any]) -> CouncilResult:
        """Run full council analysis with debate."""
        verdicts = []
        for role, analyzer in self.agents.items():
            verdict = analyzer(ticker, data)
            verdicts.append(verdict)

        debate = self._conduct_debate(verdicts)
        final = self._vote(verdicts)

        return CouncilResult(
            ticker=ticker,
            verdicts=verdicts,
            debate=debate,
            final_direction=final[0],
            final_confidence=final[1],
            consensus_score=self._compute_consensus(verdicts),
        )

    def _analyze_sentiment(self, ticker: str, data: Dict) -> AgentVerdict:
        news_sentiment = data.get("news_sentiment", 0.0)
        social_sentiment = data.get("social_sentiment", 0.0)

        avg = (news_sentiment + social_sentiment) / 2

        if avg > 0.3:
            direction = VoteDirection.BUY
        elif avg > 0.1:
            direction = VoteDirection.HOLD
        elif avg > -0.1:
            direction = VoteDirection.HOLD
        elif avg > -0.3:
            direction = VoteDirection.SELL
        else:
            direction = VoteDirection.STRONG_SELL

        confidence = min(1.0, abs(avg) + 0.3)

        return AgentVerdict(
            agent=AgentRole.SENTIMENT,
            direction=direction,
            confidence=confidence,
            reasoning=f"News sentiment {news_sentiment:.2f}, social sentiment {social_sentiment:.2f}",
            key_metrics={"news_sentiment": news_sentiment, "social_sentiment": social_sentiment},
        )

    def _analyze_technical(self, ticker: str, data: Dict) -> AgentVerdict:
        rsi = data.get("rsi", 50.0)
        macd = data.get("macd", 0.0)
        sma_50 = data.get("sma_50", 0.0)
        sma_200 = data.get("sma_200", 0.0)
        price = data.get("price", 0.0)

        score = 0.0
        if rsi < 30:
            score += 0.3
        elif rsi > 70:
            score -= 0.3

        if macd > 0:
            score += 0.2
        else:
            score -= 0.2

        if sma_50 > 0 and sma_200 > 0:
            if sma_50 > sma_200:
                score += 0.2
            else:
                score -= 0.2

        if price > sma_50 > 0:
            score += 0.15

        if score > 0.3:
            direction = VoteDirection.BUY
        elif score > 0.1:
            direction = VoteDirection.HOLD
        elif score > -0.1:
            direction = VoteDirection.HOLD
        elif score > -0.3:
            direction = VoteDirection.SELL
        else:
            direction = VoteDirection.STRONG_SELL

        return AgentVerdict(
            agent=AgentRole.TECHNICAL,
            direction=direction,
            confidence=min(1.0, abs(score) + 0.3),
            reasoning=f"RSI {rsi:.1f}, MACD {'positive' if macd > 0 else 'negative'}",
            key_metrics={"rsi": rsi, "macd": macd, "score": score},
        )

    def _analyze_fundamental(self, ticker: str, data: Dict) -> AgentVerdict:
        pe_ratio = data.get("pe_ratio", 20.0)
        roe = data.get("roe", 0.1)
        debt_to_equity = data.get("debt_to_equity", 1.0)
        revenue_growth = data.get("revenue_growth", 0.0)

        score = 0.0
        if 0 < pe_ratio < 15:
            score += 0.3
        elif pe_ratio > 30:
            score -= 0.2

        if roe > 0.15:
            score += 0.25
        elif roe < 0.05:
            score -= 0.15

        if debt_to_equity < 0.5:
            score += 0.15
        elif debt_to_equity > 2.0:
            score -= 0.2

        if revenue_growth > 0.1:
            score += 0.2

        if score > 0.3:
            direction = VoteDirection.BUY
        elif score > -0.1:
            direction = VoteDirection.HOLD
        elif score > -0.3:
            direction = VoteDirection.SELL
        else:
            direction = VoteDirection.STRONG_SELL

        return AgentVerdict(
            agent=AgentRole.FUNDAMENTAL,
            direction=direction,
            confidence=min(1.0, abs(score) + 0.3),
            reasoning=f"P/E {pe_ratio:.1f}, ROE {roe:.1%}, D/E {debt_to_equity:.2f}",
            key_metrics={"pe_ratio": pe_ratio, "roe": roe, "debt_to_equity": debt_to_equity},
        )

    def _analyze_macro(self, ticker: str, data: Dict) -> AgentVerdict:
        interest_rate = data.get("interest_rate", 5.0)
        inflation = data.get("inflation", 3.0)
        gdp_growth = data.get("gdp_growth", 2.0)

        score = 0.0
        if interest_rate < 3:
            score += 0.2
        elif interest_rate > 7:
            score -= 0.2

        if inflation < 3:
            score += 0.15
        elif inflation > 5:
            score -= 0.2

        if gdp_growth > 3:
            score += 0.2
        elif gdp_growth < 0:
            score -= 0.25

        if score > 0.2:
            direction = VoteDirection.BUY
        elif score > -0.1:
            direction = VoteDirection.HOLD
        else:
            direction = VoteDirection.SELL

        return AgentVerdict(
            agent=AgentRole.MACRO,
            direction=direction,
            confidence=min(1.0, abs(score) + 0.25),
            reasoning=f"Rates {interest_rate:.1f}%, inflation {inflation:.1f}%, GDP {gdp_growth:.1f}%",
            key_metrics={"interest_rate": interest_rate, "inflation": inflation, "gdp_growth": gdp_growth},
        )

    def _conduct_debate(self, verdicts: List[AgentVerdict]) -> List[DebateRound]:
        """Agents respond to each other's verdicts."""
        debate = []
        roles = [v.agent for v in verdicts]

        for i, v1 in enumerate(verdicts):
            for j, v2 in enumerate(verdicts):
                if i != j and v1.direction != v2.direction:
                    debate.append(DebateRound(
                        agent=v1.agent,
                        statement=f"{v1.agent.value} disagrees with {v2.agent.value}: {v1.reasoning}",
                        responding_to=v2.agent,
                    ))

        return debate

    def _vote(self, verdicts: List[AgentVerdict]) -> tuple:
        """Weighted voting to determine final direction."""
        total_weight = 0
        weighted_sum = 0

        for v in verdicts:
            weight = v.confidence
            weighted_sum += v.direction.value * weight
            total_weight += weight

        if total_weight == 0:
            return VoteDirection.HOLD, 0.0

        avg = weighted_sum / total_weight

        if avg > 1.0:
            direction = VoteDirection.STRONG_BUY
        elif avg > 0.3:
            direction = VoteDirection.BUY
        elif avg > -0.3:
            direction = VoteDirection.HOLD
        elif avg > -1.0:
            direction = VoteDirection.SELL
        else:
            direction = VoteDirection.STRONG_SELL

        confidence = min(1.0, abs(avg) / 2 + 0.3)

        return direction, confidence

    def _compute_consensus(self, verdicts: List[AgentVerdict]) -> float:
        """Compute consensus score (-1 to 1)."""
        values = [v.direction.value for v in verdicts]
        avg = sum(values) / len(values) if values else 0
        return max(-1.0, min(1.0, avg / 2))
