"""Tests for debate orchestrator service."""

import pytest
from finscrape.services.debate_orchestrator import (
    Agent,
    DebateRound,
    DebateRun,
    JudgeVerdict,
    RunStatus,
    RoundType,
    Task,
    VerdictType,
    advance_to_debating,
    calculate_tokens_used,
    check_round_completion,
    check_token_budget,
    complete_debate,
    create_debate_run,
    create_round_complete_event,
    create_stream_event,
    create_verdict_event,
    determine_round_type,
    evaluate_argument_quality,
    estimate_remaining_budget,
    generate_verdict,
    get_debate_summary,
    get_next_agent,
    should_continue_debating,
    start_debate,
)


@pytest.fixture
def sample_agents():
    return [
        Agent("a1", "Alice", stance="pro"),
        Agent("a2", "Bob", stance="con"),
    ]


@pytest.fixture
def sample_task():
    return Task("AI Safety", "Should AI development be regulated?")


@pytest.fixture
def sample_rounds():
    return [
        DebateRound(1, RoundType.OPENING, "a1", "AI regulation is essential for safety.", tokens_used=50),
        DebateRound(1, RoundType.OPENING, "a2", "AI regulation stifles innovation.", tokens_used=45),
    ]


class TestRoundType:
    def test_opening(self):
        assert determine_round_type(1, 3) == RoundType.OPENING

    def test_closing(self):
        assert determine_round_type(3, 3) == RoundType.CLOSING

    def test_rebuttal(self):
        assert determine_round_type(2, 3) == RoundType.REBUTTAL


class TestGetNextAgent:
    def test_forward(self, sample_agents):
        result = get_next_agent(sample_agents, "a1", RoundType.OPENING)
        assert result.agent_id == "a2"

    def test_reverse(self, sample_agents):
        result = get_next_agent(sample_agents, "a2", RoundType.REBUTTAL)
        assert result.agent_id == "a1"

    def test_wrap_around(self, sample_agents):
        result = get_next_agent(sample_agents, "a2", RoundType.OPENING)
        assert result.agent_id == "a1"


class TestRoundCompletion:
    def test_incomplete(self, sample_agents):
        rounds = [DebateRound(1, RoundType.OPENING, "a1", "test")]
        assert not check_round_completion(rounds, sample_agents, 1)

    def test_complete(self, sample_agents, sample_rounds):
        assert check_round_completion(sample_rounds, sample_agents, 1)


class TestTokenManagement:
    def test_calculate_tokens(self, sample_rounds):
        assert calculate_tokens_used(sample_rounds) == 95

    def test_check_budget_available(self, sample_rounds):
        assert check_token_budget(sample_rounds, 1000)

    def test_check_budget_exhausted(self, sample_rounds):
        assert not check_token_budget(sample_rounds, 50)

    def test_estimate_remaining(self, sample_rounds):
        assert estimate_remaining_budget(sample_rounds, 100) == 5


class TestArgumentQuality:
    def test_quality_scores(self):
        result = evaluate_argument_quality(
            "AI regulation is important. It helps ensure safety.",
            "AI Safety",
            "pro",
        )
        assert 0 <= result["overall"] <= 1
        assert "structure" in result
        assert "relevance" in result

    def test_empty_argument(self):
        result = evaluate_argument_quality("", "topic", "neutral")
        assert result["word_count"] == 0


class TestVerdict:
    def test_generate_verdict_with_rounds(self, sample_rounds, sample_agents, sample_task):
        verdict = generate_verdict(sample_rounds, sample_agents, sample_task)
        assert verdict.verdict_type in [VerdictType.WINNER, VerdictType.DRAW, VerdictType.INCONCLUSIVE]
        assert verdict.scores

    def test_generate_verdict_no_rounds(self, sample_agents, sample_task):
        verdict = generate_verdict([], sample_agents, sample_task)
        assert verdict.verdict_type == VerdictType.INCONCLUSIVE


class TestStreamEvents:
    def test_create_event(self):
        event = create_stream_event("test", {"key": "value"})
        assert event["event"] == "test"
        assert event["data"]["key"] == "value"
        assert "timestamp" in event

    def test_round_complete_event(self):
        round = DebateRound(1, RoundType.OPENING, "a1", "content")
        agent = Agent("a1", "Alice")
        event = create_round_complete_event(round, agent)
        assert event["event"] == "round_complete"
        assert event["data"]["agent_id"] == "a1"

    def test_verdict_event(self):
        verdict = JudgeVerdict("a1", VerdictType.WINNER, "Good argument")
        event = create_verdict_event(verdict)
        assert event["event"] == "verdict"
        assert event["data"]["winner_id"] == "a1"


class TestBudgetPolicy:
    def test_continue_at_start(self, sample_rounds):
        should, reason = should_continue_debating(sample_rounds, 3, 10000)
        assert should

    def test_stop_at_max_rounds(self, sample_rounds):
        should, reason = should_continue_debating(sample_rounds, 1, 10000)
        assert not should
        assert "maximum rounds" in reason

    def test_stop_at_token_limit(self, sample_rounds):
        should, reason = should_continue_debating(sample_rounds, 3, 50)
        assert not should
        assert "budget" in reason


class TestRunManagement:
    def test_create_run(self, sample_task, sample_agents):
        run = create_debate_run("r1", sample_task, sample_agents)
        assert run.run_id == "r1"
        assert run.status == RunStatus.PENDING

    def test_create_run_insufficient_agents(self, sample_task):
        with pytest.raises(ValueError):
            create_debate_run("r1", sample_task, [Agent("a1", "Solo")])

    def test_lifecycle(self, sample_task, sample_agents):
        run = create_debate_run("r1", sample_task, sample_agents)
        run = start_debate(run)
        assert run.status == RunStatus.PLANNING

        run = advance_to_debating(run)
        assert run.status == RunStatus.DEBATING

        verdict = JudgeVerdict("a1", VerdictType.WINNER, "Better args")
        run = complete_debate(run, verdict)
        assert run.status == RunStatus.COMPLETED
        assert run.verdict.winner_id == "a1"


class TestSummary:
    def test_summary(self, sample_task, sample_agents, sample_rounds):
        run = create_debate_run("r1", sample_task, sample_agents)
        run.rounds = sample_rounds
        run = complete_debate(run, JudgeVerdict("a1", VerdictType.WINNER, "Better"))

        summary = get_debate_summary(run)
        assert summary["run_id"] == "r1"
        assert summary["total_rounds"] == 2
        assert summary["verdict"]["winner"] == "a1"
