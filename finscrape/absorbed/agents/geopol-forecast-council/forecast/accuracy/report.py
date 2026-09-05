"""Aggregate evaluated predictions into per-model / per-lineage accuracy reports."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent.parent
LEADERBOARD_PATH = ROOT / "reports" / "ACCURACY.md"


def _rows_for_rollup(conn: sqlite3.Connection, where: str = "", params: tuple = ()) -> list[sqlite3.Row]:
    sql = f"""
        SELECT p.run_id, p.member, p.model, p.lineage, p.horizon,
               p.confidence, p.prediction_text,
               e.verdict, e.score, e.rationale, e.improvement_note,
               p.horizon_target_utc
        FROM predictions p
        JOIN evaluations e ON e.pred_id = p.pred_id
        {where}
    """
    return conn.execute(sql, params).fetchall()


def _rollup(rows: list[sqlite3.Row], key: str) -> list[dict]:
    """Aggregate by a grouping key (e.g. 'model', 'lineage', 'horizon')."""
    buckets: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        buckets.setdefault(r[key], []).append(r)

    out = []
    for k, rs in buckets.items():
        scored = [r for r in rs if r["score"] is not None]
        if not scored:
            continue
        scores = [r["score"] for r in scored]
        conf_deltas = [r["score"] - (r["confidence"] or 0.0)
                       for r in scored if r["confidence"] is not None]
        brier = mean([(r["score"] - (r["confidence"] or 0.0)) ** 2
                      for r in scored if r["confidence"] is not None]) if conf_deltas else None
        verdict_counts: dict[str, int] = {}
        for r in rs:
            verdict_counts[r["verdict"]] = verdict_counts.get(r["verdict"], 0) + 1
        out.append({
            key: k,
            "n": len(rs),
            "n_scored": len(scored),
            "mean_score": round(mean(scores), 3),
            "mean_confidence": round(mean([r["confidence"] for r in scored
                                           if r["confidence"] is not None] or [0.0]), 3),
            "calibration_delta": round(mean(conf_deltas), 3) if conf_deltas else None,
            "brier": round(brier, 4) if brier is not None else None,
            "verdicts": verdict_counts,
        })
    out.sort(key=lambda x: x["mean_score"], reverse=True)
    return out


def _fmt_pct(x: float) -> str:
    return f"{x*100:.1f}%"


def _table(rows: list[dict], key: str, label: str) -> str:
    if not rows:
        return f"_No evaluated predictions yet._\n"
    L = [f"| {label} | N | Mean score | Mean conf | Calibration Δ | Brier | Correct | Partial | Wrong |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        v = r["verdicts"]
        correct = v.get("correct", 0) + v.get("mostly_correct", 0)
        partial = v.get("partial", 0)
        wrong = v.get("wrong", 0) + v.get("mostly_wrong", 0)
        cal = f"{r['calibration_delta']:+.3f}" if r["calibration_delta"] is not None else "—"
        brier = f"{r['brier']}" if r["brier"] is not None else "—"
        L.append(f"| {r[key]} | {r['n']} | {_fmt_pct(r['mean_score'])} | "
                 f"{_fmt_pct(r['mean_confidence'])} | {cal} | {brier} | "
                 f"{correct} | {partial} | {wrong} |")
    return "\n".join(L) + "\n"


def _improvement_themes(rows: list[sqlite3.Row], max_items: int = 20) -> list[dict]:
    notes = []
    for r in rows:
        if r["score"] is not None and r["score"] < 0.5 and r["improvement_note"]:
            notes.append({
                "model": r["model"], "horizon": r["horizon"],
                "verdict": r["verdict"], "score": r["score"],
                "prediction": r["prediction_text"][:200],
                "note": r["improvement_note"],
            })
    notes.sort(key=lambda x: x["score"])
    return notes[:max_items]


def generate_leaderboard(conn: sqlite3.Connection) -> Path:
    rows = _rows_for_rollup(conn)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    n_runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    n_preds = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    n_evals = conn.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]

    L = [
        "# Council accuracy leaderboard",
        "",
        f"_Generated {now}. Runs: {n_runs}. Predictions recorded: {n_preds}. "
        f"Predictions evaluated: {n_evals}._",
        "",
        "Scores follow a 5-point ordinal rubric: `correct=1.0`, `mostly_correct=0.75`, "
        "`partial=0.5`, `mostly_wrong=0.25`, `wrong=0.0`. "
        "`Calibration Δ` is mean(score − confidence); negative means over-confident. "
        "`Brier` is mean squared error between confidence and realised score (lower is better).",
        "",
        "## By model",
        "",
        _table(_rollup(rows, "model"), "model", "Model"),
        "## By lineage",
        "",
        _table(_rollup(rows, "lineage"), "lineage", "Lineage"),
        "## By horizon",
        "",
        _table(_rollup(rows, "horizon"), "horizon", "Horizon"),
        "## Improvement themes (worst-scoring predictions with notes)",
        "",
    ]

    themes = _improvement_themes(rows)
    if themes:
        for t in themes:
            L.append(f"- **{t['model']}** · `{t['horizon']}` · "
                     f"{t['verdict']} ({t['score']}): {t['note']}")
            L.append(f"  > {t['prediction']}")
    else:
        L.append("_No low-scoring predictions with improvement notes yet._")

    L.append("")
    L.append("---")
    L.append("")
    L.append("Suggestions in this report are advisory. Prompt edits to "
            "`prompts/council_member.md` are human-gated — review the themes "
            "above and apply changes manually.")

    LEADERBOARD_PATH.write_text("\n".join(L))
    return LEADERBOARD_PATH


def generate_per_run_report(conn: sqlite3.Connection, run_id: str) -> Path | None:
    rows = _rows_for_rollup(conn, "WHERE p.run_id = ?", (run_id,))
    if not rows:
        return None
    run = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    out = ROOT / "reports" / run_id / "accuracy.md"

    L = [
        f"# Accuracy review — {run_id}",
        "",
        f"Scenario: {run['scenario']}",
        f"Run created: {run['created_utc']}",
        f"Evaluations: {len(rows)}",
        "",
        "## By model (this run)",
        "",
        _table(_rollup(rows, "model"), "model", "Model"),
        "## Predictions",
        "",
    ]
    for r in rows:
        cal = ""
        if r["confidence"] is not None and r["score"] is not None:
            cal = f" · conf {r['confidence']} → score {r['score']} (Δ {r['score']-r['confidence']:+.2f})"
        L.append(f"### [{r['horizon']}] {r['member']} — **{r['verdict']}**{cal}")
        L.append("")
        L.append(f"> {r['prediction_text']}")
        L.append("")
        L.append(f"**Evaluator rationale:** {r['rationale']}")
        if r["improvement_note"]:
            L.append("")
            L.append(f"**Improvement note:** {r['improvement_note']}")
        L.append("")

    out.write_text("\n".join(L))
    return out
