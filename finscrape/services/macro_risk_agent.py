"""
Macro Risk Agent — Extracted from Unified-Marco-Markets patterns.

Multi-agent macro risk analysis with:
- Tariff index and momentum analysis
- Shock score detection
- Geopolitical event monitoring
- Weight adjustment signals
- Confidence scoring
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class SignalSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentSignal:
    agent: str
    signal: str
    reason: str
    severity: SignalSeverity
    confidence: float
    weight_adjustment: Dict[str, float] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class MacroState:
    tariff_index: float = 0.0
    tariff_momentum: float = 0.0
    shock_score: float = 0.0
    geopolitical_risk: float = 0.0
    energy_shock: float = 0.0
    liquidity_stress: float = 0.0
    data_ts: str = ""

    def __post_init__(self):
        if not self.data_ts:
            self.data_ts = datetime.now(timezone.utc).isoformat()


class MacroAgent:
    """Analyze macro-economic risk signals."""

    def evaluate(self, state: MacroState) -> List[AgentSignal]:
        signals: List[AgentSignal] = []
        now = datetime.now(timezone.utc).isoformat()

        if state.tariff_momentum > 5.0:
            signals.append(AgentSignal(
                agent="macro_agent",
                signal="TARIFF_ACCELERATION",
                reason=f"Tariff momentum {state.tariff_momentum:.2f} - rapid policy tightening",
                severity=SignalSeverity.MEDIUM,
                confidence=0.75,
                weight_adjustment={"shock_score": 1.3, "tariff_momentum": 1.5},
            ))

        if state.shock_score > 2.0:
            signals.append(AgentSignal(
                agent="macro_agent",
                signal="NEWS_SHOCK_HIGH",
                reason=f"Shock score {state.shock_score:.2f} - significant geopolitical event",
                severity=SignalSeverity.HIGH,
                confidence=0.80,
                weight_adjustment={"shock_score": 1.5},
            ))

        if state.tariff_index > 70:
            signals.append(AgentSignal(
                agent="macro_agent",
                signal="HIGH_TARIFF_REGIME",
                reason=f"Tariff index at {state.tariff_index:.1f} - elevated trade risk",
                severity=SignalSeverity.MEDIUM,
                confidence=0.70,
            ))

        if state.geopolitical_risk > 0.7:
            signals.append(AgentSignal(
                agent="macro_agent",
                signal="GEOPOLITICAL_ELEVATED",
                reason=f"Geopolitical risk at {state.geopolitical_risk:.2f}",
                severity=SignalSeverity.HIGH,
                confidence=0.75,
                weight_adjustment={"geopolitical_risk": 1.4},
            ))

        return signals


class ConflictAgent:
    """Analyze conflict and sanctions signals."""

    def evaluate(self, state: MacroState) -> List[AgentSignal]:
        signals: List[AgentSignal] = []

        if state.geopolitical_risk > 0.8:
            signals.append(AgentSignal(
                agent="conflict_agent",
                signal="CONFLICT_ESCALATION",
                reason=f"Geopolitical risk critical at {state.geopolitical_risk:.2f}",
                severity=SignalSeverity.CRITICAL,
                confidence=0.85,
                weight_adjustment={"risk_off": 1.5},
            ))

        return signals


class EnergyShockAgent:
    """Analyze energy market shocks."""

    def evaluate(self, state: MacroState) -> List[AgentSignal]:
        signals: List[AgentSignal] = []

        if state.energy_shock > 0.6:
            signals.append(AgentSignal(
                agent="energy_shock_agent",
                signal="ENERGY_DISRUPTION",
                reason=f"Energy shock score {state.energy_shock:.2f}",
                severity=SignalSeverity.MEDIUM if state.energy_shock < 0.8 else SignalSeverity.HIGH,
                confidence=0.70,
                weight_adjustment={"energy_weight": 1.3},
            ))

        return signals


class LiquidityAgent:
    """Analyze market liquidity conditions."""

    def evaluate(self, state: MacroState) -> List[AgentSignal]:
        signals: List[AgentSignal] = []

        if state.liquidity_stress > 0.7:
            signals.append(AgentSignal(
                agent="liquidity_agent",
                signal="LIQUIDITY_STRESS",
                reason=f"Liquidity stress at {state.liquidity_stress:.2f}",
                severity=SignalSeverity.HIGH,
                confidence=0.75,
                weight_adjustment={"liquidity_weight": 1.4},
            ))

        return signals


class MacroRiskEngine:
    """Orchestrate multiple agents for comprehensive risk analysis."""

    def __init__(self) -> None:
        self.agents = [
            MacroAgent(),
            ConflictAgent(),
            EnergyShockAgent(),
            LiquidityAgent(),
        ]

    def analyze(self, state: MacroState) -> Dict[str, Any]:
        all_signals: List[AgentSignal] = []
        for agent in self.agents:
            all_signals.extend(agent.evaluate(state))

        # Aggregate confidence
        if all_signals:
            avg_confidence = sum(s.confidence for s in all_signals) / len(all_signals)
            max_severity = max(all_signals, key=lambda s: list(SignalSeverity).index(s.severity))
        else:
            avg_confidence = 0.0
            max_severity = SignalSeverity.LOW

        # Aggregate weight adjustments
        combined_adjustments: Dict[str, float] = {}
        for signal in all_signals:
            for key, value in signal.weight_adjustment.items():
                combined_adjustments[key] = max(combined_adjustments.get(key, 1.0), value)

        return {
            "signals": all_signals,
            "signal_count": len(all_signals),
            "avg_confidence": avg_confidence,
            "max_severity": max_severity.value,
            "weight_adjustments": combined_adjustments,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
