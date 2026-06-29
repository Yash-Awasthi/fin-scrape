"""GET /api/accuracy — hit-rate, by-verdict, equity curve from accuracy_outcomes (Phase 7)."""

from __future__ import annotations

from fastapi import APIRouter

from server import db
from server.accuracy import aggregate

router = APIRouter()


@router.get("/api/accuracy")
async def accuracy() -> dict:
    rows = await db.pool().fetch(
        "SELECT verdict, correct, checked_at FROM accuracy_outcomes ORDER BY checked_at"
    )
    return aggregate(
        [
            {
                "verdict": r["verdict"],
                "correct": r["correct"],
                "checked_at": r["checked_at"].isoformat() if r["checked_at"] else "",
            }
            for r in rows
        ]
    )
