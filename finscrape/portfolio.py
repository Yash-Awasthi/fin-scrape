"""
Portfolio tracking — watchlists, positions, and position-aware signal weighting.

Stores portfolio data in the same SQLite database as the pipeline state.
Signals are weighted by position size so that events affecting your largest
holdings surface with higher priority.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """A single holding in the portfolio."""

    ticker: str
    shares: float = 0.0
    avg_cost: float = 0.0
    current_price: float = 0.0
    tags: list[str] = field(default_factory=list)

    @property
    def market_value(self) -> float:
        return self.shares * self.current_price

    @property
    def cost_basis(self) -> float:
        return self.shares * self.avg_cost

    @property
    def unrealized_pnl(self) -> float:
        if self.avg_cost == 0:
            return 0.0
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "shares": self.shares,
            "avg_cost": self.avg_cost,
            "current_price": self.current_price,
            "tags": self.tags,
            "market_value": round(self.market_value, 2),
            "cost_basis": round(self.cost_basis, 2),
            "unrealized_pnl": round(self.unrealized_pnl, 2),
            "unrealized_pnl_pct": round(self.unrealized_pnl_pct, 2),
        }

    @classmethod
    def from_dict(cls, d: dict) -> Position:
        return cls(
            ticker=d["ticker"],
            shares=d.get("shares", 0.0),
            avg_cost=d.get("avg_cost", 0.0),
            current_price=d.get("current_price", 0.0),
            tags=d.get("tags", []),
        )


@dataclass
class Watchlist:
    """A named group of tickers the user wants to track."""

    name: str
    tickers: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tickers": self.tickers,
            "description": self.description,
        }


class PortfolioManager:
    """
    SQLite-backed portfolio state: positions, watchlists, and signal weighting.

    Tables:
      - positions: ticker, shares, avg_cost, current_price, tags
      - watchlists: name, tickers (JSON), description
      - alerts: triggered portfolio-level alerts
    """

    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            from finscrape.storage import _project_root
            data_dir = _project_root() / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "finscrape.db"
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_tables()

    def _init_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS positions (
                ticker TEXT PRIMARY KEY,
                shares REAL NOT NULL DEFAULT 0,
                avg_cost REAL NOT NULL DEFAULT 0,
                current_price REAL NOT NULL DEFAULT 0,
                tags TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS watchlists (
                name TEXT PRIMARY KEY,
                tickers TEXT NOT NULL DEFAULT '[]',
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS portfolio_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                event_id INTEGER,
                triggered_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_palerts_ticker ON portfolio_alerts(ticker);
        """)
        self._conn.commit()

    # --- Positions ---

    def add_position(self, ticker: str, shares: float, avg_cost: float,
                     current_price: float = 0.0, tags: list[str] | None = None) -> None:
        """Add or update a position.

        Raises ValueError if shares or avg_cost are negative.
        """
        if shares < 0:
            raise ValueError(f"shares must be >= 0, got {shares}")
        if avg_cost < 0:
            raise ValueError(f"avg_cost must be >= 0, got {avg_cost}")
        if current_price < 0:
            raise ValueError(f"current_price must be >= 0, got {current_price}")
        ticker = ticker.strip().upper()
        if not ticker or len(ticker) > 10:
            raise ValueError(f"Invalid ticker: {ticker!r}")
        self._conn.execute(
            """INSERT INTO positions (ticker, shares, avg_cost, current_price, tags, updated_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT(ticker) DO UPDATE SET
                 shares = excluded.shares,
                 avg_cost = excluded.avg_cost,
                 current_price = excluded.current_price,
                 tags = excluded.tags,
                 updated_at = datetime('now')""",
            (ticker.upper(), shares, avg_cost, current_price, json.dumps(tags or [])),
        )
        self._conn.commit()

    def remove_position(self, ticker: str) -> bool:
        """Remove a position. Returns True if it existed."""
        cur = self._conn.execute("DELETE FROM positions WHERE ticker = ?", (ticker.upper(),))
        self._conn.commit()
        return cur.rowcount > 0

    def get_position(self, ticker: str) -> Position | None:
        row = self._conn.execute(
            "SELECT ticker, shares, avg_cost, current_price, tags FROM positions WHERE ticker = ?",
            (ticker.upper(),),
        ).fetchone()
        if not row:
            return None
        return Position(
            ticker=row[0], shares=row[1], avg_cost=row[2],
            current_price=row[3], tags=json.loads(row[4]),
        )

    def get_all_positions(self) -> list[Position]:
        rows = self._conn.execute(
            "SELECT ticker, shares, avg_cost, current_price, tags FROM positions ORDER BY ticker"
        ).fetchall()
        return [
            Position(ticker=r[0], shares=r[1], avg_cost=r[2],
                     current_price=r[3], tags=json.loads(r[4]))
            for r in rows
        ]

    def update_prices(self, prices: dict[str, float]) -> None:
        """Batch update current prices for held positions."""
        for ticker, price in prices.items():
            self._conn.execute(
                "UPDATE positions SET current_price = ?, updated_at = datetime('now') WHERE ticker = ?",
                (price, ticker.upper()),
            )
        self._conn.commit()

    def portfolio_tickers(self) -> set[str]:
        """All tickers in positions."""
        rows = self._conn.execute("SELECT ticker FROM positions").fetchall()
        return {r[0] for r in rows}

    def total_value(self) -> float:
        positions = self.get_all_positions()
        return sum(p.market_value for p in positions)

    def total_pnl(self) -> float:
        positions = self.get_all_positions()
        return sum(p.unrealized_pnl for p in positions)

    # --- Watchlists ---

    def create_watchlist(self, name: str, tickers: list[str] | None = None,
                         description: str = "") -> None:
        self._conn.execute(
            """INSERT INTO watchlists (name, tickers, description)
               VALUES (?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                 tickers = excluded.tickers,
                 description = excluded.description""",
            (name, json.dumps([t.upper() for t in (tickers or [])]), description),
        )
        self._conn.commit()

    def get_watchlist(self, name: str) -> Watchlist | None:
        row = self._conn.execute(
            "SELECT name, tickers, description FROM watchlists WHERE name = ?", (name,)
        ).fetchone()
        if not row:
            return None
        return Watchlist(name=row[0], tickers=json.loads(row[1]), description=row[2])

    def get_all_watchlists(self) -> list[Watchlist]:
        rows = self._conn.execute(
            "SELECT name, tickers, description FROM watchlists ORDER BY name"
        ).fetchall()
        return [Watchlist(name=r[0], tickers=json.loads(r[1]), description=r[2]) for r in rows]

    def add_to_watchlist(self, name: str, tickers: list[str]) -> None:
        """Add tickers to an existing watchlist (creates if needed)."""
        wl = self.get_watchlist(name)
        if wl:
            existing = set(wl.tickers)
            existing.update(t.upper() for t in tickers)
            self._conn.execute(
                "UPDATE watchlists SET tickers = ? WHERE name = ?",
                (json.dumps(sorted(existing)), name),
            )
        else:
            self.create_watchlist(name, tickers)
        self._conn.commit()

    def remove_from_watchlist(self, name: str, tickers: list[str]) -> None:
        wl = self.get_watchlist(name)
        if not wl:
            return
        remaining = [t for t in wl.tickers if t not in {tk.upper() for tk in tickers}]
        self._conn.execute(
            "UPDATE watchlists SET tickers = ? WHERE name = ?",
            (json.dumps(remaining), name),
        )
        self._conn.commit()

    def delete_watchlist(self, name: str) -> bool:
        cur = self._conn.execute("DELETE FROM watchlists WHERE name = ?", (name,))
        self._conn.commit()
        return cur.rowcount > 0

    def all_watched_tickers(self) -> set[str]:
        """Union of all watchlist tickers + position tickers."""
        tickers = self.portfolio_tickers()
        for wl in self.get_all_watchlists():
            tickers.update(wl.tickers)
        return tickers

    # --- Signal Weighting ---

    def weight_signal(self, event: dict) -> dict:
        """
        Enrich a pipeline event with portfolio-aware weighting.

        Adds:
          - portfolio_relevance: float 0–1 (how relevant to the user's holdings)
          - position_weight: float (based on position size relative to portfolio)
          - weighted_score: signal_score adjusted by position weight
          - in_portfolio: bool
          - in_watchlist: list[str] of matching watchlist names
        """
        event_tickers = set(event.get("tickers", []))
        held_tickers = self.portfolio_tickers()
        watched = self.all_watched_tickers()

        overlap_held = event_tickers & held_tickers
        overlap_watched = event_tickers & watched

        # Calculate position weight (fraction of portfolio value)
        position_weight = 0.0
        total = self.total_value()
        if total > 0 and overlap_held:
            for t in overlap_held:
                pos = self.get_position(t)
                if pos:
                    position_weight += pos.market_value / total

        # Relevance: 1.0 if in portfolio, 0.6 if in watchlist only, 0.0 otherwise
        if overlap_held:
            relevance = min(1.0, 0.7 + position_weight * 0.3)
        elif overlap_watched:
            relevance = 0.6
        else:
            relevance = 0.0

        # Weighted score: amplify signal by position weight
        base_score = event.get("signal_score", 0)
        weight_multiplier = 1.0 + position_weight  # 1.0x to 2.0x
        weighted_score = max(-5, min(5, round(base_score * weight_multiplier)))

        # Which watchlists match?
        matching_watchlists = []
        for wl in self.get_all_watchlists():
            if event_tickers & set(wl.tickers):
                matching_watchlists.append(wl.name)

        enriched = dict(event)
        enriched["portfolio_relevance"] = round(relevance, 2)
        enriched["position_weight"] = round(position_weight, 4)
        enriched["weighted_score"] = weighted_score
        enriched["in_portfolio"] = bool(overlap_held)
        enriched["in_watchlist"] = matching_watchlists
        return enriched

    def filter_relevant_events(self, events: list[dict], min_relevance: float = 0.1) -> list[dict]:
        """Filter and weight events, returning only those relevant to the portfolio."""
        weighted = [self.weight_signal(e) for e in events]
        relevant = [e for e in weighted if e["portfolio_relevance"] >= min_relevance]
        return sorted(relevant, key=lambda e: abs(e["weighted_score"]), reverse=True)

    # --- Portfolio Alerts ---

    def add_alert(self, ticker: str, alert_type: str, message: str,
                  event_id: int | None = None) -> int:
        cur = self._conn.execute(
            "INSERT INTO portfolio_alerts (ticker, alert_type, message, event_id) VALUES (?, ?, ?, ?)",
            (ticker.upper(), alert_type, message, event_id),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_recent_alerts(self, limit: int = 50) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, ticker, alert_type, message, event_id, triggered_at "
            "FROM portfolio_alerts ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {"id": r[0], "ticker": r[1], "alert_type": r[2],
             "message": r[3], "event_id": r[4], "triggered_at": r[5]}
            for r in rows
        ]

    def check_and_alert(self, events: list[dict]) -> list[dict]:
        """
        Check events against portfolio and generate alerts for significant ones.

        Alerts are generated when:
          - INVEST/PULL_OUT verdict on a held position
          - High-confidence signal (≥0.8) on a watched ticker
          - Large price move (|score| ≥ 4) on a held position
        """
        alerts = []
        held = self.portfolio_tickers()
        watched = self.all_watched_tickers()

        for event in events:
            event_tickers = set(event.get("tickers", []))
            verdict = event.get("verdict", "OBSERVE")
            confidence = event.get("confidence", 0.0)
            score = event.get("signal_score", 0)
            event_id = event.get("id")

            overlap_held = event_tickers & held
            overlap_watched = event_tickers & watched

            for ticker in overlap_held:
                if verdict in ("INVEST", "PULL_OUT"):
                    alert = {
                        "ticker": ticker,
                        "alert_type": f"position_{verdict.lower()}",
                        "message": f"{verdict} signal on held position {ticker}: {event.get('subject', '')}",
                        "event_id": event_id,
                    }
                    self.add_alert(**alert)
                    alerts.append(alert)

                if abs(score) >= 4:
                    alert = {
                        "ticker": ticker,
                        "alert_type": "high_impact",
                        "message": f"High-impact signal ({score:+d}) on {ticker}: {event.get('subject', '')}",
                        "event_id": event_id,
                    }
                    self.add_alert(**alert)
                    alerts.append(alert)

            for ticker in (overlap_watched - overlap_held):
                if confidence >= 0.8 and verdict in ("INVEST", "PULL_OUT"):
                    alert = {
                        "ticker": ticker,
                        "alert_type": f"watchlist_{verdict.lower()}",
                        "message": f"{verdict} signal on watched ticker {ticker} (conf: {confidence:.0%}): {event.get('subject', '')}",
                        "event_id": event_id,
                    }
                    self.add_alert(**alert)
                    alerts.append(alert)

        return alerts

    # --- Summary ---

    def summary(self) -> dict:
        """Portfolio summary for dashboard/Telegram."""
        positions = self.get_all_positions()
        watchlists = self.get_all_watchlists()
        return {
            "positions": len(positions),
            "total_value": round(self.total_value(), 2),
            "total_pnl": round(self.total_pnl(), 2),
            "tickers": sorted(self.portfolio_tickers()),
            "watchlists": [wl.to_dict() for wl in watchlists],
            "watched_tickers": sorted(self.all_watched_tickers()),
        }

    def close(self) -> None:
        self._conn.close()
