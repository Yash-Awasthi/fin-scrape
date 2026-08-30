"""Debate Orchestrator.

Extracted from ai-colosseum-debate (inspiration).
Multi-agent debate management with SSE streaming, judge evaluation,
round management, and verdict generation.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RoundType(str, Enum):
    OPENING = "opening"
    REBUTTAL = "rebuttal"
    CLOSING = "closing"


class VerdictType(str, Enum):
    WINNER = "winner"
    DRAW = "draw"
    INCONCLUSIVE = "inconclusive"


class RunStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    DEBATING = "debating"
    JUDGING = "judging"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Agent:
    """Debate agent."""
    agent_id: str
    display_name: str
    system_prompt: str = ""
    stance: str = "neutral"  # "pro", "con", "neutral"


@dataclass
class Task:
    """Debate task/topic."""
    title: str
    description: str = ""
    context: str = ""


@dataclass
class DebateRound:
    """Single debate round."""
    round_id: int
    round_type: RoundType
    agent_id: str
    content: str
    timestamp: float = field(default_factory=time.time)
    tokens_used: int = 0


@dataclass
class JudgeVerdict:
    """Judge's verdict on a debate."""
    winner_id: Optional[str]
    verdict_type: VerdictType
    reasoning: str
    scores: dict = field(default_factory=dict)  # agent_id -> score
    confidence: float = 0.5


@dataclass
class DebateRun:
    """Complete debate run."""
    run_id: str
    task: Task
    agents: list[Agent]
    rounds: list[DebateRound] = field(default_factory=list)
    verdict: Optional[JudgeVerdict] = None
    status: RunStatus = RunStatus.PENDING
    created_at: float = field(default_factory=time.time)
    max_rounds: int = 3
    token_budget: int = 10000


# --- Round Management ---

def determine_round_type(
    current_round: int,
    max_rounds: int,
) -> RoundType:
    """Determine the type of round based on position.

    Args:
        current_round: Current round number (1-indexed)
        max_rounds: Maximum number of rounds

    Returns:
        Round type for this round
    """
    if current_round == 1:
        return RoundType.OPENING
    elif current_round == max_rounds:
        return RoundType.CLOSING
    else:
        return RoundType.REBUTTAL


def get_next_agent(
    agents: list[Agent],
    current_agent_id: str,
    round_type: RoundType,
) -> Agent:
    """Get the next agent to speak.

    In opening rounds, agents speak in order.
    In rebuttal rounds, agents speak in reverse order.
    In closing rounds, agents speak in order.

    Args:
        agents: List of debate agents
        current_agent_id: Current agent's ID
        round_type: Current round type

    Returns:
        Next agent to speak
    """
    if not agents:
        raise ValueError("No agents provided")

    current_idx = next(
        (i for i, a in enumerate(agents) if a.agent_id == current_agent_id),
        -1
    )

    if round_type == RoundType.REBUTTAL:
        next_idx = (current_idx - 1) % len(agents)
    else:
        next_idx = (current_idx + 1) % len(agents)

    return agents[next_idx]


def check_round_completion(
    rounds: list[DebateRound],
    agents: list[Agent],
    current_round: int,
) -> bool:
    """Check if all agents have spoken in the current round.

    Args:
        rounds: List of completed rounds
        agents: List of debate agents
        current_round: Current round number

    Returns:
        True if all agents have spoken
    """
    agents_in_round = [
        r.agent_id for r in rounds
        if r.round_id == current_round
    ]
    return len(agents_in_round) >= len(agents)


# --- Token Management ---

def calculate_tokens_used(rounds: list[DebateRound]) -> int:
    """Calculate total tokens used across all rounds.

    Args:
        rounds: List of completed rounds

    Returns:
        Total tokens used
    """
    return sum(r.tokens_used for r in rounds)


def check_token_budget(
    rounds: list[DebateRound],
    token_budget: int,
) -> bool:
    """Check if token budget is still available.

    Args:
        rounds: List of completed rounds
        token_budget: Maximum tokens allowed

    Returns:
        True if budget is available
    """
    return calculate_tokens_used(rounds) < token_budget


def estimate_remaining_budget(
    rounds: list[DebateRound],
    token_budget: int,
) -> int:
    """Estimate remaining token budget.

    Args:
        rounds: List of completed rounds
        token_budget: Maximum tokens allowed

    Returns:
        Remaining tokens
    """
    return max(0, token_budget - calculate_tokens_used(rounds))


# --- Judge Evaluation ---

