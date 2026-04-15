"""
Insider trading tracker backed by SQLite.

Fetches Form 4 filings from SEC EDGAR, stores insider transactions in a
local SQLite database, and provides analysis utilities for detecting
unusual activity and computing insider sentiment.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from finscrape.edgar.filings import FilingFetcher, FilingType, Filing
from finscrape.edgar.parser import FilingParser

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path("data/insider_trades.db")

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS insider_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    insider_name TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    transaction_type TEXT NOT NULL,
    shares REAL NOT NULL DEFAULT 0,
    price REAL NOT NULL DEFAULT 0,
    total_value REAL NOT NULL DEFAULT 0,
    date TEXT NOT NULL,
    is_10b5_plan INTEGER NOT NULL DEFAULT 0,
    accession_number TEXT UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_insider_ticker_date
ON insider_transactions (ticker, date);
"""


@dataclass
class InsiderTransaction:
    """A single insider trading transaction."""
    ticker: str
    insider_name: str
    title: str
    transaction_type: str  # buy / sell / gift
    shares: float
    price: float
    total_value: float
    date: str  # ISO YYYY-MM-DD
    is_10b5_plan: bool

    def to_dict(self) -> dict:
        return asdict(self)


class InsiderTracker:
    """Track and analyse insider trading activity.

    Uses a local SQLite database for persistence and the EDGAR FilingFetcher /
    FilingParser pipeline to ingest new Form 4 filings.
    """

    def __init__(
        self,
        db_path: Optional[str | Path] = None,
        fetcher: Optional[FilingFetcher] = None,
        parser: Optional[FilingParser] = None,
    ):
        self._db_path = str(db_path or DEFAULT_DB_PATH)
        self._fetcher = fetcher or FilingFetcher()
        self._parser = parser or FilingParser()
        self._init_db()

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE_SQL)
            conn.execute(_CREATE_INDEX_SQL)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _store_transaction(self, txn: InsiderTransaction, accession: str = "") -> None:
        """Insert a transaction into the database (ignore duplicates)."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO insider_transactions
                    (ticker, insider_name, title, transaction_type,
                     shares, price, total_value, date, is_10b5_plan,
                     accession_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    txn.ticker,
                    txn.insider_name,
                    txn.title,
                    txn.transaction_type,
                    txn.shares,
                    txn.price,
                    txn.total_value,
                    txn.date,
                    int(txn.is_10b5_plan),
                    accession or None,
                ),
            )

    def _load_transactions(
        self, ticker: str, since: str, txn_type: Optional[str] = None
    ) -> list[InsiderTransaction]:
        """Load transactions from the DB for a ticker since a given date."""
        query = (
            "SELECT ticker, insider_name, title, transaction_type, "
            "shares, price, total_value, date, is_10b5_plan "
            "FROM insider_transactions WHERE ticker = ? AND date >= ?"
        )
        params: list = [ticker.upper(), since]
        if txn_type:
            query += " AND transaction_type = ?"
            params.append(txn_type)
        query += " ORDER BY date DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            InsiderTransaction(
                ticker=r[0],
                insider_name=r[1],
                title=r[2],
                transaction_type=r[3],
                shares=r[4],
                price=r[5],
                total_value=r[6],
                date=r[7],
                is_10b5_plan=bool(r[8]),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_recent_insider_trades(
        self, ticker: str, days: int = 30
    ) -> list[InsiderTransaction]:
        """Fetch recent Form 4 filings for *ticker* and return parsed transactions.

        New filings are fetched from EDGAR and stored in the local database.
        Previously-fetched transactions are returned from the DB cache.

        Args:
            ticker: Stock ticker symbol.
            days: How many days back to look.

        Returns:
            List of InsiderTransaction sorted by date descending.
        """
        ticker = ticker.upper()
        since = (date.today() - timedelta(days=days)).isoformat()

        # Fetch new filings from EDGAR
        filings = self._fetcher.get_recent_filings(
            ticker, FilingType.FORM_4, limit=20
        )

        for filing in filings:
            self._ingest_filing(filing, ticker)

        return self._load_transactions(ticker, since)

    def detect_unusual_activity(self, ticker: str) -> dict:
        """Detect unusual insider trading activity for a ticker.

        Unusual activity is defined as:
        - 3+ distinct insiders buying or selling in the same 7-day window
          ("cluster_buy" or "cluster_sell")
        - A single transaction exceeding $1 000 000 ("large_single")

        Args:
            ticker: Stock ticker symbol.

        Returns:
            Dict with keys: is_unusual, signal_type, details.
        """
        ticker = ticker.upper()
        since = (date.today() - timedelta(days=30)).isoformat()
        txns = self._load_transactions(ticker, since)

        if not txns:
            return {"is_unusual": False, "signal_type": None, "details": "No recent insider transactions found."}

        # --- Check for large single transaction ---
        for txn in txns:
            if txn.total_value and txn.total_value > 1_000_000:
                return {
                    "is_unusual": True,
                    "signal_type": "large_single",
                    "details": (
                        f"{txn.insider_name} ({txn.title}) {txn.transaction_type} "
                        f"${txn.total_value:,.0f} of {ticker} on {txn.date}."
                    ),
                }

        # --- Check for cluster activity within 7-day windows ---
        for txn_type in ("buy", "sell"):
            typed = [t for t in txns if t.transaction_type == txn_type]
            if len(typed) < 3:
                continue

            # Sort by date
            typed.sort(key=lambda t: t.date)

            # Sliding window: check every 7-day window
            for i, anchor in enumerate(typed):
                try:
                    anchor_dt = datetime.strptime(anchor.date, "%Y-%m-%d")
                except (ValueError, TypeError):
                    continue
                window_end = anchor_dt + timedelta(days=7)
                names_in_window: set[str] = set()
                for other in typed[i:]:
                    try:
                        other_dt = datetime.strptime(other.date, "%Y-%m-%d")
                    except (ValueError, TypeError):
                        continue
                    if other_dt <= window_end:
                        names_in_window.add(other.insider_name)

                if len(names_in_window) >= 3:
                    signal = f"cluster_{txn_type}"
                    return {
                        "is_unusual": True,
                        "signal_type": signal,
                        "details": (
                            f"{len(names_in_window)} insiders {txn_type}ing {ticker} "
                            f"within a 7-day window starting {anchor.date}: "
                            f"{', '.join(sorted(names_in_window))}."
                        ),
                    }

        return {"is_unusual": False, "signal_type": None, "details": "Activity within normal range."}

    def get_insider_sentiment(self, ticker: str) -> float:
        """Compute insider sentiment score for a ticker.

        Sentiment is a float between -1.0 (all sells) and +1.0 (all buys),
        weighted by transaction value.  Gift transactions are excluded.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            Float from -1.0 to 1.0.  Returns 0.0 if no data.
        """
        ticker = ticker.upper()
        since = (date.today() - timedelta(days=90)).isoformat()
        txns = self._load_transactions(ticker, since)

        buy_value = 0.0
        sell_value = 0.0

        for txn in txns:
            if txn.transaction_type == "buy":
                buy_value += txn.total_value or 0.0
            elif txn.transaction_type == "sell":
                sell_value += txn.total_value or 0.0
            # gifts are ignored

        total = buy_value + sell_value
        if total == 0:
            return 0.0

        # Sentiment: +1 = all buys, -1 = all sells
        sentiment = (buy_value - sell_value) / total
        return round(max(-1.0, min(1.0, sentiment)), 4)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ingest_filing(self, filing: Filing, ticker: str) -> None:
        """Download, parse, and store a single Form 4 filing."""
        try:
            text = self._fetcher.get_filing_document(filing)
            if not text:
                return

            parsed = self._parser.parse_form4(text)
            if not parsed.get("insider_name"):
                return

            txn = InsiderTransaction(
                ticker=ticker,
                insider_name=parsed.get("insider_name", ""),
                title=parsed.get("insider_title", ""),
                transaction_type=parsed.get("transaction_type", "unknown"),
                shares=parsed.get("shares") or 0.0,
                price=parsed.get("price_per_share") or 0.0,
                total_value=parsed.get("total_value") or 0.0,
                date=filing.filed_date,
                is_10b5_plan=parsed.get("is_10b5_plan", False),
            )
            self._store_transaction(txn, filing.accession_number)
        except Exception as exc:
            logger.warning("Failed to ingest Form 4 filing %s: %s", filing.accession_number, exc)
