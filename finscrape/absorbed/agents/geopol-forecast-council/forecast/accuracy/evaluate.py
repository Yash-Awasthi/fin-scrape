"""Evaluate due predictions against fresh grounding."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..grounding import format_grounding_block, run_grounding
from ..openrouter import call_json
from .db import record_evaluation

ROOT = Path(__file__).resolve().parent.parent.parent
EVALUATOR_PROMPT = (ROOT / "prompts/accuracy_evaluator.md").read_text()

DEFAULT_EVALUATOR = "google/gemini-3-flash-preview"

VERDICT_SCORES = {
    "correct": 1.0, "mostly_correct": 0.75, "partial": 0.5,
    "mostly_wrong": 0.25, "wrong": 0.0, "undetermined": None,
}

VERDICT_SCHEMA = {
    "name": "verdict",
    "schema": {
        "type": "object",
        "required": ["verdict", "rationale", "evidence"],
        "properties": {
            "verdict": {"type": "string", "enum": list(VERDICT_SCORES.keys())},
            "score": {"type": ["number", "null"]},
            "rationale": {"type": "string"},
            "evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"source": {"type": "string"}, "snippet": {"type": "string"}},
                    "required": ["source", "snippet"],
                },
            },
            "improvement_note": {"type": ["string", "null"]},
        },
    },
}


def _evaluator_user_msg(row: sqlite3.Row, grounding_block: str, now_iso: str) -> str:
    return (
        f"# Prediction under evaluation\n\n"
        f"- Made at: {row['created_utc']}\n"
        f"- Horizon: {row['horizon']}\n"
        f"- Horizon target (should have resolved by): {row['horizon_target_utc']}\n"
        f"- Evaluation time (now): {now_iso}\n"
        f"- Source model: {row['model']} ({row['lineage']})\n"
        f"- Stated confidence: {row['confidence']}\n\n"
        f"## Prediction text\n\n{row['prediction_text']}\n\n"
        f"## Supporting reasoning (original)\n\n{row['supporting_reasoning'] or '(none)'}\n\n"
        f"## Scenario context\n\n{row['scenario']}\n\n"
        f"## Fresh grounding pack (gathered now)\n\n{grounding_block}\n"
    )


def _scenario_query(row: sqlite3.Row) -> str:
    """Build a focused grounding query from the prediction + scenario."""
    return f"{row['scenario']}\n\nSpecific claim to verify:\n{row['prediction_text']}"


def evaluate_due(conn: sqlite3.Connection, rows: list[sqlite3.Row],
                 evaluator_model: str = DEFAULT_EVALUATOR,
                 grounding_tools: list[str] | None = None,
                 rss_feeds: list[str] | None = None,
                 verbose: bool = True) -> dict:
    """Evaluate a batch of due predictions. Groundings are cached per prediction
    (each prediction gets its own scoped grounding, since claims differ)."""
    grounding_tools = grounding_tools or ["sonar", "tavily"]
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stats = {"evaluated": 0, "failed": 0, "by_verdict": {}}

    for row in rows:
        pred_id = row["pred_id"]
        label = f"pred#{pred_id} [{row['member']} · {row['horizon']}]"
        if verbose:
            print(f"[eval] {label} — grounding…")

        try:
            grounding = run_grounding(_scenario_query(row), grounding_tools,
                                      rss_feeds=rss_feeds or [])
            grounding_block = format_grounding_block(grounding)

            result = call_json(
                evaluator_model, EVALUATOR_PROMPT,
                _evaluator_user_msg(row, grounding_block, now_iso),
                temperature=0.1, response_schema=VERDICT_SCHEMA,
            )
            verdict = result.get("verdict", "undetermined")
            score = result.get("score")
            if score is None and verdict in VERDICT_SCORES:
                score = VERDICT_SCORES[verdict]

            record_evaluation(
                conn, pred_id, evaluator_model, verdict,
                score if verdict != "undetermined" else None,
                result.get("rationale", ""),
                result.get("evidence", []),
                result.get("improvement_note"),
            )
            stats["evaluated"] += 1
            stats["by_verdict"][verdict] = stats["by_verdict"].get(verdict, 0) + 1
            if verbose:
                print(f"         → {verdict} (score={score})")
        except Exception as e:
            stats["failed"] += 1
            if verbose:
                print(f"         ! failed: {e}")

    return stats
