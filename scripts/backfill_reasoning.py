"""Backfill LLM reasoning into events stored without it (heuristic-era rows).

Runs the configured AI provider (dev mode → local Ollama qwen) over each
event's subject/tickers/verdict and persists the reasoning into SQLite, so
the dashboard's signal feed and modals show analysis for everything.

Usage:
    python scripts/backfill_reasoning.py [--limit N]
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finscrape.analysis.ai_client import call_ai  # noqa: E402
from finscrape.devmode import apply_to_env  # noqa: E402

PROMPT = (
    "Headline: {subject}\n"
    "Verdict: {verdict} (signal {score:+d}, confidence {confidence:.0%})\n"
    "Tickers: {tickers}\n\n"
    "Respond as JSON with keys: \"relevant\" (true) and \"reasoning\" "
    "(1-2 concrete sentences on why this news moves these tickers this way)."
)

SYSTEM = "You are a geopolitical market analyst. Answer in strict JSON only."


def main() -> int:
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 100
    apply_to_env()  # dev-mode provider → env, same wiring main.py uses
    conn = sqlite3.connect(ROOT / "data" / "finscrape.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, subject, verdict, signal_score, confidence, tickers FROM events "
        "WHERE reasoning IS NULL OR reasoning = '' ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    print(f"backfilling reasoning for {len(rows)} events")

    done = failed = 0
    for row in rows:
        try:
            tickers = json.loads(row["tickers"]) if row["tickers"] else []
        except ValueError:
            tickers = []
        result = call_ai(
            PROMPT.format(
                subject=row["subject"], verdict=row["verdict"],
                score=row["signal_score"], confidence=row["confidence"] or 0,
                tickers=", ".join(tickers) or "none",
            ),
            SYSTEM,
        )
        reasoning = (result or {}).get("reasoning") or (result or {}).get("summary") or ""
        if reasoning:
            conn.execute(
                "UPDATE events SET reasoning = ? WHERE id = ?", (reasoning, row["id"])
            )
            conn.commit()
            done += 1
            print(f"  [{done}] #{row['id']} {row['subject'][:50]}")
        else:
            failed += 1
            print(f"  [SKIP] #{row['id']} {row['subject'][:50]} (no AI response)")
            time.sleep(1)

    print(f"done: {done} enriched, {failed} skipped")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
