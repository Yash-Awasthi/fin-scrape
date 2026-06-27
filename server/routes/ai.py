"""On-demand AI expansion: GET /api/ai/analyze?id= (cache → LLM → merge tickers)."""

from __future__ import annotations

import asyncio
import hashlib

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from server import db, queries
from server.ai import analyze_event
from server.settings import get_settings
from server.ws import hub

router = APIRouter()


@router.get("/api/ai/analyze")
async def analyze(id: int = Query(...)) -> dict:
    pool = db.pool()
    cache_key = hashlib.sha256(f"{get_settings().ai_model}:{id}".encode()).hexdigest()

    cached = await queries.get_ai_cache(pool, cache_key)
    if cached:
        return cached

    event = await queries.get_event_by_id(pool, id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    result = await asyncio.to_thread(analyze_event, event)
    merged = await queries.save_ai_cache(pool, cache_key, id, result)
    # If AI discovered new tickers, tell live clients to refresh.
    if len(merged) > len(event.get("tickers") or []):
        await hub.broadcast(
            jsonable_encoder(
                {"type": "ai_updated", "stats": await queries.get_stats(pool)}
            )
        )
    return result