def evaluate_argument_quality(
    argument: str,
    topic: str,
    stance: str,
) -> dict:
    """Evaluate the quality of a debate argument.

    Uses heuristic scoring based on argument characteristics.

    Args:
        argument: The debate argument text
        topic: The debate topic
        stance: The agent's stance (pro/con/neutral)

    Returns:
        Quality scores
    """
    word_count = len(argument.split())
    sentence_count = max(1, argument.count('.') + argument.count('!') + argument.count('?'))

    # Structure score (paragraphs, sentences)
    paragraphs = max(1, argument.count('\n\n') + 1)
    structure_score = min(1.0, (paragraphs * 0.3 + sentence_count * 0.1))

    # Length score (optimal 100-300 words)
    if word_count < 50:
        length_score = 0.3
    elif word_count < 100:
        length_score = 0.6
    elif word_count <= 300:
        length_score = 1.0
    elif word_count <= 500:
        length_score = 0.8
    else:
        length_score = 0.6

    # Relevance score (keyword matching)
    topic_words = set(topic.lower().split())
    arg_words = set(argument.lower().split())
    overlap = len(topic_words & arg_words)
    relevance_score = min(1.0, overlap / max(1, len(topic_words)) * 2)

    # Stance consistency (check if argument aligns with stance)
    stance_keywords = {
        "pro": ["agree", "support", "benefit", "advantage", "strength"],
        "con": ["disagree", "oppose", "risk", "weakness", "concern"],
        "neutral": ["consider", "aspect", "factor", "perspective"],
    }
    stance_words = set(stance_keywords.get(stance, []))
    stance_overlap = len(stance_words & arg_words)
    stance_score = min(1.0, stance_overlap * 0.3)

    overall = (
        structure_score * 0.2 +
        length_score * 0.2 +
        relevance_score * 0.4 +
        stance_score * 0.2
    )

    return {
        "overall": round(overall, 3),
        "structure": round(structure_score, 3),
        "length": round(length_score, 3),
        "relevance": round(relevance_score, 3),
        "stance_consistency": round(stance_score, 3),
        "word_count": word_count,
    }


def generate_verdict(
    rounds: list[DebateRound],
    agents: list[Agent],
    task: Task,
) -> JudgeVerdict:
    """Generate a verdict based on debate rounds.

    Args:
        rounds: All debate rounds
        agents: List of agents
        task: The debate task

    Returns:
        Judge verdict with winner and reasoning
    """
    if not rounds:
        return JudgeVerdict(
            winner_id=None,
            verdict_type=VerdictType.INCONCLUSIVE,
            reasoning="No rounds completed",
            confidence=0.0,
        )

    # Score each agent
    agent_scores = {}
    for agent in agents:
        agent_rounds = [r for r in rounds if r.agent_id == agent.agent_id]
        if not agent_rounds:
            agent_scores[agent.agent_id] = 0.0
            continue

        total_score = 0.0
        for r in agent_rounds:
            quality = evaluate_argument_quality(r.content, task.title, agent.stance)
            total_score += quality["overall"]

        agent_scores[agent.agent_id] = round(total_score / len(agent_rounds), 3)

    # Determine winner
    if not agent_scores:
        return JudgeVerdict(
            winner_id=None,
            verdict_type=VerdictType.INCONCLUSIVE,
            reasoning="No agents scored",
            confidence=0.0,
        )

    sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
    winner_id, winner_score = sorted_agents[0]

    if len(sorted_agents) > 1:
        runner_up_score = sorted_agents[1][1]
        margin = winner_score - runner_up_score
    else:
        margin = winner_score

    # Determine verdict type
    if margin < 0.1:
        verdict_type = VerdictType.DRAW
    elif winner_score < 0.3:
        verdict_type = VerdictType.INCONCLUSIVE
    else:
        verdict_type = VerdictType.WINNER

    # Generate reasoning
    if verdict_type == VerdictType.DRAW:
        reasoning = f"Debate was closely contested. {sorted_agents[0][0]} scored {winner_score:.2f}, {sorted_agents[1][0]} scored {sorted_agents[1][1]:.2f}."
    elif verdict_type == VerdictType.WINNER:
        reasoning = f"{winner_id} presented stronger arguments with a score of {winner_score:.2f}."
    else:
        reasoning = "Neither agent presented sufficiently compelling arguments."

    return JudgeVerdict(
        winner_id=winner_id if verdict_type == VerdictType.WINNER else None,
        verdict_type=verdict_type,
        reasoning=reasoning,
        scores=agent_scores,
        confidence=min(1.0, margin * 2 + 0.3),
    )


# --- Stream Events ---

def create_stream_event(
    event_type: str,
    data: dict,
) -> dict:
    """Create a stream event for SSE.

    Args:
        event_type: Type of event
        data: Event data

    Returns:
        Formatted stream event
    """
    return {
        "event": event_type,
        "data": data,
        "timestamp": time.time(),
    }


