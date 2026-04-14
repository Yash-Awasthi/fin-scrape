"""
Adaptive selector tracking — survive site redesigns without code changes.

Tracks which CSS selectors work for which sources. When a selector stops
matching, the system logs it and can fall back to alternatives. Over time
this builds a resilience profile per source.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SelectorRecord:
    """A tracked CSS/XPath selector for a specific source and purpose."""
    source: str
    purpose: str  # e.g., "article_links", "article_text", "title", "date"
    selector: str
    selector_type: str = "css"  # "css" or "xpath"
    hit_count: int = 0
    miss_count: int = 0
    last_hit: Optional[str] = None
    last_miss: Optional[str] = None
    is_primary: bool = True

    @property
    def reliability(self) -> float:
        """How reliable this selector is (0.0 to 1.0)."""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.5  # unknown
        return self.hit_count / total

    @property
    def is_healthy(self) -> bool:
        """Whether this selector is considered healthy."""
        if self.hit_count + self.miss_count < 3:
            return True  # not enough data
        return self.reliability >= 0.5


class SelectorTracker:
    """Tracks selector success/failure to detect site redesigns.

    Usage:
        tracker = SelectorTracker(db_path)

        # Register selectors for a source
        tracker.register("yahoo", "article_links", "a.js-content-viewer")
        tracker.register("yahoo", "article_links", "li.js-stream-content a",
                         is_primary=False)

        # Track results during scraping
        elements = page.css("a.js-content-viewer")
        if elements:
            tracker.record_hit("yahoo", "article_links", "a.js-content-viewer")
        else:
            tracker.record_miss("yahoo", "article_links", "a.js-content-viewer")
            # Try fallback
            fallbacks = tracker.get_fallbacks("yahoo", "article_links")
            ...
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_tables()

    def _init_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS selectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                purpose TEXT NOT NULL,
                selector TEXT NOT NULL,
                selector_type TEXT NOT NULL DEFAULT 'css',
                hit_count INTEGER NOT NULL DEFAULT 0,
                miss_count INTEGER NOT NULL DEFAULT 0,
                last_hit TEXT,
                last_miss TEXT,
                is_primary INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(source, purpose, selector)
            );
            CREATE INDEX IF NOT EXISTS idx_sel_source ON selectors(source);
            CREATE INDEX IF NOT EXISTS idx_sel_purpose ON selectors(source, purpose);

            CREATE TABLE IF NOT EXISTS selector_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                purpose TEXT NOT NULL,
                selector TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_alerts_source ON selector_alerts(source);
        """)
        self._conn.commit()

    def register(
        self,
        source: str,
        purpose: str,
        selector: str,
        selector_type: str = "css",
        is_primary: bool = True,
    ) -> None:
        """Register a selector for tracking."""
        self._conn.execute(
            """INSERT OR IGNORE INTO selectors
               (source, purpose, selector, selector_type, is_primary)
               VALUES (?, ?, ?, ?, ?)""",
            (source, purpose, selector, selector_type, int(is_primary)),
        )
        self._conn.commit()

    def record_hit(self, source: str, purpose: str, selector: str) -> None:
        """Record that a selector matched elements successfully."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """UPDATE selectors SET hit_count = hit_count + 1, last_hit = ?
               WHERE source = ? AND purpose = ? AND selector = ?""",
            (now, source, purpose, selector),
        )
        self._conn.commit()

    def record_miss(self, source: str, purpose: str, selector: str) -> None:
        """Record that a selector failed to match any elements."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """UPDATE selectors SET miss_count = miss_count + 1, last_miss = ?
               WHERE source = ? AND purpose = ? AND selector = ?""",
            (now, source, purpose, selector),
        )
        self._conn.commit()

        # Check if this selector has become unreliable
        row = self._conn.execute(
            "SELECT hit_count, miss_count FROM selectors WHERE source = ? AND purpose = ? AND selector = ?",
            (source, purpose, selector),
        ).fetchone()
        if row:
            total = row[0] + row[1]
            if total >= 5 and row[0] / total < 0.3:
                self._create_alert(
                    source, purpose, selector, "degraded",
                    f"Selector reliability dropped to {row[0]/total:.0%} "
                    f"({row[0]} hits / {row[1]} misses)",
                )

    def get_selector(self, source: str, purpose: str) -> Optional[str]:
        """Get the best selector for a source+purpose (primary first, then by reliability)."""
        rows = self._conn.execute(
            """SELECT selector, hit_count, miss_count, is_primary
               FROM selectors WHERE source = ? AND purpose = ?
               ORDER BY is_primary DESC,
                        CASE WHEN hit_count + miss_count = 0 THEN 0.5
                             ELSE CAST(hit_count AS REAL) / (hit_count + miss_count) END DESC""",
            (source, purpose),
        ).fetchall()
        if not rows:
            return None
        return rows[0][0]

    def get_fallbacks(self, source: str, purpose: str) -> list[str]:
        """Get fallback selectors (non-primary, ordered by reliability)."""
        rows = self._conn.execute(
            """SELECT selector FROM selectors
               WHERE source = ? AND purpose = ? AND is_primary = 0
               ORDER BY CASE WHEN hit_count + miss_count = 0 THEN 0.5
                             ELSE CAST(hit_count AS REAL) / (hit_count + miss_count) END DESC""",
            (source, purpose),
        ).fetchall()
        return [r[0] for r in rows]

    def get_health_report(self, source: Optional[str] = None) -> list[dict]:
        """Get health report for all tracked selectors (or just one source)."""
        if source:
            rows = self._conn.execute(
                "SELECT * FROM selectors WHERE source = ? ORDER BY purpose", (source,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM selectors ORDER BY source, purpose"
            ).fetchall()

        cols = [d[0] for d in self._conn.execute("SELECT * FROM selectors LIMIT 0").description]
        report = []
        for row in rows:
            d = dict(zip(cols, row))
            total = d["hit_count"] + d["miss_count"]
            d["reliability"] = d["hit_count"] / total if total > 0 else None
            d["is_primary"] = bool(d["is_primary"])
            d["is_healthy"] = d["reliability"] is None or d["reliability"] >= 0.5
            report.append(d)
        return report

    def get_degraded_selectors(self) -> list[dict]:
        """Get all selectors with reliability below 50%."""
        return [s for s in self.get_health_report() if s.get("is_healthy") is False]

    def get_alerts(self, source: Optional[str] = None, limit: int = 50) -> list[dict]:
        """Get recent selector alerts."""
        if source:
            rows = self._conn.execute(
                "SELECT * FROM selector_alerts WHERE source = ? ORDER BY id DESC LIMIT ?",
                (source, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM selector_alerts ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

        cols = [d[0] for d in self._conn.execute("SELECT * FROM selector_alerts LIMIT 0").description]
        return [dict(zip(cols, row)) for row in rows]

    def _create_alert(self, source: str, purpose: str, selector: str,
                      alert_type: str, message: str) -> None:
        """Create a selector health alert."""
        self._conn.execute(
            """INSERT INTO selector_alerts (source, purpose, selector, alert_type, message)
               VALUES (?, ?, ?, ?, ?)""",
            (source, purpose, selector, alert_type, message),
        )
        self._conn.commit()
        logger.warning("[%s] Selector alert (%s): %s — %s", source, alert_type, selector, message)

    def close(self) -> None:
        self._conn.close()
