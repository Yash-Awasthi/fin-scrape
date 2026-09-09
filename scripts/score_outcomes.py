"""Score pending signal outcomes against the 5-day forward window.

Backfills `signal_outcomes` rows recorded before the monitor's automatic
outcome loop existed (or after any DB restore). Idempotent: `check_outcomes`
only ever touches rows still `pending`, so re-runs never double-score.

Usage:
    python scripts/score_outcomes.py [--hours N] [--verbose]

`--hours` overrides the maturity horizon (default: WINDOW_DAYS*24 = 120h).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finscrape.accuracy import AccuracyTracker  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=float, default=None,
                        help="maturity horizon in hours (default: WINDOW_DAYS*24)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    tracker = AccuracyTracker()
    results = tracker.check_outcomes(hours_after=args.hours)
    if not results:
        print("No pending signals with an elapsed window — nothing to score.")
    else:
        counts: dict[str, int] = {}
        for r in results:
            counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
            if args.verbose:
                symbol = {"correct": "+", "incorrect": "-", "neutral": "~"}.get(r["outcome"], "?")
                print(f"  [{symbol}] #{r['event_id']} {r['ticker']} {r['verdict']} "
                      f"-> {r['price_change_pct']:+.2f}% ({r['outcome']})")
        print(f"Scored {len(results)} signals: {counts}")

    tracker.update_accuracy_stats()
    total, scored = tracker._conn.execute(
        "SELECT COUNT(*), SUM(CASE WHEN outcome != 'pending' THEN 1 ELSE 0 END) "
        "FROM signal_outcomes"
    ).fetchone()
    print(f"signal_outcomes: {total} total, {scored} scored")
    return 0


if __name__ == "__main__":
    sys.exit(main())