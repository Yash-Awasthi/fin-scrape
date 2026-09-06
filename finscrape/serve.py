"""WorldFin local server — the whole product on localhost, no Postgres.

Serves the built SPA (web/dist) and the same /api contract the production
server exposes, backed by SQLite (data/finscrape.db) and the live global
quotes layer (finscrape.exchanges). See docs/FRONTEND_DESIGN.md.

Run:
    python main.py serve --port 8080
    → http://localhost:8080
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from finscrape.exchanges import get_global_quotes

app = FastAPI(title="WorldFin Local", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

_ROOT = Path(__file__).resolve().parent.parent
_DB = _ROOT / "data" / "finscrape.db"
_DIST = _ROOT / "web" / "dist"


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _require_db() -> sqlite3.Connection:
    if not _DB.exists():
        raise HTTPException(status_code=503, detail="no local DB yet — run: main.py scrape")
    return _db()


# ── quotes (the live market feed) ────────────────────────────────────────────


@app.get("/api/quotes")
async def quotes(symbols: str = Query(..., description="comma-separated Yahoo symbols")) -> dict:
    """Live quotes for the given symbols. Symbols carry their Yahoo suffix
    ('RELIANCE.NS', '600519.SS'); bare 6-digit codes are inferred as China
    A-shares; other bare symbols are treated as US."""
    wanted = []
    for raw in symbols.split(","):
        symbol = raw.strip().upper()
        if not symbol:
            continue
        if "." in symbol:
            # already suffixed — exchanges.resolve_symbol passes it through,
            # and China suffixes still route to the native adapters
            wanted.append(("", symbol))
        elif re.fullmatch(r"[045689]\d{5}", symbol):
            # bare 6-digit → China A-share (SSE: 6/5/9, SZSE: 0/3, BSE-share of 4/8 → SZSE bucket)
            code = "SSE" if symbol.startswith(("5", "6", "9")) else "SZSE"
            wanted.append((code, symbol))
        else:
            wanted.append(("", symbol))
    quotes = get_global_quotes(wanted)
    return {"quotes": list(quotes.values()), "as_of": None}


# ── events / stats / suggestions (SQLite) ────────────────────────────────────


@app.get("/api/events")
async def events(limit: int = Query(200, ge=1, le=500)) -> dict:
    conn = _require_db()
    rows = conn.execute(
        "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return {"events": [_event_row(r) for r in rows]}


# Coarse keyword → coordinates for globe bars (city/region-level precision is a
# production-geocoder concern; this makes the local globe meaningful).
_GEO_KEYWORDS: list[tuple[str, float, float]] = [
    ("ukraine", 48.4, 31.2), ("russia", 55.8, 37.6), ("moscow", 55.8, 37.6),
    ("kyiv", 50.5, 30.5), ("israel", 31.8, 35.2), ("gaza", 31.5, 34.5),
    ("iran", 35.7, 51.4), ("tehran", 35.7, 51.4), ("iraq", 33.3, 44.4),
    ("taiwan", 25.0, 121.5), ("china", 39.9, 116.4), ("beijing", 39.9, 116.4),
    ("japan", 35.7, 139.7), ("tokyo", 35.7, 139.7), ("korea", 37.6, 127.0),
    ("india", 28.6, 77.2), ("delhi", 28.6, 77.2), ("mumbai", 19.1, 72.9),
    ("pakistan", 33.7, 73.1), ("afghanistan", 34.5, 69.2),
    ("germany", 52.5, 13.4), ("berlin", 52.5, 13.4), ("france", 48.9, 2.35),
    ("paris", 48.9, 2.35), ("london", 51.5, -0.13), ("britain", 51.5, -0.13),
    ("uk ", 51.5, -0.13), ("europe", 50.1, 8.7), ("brussels", 50.9, 4.4),
    ("italy", 41.9, 12.5), ("rome", 41.9, 12.5), ("spain", 40.4, -3.7),
    ("switzerland", 46.9, 7.4), ("netherlands", 52.4, 4.9),
    ("brazil", -15.8, -47.9), ("mexico", 19.4, -99.1), ("canada", 45.4, -75.7),
    ("ottawa", 45.4, -75.7), ("washington", 38.9, -77.0), ("u.s.", 38.9, -77.0),
    ("united states", 38.9, -77.0), ("white house", 38.9, -77.0),
    ("new york", 40.7, -74.0), ("wall street", 40.7, -74.0),
    ("nigeria", 9.1, 7.4), ("south africa", -25.7, 28.2), ("egypt", 30.0, 31.2),
    ("saudi", 24.7, 46.7), ("turkey", 39.9, 32.9), ("indonesia", -6.2, 106.8),
    ("australia", -35.3, 149.1), ("singapore", 1.35, 103.8),
    ("greenland", 64.2, -51.7), ("venezuela", 10.5, -66.9),
    ("philippines", 14.6, 121.0), ("thailand", 13.8, 100.5),
    ("vietnam", 21.0, 105.8), ("poland", 52.2, 21.0), ("sweden", 59.3, 18.1),
]


# Ticker → HQ coordinates: company events plot at HQ (terminal convention).
_TICKER_HQ: dict[str, tuple[float, float]] = {
    "NVDA": (37.37, -121.92), "AAPL": (37.33, -122.03), "MSFT": (47.64, -122.13),
    "GOOGL": (37.42, -122.08), "AMZN": (47.61, -122.33), "META": (37.48, -122.16),
    "TSLA": (37.49, -121.94), "JPM": (40.71, -74.01), "GS": (40.71, -74.01),
    "XOM": (32.78, -96.80), "CVX": (37.77, -122.42), "COP": (29.76, -95.37),
    "RTX": (42.35, -71.06), "LMT": (39.05, -77.11), "NOC": (38.92, -77.02),
    "BA": (41.88, -87.63), "GE": (42.36, -71.06), "CAT": (40.69, -89.59),
    "IBM": (41.03, -73.76), "INTC": (45.54, -122.86), "AMD": (37.39, -121.91),
    "QCOM": (32.90, -117.19), "ORCL": (37.53, -122.26), "CRM": (37.77, -122.41),
    "NFLX": (37.25, -121.96), "DIS": (33.81, -117.92), "WMT": (36.37, -94.21),
    "KO": (33.75, -84.39), "PEP": (41.06, -73.70), "MCD": (41.88, -87.63),
    "NKE": (45.50, -122.68), "JNJ": (40.50, -74.41), "PFE": (40.75, -73.98),
    "MRK": (40.51, -74.46), "ABBV": (42.10, -87.94), "LLY": (39.77, -86.16),
    "UNH": (44.86, -93.46), "CSCO": (37.41, -121.93), "TXN": (32.78, -96.80),
    "MU": (37.23, -121.68), "ARM": (37.36, -122.06), "SMCI": (37.38, -121.89),
    "TSM": (24.79, 121.01), "BABA": (30.27, 120.16), "TCEHY": (22.54, 114.06),
    "RELIANCE.NS": (19.08, 72.88), "TCS.NS": (19.02, 72.85), "INFY.NS": (12.97, 77.59),
    "600519.SS": (27.83, 106.63), "0700.HK": (22.54, 114.06),
    "SHEL.L": (51.51, -0.12), "BP.L": (51.51, -0.12), "SAP.DE": (49.29, 8.64),
    "SIE.DE": (48.77, 11.43), "ASML.AS": (51.41, 5.46), "MC.PA": (48.87, 2.33),
    "7203.T": (35.02, 137.01), "6758.T": (35.66, 139.70), "005930.KS": (37.26, 127.06),
    "BHP.AX": (-37.81, 144.96), "SAN.MC": (40.42, -3.70),
}


def _derive_geo(row: dict) -> tuple[float | None, float | None]:
    """Best-effort lat/lon: stored coords → subject keywords → ticker HQ."""
    if row.get("lat") is not None and row.get("lon") is not None:
        return row["lat"], row["lon"]
    subject = (row.get("subject") or "").lower()
    for keyword, lat, lon in _GEO_KEYWORDS:
        if keyword in subject:
            return lat, lon
    # company events plot at HQ — terminal convention for globe visualization
    for ticker in row.get("tickers") or []:
        if ticker in _TICKER_HQ:
            return _TICKER_HQ[ticker]
    return None, None


def _event_row(r: sqlite3.Row) -> dict:
    d = dict(r)
    for key in ("tickers", "sources", "articles", "affected_entities", "second_order_effects"):
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except ValueError:
                d[key] = []
    d.setdefault("lat", None)
    d.setdefault("lon", None)
    d.setdefault("reasoning", "")
    d.setdefault("novelty", "standard")
    d.setdefault("actionability", "low")
    d.setdefault("key_metrics", {})
    d.setdefault("sector_impact", "")
    lat, lon = _derive_geo(d)
    d["lat"], d["lon"] = lat, lon
    return d


@app.get("/api/stats")
async def stats() -> dict:
    conn = _require_db()
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    verdicts = dict(
        conn.execute("SELECT verdict, COUNT(*) FROM events GROUP BY verdict").fetchall()
    )
    last = conn.execute("SELECT MAX(created_at) FROM events").fetchone()[0]
    return {"total_events": total, "by_verdict": verdicts, "last_update": last}


@app.get("/api/dates")
async def dates() -> dict:
    """Day → event-count buckets (the Dates calendar panel)."""
    conn = _require_db()
    rows = conn.execute(
        "SELECT SUBSTR(COALESCE(created_at, timestamp), 1, 10) AS day, COUNT(*) AS n "
        "FROM events GROUP BY day ORDER BY day DESC LIMIT 60"
    ).fetchall()
    return {
        "dates": [
            {"day": r["day"], "count": r["n"]}
            for r in rows
            if r["day"]
        ]
    }



@app.get("/api/suggestions")
async def suggestions(limit: int = Query(10, ge=1, le=50)) -> dict:
    """Same suggestion contract as server/, computed over SQLite."""
    conn = _require_db()
    rows = conn.execute(
        """
        SELECT e.tickers, e.signal_score, e.confidence, e.verdict, e.subject, e.timestamp, e.created_at
        FROM events e WHERE e.id > (
            SELECT COALESCE(MAX(id), 0) - 300 FROM events
        ) ORDER BY e.id DESC
        """
    ).fetchall()

    stats: dict[str, dict] = {}
    import time as _time

    now = _time.time()
    for r in rows:
        try:
            tickers = json.loads(r["tickers"]) if isinstance(r["tickers"], str) else (r["tickers"] or [])
        except ValueError:
            continue
        weight = 0.5 + 0.5 * float(r["confidence"] or 0)
        directional = 1.0 if r["verdict"] in ("INVEST", "PULL_OUT") else 0.4
        # age bucket from created_at (iso strings): <12h = recent, 12-48h = baseline
        try:
            from datetime import datetime

            ts = datetime.fromisoformat(str(r["created_at"]))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            age_h = (datetime.now(UTC) - ts).total_seconds() / 3600
        except ValueError:
            age_h = 999.0
        bucket = "recent" if age_h <= 12 else "baseline" if age_h <= 48 else "old"
        for t in tickers:
            s = stats.setdefault(
                t, {"mentions": 0, "score_sum": 0.0, "trust_sum": 0.0, "latest": None,
                    "verdict": None, "recent": 0.0, "baseline": 0.0}
            )
            s["mentions"] += 1
            s["score_sum"] += float(r["signal_score"] or 0) * weight
            s["trust_sum"] += directional * weight
            if bucket == "recent":
                s["recent"] += 1
            elif bucket == "baseline":
                s["baseline"] += 1
            if s["latest"] is None:
                s["latest"], s["verdict"] = r["subject"], r["verdict"]

    def score(s: dict) -> float:
        avg = s["score_sum"] / s["mentions"]
        trust = s["trust_sum"] / s["mentions"]
        return round(s["mentions"] * (0.5 + abs(avg) / 10) * (0.5 + trust) * 10, 2)

    for s in stats.values():
        s["momentum"] = round(s["recent"] / max(1.0, s["baseline"]), 2)

    ranked = sorted(
        stats.items(),
        key=lambda kv: -(score(kv[1]) * (1 + min(2.0, kv[1]["momentum"]))),
    )[:limit]
    return {
        "suggestions": [
            {
                "ticker": t,
                "score": score(s),
                "mentions": s["mentions"],
                "momentum": s["momentum"],
                "avg_score": round(s["score_sum"] / s["mentions"], 2),
                "trust": round(s["trust_sum"] / s["mentions"], 2),
                "latest_subject": s["latest"],
                "latest_verdict": s["verdict"],
                "sector": None,
                "last_seen": None,
            }
            for t, s in ranked
        ]
    }


# ── world feeds (RSS proxy, registry-allowlisted) ────────────────────────────


@app.get("/api/feeds")
async def feeds() -> dict:
    from finscrape.scrapers.world.feeds import FEEDS

    return {
        "feeds": [
            {"key": f.key, "name": f.name, "tier": f.tier, "region": f.region} for f in FEEDS
        ]
    }


@app.get("/api/rss-proxy")
async def rss_proxy(feed: str, limit: int = Query(20, ge=1, le=50)) -> dict:
    import feedparser

    from finscrape.scrapers.fastfetch import fast_get
    from finscrape.scrapers.world.feeds import get_feed

    f = get_feed(feed)
    if f is None:
        raise HTTPException(status_code=400, detail="unknown feed key")
    raw = fast_get(f.url)
    parsed = feedparser.parse(raw) if raw else None
    items = [
        {
            "title": (e.get("title") or "").strip(),
            "link": (e.get("link") or "").strip(),
            "published": e.get("published", ""),
        }
        for e in (parsed.entries if parsed else [])[:limit]
    ]
    return {"feed": feed, "name": f.name, "tier": f.tier, "items": items}


@app.get("/api/correlations")
async def correlations(date: str | None = Query(None)) -> dict:
    """Lightweight local correlation: same ticker covered by 2+ independent
    sources within 48h (multi-source corroboration), newest first."""
    conn = _require_db()
    rows = conn.execute(
        """
        SELECT e.id, e.subject, e.verdict, e.signal_score, e.tickers, e.sources, e.timestamp
        FROM events e
        WHERE e.timestamp >= datetime('now', '-2 days')
        ORDER BY e.id DESC LIMIT 200
        """
    ).fetchall()
    import json as _json

    by_ticker: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        try:
            tickers = _json.loads(r["tickers"]) if isinstance(r["tickers"], str) else []
        except ValueError:
            continue
        for t in tickers:
            by_ticker.setdefault(t, []).append(r)

    signals = []
    for ticker, evs in by_ticker.items():
        if len(evs) < 2:
            continue
        seen_sources: set[str] = set()
        for ev in evs:
            try:
                srcs = _json.loads(ev["sources"]) if isinstance(ev["sources"], str) else []
            except ValueError:
                srcs = []
            seen_sources.update(srcs.split("/")[-1] if "/" in s else s for s in srcs)
        if len(seen_sources) < 2:
            continue
        confidence = min(0.95, 0.4 + 0.15 * len(seen_sources) + 0.05 * min(3, len(evs)))
        signals.append({
            "signal_type": "multi_source_corroboration",
            "confidence": round(confidence, 2),
            "payload": {"ticker": ticker, "subject": evs[0]["subject"], "sources": sorted(seen_sources)},
            "detected_at": evs[0]["timestamp"],
        })
    signals.sort(key=lambda s: s["detected_at"] or "", reverse=True)
    return {"correlations": signals[:20]}


@app.get("/api/accuracy")
async def accuracy() -> dict:
    """Hit-rate over recorded signal outcomes (finscrape accuracy tracker tables)."""
    conn = _require_db()
    has = conn.execute(
        "SELECT name FROM sqlite_master WHERE name='signal_outcomes'"
    ).fetchone()
    if not has:
        return {"total": 0, "scored": 0, "hits": 0, "hit_rate": 0, "by_verdict": {}, "equity_curve": []}

    rows = conn.execute(
        "SELECT verdict, outcome, checked_at FROM signal_outcomes "
        "WHERE outcome IS NOT NULL ORDER BY checked_at"
    ).fetchall()
    scored = len(rows)
    hits = sum(1 for r in rows if r["outcome"] == "correct")
    by_verdict: dict[str, dict] = {}
    for r in rows:
        b = by_verdict.setdefault(r["verdict"], {"hits": 0, "total": 0})
        b["total"] += 1
        if r["outcome"] == "correct":
            b["hits"] += 1
    for b in by_verdict.values():
        b["hit_rate"] = round(b["hits"] / b["total"], 3) if b["total"] else 0.0

    equity, cum = [], 0
    for r in rows:
        cum += 1 if r["outcome"] == "correct" else -1
        equity.append(cum)

    return {
        "total": scored,
        "scored": scored,
        "hits": hits,
        "hit_rate": round(hits / scored, 3) if scored else 0.0,
        "by_verdict": by_verdict,
        "equity_curve": equity,
    }


@app.get("/api/sentiment")
async def sentiment(ticker: str = Query(...)) -> dict:
    """Sentiment for a ticker, derived from our own stored events mentioning it
    (finance-lexicon scored) — the local stand-in for the social scrape."""
    conn = _require_db()
    rows = conn.execute(
        "SELECT subject, tickers, articles, timestamp FROM events ORDER BY id DESC LIMIT 300"
    ).fetchall()
    from finscrape.services.sentiment_analyzer import SentimentAnalyzer

    bull = bear = neut = 0
    total_score = 0.0
    posts: list[dict] = []
    t = ticker.strip().upper()
    for r in rows:
        try:
            tickers = json.loads(r["tickers"]) if isinstance(r["tickers"], str) else []
        except ValueError:
            tickers = []
        mention = t in [str(x).upper() for x in tickers]
        if not mention:
            continue
        result = SentimentAnalyzer.analyze_text(r["subject"])
        total_score += result.score
        if result.score > 0.05:
            bull += 1
        elif result.score < -0.05:
            bear += 1
        else:
            neut += 1
        try:
            links = json.loads(r["articles"]) if isinstance(r["articles"], str) else []
        except ValueError:
            links = []
        posts.append({"text": r["subject"], "author": "news", "platform": "events",
                      "url": links[0] if links else ""})
    total = bull + bear + neut
    return {
        "ticker": t,
        "sentiment_score": round(total_score / total, 2) if total else 0.0,
        "bullish_count": bull,
        "bearish_count": bear,
        "neutral_count": neut,
        "total_posts": total,
        "bullish_pct": round(bull / total, 2) if total else 0.0,
        "volume_spike": total >= 5,
        "platforms": ["events"],
        "top_posts": posts[:5],
    }


@app.get("/api/portfolio")
async def portfolio() -> dict:
    """Positions + watchlists from the finscrape portfolio manager (SQLite)."""
    from finscrape.portfolio import PortfolioManager

    pm = PortfolioManager()
    positions = [p.to_dict() for p in pm.get_all_positions()]
    conn = _require_db()
    watchlists = [
        {"name": r["name"], "tickers": json.loads(r["tickers"])}
        for r in conn.execute("SELECT name, tickers FROM watchlists")
    ]
    return {
        "positions": positions,
        "watchlists": watchlists,
        "summary": {
            "position_count": len(positions),
            "cost_basis": round(sum(p.get("avg_cost", 0) * p.get("shares", 0) for p in positions), 2),
        },
    }


@app.get("/api/candles")
async def candles(
    symbol: str = Query(...),
    period: str = Query("1mo", pattern="^(1d|5d|1mo|3mo|6mo|1y|2y)$"),
    interval: str = Query("1d", pattern="^(5m|15m|1h|1d|1wk)$"),
) -> dict:
    """OHLCV candles for the chart panel. View-only market data."""
    try:
        import yfinance as yf

        hist = yf.Ticker(symbol.strip().upper()).history(period=period, interval=interval)
        if hist.empty:
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"candle fetch failed: {e}") from e


@app.get("/api/agents/analyze")
async def agents_analyze(
    ticker: str = Query(...),
    analysts: str = Query("market,news", description="comma-separated analyst set"),
    debate_rounds: int = Query(1, ge=1, le=3),
) -> dict:
    """Multi-agent ANALYSIS for a ticker — view-based intelligence only.

    Analyst personas debate using live market facts; the result is commentary
    (decision + reasoning). Nothing is executed: no orders, no accounts.
    Runs on the configured AI provider (local Ollama in dev mode).
    """
    from finscrape.trading.pipeline import run_analysis

    result = run_analysis(
        ticker=ticker.strip().upper(),
        debate_rounds=debate_rounds,
        selected_analysts=tuple(a.strip() for a in analysts.split(",") if a.strip()),
        save_reports=False,
    )
    return {
        "ticker": result["ticker"],
        "trade_date": result["trade_date"],
        "signal": result["signal"],
        "decision": result["decision"],
        "duration_seconds": result["duration_seconds"],
        "errors": result.get("errors", []),
    }


@app.get("/api/predict/{event_id}")
async def predict_event(event_id: int) -> dict:
    """Calibrated Event-Impact Probability for one stored event — the reliability
    evidence (per verdict/source/type hit-rates, sample sizes) is attached."""
    conn = _require_db()
    row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="event not found")
    event = _event_row(row)

    from finscrape import prediction

    outcomes = prediction.load_outcomes(_DB)
    verdict = event.get("verdict") or "OBSERVE"
    source = (event.get("sources") or ["local"])[0] if event.get("sources") else "local"
    result = prediction.predict(
        text=f"{event['subject']}. {event.get('reasoning', '')}",
        verdict=verdict,
        confidence=float(event.get("confidence") or 0.5),
        source=source,
        event_type=event.get("event_type") or "other",
        outcomes=outcomes,
    )
    result["event"] = {"id": event["id"], "subject": event["subject"],
                       "verdict": verdict, "signal_score": event.get("signal_score"),
                       "ticker": (event.get("tickers") or [""])[0] if isinstance(event.get("tickers"), list) else ""}
    return result


@app.get("/api/reliability")
async def reliability() -> dict:
    """Reliability tables + Brier score — the audit view of prediction quality."""
    from finscrape import prediction

    outcomes = prediction.load_outcomes(_DB)
    tables = prediction.reliability_tables(outcomes)
    return {"reliability": tables, "brier": prediction.brier_summary(outcomes)}


@app.get("/api/alerts")
async def alerts(limit: int = Query(30, ge=1, le=200)) -> dict:
    """Fired alerts (pipeline correlation + rule triggers), newest first."""
    conn = _require_db()
    has = conn.execute("SELECT name FROM sqlite_master WHERE name='alert_history'").fetchone()
    if not has:
        return {"alerts": []}
    rows = conn.execute(
        "SELECT id, action_type, event_subject, event_tickers, fired_at FROM alert_history "
        "WHERE event_subject != 'test event' ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    import json as _json

    out = []
    for r in rows:
        try:
            tickers = _json.loads(r["event_tickers"]) if isinstance(r["event_tickers"], str) else []
        except ValueError:
            tickers = []
        out.append({
            "id": r["id"], "action_type": r["action_type"],
            "subject": r["event_subject"], "tickers": tickers, "fired_at": r["fired_at"],
        })
    return {"alerts": out}


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "mode": "local",
        "db": _DB.exists(),
        "llm": True,
        "sources": [],
    }


# ── websocket (same message contract as server/ws.py: init/new_events/pong) ──


@app.get("/api/ai/analyze")
async def ai_analyze(id: int = Query(...)) -> dict:
    """LLM reasoning for one event — runs the local model (dev-mode provider,
    e.g. Ollama qwen) over the event's subject, verdict and tickers."""
    conn = _require_db()
    row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="event not found")
    event = _event_row(row)

    from finscrape.analysis.ai_client import call_ai

    prompt = (
        f"Headline: {event['subject']}\n"
        f"Verdict so far: {event['verdict']} (signal {event['signal_score']:+d}, "
        f"confidence {event['confidence']})\n"
        f"Tickers: {', '.join(event['tickers']) or 'none'}\n"
        "Analyze the market impact. Respond as JSON with keys: "
        '"summary" (2-3 sentences of reasoning), '
        '"ticker_impacts" (list of {ticker, direction, estimated_pct, reason}), '
        '"verdict_reason" (why this verdict is right or wrong).'
    )
    result = call_ai(prompt, "You are a geopolitical market analyst. Answer in strict JSON only.")
    if not result:
        raise HTTPException(status_code=503, detail="no AI backend available (dev mode off or model down)")

    impacts = result.get("ticker_impacts") or []
    return {
        "summary": result.get("summary") or result.get("reasoning") or "",
        "ticker_impacts": impacts if isinstance(impacts, list) else [],
        "verdict_reason": result.get("verdict_reason") or "",
    }


@app.websocket("/ws")
async def ws(websocket: WebSocket) -> None:
    """Realtime hub: pushes the recent-event snapshot on connect, then echoes
    pings; new-event broadcast arrives when the local pipeline runs."""
    await websocket.accept()
    try:
        if _DB.exists():
            conn = _db()
            rows = conn.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT 200"
            ).fetchall()
            await websocket.send_json({"type": "init", "events": [_event_row(r) for r in rows]})
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        return


# ── static SPA ───────────────────────────────────────────────────────────────

if _DIST.exists():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(_DIST / "index.html")

    @app.get("/{path:path}")
    async def spa_fallback(path: str) -> FileResponse:
        candidate = _DIST / path
        if candidate.is_file():
            return FileResponse(candidate)
        if (candidate / "index.html").is_file():  # directory entries ("/app/")
            return FileResponse(candidate / "index.html")
        return FileResponse(_DIST / "index.html")
