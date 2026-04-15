"""
Base agent class and data structures for the Multi-Agent AI Council.

Each agent is a distinct analytical persona that independently evaluates
financial news articles and produces a structured verdict.
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any

from finscrape.analysis.ai_client import call_ai

logger = logging.getLogger(__name__)


@dataclass
class AgentVerdict:
    """Structured output from a single agent's analysis of an article."""

    agent_name: str
    verdict: str  # INVEST, OBSERVE, CAUTIOUS, PULL_OUT
    signal_score: int  # -5 to +5
    confidence: float  # 0.0 to 1.0
    reasoning: str = ""
    tickers: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    key_insights: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate and clamp fields to valid ranges."""
        self.signal_score = max(-5, min(5, int(self.signal_score)))
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        if self.verdict not in ("INVEST", "OBSERVE", "CAUTIOUS", "PULL_OUT"):
            self.verdict = self._verdict_from_score(self.signal_score)

    @staticmethod
    def _verdict_from_score(score: int) -> str:
        if score >= 3:
            return "INVEST"
        elif score >= 1:
            return "OBSERVE"
        elif score >= -1:
            return "CAUTIOUS"
        else:
            return "PULL_OUT"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> AgentVerdict:
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


AGENT_RESPONSE_SCHEMA = """\
{
  "verdict": "INVEST/OBSERVE/CAUTIOUS/PULL_OUT",
  "signal_score": integer from -5 to 5,
  "confidence": float from 0.0 to 1.0,
  "reasoning": "2-4 sentence analysis from your perspective",
  "tickers": ["TICK1", "TICK2"],
  "risk_factors": ["risk 1", "risk 2"],
  "key_insights": ["insight 1", "insight 2"]
}"""


AGENT_USER_PROMPT = """\
Analyze the following financial news article from your specific perspective.
Return a single JSON object with your analysis. No markdown, no explanation outside the JSON.

SCHEMA (follow exactly):
{schema}

HEADLINE: {title}
ARTICLE: {text}
{metadata_section}"""


class BaseAgent(ABC):
    """
    Abstract base class for all AI council agents.

    Each agent has a unique persona defined by its name, role description,
    system prompt, and analysis weight. Subclasses must implement the
    `system_prompt` property to define their analytical perspective.
    """

    def __init__(self, weight: float = 1.0, model: str | None = None):
        self.weight = weight
        self.model = model

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this agent (e.g. 'analyst', 'contrarian')."""
        ...

    @property
    @abstractmethod
    def role(self) -> str:
        """One-line description of this agent's analytical role."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Full system prompt that establishes this agent's perspective."""
        ...

    def analyze(
        self,
        title: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> AgentVerdict:
        """
        Analyze a financial news article and return a structured verdict.

        Uses the shared call_ai() function from the existing AI client.
        Returns a default low-confidence verdict on any failure.
        """
        metadata = metadata or {}
        metadata_section = ""
        if metadata:
            parts = [f"{k}: {v}" for k, v in metadata.items()]
            metadata_section = "METADATA:\n" + "\n".join(parts)

        prompt = AGENT_USER_PROMPT.format(
            schema=AGENT_RESPONSE_SCHEMA,
            title=title,
            text=text,
            metadata_section=metadata_section,
        )

        raw = call_ai(prompt, self.system_prompt, model=self.model)

        if raw is None:
            logger.warning("[%s] AI call returned None — using default verdict", self.name)
            return AgentVerdict(
                agent_name=self.name,
                verdict="CAUTIOUS",
                signal_score=0,
                confidence=0.1,
                reasoning=f"Agent '{self.name}' failed to produce analysis.",
            )

        return self._parse_response(raw)

    def _parse_response(self, raw: dict) -> AgentVerdict:
        """Convert the raw AI response dict into an AgentVerdict."""
        try:
            return AgentVerdict(
                agent_name=self.name,
                verdict=raw.get("verdict", "CAUTIOUS"),
                signal_score=raw.get("signal_score", 0),
                confidence=raw.get("confidence", 0.5),
                reasoning=raw.get("reasoning", ""),
                tickers=raw.get("tickers", []) if isinstance(raw.get("tickers"), list) else [],
                risk_factors=raw.get("risk_factors", []) if isinstance(raw.get("risk_factors"), list) else [],
                key_insights=raw.get("key_insights", []) if isinstance(raw.get("key_insights"), list) else [],
            )
        except Exception as e:
            logger.error("[%s] Failed to parse response: %s", self.name, e)
            return AgentVerdict(
                agent_name=self.name,
                verdict="CAUTIOUS",
                signal_score=0,
                confidence=0.1,
                reasoning=f"Agent '{self.name}' produced unparseable response.",
            )
