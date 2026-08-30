"""
Monte Carlo Simulator — Extracted from Scenario Lab patterns.

Monte Carlo tree search for real-world event simulation:
- Market shock domain modeling
- Actor behavior profiles
- Phase-based simulation
- Branch scoring and ranking
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class Actor:
    name: str
    behavior_profile: Dict[str, float] = field(default_factory=dict)
    influence: float = 1.0
    risk_tolerance: float = 0.5


@dataclass
class SimulationState:
    phase: str
    actors: List[Actor]
    metrics: Dict[str, float] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    depth: int = 0
    score: float = 0.0


@dataclass
class SimulationNode:
    state: SimulationState
    action: Optional[str] = None
    parent: Optional['SimulationNode'] = None
    children: List['SimulationNode'] = field(default_factory=list)
    visits: int = 0
    total_score: float = 0.0

    @property
    def q_value(self) -> float:
        return self.total_score / max(self.visits, 1)

    def ucb1(self, exploration: float = 1.414) -> float:
        if self.visits == 0:
            return float('inf')
        return self.q_value + exploration * math.sqrt(math.log(max(self.parent.visits, 1)) / self.visits)


@dataclass
class DomainPack:
    name: str
    phases: List[str]
    actions: List[str]
    metrics_schema: Dict[str, str] = field(default_factory=dict)

    def validate(self, state: SimulationState) -> List[str]:
        return []

    def suggest_actors(self) -> List[str]:
        return []

    def score_branch(self, state: SimulationState) -> float:
        return 0.0


class MarketShockDomain(DomainPack):
    """Market shock domain pack."""

    def __init__(self) -> None:
        super().__init__(
            name="market-shock",
            phases=["trigger", "repricing", "policy-response", "liquidity-stabilization", "resolution"],
            actions=[
                "rate_cut", "rate_hike", "liquidity_injection",
                "forward_guidance", "emergency_meeting", "do_nothing",
            ],
            metrics_schema={
                "contagion_risk": "float",
                "liquidity_stress": "float",
                "policy_credibility": "float",
                "rate_pressure": "float",
            },
        )

    def score_branch(self, state: SimulationState) -> float:
        metrics = state.metrics
        risk = metrics.get("contagion_risk", 0.5)
        liquidity = metrics.get("liquidity_stress", 0.5)
        credibility = metrics.get("policy_credibility", 0.5)

        # Lower risk and stress, higher credibility = better
        return (1 - risk) * 0.4 + (1 - liquidity) * 0.3 + credibility * 0.3


class MonteCarloSimulator:
    """Monte Carlo tree search simulator."""

    def __init__(
        self,
        domain: DomainPack,
        iterations: int = 100,
        max_depth: int = 5,
        c_puct: float = 1.414,
    ) -> None:
        self.domain = domain
        self.iterations = iterations
        self.max_depth = max_depth
        self.c_puct = c_puct

    def simulate(self, initial_state: SimulationState) -> List[Dict[str, Any]]:
        """Run MCTS and return ranked branches."""
        root = SimulationNode(state=initial_state)

        for _ in range(self.iterations):
            node = self._select(root)
            if node.state.depth < self.max_depth:
                children = self._expand(node)
                if children:
                    leaf = random.choice(children)
                    score = self._rollout(leaf)
                    self._backpropagate(leaf, score)
                else:
                    score = self._rollout(node)
                    self._backpropagate(node, score)
            else:
                score = self._rollout(node)
                self._backpropagate(node, score)

        # Rank children by Q-value
        branches = []
        for child in root.children:
            branches.append({
                "action": child.action,
                "score": child.q_value,
                "visits": child.visits,
                "phase": child.state.phase,
                "metrics": child.state.metrics,
            })

        branches.sort(key=lambda b: b["score"], reverse=True)
        return branches

    def _select(self, node: SimulationNode) -> SimulationNode:
        """Select leaf node using UCB1."""
        while node.children:
            node = max(node.children, key=lambda n: n.ucb1(self.c_puct))
        return node

    def _expand(self, node: SimulationNode) -> List[SimulationNode]:
        """Expand node with possible actions."""
        children = []
        for action in self.domain.actions:
            new_state = self._apply_action(node.state, action)
            child = SimulationNode(
                state=new_state,
                action=action,
                parent=node,
            )
            children.append(child)
            node.children.append(child)
        return children

    def _rollout(self, node: SimulationNode) -> float:
        """Simulate from node to terminal state."""
        state = node.state
        for _ in range(self.max_depth - state.depth):
            action = random.choice(self.domain.actions)
            state = self._apply_action(state, action)
        return self.domain.score_branch(state)

    def _backpropagate(self, node: SimulationNode, score: float) -> None:
        """Backpropagate score up the tree."""
        current = node
        while current:
            current.visits += 1
            current.total_score += score
            current = current.parent

    def _apply_action(self, state: SimulationState, action: str) -> SimulationState:
        """Apply action and transition to next phase."""
        new_metrics = dict(state.metrics)

        # Simple metric updates based on action
        if action == "rate_cut":
            new_metrics["rate_pressure"] = max(0, new_metrics.get("rate_pressure", 0.5) - 0.2)
            new_metrics["liquidity_stress"] = max(0, new_metrics.get("liquidity_stress", 0.5) - 0.1)
        elif action == "liquidity_injection":
            new_metrics["liquidity_stress"] = max(0, new_metrics.get("liquidity_stress", 0.5) - 0.3)
            new_metrics["contagion_risk"] = max(0, new_metrics.get("contagion_risk", 0.5) - 0.1)
        elif action == "do_nothing":
            new_metrics["contagion_risk"] = min(1, new_metrics.get("contagion_risk", 0.5) + 0.1)

        # Advance phase
        phase_idx = self.domain.phases.index(state.phase) if state.phase in self.domain.phases else 0
        next_phase = self.domain.phases[min(phase_idx + 1, len(self.domain.phases) - 1)]

        return SimulationState(
            phase=next_phase,
            actors=list(state.actors),
            metrics=new_metrics,
            depth=state.depth + 1,
        )
