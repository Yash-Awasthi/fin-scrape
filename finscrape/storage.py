"""
SQLite-backed state persistence for the FinScrape pipeline.

Replaces the old JSON file storage with proper SQLite for:
- Fast visited URL lookups (indexed)
- Queryable event history
- Entity index with full-text matching
- Concurrent-safe writes
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _project_root() -> Path:
    """Find project root by looking for main.py or .git."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "main.py").exists() or (parent / ".git").exists():
            return parent
    return current.parent


class StateManager:
    """SQLite-backed pipeline state: visited URLs, events, entity index."""

    def __init__(self, data_dir: str | None = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = _project_root() / "data"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "finscrape.db"
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_tables()
        self._migrate_event_columns()
        self._migrate_json()

    def _init_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS visited_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                visited_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(source, url)
            );
            CREATE INDEX IF NOT EXISTS idx_visited_source ON visited_urls(source);
            CREATE INDEX IF NOT EXISTS idx_visited_url ON visited_urls(url);

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                event_type TEXT NOT NULL DEFAULT 'other',
                tickers TEXT NOT NULL DEFAULT '[]',
                impact_direction TEXT NOT NULL DEFAULT 'neutral',
                signal_score INTEGER NOT NULL DEFAULT 0,
                confidence REAL NOT NULL DEFAULT 0.5,
                verdict TEXT NOT NULL DEFAULT 'OBSERVE',
                heuristic_impact REAL NOT NULL DEFAULT 0.0,
                divergence_flag INTEGER NOT NULL DEFAULT 0,
                sources TEXT NOT NULL DEFAULT '[]',
                articles TEXT NOT NULL DEFAULT '[]',
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_events_verdict ON events(verdict);
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);

            CREATE TABLE IF NOT EXISTS entity_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                company TEXT NOT NULL,
                ticker TEXT NOT NULL,
                UNIQUE(keyword, company, ticker)
            );
            CREATE INDEX IF NOT EXISTS idx_entity_keyword ON entity_index(keyword);
        """)
        self._conn.commit()

    def _migrate_json(self) -> None:
        """One-time migration from old JSON files to SQLite."""
        visited_json = self.data_dir / "visited_urls.json"
        events_json = self.data_dir / "events.json"
        entity_json = self.data_dir / "entity_index.json"

        if visited_json.exists():
            try:
                with open(visited_json) as f:
                    data = json.load(f)
                for source, urls in data.items():
                    for url in urls:
                        self._conn.execute(
                            "INSERT OR IGNORE INTO visited_urls (source, url) VALUES (?, ?)",
                            (source, url),
                        )
                self._conn.commit()
                visited_json.rename(visited_json.with_suffix(".json.bak"))
                logger.info("Migrated visited_urls.json → SQLite")
            except Exception as e:
                logger.warning("Failed to migrate visited_urls.json: %s", e)

        if events_json.exists():
            try:
                with open(events_json) as f:
                    events = json.load(f)
                for ev in events:
                    self._insert_event(ev)
                self._conn.commit()
                events_json.rename(events_json.with_suffix(".json.bak"))
                logger.info("Migrated events.json → SQLite (%d events)", len(events))
            except Exception as e:
                logger.warning("Failed to migrate events.json: %s", e)

        if entity_json.exists():
            try:
                with open(entity_json) as f:
                    data = json.load(f)
                for keyword, entries in data.items():
                    for company, ticker in entries:
                        self._conn.execute(
                            "INSERT OR IGNORE INTO entity_index (keyword, company, ticker) VALUES (?, ?, ?)",
                            (keyword, company, ticker),
                        )
                self._conn.commit()
                entity_json.rename(entity_json.with_suffix(".json.bak"))
                logger.info("Migrated entity_index.json → SQLite")
            except Exception as e:
                logger.warning("Failed to migrate entity_index.json: %s", e)

    # --- Visited URLs ---

    def get_visited(self, source: str) -> set[str]:
        """Return set of visited URLs for a source (fast lookup)."""
        rows = self._conn.execute(
            "SELECT url FROM visited_urls WHERE source = ?", (source,)
        ).fetchall()
        return {r[0] for r in rows}

    def add_visited(self, source: str, url: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO visited_urls (source, url) VALUES (?, ?)",
            (source, url),
        )
        self._conn.commit()

    def visited_count(self, source: str | None = None) -> int:
        if source:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM visited_urls WHERE source = ?", (source,)
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) FROM visited_urls").fetchone()
        return row[0] if row else 0

    # --- Events ---

    # Columns added after the original schema; older DBs are migrated lazily.
    _EXTRA_EVENT_COLUMNS = (
        "reasoning", "magnitude", "novelty", "actionability",
        "sector_impact", "key_metrics", "second_order_effects",
        "affected_entities", "lat", "lon",
    )

    def _migrate_event_columns(self) -> None:
        existing = {r[1] for r in self._conn.execute("PRAGMA table_info(events)")}
        for column in self._EXTRA_EVENT_COLUMNS:
            if column not in existing:
                self._conn.execute(f"ALTER TABLE events ADD COLUMN {column} DEFAULT NULL")
        self._conn.commit()

    def _insert_event(self, ev: dict) -> int:
        cur = self._conn.execute(
            """INSERT INTO events
               (subject, event_type, tickers, impact_direction, signal_score,
                confidence, verdict, heuristic_impact, divergence_flag,
                sources, articles, timestamp,
                reasoning, magnitude, novelty, actionability, sector_impact,
                key_metrics, second_order_effects, affected_entities, lat, lon)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ev.get("subject", ""),
                ev.get("event_type", "other"),
                json.dumps(ev.get("tickers", [])),
                ev.get("impact_direction", "neutral"),
                ev.get("signal_score", 0),
                ev.get("confidence", 0.5),
                ev.get("verdict", "OBSERVE"),
                ev.get("heuristic_impact", 0.0),
                1 if ev.get("divergence_flag") else 0,
                json.dumps(ev.get("sources", [])),
                json.dumps(ev.get("articles", [])),
                ev.get("timestamp", datetime.now(UTC).isoformat()),
                ev.get("reasoning", ""),
                ev.get("magnitude", "medium"),
                ev.get("novelty", "standard"),
                ev.get("actionability", "low"),
                ev.get("sector_impact", ""),
                json.dumps(ev.get("key_metrics", {})),
                json.dumps(ev.get("second_order_effects", [])),
                json.dumps(ev.get("affected_entities", [])),
                ev.get("lat"),
                ev.get("lon"),
            ),
        )
        return cur.lastrowid or 0

    def add_event(self, event: dict) -> int:
        """Insert an event and return its ID."""
        row_id = self._insert_event(event)
        self._conn.commit()
        return row_id

    def save_events(self) -> None:
        """Commit pending changes (for backward compat)."""
        self._conn.commit()

    def get_recent_events(self, limit: int = 100) -> list[dict]:
        """Get recent events as dicts."""
        rows = self._conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        cols = [d[0] for d in self._conn.execute("SELECT * FROM events LIMIT 0").description]
        events = []
        for row in rows:
            ev = dict(zip(cols, row))
            ev["tickers"] = json.loads(ev["tickers"])
            ev["sources"] = json.loads(ev["sources"])
            ev["articles"] = json.loads(ev["articles"])
            ev["divergence_flag"] = bool(ev["divergence_flag"])
            events.append(ev)
        return events

    @property
    def events(self) -> list[dict]:
        """Backward-compat property — returns recent events."""
        return self.get_recent_events(100)

    def update_event(self, event_id: int, **kwargs: Any) -> None:
        """Update specific fields of an event."""
        for key, value in kwargs.items():
            if key in ("tickers", "sources", "articles"):
                value = json.dumps(value)
            elif key == "divergence_flag":
                value = 1 if value else 0
            self._conn.execute(
                f"UPDATE events SET {key} = ? WHERE id = ?", (value, event_id)
            )
        self._conn.commit()

    def event_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()
        return row[0] if row else 0

    def get_events_by_ticker(self, ticker: str, limit: int = 50) -> list[dict]:
        """Find events mentioning a specific ticker."""
        rows = self._conn.execute(
            "SELECT * FROM events WHERE tickers LIKE ? ORDER BY id DESC LIMIT ?",
            (f'%"{ticker}"%', limit),
        ).fetchall()
        cols = [d[0] for d in self._conn.execute("SELECT * FROM events LIMIT 0").description]
        events = []
        for row in rows:
            ev = dict(zip(cols, row))
            ev["tickers"] = json.loads(ev["tickers"])
            ev["sources"] = json.loads(ev["sources"])
            ev["articles"] = json.loads(ev["articles"])
            ev["divergence_flag"] = bool(ev["divergence_flag"])
            events.append(ev)
        return events

    def get_events_by_verdict(self, verdict: str, limit: int = 50) -> list[dict]:
        """Find events with a specific verdict."""
        rows = self._conn.execute(
            "SELECT * FROM events WHERE verdict = ? ORDER BY id DESC LIMIT ?",
            (verdict, limit),
        ).fetchall()
        cols = [d[0] for d in self._conn.execute("SELECT * FROM events LIMIT 0").description]
        events = []
        for row in rows:
            ev = dict(zip(cols, row))
            ev["tickers"] = json.loads(ev["tickers"])
            ev["sources"] = json.loads(ev["sources"])
            ev["articles"] = json.loads(ev["articles"])
            ev["divergence_flag"] = bool(ev["divergence_flag"])
            events.append(ev)
        return events

    # --- Entity Index ---

    def resolve_entity_tickers(self, text: str) -> list[str]:
        """Look up tickers from entity index based on text content."""
        text_lower = text.lower()
        words = set(text_lower.split())
        tickers = []

        for word in words:
            rows = self._conn.execute(
                "SELECT company, ticker FROM entity_index WHERE keyword = ?", (word,)
            ).fetchall()
            for company, ticker in rows:
                if company.lower() in text_lower:
                    tickers.append(ticker)

        return tickers

    def add_entity(self, keyword: str, company: str, ticker: str) -> None:
        """Add an entity mapping to the index."""
        self._conn.execute(
            "INSERT OR IGNORE INTO entity_index (keyword, company, ticker) VALUES (?, ?, ?)",
            (keyword.lower(), company, ticker.upper()),
        )
        self._conn.commit()

    def seed_entity_index(self, entities: dict[str, list[tuple[str, str]]]) -> None:
        """Bulk seed the entity index. Format: {"keyword": [("Company Name", "TICK"), ...]}"""
        for keyword, entries in entities.items():
            for company, ticker in entries:
                self._conn.execute(
                    "INSERT OR IGNORE INTO entity_index (keyword, company, ticker) VALUES (?, ?, ?)",
                    (keyword.lower(), company, ticker.upper()),
                )
        self._conn.commit()

    # --- Stats ---

    def stats(self) -> dict:
        """Return storage statistics."""
        return {
            "events": self.event_count(),
            "visited_urls": self.visited_count(),
            "entity_entries": self._conn.execute("SELECT COUNT(*) FROM entity_index").fetchone()[0],
            "db_size_kb": round(self.db_path.stat().st_size / 1024, 1) if self.db_path.exists() else 0,
        }

    def close(self) -> None:
        self._conn.close()
