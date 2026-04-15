"""Tests for finscrape.accuracy.AccuracyTracker."""

import pytest
import sqlite3
from datetime import datetime, timezone, timedelta

from finscrape.accuracy import AccuracyTracker


@pytest.fixture()
def tracker(tmp_path):
    """Create an AccuracyTracker backed by a temporary directory."""
    t = AccuracyTracker(data_dir=str(tmp_path))
    yield t
    t.close()


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------

class TestTableCreation:
    def test_db_file_exists(self, tracker, tmp_path):
        assert (tmp_path / "finscrape.db").exists()

    def test_tables_exist(self, tracker):
        tables = {
            row[0]
            for row in tracker._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "signal_outcomes" in tables
        assert "accuracy_stats" in tables


# ---------------------------------------------------------------------------
# Recording signals
# ---------------------------------------------------------------------------

class TestRecordSignal:
    def test_record_returns_id(self, tracker):
        sid = tracker.record_signal(
            event_id=1, ticker="AAPL", signal_score=4,
            confidence=0.85, verdict="INVEST", price_at_signal=150.0,
        )
        assert isinstance(sid, int)
        assert sid >= 1

    def test_record_stores_data(self, tracker):
        tracker.record_signal(
            event_id=42, ticker="tsla", signal_score=-3,
            confidence=0.9, verdict="PULL_OUT", price_at_signal=200.0,
            source="bloomberg", event_type="earnings",
        )
        row = tracker._conn.execute(
            "SELECT event_id, ticker, signal_score, confidence, verdict, "
            "price_at_signal, source, event_type, outcome FROM signal_outcomes"
        ).fetchone()
        assert row[0] == 42
        assert row[1] == "TSLA"  # uppercased
        assert row[2] == -3
        assert row[3] == 0.9
        assert row[4] == "PULL_OUT"
        assert row[5] == 200.0
        assert row[6] == "bloomberg"
        assert row[7] == "earnings"
        assert row[8] == "pending"

    def test_record_multiple_signals(self, tracker):
        for i in range(5):
            tracker.record_signal(
                event_id=i, ticker="AAPL", signal_score=3,
                confidence=0.8, verdict="INVEST", price_at_signal=150.0 + i,
            )
        count = tracker._conn.execute("SELECT COUNT(*) FROM signal_outcomes").fetchone()[0]
        assert count == 5


# ---------------------------------------------------------------------------
# Outcome determination
# ---------------------------------------------------------------------------

class TestDetermineOutcome:
    def test_invest_correct_price_up(self, tracker):
        assert tracker._determine_outcome("INVEST", 2.5) == "correct"

    def test_invest_incorrect_price_down(self, tracker):
        assert tracker._determine_outcome("INVEST", -2.5) == "incorrect"

    def test_invest_neutral_small_move(self, tracker):
        assert tracker._determine_outcome("INVEST", 0.5) == "neutral"
        assert tracker._determine_outcome("INVEST", -0.3) == "neutral"

    def test_pullout_correct_price_down(self, tracker):
        assert tracker._determine_outcome("PULL_OUT", -3.0) == "correct"

    def test_pullout_incorrect_price_up(self, tracker):
        assert tracker._determine_outcome("PULL_OUT", 3.0) == "incorrect"

    def test_pullout_neutral_small_move(self, tracker):
        assert tracker._determine_outcome("PULL_OUT", -0.5) == "neutral"

    def test_observe_always_neutral(self, tracker):
        assert tracker._determine_outcome("OBSERVE", 10.0) == "neutral"
        assert tracker._determine_outcome("OBSERVE", -10.0) == "neutral"

    def test_cautious_always_neutral(self, tracker):
        assert tracker._determine_outcome("CAUTIOUS", 5.0) == "neutral"
        assert tracker._determine_outcome("CAUTIOUS", -5.0) == "neutral"

    def test_threshold_boundary(self, tracker):
        # Exactly 1% should be correct for INVEST
        assert tracker._determine_outcome("INVEST", 1.0) == "correct"
        # Just below should be neutral
        assert tracker._determine_outcome("INVEST", 0.99) == "neutral"
        # Exactly -1% should be correct for PULL_OUT
        assert tracker._determine_outcome("PULL_OUT", -1.0) == "correct"


# ---------------------------------------------------------------------------
# Check outcomes with mock prices
# ---------------------------------------------------------------------------

def _make_mock_price_fetcher(prices: dict):
    """Create a mock price fetcher that returns fixed prices."""
    def fetcher(tickers):
        return [{"ticker": t, "price": prices[t]} for t in tickers if t in prices]
    return fetcher


class TestCheckOutcomes:
    def _insert_old_signal(self, tracker, event_id, ticker, verdict, price,
                           hours_ago=25, source="", event_type="other",
                           signal_score=3, confidence=0.8):
        """Insert a signal with a past verdict_at timestamp."""
        past = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
        tracker._conn.execute(
            """INSERT INTO signal_outcomes
               (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                price_at_signal, source, event_type, outcome)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (event_id, ticker, past, signal_score, confidence, verdict, price,
             source, event_type),
        )
        tracker._conn.commit()

    def test_invest_correct(self, tracker):
        self._insert_old_signal(tracker, 1, "AAPL", "INVEST", 150.0)
        # Price went up 3.3%
        results = tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({"AAPL": 155.0}),
        )
        assert len(results) == 1
        assert results[0]["outcome"] == "correct"
        assert results[0]["price_change_pct"] == pytest.approx(3.3333, rel=0.01)

    def test_invest_incorrect(self, tracker):
        self._insert_old_signal(tracker, 1, "AAPL", "INVEST", 150.0)
        results = tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({"AAPL": 145.0}),
        )
        assert len(results) == 1
        assert results[0]["outcome"] == "incorrect"

    def test_pullout_correct(self, tracker):
        self._insert_old_signal(tracker, 1, "TSLA", "PULL_OUT", 200.0)
        results = tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({"TSLA": 190.0}),
        )
        assert len(results) == 1
        assert results[0]["outcome"] == "correct"

    def test_pullout_incorrect(self, tracker):
        self._insert_old_signal(tracker, 1, "TSLA", "PULL_OUT", 200.0)
        results = tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({"TSLA": 210.0}),
        )
        assert len(results) == 1
        assert results[0]["outcome"] == "incorrect"

    def test_observe_neutral(self, tracker):
        self._insert_old_signal(tracker, 1, "GOOG", "OBSERVE", 100.0)
        results = tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({"GOOG": 120.0}),
        )
        assert len(results) == 1
        assert results[0]["outcome"] == "neutral"

    def test_no_pending_signals(self, tracker):
        results = tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({}),
        )
        assert results == []

    def test_signal_too_recent_not_checked(self, tracker):
        """Signals less than hours_after old should not be checked."""
        self._insert_old_signal(tracker, 1, "AAPL", "INVEST", 150.0, hours_ago=2)
        results = tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({"AAPL": 155.0}),
        )
        assert results == []

    def test_missing_price_data_skipped(self, tracker):
        self._insert_old_signal(tracker, 1, "AAPL", "INVEST", 150.0)
        # Price fetcher returns nothing for AAPL
        results = tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({}),
        )
        assert results == []
        # Signal should still be pending
        row = tracker._conn.execute(
            "SELECT outcome FROM signal_outcomes WHERE event_id = 1"
        ).fetchone()
        assert row[0] == "pending"

    def test_multiple_tickers_checked(self, tracker):
        self._insert_old_signal(tracker, 1, "AAPL", "INVEST", 150.0)
        self._insert_old_signal(tracker, 2, "TSLA", "PULL_OUT", 200.0)
        self._insert_old_signal(tracker, 3, "GOOG", "OBSERVE", 100.0)
        results = tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({
                "AAPL": 160.0,
                "TSLA": 180.0,
                "GOOG": 105.0,
            }),
        )
        assert len(results) == 3
        outcomes = {r["ticker"]: r["outcome"] for r in results}
        assert outcomes["AAPL"] == "correct"
        assert outcomes["TSLA"] == "correct"
        assert outcomes["GOOG"] == "neutral"

    def test_already_checked_not_rechecked(self, tracker):
        """Signals already checked (not pending) should not be rechecked."""
        self._insert_old_signal(tracker, 1, "AAPL", "INVEST", 150.0)
        # Check once
        tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({"AAPL": 155.0}),
        )
        # Check again: should return nothing
        results = tracker.check_outcomes(
            hours_after=24,
            price_fetcher=_make_mock_price_fetcher({"AAPL": 140.0}),
        )
        assert results == []

    def test_custom_hours_lookback(self, tracker):
        self._insert_old_signal(tracker, 1, "AAPL", "INVEST", 150.0, hours_ago=50)
        # 24h lookback: should find it
        results = tracker.check_outcomes(
            hours_after=48,
            price_fetcher=_make_mock_price_fetcher({"AAPL": 155.0}),
        )
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Accuracy stats
# ---------------------------------------------------------------------------

class TestAccuracyStats:
    def _populate_outcomes(self, tracker):
        """Insert pre-checked outcomes directly."""
        now = datetime.now(timezone.utc).isoformat()
        past = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        signals = [
            # event_id, ticker, verdict, price_at_signal, price_at_check, change_pct, outcome, source, event_type
            (1, "AAPL", "INVEST", 150.0, 155.0, 3.33, "correct", "yahoo", "earnings", 0.9),
            (2, "AAPL", "INVEST", 150.0, 145.0, -3.33, "incorrect", "yahoo", "earnings", 0.7),
            (3, "TSLA", "PULL_OUT", 200.0, 190.0, -5.0, "correct", "bloomberg", "guidance", 0.85),
            (4, "TSLA", "PULL_OUT", 200.0, 210.0, 5.0, "incorrect", "bloomberg", "guidance", 0.6),
            (5, "GOOG", "OBSERVE", 100.0, 102.0, 2.0, "neutral", "reuters", "other", 0.5),
            (6, "MSFT", "INVEST", 300.0, 310.0, 3.33, "correct", "yahoo", "product_launch", 0.95),
        ]
        for eid, ticker, verdict, p1, p2, chg, outcome, source, etype, conf in signals:
            tracker._conn.execute(
                """INSERT INTO signal_outcomes
                   (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                    price_at_signal, price_at_check, price_change_pct, outcome,
                    checked_at, source, event_type)
                   VALUES (?, ?, ?, 3, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (eid, ticker, past, conf, verdict, p1, p2, chg, outcome, now, source, etype),
            )
        tracker._conn.commit()

    def test_update_accuracy_stats(self, tracker):
        self._populate_outcomes(tracker)
        tracker.update_accuracy_stats()
        rows = tracker._conn.execute("SELECT COUNT(*) FROM accuracy_stats").fetchone()
        assert rows[0] > 0

    def test_get_accuracy_report(self, tracker):
        self._populate_outcomes(tracker)
        report = tracker.get_accuracy_report()
        assert "overall_accuracy" in report
        assert "per_verdict" in report
        assert "best_sources" in report
        assert "worst_sources" in report
        # 3 correct out of 5 scored (excluding neutral OBSERVE) = 60%
        # INVEST: 2 correct + 1 incorrect = 3; PULL_OUT: 1 correct + 1 incorrect = 2
        assert report["total_scored"] == 5
        assert report["correct"] == 3
        assert report["incorrect"] == 2
        assert report["overall_accuracy"] == 60.0

    def test_get_accuracy_report_per_verdict(self, tracker):
        self._populate_outcomes(tracker)
        report = tracker.get_accuracy_report()
        assert "INVEST" in report["per_verdict"]
        assert "PULL_OUT" in report["per_verdict"]
        # INVEST: 2 correct out of 3 scored = 66.67%
        assert report["per_verdict"]["INVEST"]["total"] == 3
        assert report["per_verdict"]["INVEST"]["correct"] == 2
        # PULL_OUT: 1 correct out of 1 scored... wait, 1 correct, 1 incorrect
        assert report["per_verdict"]["PULL_OUT"]["total"] == 2
        assert report["per_verdict"]["PULL_OUT"]["correct"] == 1

    def test_confidence_when_correct_vs_incorrect(self, tracker):
        self._populate_outcomes(tracker)
        report = tracker.get_accuracy_report()
        # Correct: 0.9, 0.85, 0.95 -> avg 0.9
        assert report["avg_confidence_when_correct"] == pytest.approx(0.9, rel=0.01)
        # Incorrect: 0.7, 0.6 -> avg 0.65
        assert report["avg_confidence_when_incorrect"] == pytest.approx(0.65, rel=0.01)

    def test_source_accuracy_in_report(self, tracker):
        self._populate_outcomes(tracker)
        report = tracker.get_accuracy_report()
        sources = {s["source"]: s for s in report["best_sources"]}
        assert "yahoo" in sources
        assert "bloomberg" in sources

    def test_empty_report(self, tracker):
        """Report with no signals should return zero values."""
        report = tracker.get_accuracy_report()
        assert report["overall_accuracy"] == 0.0
        assert report["total_scored"] == 0
        assert report["per_verdict"] == {}
        assert report["best_sources"] == []

    def test_all_correct(self, tracker):
        now = datetime.now(timezone.utc).isoformat()
        past = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        for i in range(3):
            tracker._conn.execute(
                """INSERT INTO signal_outcomes
                   (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                    price_at_signal, price_at_check, price_change_pct, outcome,
                    checked_at, source, event_type)
                   VALUES (?, 'AAPL', ?, 3, 0.9, 'INVEST', 150.0, 155.0, 3.33, 'correct', ?, 'yahoo', 'earnings')""",
                (i, past, now),
            )
        tracker._conn.commit()
        report = tracker.get_accuracy_report()
        assert report["overall_accuracy"] == 100.0
        assert report["correct"] == 3
        assert report["incorrect"] == 0

    def test_all_incorrect(self, tracker):
        now = datetime.now(timezone.utc).isoformat()
        past = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        for i in range(3):
            tracker._conn.execute(
                """INSERT INTO signal_outcomes
                   (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                    price_at_signal, price_at_check, price_change_pct, outcome,
                    checked_at, source, event_type)
                   VALUES (?, 'AAPL', ?, 3, 0.5, 'INVEST', 150.0, 140.0, -6.67, 'incorrect', ?, 'yahoo', 'earnings')""",
                (i, past, now),
            )
        tracker._conn.commit()
        report = tracker.get_accuracy_report()
        assert report["overall_accuracy"] == 0.0
        assert report["correct"] == 0
        assert report["incorrect"] == 3


# ---------------------------------------------------------------------------
# Ticker accuracy
# ---------------------------------------------------------------------------

class TestTickerAccuracy:
    def test_get_ticker_accuracy(self, tracker):
        now = datetime.now(timezone.utc).isoformat()
        past = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        # 2 correct, 1 incorrect for AAPL
        for outcome, conf in [("correct", 0.9), ("correct", 0.8), ("incorrect", 0.6)]:
            tracker._conn.execute(
                """INSERT INTO signal_outcomes
                   (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                    price_at_signal, price_at_check, price_change_pct, outcome,
                    checked_at, source, event_type)
                   VALUES (1, 'AAPL', ?, 3, ?, 'INVEST', 150.0, 155.0, 3.0, ?, ?, '', 'other')""",
                (past, conf, outcome, now),
            )
        tracker._conn.commit()

        result = tracker.get_ticker_accuracy("AAPL")
        assert result["ticker"] == "AAPL"
        assert result["total_signals"] == 3
        assert result["scored"] == 3
        assert result["correct"] == 2
        assert result["incorrect"] == 1
        assert result["accuracy_pct"] == pytest.approx(66.67, rel=0.01)

    def test_ticker_accuracy_empty(self, tracker):
        result = tracker.get_ticker_accuracy("AAPL")
        assert result["total_signals"] == 0
        assert result["accuracy_pct"] == 0.0

    def test_ticker_case_insensitive(self, tracker):
        now = datetime.now(timezone.utc).isoformat()
        past = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        tracker._conn.execute(
            """INSERT INTO signal_outcomes
               (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                price_at_signal, price_at_check, price_change_pct, outcome,
                checked_at, source, event_type)
               VALUES (1, 'AAPL', ?, 3, 0.8, 'INVEST', 150.0, 155.0, 3.0, 'correct', ?, '', 'other')""",
            (past, now),
        )
        tracker._conn.commit()
        # Query with lowercase
        result = tracker.get_ticker_accuracy("aapl")
        assert result["ticker"] == "AAPL"
        assert result["total_signals"] == 1


# ---------------------------------------------------------------------------
# Source accuracy
# ---------------------------------------------------------------------------

class TestSourceAccuracy:
    def test_get_source_accuracy(self, tracker):
        now = datetime.now(timezone.utc).isoformat()
        past = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        for outcome in ["correct", "correct", "incorrect"]:
            tracker._conn.execute(
                """INSERT INTO signal_outcomes
                   (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                    price_at_signal, price_at_check, price_change_pct, outcome,
                    checked_at, source, event_type)
                   VALUES (1, 'AAPL', ?, 3, 0.8, 'INVEST', 150.0, 155.0, 3.0, ?, ?, 'yahoo', 'other')""",
                (past, outcome, now),
            )
        tracker._conn.commit()

        result = tracker.get_source_accuracy("yahoo")
        assert result["source"] == "yahoo"
        assert result["total_signals"] == 3
        assert result["correct"] == 2
        assert result["incorrect"] == 1
        assert result["accuracy_pct"] == pytest.approx(66.67, rel=0.01)

    def test_source_accuracy_empty(self, tracker):
        result = tracker.get_source_accuracy("nonexistent")
        assert result["total_signals"] == 0
        assert result["accuracy_pct"] == 0.0


# ---------------------------------------------------------------------------
# Pending signals query
# ---------------------------------------------------------------------------

class TestPendingSignals:
    def test_get_pending_signals(self, tracker):
        past = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        tracker._conn.execute(
            """INSERT INTO signal_outcomes
               (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                price_at_signal, outcome, source, event_type)
               VALUES (1, 'AAPL', ?, 3, 0.8, 'INVEST', 150.0, 'pending', 'yahoo', 'other')""",
            (past,),
        )
        tracker._conn.commit()

        pending = tracker.get_pending_signals(older_than_hours=24)
        assert len(pending) == 1
        assert pending[0]["ticker"] == "AAPL"

    def test_recent_signal_not_pending(self, tracker):
        recent = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        tracker._conn.execute(
            """INSERT INTO signal_outcomes
               (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                price_at_signal, outcome, source, event_type)
               VALUES (1, 'AAPL', ?, 3, 0.8, 'INVEST', 150.0, 'pending', '', 'other')""",
            (recent,),
        )
        tracker._conn.commit()

        pending = tracker.get_pending_signals(older_than_hours=24)
        assert len(pending) == 0