def create_round_complete_event(
    round: DebateRound,
    agent: Agent,
) -> dict:
    """Create a round complete event.

    Args:
        round: Completed debate round
        agent: Agent who spoke

    Returns:
        Stream event
    """
    return create_stream_event("round_complete", {
        "round_id": round.round_id,
        "round_type": round.round_type.value,
        "agent_id": agent.agent_id,
        "display_name": agent.display_name,
        "tokens_used": round.tokens_used,
    })


def create_verdict_event(
    verdict: JudgeVerdict,
) -> dict:
    """Create a verdict event.

    Args:
        verdict: Judge's verdict

    Returns:
        Stream event
    """
    return create_stream_event("verdict", {
        "winner_id": verdict.winner_id,
        "verdict_type": verdict.verdict_type.value,
        "reasoning": verdict.reasoning,
        "scores": verdict.scores,
        "confidence": verdict.confidence,
    })


# --- Budget Policy ---

def should_continue_debating(
    rounds: list[DebateRound],
    max_rounds: int,
    token_budget: int,
    min_quality_threshold: float = 0.7,
) -> tuple[bool, str]:
    """Determine if the debate should continue.

    Args:
        rounds: Completed rounds
        max_rounds: Maximum rounds allowed
        token_budget: Token budget
        min_quality_threshold: Minimum quality to continue

    Returns:
        Tuple of (should_continue, reason)
    """
    current_round = max((r.round_id for r in rounds), default=0)

    # Check round limit
    if current_round >= max_rounds:
        return False, f"Reached maximum rounds ({max_rounds})"

    # Check token budget
    if not check_token_budget(rounds, token_budget):
        remaining = estimate_remaining_budget(rounds, token_budget)
        return False, f"Token budget exhausted ({remaining} remaining)"

    # Check quality (if we have enough rounds)
    if len(rounds) >= 4:
        recent_scores = []
        for r in rounds[-2:]:
            quality = evaluate_argument_quality(r.content, "", "neutral")
            recent_scores.append(quality["overall"])

        avg_recent = sum(recent_scores) / len(recent_scores)
        if avg_recent < min_quality_threshold:
            return False, f"Quality below threshold ({avg_recent:.2f} < {min_quality_threshold})"

    return True, "Debate should continue"


# --- Run Management ---

def create_debate_run(
    run_id: str,
    task: Task,
    agents: list[Agent],
    max_rounds: int = 3,
    token_budget: int = 10000,
) -> DebateRun:
    """Create a new debate run.

    Args:
        run_id: Unique run identifier
        task: Debate task
        agents: List of agents
        max_rounds: Maximum rounds
        token_budget: Token budget

    Returns:
        New debate run
    """
    if len(agents) < 2:
        raise ValueError("At least 2 agents required for a debate")

    return DebateRun(
        run_id=run_id,
        task=task,
        agents=agents,
        status=RunStatus.PENDING,
        max_rounds=max_rounds,
        token_budget=token_budget,
    )


def start_debate(run: DebateRun) -> DebateRun:
    """Start a debate run.

    Args:
        run: Debate run to start

    Returns:
        Updated debate run
    """
    run.status = RunStatus.PLANNING
    return run


def advance_to_debating(run: DebateRun) -> DebateRun:
    """Advance run to debating phase.

    Args:
        run: Debate run

    Returns:
        Updated debate run
    """
    run.status = RunStatus.DEBATING
    return run


def complete_debate(
    run: DebateRun,
    verdict: JudgeVerdict,
) -> DebateRun:
    """Complete a debate run with a verdict.

    Args:
        run: Debate run
        verdict: Final verdict

    Returns:
        Completed debate run
    """
    run.verdict = verdict
    run.status = RunStatus.COMPLETED
    return run


def get_debate_summary(run: DebateRun) -> dict:
    """Get a summary of the debate run.

    Args:
        run: Debate run

    Returns:
        Debate summary
    """
    return {
        "run_id": run.run_id,
        "task": run.task.title,
        "agents": [
            {"id": a.agent_id, "name": a.display_name, "stance": a.stance}
            for a in run.agents
        ],
        "total_rounds": len(run.rounds),
        "total_tokens": calculate_tokens_used(run.rounds),
        "status": run.status.value,
        "verdict": {
            "winner": run.verdict.winner_id if run.verdict else None,
            "type": run.verdict.verdict_type.value if run.verdict else None,
            "reasoning": run.verdict.reasoning if run.verdict else None,
            "scores": run.verdict.scores if run.verdict else {},
        } if run.verdict else None,
        "duration_seconds": time.time() - run.created_at,
    }
