"""
Tests for grounded lessons read-back: AccuracyTracker.get_lessons() and the
judge's LESSONS block. Debators never see lessons — only the judge prompt
does, and only when the accuracy DB actually has scored history.

All AI calls are mocked — no network, no real LLM.
"""

from __future__ import annotations

import sys
import types
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from finscrape.accuracy import AccuracyTracker

# Same ai_client stubbing trick as tests/test_judge.py and tests/test_agents.py:
# fake out finscrape.analysis.ai_client before importing finscrape.agents.judge
# so the import chain stays offline (no requests/dotenv).
_ai_client_mod = types.ModuleType("finscrape.analysis.ai_client")
_ai_client_mod.call_ai = MagicMock(return_value=None)
sys.modules["finscrape.analysis.ai_client"] = _ai_client_mod

import finscrape.analysis.constants  # noqa: F401
from finscrape.agents.base import AgentVerdict
from finscrape.agents.judge import format_lessons_block, judge_debate

del sys.modules["finscrape.analysis.ai_client"]


@pytest.fixture()
def tracker(tmp_path):
    """AccuracyTracker backed by a temporary directory, matching tests/test_accuracy.py."""
    t = AccuracyTracker(data_dir=str(tmp_path))
    yield t
    t.close()


def _seed_aapl_invest_calls(tracker, n_incorrect: int = 4, n_correct: int = 1, source: str = "yahoo"):
    """Seed n_incorrect + n_correct scored INVEST rows on AAPL, already checked."""
    now = datetime.now(UTC)
    outcomes = ["incorrect"] * n_incorrect + ["correct"] * n_correct
    for i, outcome in enumerate(outcomes):
        verdict_at = (now - timedelta(hours=30 + i)).isoformat()
        pct = -3.5 if outcome == "incorrect" else 4.0
        price_at_check = 150.0 * (1 + pct / 100)
        tracker._conn.execute(
            """INSERT INTO signal_outcomes
               (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                price_at_signal, price_at_check, price_change_pct, outcome,
                checked_at, source, event_type)
               VALUES (?, 'AAPL', ?, 3, 0.8, 'INVEST', 150.0, ?, ?, ?, ?, ?, 'earnings')""",
            (i, verdict_at, price_at_check, pct, outcome, now.isoformat(), source),
        )
    tracker._conn.commit()


def _dummy_verdicts() -> list[AgentVerdict]:
    return [
        AgentVerdict(agent_name="analyst", verdict="INVEST", signal_score=3, confidence=0.8,
                     reasoning="Strong quarter."),
        AgentVerdict(agent_name="risk", verdict="CAUTIOUS", signal_score=-1, confidence=0.6,
                     reasoning="Margin pressure."),
    ]


def _dummy_stats() -> dict:
    return {"consensus_score_raw": 1.0, "agreement_level": 0.5, "dissenting_agents": []}


# ---------------------------------------------------------------------------
# AccuracyTracker.get_lessons()
# ---------------------------------------------------------------------------

class TestGetLessons:
    def test_reports_hit_rate_and_wrong_calls(self, tracker):
        _seed_aapl_invest_calls(tracker)
        lessons = tracker.get_lessons(["AAPL"])

        aapl = lessons["tickers"]["AAPL"]
        assert aapl["total"] == 5
        assert aapl["correct"] == 1
        assert aapl["hit_rate_pct"] == 20.0

        wrong = lessons["wrong_calls"]
        assert len(wrong) == 4
        assert all(w["ticker"] == "AAPL" and w["verdict"] == "INVEST" for w in wrong)
        assert all(w["price_change_pct"] < 0 for w in wrong)

    def test_source_hit_rate_reported(self, tracker):
        _seed_aapl_invest_calls(tracker, source="yahoo")
        lessons = tracker.get_lessons(["AAPL"])
        assert lessons["sources"]["yahoo"]["total"] == 5

    def test_empty_db_returns_empty(self, tracker):
        assert tracker.get_lessons(["AAPL"]) == {}

    def test_wrong_calls_capped_at_limit(self, tracker):
        _seed_aapl_invest_calls(tracker, n_incorrect=7, n_correct=1)
        lessons = tracker.get_lessons(["AAPL"], limit=3)
        assert len(lessons["wrong_calls"]) == 3


# ---------------------------------------------------------------------------
# LESSONS block in the judge prompt only
# ---------------------------------------------------------------------------

class TestJudgeLessonsBlock:
    def test_lessons_injected_into_judge_prompt(self, tracker):
        _seed_aapl_invest_calls(tracker)
        lessons = tracker.get_lessons(["AAPL"])

        mock_call = MagicMock(return_value={
            "verdict": "CAUTIOUS", "signal_score": 0, "confidence": 0.5, "rationale": "r",
        })
        with patch("finscrape.agents.judge.call_ai", mock_call):
            judge_debate(_dummy_verdicts(), _dummy_stats(), lessons=lessons)

        prompt = mock_call.call_args[0][0]
        assert "LESSONS" in prompt
        assert "AAPL" in prompt
        assert "20" in prompt  # 20.0% hit rate

    def test_empty_db_no_lessons_block_in_judge_prompt(self, tracker):
        """Fresh empty DB -> get_lessons() returns empty and the judge prompt
        carries no LESSONS block at all — cold start is not a behavior change."""
        lessons = tracker.get_lessons(["AAPL"])
        assert lessons == {}
        assert format_lessons_block(lessons) == ""

        mock_call = MagicMock(return_value={
            "verdict": "CAUTIOUS", "signal_score": 0, "confidence": 0.5, "rationale": "r",
        })
        with patch("finscrape.agents.judge.call_ai", mock_call):
            judge_debate(_dummy_verdicts(), _dummy_stats(), lessons=lessons)

        prompt = mock_call.call_args[0][0]
        assert "LESSONS" not in prompt

    def test_no_lessons_arg_is_byte_identical_to_empty_lessons(self, tracker):
        """Old call sites that never pass `lessons` must see the exact same prompt
        as one passed an explicitly empty dict — zero regression for existing callers."""
        mock_call = MagicMock(return_value={
            "verdict": "CAUTIOUS", "signal_score": 0, "confidence": 0.5, "rationale": "r",
        })
        with patch("finscrape.agents.judge.call_ai", mock_call):
            judge_debate(_dummy_verdicts(), _dummy_stats())
            no_lessons_prompt = mock_call.call_args[0][0]

            judge_debate(_dummy_verdicts(), _dummy_stats(), lessons={})
            empty_lessons_prompt = mock_call.call_args[0][0]

        assert no_lessons_prompt == empty_lessons_prompt
