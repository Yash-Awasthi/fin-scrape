"""Portfolio + watchlist routes (Phase 13) — thin wrappers over finscrape PortfolioManager.

Storage is the existing SQLite-backed PortfolioManager at `<data_dir>/portfolio.db`
(check_same_thread=False, so the single API process can touch it from the event loop;
calls are local + fast). A module-level singleton keeps one connection.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException

from finscrape.portfolio import PortfolioManager
from server.auth import require_api_key
from server.settings import get_settings

router = APIRouter()

_pm: PortfolioManager | None = None


def _portfolio() -> PortfolioManager:
    global _pm
    if _pm is None:
        data_dir = Path(get_settings().data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        _pm = PortfolioManager(db_path=data_dir / "portfolio.db")
    return _pm


@router.get("/api/portfolio")
async def get_portfolio() -> dict:
    pm = _portfolio()
    return {
        "positions": [p.to_dict() for p in pm.get_all_positions()],
        "watchlists": [w.to_dict() for w in pm.get_all_watchlists()],
        "summary": pm.summary(),
    }


@router.post("/api/portfolio/position", dependencies=[Depends(require_api_key)])
async def add_position(payload: dict = Body(...)) -> dict:
    ticker = str(payload.get("ticker", "")).upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker required")
    try:
        shares = float(payload.get("shares", 0))
        avg_cost = float(payload.get("avg_cost", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="shares/avg_cost must be numbers")
    _portfolio().add_position(ticker, shares, avg_cost)
    return {"ok": True, "ticker": ticker}


@router.delete("/api/portfolio/position", dependencies=[Depends(require_api_key)])
async def remove_position(ticker: str) -> dict:
    removed = _portfolio().remove_position(ticker.upper().strip())
    return {"ok": removed, "ticker": ticker.upper().strip()}


@router.post("/api/portfolio/watchlist", dependencies=[Depends(require_api_key)])
async def upsert_watchlist(payload: dict = Body(...)) -> dict:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    tickers = [str(t).upper().strip() for t in (payload.get("tickers") or []) if t]
    pm = _portfolio()
    if pm.get_watchlist(name) is None:
        pm.create_watchlist(name, tickers)
    elif tickers:
        pm.add_to_watchlist(name, tickers)
    wl = pm.get_watchlist(name)
    return {"ok": True, "watchlist": wl.to_dict() if wl else None}


@router.delete("/api/portfolio/watchlist", dependencies=[Depends(require_api_key)])
async def delete_watchlist(name: str) -> dict:
    return {"ok": _portfolio().delete_watchlist(name.strip()), "name": name.strip()}
