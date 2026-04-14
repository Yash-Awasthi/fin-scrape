"""
Historical signal accuracy tracking for FinScrape.

Compares pipeline verdicts (INVEST, PULL_OUT, OBSERVE, CAUTIOUS) against
actual subsequent price movements to measure prediction quality.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _project_root() -> Path:
    """Find project root by looking for main.py or .git."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "main.py").exists() or (parent / ".git").exists():
            return parent
    return current.parent


class AccuracyTracker:
    """Track whether pipeline verdicts were correct based on price movements."""

    # Price change thresholds for determining correctness
    CORRECT_THRESHOLD_PCT = 1.0  # >= 1% move in predicted direction = correct

    def __init__(self, data_dir: str | None = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = _project_root() / "data"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "finscrape.db"
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_tables()

    def _init_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS signal_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                verdict_at TEXT NOT NULL,
                signal_score INTEGER NOT NULL DEFAULT 0,
                confidence REAL NOT NULL DEFAULT 0.5,
                verdict TEXT NOT NULL,
                check_price_at TEXT,
                price_at_signal REAL NOT NULL,
                price_at_check REAL,
                price_change_pct REAL,
                outcome TEXT DEFAULT 'pending',
                checked_at TEXT,
                source TEXT DEFAULT '',
                event_type TEXT DEFAULT 'other'
            );
            CREATE INDEX IF NOT EXISTS idx_so_event_id ON signal_outcomes(event_id);
            CREATE INDEX IF NOT EXISTS idx_so_ticker ON signal_outcomes(ticker);
            CREATE INDEX IF NOT EXISTS idx_so_verdict ON signal_outcomes(verdict);
            CREATE INDEX IF NOT EXISTS idx_so_outcome ON signal_outcomes(outcome);
            CREATE INDEX IF NOT EXISTS idx_so_verdict_at ON signal_outcomes(verdict_at);

            CREATE TABLE IF NOT EXISTS accuracy_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL DEFAULT '',
                event_type TEXT NOT NULL DEFAULT 'other',
                verdict TEXT NOT NULL,
                total_signals INTEGER NOT NULL DEFAULT 0,
                correct_count INTEGER NOT NULL DEFAULT 0,
                accuracy_pct REAL NOT NULL DEFAULT 0.0,
                avg_confidence REAL NOT NULL DEFAULT 0.0,
                avg_price_move REAL NOT NULL DEFAULT 0.0,
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(source, event_type, verdict)
            );
        """)
        self._conn.commit()

    def record_signal(
        self,
        event_id: int,
        ticker: str,
        signal_score: int,
        confidence: float,
        verdict: str,
        price_at_signal: float,
        source: str = "",
        event_type: str = "other",
    ) -> int:
        """Record a signal when it is generated.

        Returns the ID of the inserted signal_outcomes row.
        """
        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            """INSERT INTO signal_outcomes
               (event_id, ticker, verdict_at, signal_score, confidence, verdict,
                price_at_signal, source, event_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, ticker.upper(), now, signal_score, confidence, verdict,
             price_at_signal, source, event_type),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_pending_signals(self, older_than_hours: float = 24) -> list[dict]:
        """Get signals that are pending and were recorded at least `older_than_hours` ago."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=older_than_hours)).isoformat()
        rows = self._conn.execute(
            """SELECT id, event_id, ticker, verdict_at, signal_score, confidence,
                      verdict, price_at_signal, source, event_type
               FROM signal_outcomes
               WHERE outcome = 'pending' AND verdict_at <= ?""",
            (cutoff,),
        ).fetchall()
        cols = ["id", "event_id", "ticker", "verdict_at", "signal_score", "confidence",
                "verdict", "price_at_signal", "source", "event_type"]
        return [dict(zip(cols, row)) for row in rows]

    def check_outcomes(self, hours_after: float = 24, price_fetcher=None) -> list[dict]:
        """Check outcomes for signals from `hours_after` hours ago.

        Uses `price_fetcher` to get current prices. If not provided, uses
        `finscrape.market_data.get_market_data`.

        Returns list of checked signal dicts with outcomes.
        """
        if price_fetcher is None:
            from finscrape.market_data import get_market_data
            price_fetcher = get_market_data

        pending = self.get_pending_signals(older_than_hours=hours_after)
        if not pending:
            logger.info("No pending signals older than %s hours to check.", hours_after)
            return []

        # Collect unique tickers
        tickers = list({s["ticker"] for s in pending})
        market_data = price_fetcher(tickers)
        price_map = {md["ticker"]: md["price"] for md in market_data}

        now = datetime.now(timezone.utc).isoformat()
        results = []

        for signal in pending:
            ticker = signal["ticker"]
            current_price = price_map.get(ticker)

            if current_price is None:
                logger.warning("No price data for %s, skipping signal %d", ticker, signal["id"])
                continue

            price_at_signal = signal["price_at_signal"]
            if price_at_signal <= 0:
                continue

            change_pct = ((current_price - price_at_signal) / price_at_signal) * 100
            outcome = self._determine_outcome(signal["verdict"], change_pct)

            self._conn.execute(
                """UPDATE signal_outcomes
                   SET check_price_at = ?, price_at_check = ?, price_change_pct = ?,
                       outcome = ?, checked_at = ?
                   WHERE id = ?""",
                (now, current_price, round(change_pct, 4), outcome, now, signal["id"]),
            )

            signal.update({
                "price_at_check": current_price,
                "price_change_pct": round(change_pct, 4),
                "outcome": outcome,
                "checked_at": now,
            })
            results.append(signal)

        self._conn.commit()
        logger.info("Checked %d signals: %s", len(results),
                     {r["outcome"] for r in results})
        return results

    def _determine_outcome(self, verdict: str, price_change_pct: float) -> str:
        """Determine if a verdict was correct based on actual price change.

        - INVEST correct if price went up >= 1%
        - PULL_OUT correct if price went down >= 1%
        - OBSERVE/CAUTIOUS are always 'neutral'
        """
        if verdict in ("OBSERVE", "CAUTIOUS"):
            return "neutral"

        if verdict == "INVEST":
            if price_change_pct >= self.CORRECT_THRESHOLD_PCT:
                return "correct"
            elif price_change_pct <= -self.CORRECT_THRESHOLD_PCT:
                return "incorrect"
            else:
                return "neutral"

        if verdict == "PULL_OUT":
            if price_change_pct <= -self.CORRECT_THRESHOLD_PCT:
                return "correct"
            elif price_change_pct >= self.CORRECT_THRESHOLD_PCT:
                return "incorrect"
            else:
                return "neutral"

        return "neutral"

    def update_accuracy_stats(self) -> None:
        """Recalculate per-source, per-event_type, per-verdict accuracy stats."""
        now = datetime.now(timezone.utc).isoformat()

        # Clear existing stats
        self._conn.execute("DELETE FROM accuracy_stats")

        # Aggregate from signal_outcomes where outcome is not pending
        rows = self._conn.execute(
            """SELECT source, event_type, verdict,
                      COUNT(*) as total,
                      SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
                      AVG(confidence) as avg_conf,
                      AVG(ABS(price_change_pct)) as avg_move
               FROM signal_outcomes
               WHERE outcome IN ('correct', 'incorrect', 'neutral')
               GROUP BY source, event_type, verdict"""
        ).fetchall()

        for source, event_type, verdict, total, correct, avg_conf, avg_move in rows:
            accuracy = (correct / total * 100) if total > 0 else 0.0
            self._conn.execute(
                """INSERT OR REPLACE INTO accuracy_stats
                   (source, event_type, verdict, total_signals, correct_count,
                    accuracy_pct, avg_confidence, avg_price_move, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (source, event_type, verdict, total, correct,
                 round(accuracy, 2), round(avg_conf or 0, 4), round(avg_move or 0, 4), now),
            )

        self._conn.commit()
        logger.info("Updated accuracy stats from %d groups.", len(rows))

    def get_accuracy_report(self) -> dict[str, Any]:
        """Generate a comprehensive accuracy report.

        Returns dict with:
        - overall_accuracy: overall correct rate for scored verdicts
        - per_verdict: accuracy breakdown per verdict
        - best_sources / worst_sources: ranked source accuracy
        - avg_confidence_when_correct / avg_confidence_when_incorrect
        """
        # Overall stats (only scored verdicts: INVEST, PULL_OUT)
        scored = self._conn.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
                      SUM(CASE WHEN outcome = 'incorrect' THEN 1 ELSE 0 END) as incorrect
               FROM signal_outcomes
               WHERE outcome IN ('correct', 'incorrect')"""
        ).fetchone()

        total_scored = scored[0] or 0
        correct_total = scored[1] or 0
        incorrect_total = scored[2] or 0
        overall_accuracy = (correct_total / total_scored * 100) if total_scored > 0 else 0.0

        # Per-verdict breakdown
        verdict_rows = self._conn.execute(
            """SELECT verdict,
                      COUNT(*) as total,
                      SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct
               FROM signal_outcomes
               WHERE outcome IN ('correct', 'incorrect')
               GROUP BY verdict"""
        ).fetchall()
        per_verdict = {}
        for verdict, total, correct in verdict_rows:
            per_verdict[verdict] = {
                "total": total,
                "correct": correct,
                "accuracy_pct": round(correct / total * 100, 2) if total > 0 else 0.0,
            }

        # Source accuracy
        source_rows = self._conn.execute(
            """SELECT source,
                      COUNT(*) as total,
                      SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct
               FROM signal_outcomes
               WHERE outcome IN ('correct', 'incorrect') AND source != ''
               GROUP BY source
               ORDER BY (CAST(SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) AS REAL) / COUNT(*)) DESC"""
        ).fetchall()
        best_sources = []
        worst_sources = []
        for source, total, correct in source_rows:
            entry = {
                "source": source,
                "total": total,
                "correct": correct,
                "accuracy_pct": round(correct / total * 100, 2) if total > 0 else 0.0,
            }
            best_sources.append(entry)
        worst_sources = list(reversed(best_sources))

        # Confidence analysis
        conf_correct = self._conn.execute(
            "SELECT AVG(confidence) FROM signal_outcomes WHERE outcome = 'correct'"
        ).fetchone()[0]
        conf_incorrect = self._conn.execute(
            "SELECT AVG(confidence) FROM signal_outcomes WHERE outcome = 'incorrect'"
        ).fetchone()[0]

        return {
            "overall_accuracy": round(overall_accuracy, 2),
            "total_scored": total_scored,
            "correct": correct_total,
            "incorrect": incorrect_total,
            "per_verdict": per_verdict,
            "best_sources": best_sources[:5],
            "worst_sources": worst_sources[:5],
            "avg_confidence_when_correct": round(conf_correct, 4) if conf_correct else None,
            "avg_confidence_when_incorrect": round(conf_incorrect, 4) if conf_incorrect else None,
        }

    def get_ticker_accuracy(self, ticker: str) -> dict[str, Any]:
        """Get accuracy stats for a specific ticker."""
        ticker = ticker.upper()
        rows = self._conn.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
                      SUM(CASE WHEN outcome = 'incorrect' THEN 1 ELSE 0 END) as incorrect,
                      SUM(CASE WHEN outcome = 'neutral' THEN 1 ELSE 0 END) as neutral,
                      AVG(price_change_pct) as avg_move,
                      AVG(confidence) as avg_conf
               FROM signal_outcomes
               WHERE ticker = ? AND outcome != 'pending'""",
            (ticker,),
        ).fetchone()

        total, correct, incorrect, neutral, avg_move, avg_conf = rows
        scored = (correct or 0) + (incorrect or 0)
        accuracy = (correct / scored * 100) if scored > 0 else 0.0

        # Per-verdict for this ticker
        verdict_rows = self._conn.execute(
            """SELECT verdict,
                      COUNT(*) as total,
                      SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct
               FROM signal_outcomes
               WHERE ticker = ? AND outcome IN ('correct', 'incorrect')
               GROUP BY verdict""",
            (ticker,),
        ).fetchall()
        per_verdict = {}
        for verdict, vtotal, vcorrect in verdict_rows:
            per_verdict[verdict] = {
                "total": vtotal,
                "correct": vcorrect,
                "accuracy_pct": round(vcorrect / vtotal * 100, 2) if vtotal > 0 else 0.0,
            }

        return {
            "ticker": ticker,
            "total_signals": total or 0,
            "scored": scored,
            "correct": correct or 0,
            "incorrect": incorrect or 0,
            "neutral": neutral or 0,
            "accuracy_pct": round(accuracy, 2),
            "avg_price_move": round(avg_move, 4) if avg_move is not None else None,
            "avg_confidence": round(avg_conf, 4) if avg_conf is not None else None,
            "per_verdict": per_verdict,
        }

    def get_source_accuracy(self, source: str) -> dict[str, Any]:
        """Get accuracy stats for a specific source."""
        rows = self._conn.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
                      SUM(CASE WHEN outcome = 'incorrect' THEN 1 ELSE 0 END) as incorrect,
                      SUM(CASE WHEN outcome = 'neutral' THEN 1 ELSE 0 END) as neutral,
                      AVG(price_change_pct) as avg_move,
                      AVG(confidence) as avg_conf
               FROM signal_outcomes
               WHERE source = ? AND outcome != 'pending'""",
            (source,),
        ).fetchone()

        total, correct, incorrect, neutral, avg_move, avg_conf = rows
        scored = (correct or 0) + (incorrect or 0)
        accuracy = (correct / scored * 100) if scored > 0 else 0.0

        # Per-verdict for this source
        verdict_rows = self._conn.execute(
            """SELECT verdict,
                      COUNT(*) as total,
                      SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct
               FROM signal_outcomes
               WHERE source = ? AND outcome IN ('correct', 'incorrect')
               GROUP BY verdict""",
            (source,),
        ).fetchall()
        per_verdict = {}
        for verdict, vtotal, vcorrect in verdict_rows:
            per_verdict[verdict] = {
                "total": vtotal,
                "correct": vcorrect,
                "accuracy_pct": round(vcorrect / vtotal * 100, 2) if vtotal > 0 else 0.0,
            }

        return {
            "source": source,
            "total_signals": total or 0,
            "scored": scored,
            "correct": correct or 0,
            "incorrect": incorrect or 0,
            "neutral": neutral or 0,
            "accuracy_pct": round(accuracy, 2),
            "avg_price_move": round(avg_move, 4) if avg_move is not None else None,
            "avg_confidence": round(avg_conf, 4) if avg_conf is not None else None,
            "per_verdict": per_verdict,
        }

    def close(self) -> None:
        self._conn.close()
