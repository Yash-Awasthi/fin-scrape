"""SQLite registry of predictions and evaluations."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..run import _normalise_member

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "forecast" / "accuracy" / "predictions.db"
REPORTS_DIR = ROOT / "reports"

_HORIZON_RE = re.compile(r"^\s*(\d+)\s*([hdwm])\s*$", re.IGNORECASE)


def horizon_delta(h: str) -> timedelta | None:
    m = _HORIZON_RE.match(h)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    return {"h": timedelta(hours=n), "d": timedelta(days=n),
            "w": timedelta(weeks=n), "m": timedelta(days=30 * n)}.get(unit)


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    scenario TEXT NOT NULL,
    created_utc TEXT NOT NULL,
    meta_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
    pred_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    member TEXT NOT NULL,
    model TEXT NOT NULL,
    lineage TEXT NOT NULL,
    horizon TEXT NOT NULL,
    horizon_index INTEGER NOT NULL,
    horizon_target_utc TEXT NOT NULL,
    prediction_text TEXT NOT NULL,
    confidence REAL,
    change_factor TEXT,
    supporting_reasoning TEXT,
    UNIQUE(run_id, member, horizon, horizon_index)
);

CREATE TABLE IF NOT EXISTS evaluations (
    eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pred_id INTEGER NOT NULL UNIQUE REFERENCES predictions(pred_id),
    evaluated_utc TEXT NOT NULL,
    evaluator_model TEXT NOT NULL,
    verdict TEXT NOT NULL,                -- correct|mostly_correct|partial|mostly_wrong|wrong|undetermined
    score REAL,                           -- 0.0–1.0, NULL for undetermined
    rationale TEXT NOT NULL,
    evidence_json TEXT NOT NULL,          -- grounding snippets cited
    improvement_note TEXT
);

CREATE INDEX IF NOT EXISTS idx_pred_target ON predictions(horizon_target_utc);
CREATE INDEX IF NOT EXISTS idx_pred_model ON predictions(model);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _parse_created(meta: dict) -> datetime:
    s = meta.get("created", "").replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return datetime.now(timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _iter_member_predictions(member_data: dict, horizons: list[str]):
    forecasts = member_data.get("forecasts") or {}
    for horizon in horizons:
        preds = forecasts.get(horizon) or []
        for idx, p in enumerate(preds):
            if not isinstance(p, dict):
                continue
            yield horizon, idx, p


def ingest_run(run_dir: Path, conn: sqlite3.Connection) -> tuple[int, int]:
    """Ingest a single run directory. Returns (runs_added, predictions_added)."""
    meta_path = run_dir / "meta.json"
    members_dir = run_dir / "members"
    if not meta_path.exists() or not members_dir.exists():
        return (0, 0)
    meta = json.loads(meta_path.read_text())
    if meta.get("variant") == "osint-signals":
        return (0, 0)

    run_id = run_dir.name
    horizons = meta.get("horizons", [])
    created = _parse_created(meta)

    runs_added = conn.execute(
        "INSERT OR IGNORE INTO runs(run_id, scenario, created_utc, meta_json) VALUES (?,?,?,?)",
        (run_id, meta.get("scenario", ""), created.isoformat(), json.dumps(meta)),
    ).rowcount

    model_by_member = {m["name"]: m for m in meta.get("council_members", [])}

    preds_added = 0
    for mfile in sorted(members_dir.glob("*.json")):
        data = json.loads(mfile.read_text())
        if "_error" in data:
            continue
        data = _normalise_member(data, horizons)
        member = data.get("_member") or mfile.stem
        model = data.get("_model") or model_by_member.get(member, {}).get("model", "")
        lineage = data.get("_lineage") or model_by_member.get(member, {}).get("lineage", "")

        for horizon, idx, p in _iter_member_predictions(data, horizons):
            delta = horizon_delta(horizon)
            if not delta:
                continue
            target = (created + delta).isoformat()
            try:
                conf = float(p.get("confidence")) if p.get("confidence") is not None else None
            except (TypeError, ValueError):
                conf = None
            cur = conn.execute(
                """INSERT OR IGNORE INTO predictions
                   (run_id, member, model, lineage, horizon, horizon_index,
                    horizon_target_utc, prediction_text, confidence,
                    change_factor, supporting_reasoning)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (run_id, member, model, lineage, horizon, idx, target,
                 p.get("prediction", ""), conf,
                 p.get("change_factor"), p.get("supporting_reasoning")),
            )
            preds_added += cur.rowcount

    conn.commit()
    return (runs_added, preds_added)


def ingest_all(conn: sqlite3.Connection) -> tuple[int, int]:
    total_runs, total_preds = 0, 0
    if not REPORTS_DIR.exists():
        return (0, 0)
    for run_dir in sorted(REPORTS_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        r, p = ingest_run(run_dir, conn)
        total_runs += r
        total_preds += p
    return (total_runs, total_preds)


def due_predictions(conn: sqlite3.Connection, now: datetime | None = None) -> list[sqlite3.Row]:
    """Predictions whose horizon target has elapsed and which lack an evaluation."""
    now = now or datetime.now(timezone.utc)
    return conn.execute(
        """SELECT p.*, r.scenario, r.created_utc
           FROM predictions p
           JOIN runs r ON r.run_id = p.run_id
           LEFT JOIN evaluations e ON e.pred_id = p.pred_id
           WHERE e.pred_id IS NULL AND p.horizon_target_utc <= ?
           ORDER BY p.horizon_target_utc ASC""",
        (now.isoformat(),),
    ).fetchall()


def record_evaluation(conn: sqlite3.Connection, pred_id: int, evaluator_model: str,
                      verdict: str, score: float | None, rationale: str,
                      evidence: list[dict], improvement_note: str | None) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO evaluations
           (pred_id, evaluated_utc, evaluator_model, verdict, score,
            rationale, evidence_json, improvement_note)
           VALUES (?,?,?,?,?,?,?,?)""",
        (pred_id, datetime.now(timezone.utc).isoformat(), evaluator_model,
         verdict, score, rationale, json.dumps(evidence), improvement_note),
    )
    conn.commit()
