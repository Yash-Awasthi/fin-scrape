"""
SEC EDGAR filing fetcher with support for 10-K, 10-Q, 8-K, Form 4,
DEF 14A, and 13-F filings.

Uses the EDGAR EFTS full-text search API and the company filing browser.
Respects SEC rate-limiting guidelines (max 10 req/sec) and User-Agent policy.
"""

from __future__ import annotations

import logging
import re
import time
import threading
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Optional
from html.parser import HTMLParser

import requests

logger = logging.getLogger(__name__)

SEC_USER_AGENT = "FinScrape contact@finscrape.dev"

# SEC rate limit: max 10 requests per second
_RATE_LIMIT = 10
_MIN_INTERVAL = 1.0 / _RATE_LIMIT


class FilingType(str, Enum):
    """Supported SEC filing types."""
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    FORM_4 = "4"
    DEF14A = "DEF 14A"
    FORM_13F = "13-F"


@dataclass
class Filing:
    """Represents a single SEC filing."""
    cik: str
    company_name: str
    ticker: str
    filing_type: FilingType
    filed_date: str  # ISO format YYYY-MM-DD
    accession_number: str
    url: str
    document_urls: list[str] = field(default_factory=list)


class _RateLimiter:
    """Thread-safe rate limiter for SEC requests (max 10/sec)."""

    def __init__(self, max_per_second: int = _RATE_LIMIT):
        self._min_interval = 1.0 / max_per_second
        self._last_request: float = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request = time.monotonic()


