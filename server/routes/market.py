"""Live market-data routes: quotes + candles for every tracked exchange.

View-only market data served from the same global exchange layer the local
server uses (finscrape.exchanges). Network calls run in a threadpool so they
never block the event loop; failures degrade to empty/502, never crash.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/api/quotes")
async def quotes(symbols: str = Query(..., description="comma-separated Yahoo symbols")) -> dict:
    """Live quotes across all markets. Symbols carry their Yahoo suffix
    ('RELIANCE.NS', '600519.SS'); bare 6-digit codes infer China; bare = US."""
    from finscrape.exchanges import get_global_quotes

    wanted = []
    for raw in symbols.split(","):
        symbol = raw.strip().upper()
        if not symbol:
            continue
        if "." in symbol:
            wanted.append(("", symbol))  # suffix already carries the exchange
        elif len(symbol) == 6 and symbol.isdigit():
            code = "SSE" if symbol.startswith(("5", "6", "9")) else "SZSE"
            wanted.append((code, symbol))
        else:
            wanted.append(("", symbol))
    try:
        result = await asyncio.to_thread(get_global_quotes, wanted)
    except Exception:  # noqa: BLE001 — degrade to empty, never crash the panel
        result = {}
    return {"quotes": list(result.values())}


@router.get("/api/candles")
async def candles(
    symbol: str = Query(...),
    period: str = Query("1mo", pattern="^(1d|5d|1mo|3mo|6mo|1y|2y)$"),
    interval: str = Query("1d", pattern="^(5m|15m|1h|1d|1wk)$"),
) -> dict:
    """OHLCV candles for the chart panel (yfinance, threadpool)."""
    try:
        import yfinance as yf

        def _fetch() -> object:
            return yf.Ticker(symbol.strip().upper()).history(period=period, interval=interval)

        hist = await asyncio.to_thread(_fetch)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"candle fetch failed: {e}") from e

    if hist is None or hist.empty:
        raise HTTPException(status_code=404, detail=f"no data for {symbol}")
    return {
        "symbol": symbol.strip().upper(),
        "candles": [
            {
                "t": ts.isoformat(),
                "o": round(float(row["Open"]), 4),
                "h": round(float(row["High"]), 4),
                "l": round(float(row["Low"]), 4),
                "c": round(float(row["Close"]), 4),
                "v": int(row["Volume"]),
            }
            for ts, row in hist.iterrows()
        ],
    }
