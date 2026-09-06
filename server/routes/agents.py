"""Multi-agent analysis route — VIEW-BASED intelligence only.

Runs the analyst-council pipeline (finscrape.trading.pipeline) on demand for a
ticker. The result is research commentary (decision + reasoning); nothing is
executed — no orders, no accounts, no broker connections.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/api/agents/analyze")
async def agents_analyze(
    ticker: str = Query(...),
    analysts: str = Query("market,news", description="comma-separated analyst set"),
    debate_rounds: int = Query(1, ge=1, le=3),
) -> dict:
    from finscrape.trading.pipeline import run_analysis

    def _run() -> dict:
        return run_analysis(
            ticker=ticker.strip().upper(),
            debate_rounds=debate_rounds,
            selected_analysts=tuple(a.strip() for a in analysts.split(",") if a.strip()),
            save_reports=False,
        )

    # Local models can take minutes; run the blocking pipeline in a thread.
    result = await asyncio.to_thread(_run)
    return {
        "ticker": result["ticker"],
        "trade_date": result["trade_date"],
        "signal": result["signal"],
        "decision": result["decision"],
        "duration_seconds": result["duration_seconds"],
        "errors": result.get("errors", []),
    }
