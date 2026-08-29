"""
Protocols and shared types for the council package.

Defines the AiClient protocol that host apps must implement,
plus CouncilEvent for event metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class AiClient(Protocol):
    """
    Protocol for AI/LLM calls. The host app implements this.

    The judge needs to call an LLM to read the full debate transcript
    and produce its own verdict. This protocol abstracts that call.
    """

    def __call__(
        self,
        prompt: str,
        system: str,
        model: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Call an AI model and return parsed JSON response.

        Args:
            prompt: The user prompt (debate transcript + stats).
            system: The system prompt (judge instructions).
            model: Optional model override.

        Returns:
            Parsed JSON dict, or None if the call failed.
        """
        ...


@dataclass
class CouncilEvent:
    """Metadata about the event being analyzed."""

    title: str
    text: str
    source: str = ""
    age_hours: float = 0
    tickers: list[str] = field(default_factory=list)
    event_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
