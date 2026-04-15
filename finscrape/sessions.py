"""
Session management for sites requiring cookies/authentication.

Persists cookies and session state across scraping runs so that
login-gated or rate-limited sites can be accessed without
re-authenticating every time.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionCookie:
    """A single cookie with metadata."""
    name: str
    value: str
    domain: str
    path: str = "/"
    expires: float = 0.0
    secure: bool = False
    http_only: bool = False

    @property
    def is_expired(self) -> bool:
        if self.expires <= 0:
            return False  # session cookie — never expires
        return time.time() > self.expires

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "domain": self.domain,
            "path": self.path,
            "expires": self.expires,
            "secure": self.secure,
            "httpOnly": self.http_only,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SessionCookie:
        return cls(
            name=d["name"],
            value=d["value"],
            domain=d["domain"],
            path=d.get("path", "/"),
            expires=d.get("expires", 0.0),
            secure=d.get("secure", False),
            http_only=d.get("httpOnly", d.get("http_only", False)),
        )


class SessionManager:
    """Manages per-source browser sessions with persistent cookie storage.

    Cookies are stored in the same SQLite database as the rest of the pipeline.
    Each source gets its own cookie jar.

    Usage in a scraper:
        session_mgr = SessionManager(db_path)
        cookies = session_mgr.get_cookies("bloomberg")
        # ... use cookies with Fetcher/StealthyFetcher ...
        session_mgr.save_cookies("bloomberg", new_cookies)
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_tables()

    def _init_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                cookie_name TEXT NOT NULL,
                cookie_value TEXT NOT NULL,
                domain TEXT NOT NULL,
                path TEXT NOT NULL DEFAULT '/',
                expires REAL NOT NULL DEFAULT 0,
                secure INTEGER NOT NULL DEFAULT 0,
                http_only INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(source, cookie_name, domain)
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_source ON sessions(source);

            CREATE TABLE IF NOT EXISTS session_metadata (
                source TEXT PRIMARY KEY,
                user_agent TEXT,
                last_login TEXT,
                extra TEXT NOT NULL DEFAULT '{}'
            );
        """)
        self._conn.commit()

    def get_cookies(self, source: str) -> list[SessionCookie]:
        """Get all non-expired cookies for a source."""
        rows = self._conn.execute(
            """SELECT cookie_name, cookie_value, domain, path, expires, secure, http_only
               FROM sessions WHERE source = ?""",
            (source,),
        ).fetchall()

        cookies = []
        for name, value, domain, path, expires, secure, http_only in rows:
            cookie = SessionCookie(
                name=name, value=value, domain=domain, path=path,
                expires=expires, secure=bool(secure), http_only=bool(http_only),
            )
            if not cookie.is_expired:
                cookies.append(cookie)
            else:
                # Clean up expired cookies
                self._conn.execute(
                    "DELETE FROM sessions WHERE source = ? AND cookie_name = ? AND domain = ?",
                    (source, name, domain),
                )

        self._conn.commit()
        return cookies

    def save_cookies(self, source: str, cookies: list[SessionCookie]) -> None:
        """Save/update cookies for a source."""
        for c in cookies:
            self._conn.execute(
                """INSERT INTO sessions
                   (source, cookie_name, cookie_value, domain, path, expires, secure, http_only)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(source, cookie_name, domain) DO UPDATE SET
                       cookie_value = excluded.cookie_value,
                       path = excluded.path,
                       expires = excluded.expires,
                       secure = excluded.secure,
                       http_only = excluded.http_only,
                       updated_at = datetime('now')""",
                (source, c.name, c.value, c.domain, c.path, c.expires,
                 int(c.secure), int(c.http_only)),
            )
        self._conn.commit()
        logger.debug("Saved %d cookies for %s", len(cookies), source)

    def save_cookies_from_dicts(self, source: str, cookie_dicts: list[dict]) -> None:
        """Save cookies from raw dicts (e.g., from browser context.cookies())."""
        cookies = [SessionCookie.from_dict(d) for d in cookie_dicts]
        self.save_cookies(source, cookies)

    def get_cookies_as_dicts(self, source: str) -> list[dict]:
        """Get cookies as dicts ready for browser context.add_cookies()."""
        return [c.to_dict() for c in self.get_cookies(source)]

    def get_cookie_header(self, source: str) -> str:
        """Get cookies as a Cookie header string for HTTP requests."""
        cookies = self.get_cookies(source)
        if not cookies:
            return ""
        return "; ".join(f"{c.name}={c.value}" for c in cookies)

    def set_metadata(self, source: str, user_agent: str | None = None, **extra) -> None:
        """Store session metadata (user agent, login timestamp, etc.)."""
        existing_extra = {}
        row = self._conn.execute(
            "SELECT extra FROM session_metadata WHERE source = ?", (source,)
        ).fetchone()
        if row:
            existing_extra = json.loads(row[0])
        existing_extra.update(extra)

        self._conn.execute(
            """INSERT INTO session_metadata (source, user_agent, last_login, extra)
               VALUES (?, ?, datetime('now'), ?)
               ON CONFLICT(source) DO UPDATE SET
                   user_agent = COALESCE(excluded.user_agent, session_metadata.user_agent),
                   last_login = datetime('now'),
                   extra = excluded.extra""",
            (source, user_agent, json.dumps(existing_extra)),
        )
        self._conn.commit()

    def get_metadata(self, source: str) -> Optional[dict]:
        """Retrieve session metadata for a source."""
        row = self._conn.execute(
            "SELECT user_agent, last_login, extra FROM session_metadata WHERE source = ?",
            (source,),
        ).fetchone()
        if not row:
            return None
        return {
            "user_agent": row[0],
            "last_login": row[1],
            **json.loads(row[2]),
        }

    def clear_source(self, source: str) -> None:
        """Remove all cookies and metadata for a source."""
        self._conn.execute("DELETE FROM sessions WHERE source = ?", (source,))
        self._conn.execute("DELETE FROM session_metadata WHERE source = ?", (source,))
        self._conn.commit()

    def has_session(self, source: str) -> bool:
        """Check if a source has any stored cookies."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE source = ?", (source,)
        ).fetchone()
        return (row[0] or 0) > 0

    def close(self) -> None:
        self._conn.close()
