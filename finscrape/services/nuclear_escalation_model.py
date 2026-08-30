"""
Nuclear Escalation Model — Extracted from ROMANCER patterns.

Case-based reasoning for escalation risk assessment:
- Escalation ladder modeling
- Case-based reasoning with MOP (Memory Organization Packets)
- Percept-based event classification
- Outcome prediction
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EscalationRung:
    level: int
    name: str
    description: str
    severity: float  # 0.0 to 1.0


@dataclass
class EscalationEvent:
    rung_level: int
    actor: str
    action: str
    target: str
    description: str
    severity: float = 0.0


@dataclass
class Scenario:
    events: List[EscalationEvent]
    current_rung: int = 0
    outcome: str = "no_change"  # escalate, deescalate, no_change
    score: float = 0.0


class EscalationLadder:
    """Model of escalation rungs from low to nuclear."""

    def __init__(self) -> None:
        self.rungs: List[EscalationRung] = [
            EscalationRung(0, "Diplomatic Protest", "Formal diplomatic complaint", 0.1),
            EscalationRung(1, "Economic Sanctions", "Targeted economic measures", 0.2),
            EscalationRung(2, "Military Mobilization", "Forces moved to readiness", 0.3),
            EscalationRung(3, "Naval Blockade", "Sea lanes restricted", 0.4),
            EscalationRung(4, "Limited Military Strike", "Contained kinetic action", 0.5),
            EscalationRung(5, "Full Military Engagement", "Open conflict", 0.7),
            EscalationRung(6, "Nuclear Demonstration", "Nuclear weapon test/use warning", 0.85),
            EscalationRung(7, "Limited Nuclear Strike", "Tactical nuclear weapon use", 0.95),
            EscalationRung(8, "Full Nuclear Exchange", "Strategic nuclear weapons", 1.0),
        ]

    def get_rung(self, level: int) -> Optional[EscalationRung]:
        for rung in self.rungs:
            if rung.level == level:
                return rung
        return None

    def get_severity(self, level: int) -> float:
        rung = self.get_rung(level)
        return rung.severity if rung else 0.0

    def classify_event(self, event: EscalationEvent) -> int:
        """Classify an event into a rung level."""
        keywords = {
            0: ["protest", "condemn", "diplomatic", "summon"],
            1: ["sanction", "tariff", "restrict", "ban"],
            2: ["mobilize", "deploy", "exercise", "readiness"],
            3: ["blockade", "intercept", "patrol", "enforce"],
            4: ["strike", "attack", "bomb", "target"],
            5: ["invasion", "offensive", "engagement", "combat"],
            6: ["nuclear test", "nuclear threat", "missile launch"],
            7: ["tactical nuclear", "limited nuclear", "nuclear strike"],
            8: ["strategic nuclear", "full exchange", "nuclear war"],
        }

        action_lower = event.action.lower()
        for level, words in keywords.items():
            for word in words:
                if word in action_lower:
                    return level

        return event.rung_level


class CaseBasedReasoner:
    """Case-based reasoning for escalation prediction."""

    def __init__(self) -> None:
        self.cases: List[Dict[str, Any]] = []
        self.outcomes: Dict[str, int] = {
            "escalate": 0,
            "deescalate": 0,
            "no_change": 0,
        }

    def add_case(self, scenario: Scenario, outcome: str) -> None:
        """Store a historical case."""
        self.cases.append({
            "events": scenario.events,
            "current_rung": scenario.current_rung,
            "outcome": outcome,
        })
        self.outcomes[outcome] = self.outcomes.get(outcome, 0) + 1

    def predict_outcome(self, scenario: Scenario) -> Dict[str, float]:
        """Predict outcome based on similar cases."""
        if not self.cases:
            return {"escalate": 0.33, "deescalate": 0.33, "no_change": 0.34}

        similarities: List[float] = []
        case_outcomes: List[str] = []

        for case in self.cases:
            sim = self._similarity(scenario, case)
            similarities.append(sim)
            case_outcomes.append(case["outcome"])

        # Weighted voting
        weights = {"escalate": 0.0, "deescalate": 0.0, "no_change": 0.0}
        total_weight = sum(similarities)

        for sim, outcome in zip(similarities, case_outcomes):
            weights[outcome] += sim

        if total_weight > 0:
            for key in weights:
                weights[key] /= total_weight

        return weights

    def _similarity(self, scenario: Scenario, case: Dict[str, Any]) -> float:
        """Calculate similarity between scenario and case."""
        # Simple similarity based on rung level difference
        rung_diff = abs(scenario.current_rung - case["current_rung"])
        event_count_diff = abs(len(scenario.events) - len(case["events"]))

        sim = 1.0 / (1.0 + rung_diff * 0.3 + event_count_diff * 0.1)
        return sim

    def get_statistics(self) -> Dict[str, Any]:
        """Get case base statistics."""
        total = sum(self.outcomes.values())
        return {
            "total_cases": total,
            "outcomes": dict(self.outcomes),
            "escalation_rate": self.outcomes.get("escalate", 0) / max(total, 1),
        }


def assess_escalation_risk(
    events: List[EscalationEvent],
    ladder: EscalationLadder,
    reasoner: CaseBasedReasoner,
) -> Dict[str, Any]:
    """Assess escalation risk from a list of events."""
    current_rung = max((ladder.classify_event(e) for e in events), default=0)

    scenario = Scenario(events=events, current_rung=current_rung)
    prediction = reasoner.predict_outcome(scenario)

    severity = ladder.get_severity(current_rung)

    return {
        "current_rung": current_rung,
        "severity": severity,
        "prediction": prediction,
        "highest_rung_name": ladder.get_rung(current_rung).name if ladder.get_rung(current_rung) else "Unknown",
        "escalation_probability": prediction.get("escalate", 0),
    }