class FilingFetcher:
    """Fetch SEC filings from EDGAR APIs.

    Supports:
    - EFTS full-text search API
    - EDGAR company filing browser
    - Individual filing document retrieval

    Respects SEC rate limiting (10 req/sec) and User-Agent requirements.
    """

    EFTS_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
    COMPANY_BROWSE_URL = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        "?action=getcompany&CIK={cik}&type={type}"
        "&dateb=&owner=include&count={count}"
    )
    FILING_BASE_URL = "https://www.sec.gov/Archives/edgar/data"
    CIK_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"

    def __init__(
        self,
        user_agent: str = SEC_USER_AGENT,
        rate_limiter: Optional[_RateLimiter] = None,
        session: Optional[requests.Session] = None,
    ):
        self.user_agent = user_agent
        self._rate_limiter = rate_limiter or _RateLimiter()
        self._session = session or requests.Session()
        self._session.headers.update({"User-Agent": self.user_agent})
        self._ticker_to_cik: dict[str, str] = {}
        self._cik_to_ticker: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_recent_filings(
        self,
        ticker: str,
        filing_type: FilingType,
        limit: int = 10,
    ) -> list[Filing]:
        """Fetch recent filings for a ticker and filing type.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL").
            filing_type: Type of filing to search for.
            limit: Maximum number of filings to return.

        Returns:
            List of Filing objects ordered by date descending.
        """
        cik = self._resolve_cik(ticker)
        if not cik:
            logger.warning("Could not resolve CIK for ticker %s", ticker)
            return []

        filings = self._search_filings(cik, filing_type, limit)

        # Attach ticker/company info
        for f in filings:
            f.ticker = ticker.upper()

        return filings[:limit]

    def get_filing_document(self, filing: Filing) -> str:
        """Fetch the raw text content of a filing's primary document.

        Args:
            filing: A Filing object with document_urls or url populated.

        Returns:
            Raw text content of the filing.
        """
        # Try document URLs first (usually the actual filing doc)
        for doc_url in filing.document_urls:
            text = self._fetch_document_text(doc_url)
            if text:
                return text

        # Fall back to the main filing URL
        if filing.url:
            text = self._fetch_document_text(filing.url)
            if text:
                return text

        return ""

    # ------------------------------------------------------------------
    # CIK resolution
    # ------------------------------------------------------------------

    def _resolve_cik(self, ticker: str) -> Optional[str]:
        """Resolve a ticker symbol to a CIK number."""
        ticker = ticker.upper()
        if ticker in self._ticker_to_cik:
            return self._ticker_to_cik[ticker]

        self._load_ticker_map()
        return self._ticker_to_cik.get(ticker)

    def _load_ticker_map(self) -> None:
        """Load the SEC CIK-to-ticker JSON mapping."""
        if self._ticker_to_cik:
            return

        try:
            self._rate_limiter.wait()
            resp = self._session.get(self.CIK_TICKER_URL, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for entry in data.values():
                cik = str(entry.get("cik_str", ""))
                ticker = entry.get("ticker", "").upper()
                if cik and ticker:
                    self._ticker_to_cik[ticker] = cik
                    self._cik_to_ticker[cik.lstrip("0")] = ticker
        except Exception as exc:
            logger.warning("Failed to load CIK-ticker map: %s", exc)

    # ------------------------------------------------------------------
    # Filing search
    # ------------------------------------------------------------------

    def _search_filings(
        self, cik: str, filing_type: FilingType, limit: int
    ) -> list[Filing]:
        """Search EDGAR for filings using the company browse endpoint."""
        type_str = filing_type.value
        url = self.COMPANY_BROWSE_URL.format(
            cik=cik, type=type_str, count=limit
        )

        self._rate_limiter.wait()
        try:
            resp = self._session.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("EDGAR browse request failed: %s", exc)
            return []

        return self._parse_browse_response(resp.text, cik, filing_type)

    def _parse_browse_response(
        self, html: str, cik: str, filing_type: FilingType
    ) -> list[Filing]:
        """Parse the EDGAR company filing browser HTML response."""
        filings: list[Filing] = []

        # Extract company name
        company_match = re.search(
            r'companyName"?>([^<]+)', html
        )
        company_name = company_match.group(1).strip() if company_match else ""

        # Find filing rows - each row has: type, date, accession link
        # Pattern for the filing table rows
        row_pattern = re.compile(
            r'<tr[^>]*>.*?<td[^>]*>([^<]*?'
            + re.escape(filing_type.value)
            + r'[^<]*?)</td>'
            + r'.*?<a\s+href="([^"]+)"[^>]*>.*?</a>'
            + r'.*?<td[^>]*>(\d{4}-\d{2}-\d{2})</td>',
            re.DOTALL,
        )

        for match in row_pattern.finditer(html):
            doc_href = match.group(2)
            filed_date = match.group(3)

            # Extract accession number from URL
            acc_match = re.search(r'(\d{10}-\d{2}-\d{6})', doc_href)
            accession = acc_match.group(1) if acc_match else ""

            full_url = doc_href
            if doc_href.startswith("/"):
                full_url = "https://www.sec.gov" + doc_href

            filings.append(
                Filing(
                    cik=cik,
                    company_name=company_name,
                    ticker="",
                    filing_type=filing_type,
                    filed_date=filed_date,
                    accession_number=accession,
                    url=full_url,
                    document_urls=[],
                )
            )

        # If regex parsing didn't work, try a simpler approach
        if not filings:
            filings = self._parse_browse_simple(html, cik, filing_type)

        return filings

    def _parse_browse_simple(
        self, html: str, cik: str, filing_type: FilingType
    ) -> list[Filing]:
        """Simpler fallback parsing for EDGAR browse results."""
        filings: list[Filing] = []

        # Find all accession number links and dates
        links = re.findall(
            r'href="(/Archives/edgar/data/[^"]+)"', html
        )
        dates = re.findall(r'(\d{4}-\d{2}-\d{2})', html)

        company_match = re.search(r'companyName"?>([^<]+)', html)
        company_name = company_match.group(1).strip() if company_match else ""

        for i, link in enumerate(links):
            acc_match = re.search(r'(\d{10}-\d{2}-\d{6})', link)
            accession = acc_match.group(1) if acc_match else ""
            filed_date = dates[i] if i < len(dates) else ""

            filings.append(
                Filing(
                    cik=cik,
                    company_name=company_name,
                    ticker="",
                    filing_type=filing_type,
                    filed_date=filed_date,
                    accession_number=accession,
                    url="https://www.sec.gov" + link,
                    document_urls=[],
                )
            )

        return filings

    # ------------------------------------------------------------------
    # Document fetching
    # ------------------------------------------------------------------

    def _fetch_document_text(self, url: str) -> str:
        """Fetch and extract text from a filing document URL."""
        self._rate_limiter.wait()
        try:
            resp = self._session.get(url, timeout=30)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to fetch document %s: %s", url, exc)
            return ""

        content = resp.text
        if not content:
            return ""

        # If it looks like HTML, strip tags
        if "<html" in content.lower() or "<body" in content.lower():
            return self._strip_html(content)

        return content

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip HTML tags and return plain text."""

        class _HTMLTextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.pieces: list[str] = []
                self._skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style"):
                    self._skip = True

            def handle_endtag(self, tag):
                if tag in ("script", "style"):
                    self._skip = False

            def handle_data(self, data):
                if not self._skip:
                    self.pieces.append(data)

        extractor = _HTMLTextExtractor()
        try:
            extractor.feed(html)
        except Exception:
            # Fall back to regex stripping
            return re.sub(r'<[^>]+>', ' ', html)

        text = " ".join(extractor.pieces)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
