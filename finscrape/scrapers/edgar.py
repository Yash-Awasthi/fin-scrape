"""
SEC EDGAR 8-K filing scraper.

Fetches recent 8-K filings (material events) from the EDGAR full-text
search API and extracts filing content as ScrapedArticle objects.

8-K filings cover material events: earnings, M&A, executive changes,
bankruptcy, asset sales, delistings, etc.
"""

from __future__ import annotations

import json
import logging
import re
import datetime
from typing import Optional
from xml.etree import ElementTree

from finscrape.scrapers import BaseScraper, MAX_WORDS
from finscrape.models import ScrapedArticle

logger = logging.getLogger(__name__)

SEC_USER_AGENT = "FinScrape/0.3 (contact@finscrape.dev)"

# EDGAR full-text search API (JSON, no auth needed)
EFTS_SEARCH_URL = (
    "https://efts.sec.gov/LATEST/search-index"
    "?q=%228-K%22&forms=8-K&dateRange=custom"
    "&startdt={start}&enddt={end}"
)

# Filing document base URL
FILING_BASE_URL = "https://www.sec.gov/Archives/edgar/data"

# CIK-to-ticker mapping endpoint
CIK_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"


class EdgarScraper(BaseScraper):
    name = "edgar"

    def __init__(self, max_articles: int = 20):
        super().__init__(max_articles=max_articles)
        self._cik_to_ticker: dict[str, str] = {}

    def scrape_news(self) -> list[ScrapedArticle]:
        self._load_cik_ticker_map()

        filings = self._fetch_recent_filings()
        logger.info("[%s] Found %d recent 8-K filings", self.name, len(filings))

        articles: list[ScrapedArticle] = []
        for filing in filings[: self.max_articles]:
            article = self._process_filing(filing)
            if article and article.has_content:
                articles.append(article)

        logger.info("[%s] Produced %d valid articles", self.name, len(articles))
        return articles

    # ------------------------------------------------------------------
    # CIK → Ticker mapping
    # ------------------------------------------------------------------

    def _load_cik_ticker_map(self) -> None:
        """Load the SEC CIK-to-ticker JSON mapping."""
        try:
            page = self.fetch_page(CIK_TICKER_URL)
            if not page:
                logger.warning("[%s] Could not fetch CIK ticker map", self.name)
                return
            raw = page.text
            if not raw:
                return
            data = json.loads(raw)
            for entry in data.values():
                cik = str(entry.get("cik_str", "")).lstrip("0")
                ticker = entry.get("ticker", "")
                if cik and ticker:
                    self._cik_to_ticker[cik] = ticker.upper()
            logger.info(
                "[%s] Loaded %d CIK→ticker mappings", self.name, len(self._cik_to_ticker)
            )
        except Exception as e:
            logger.warning("[%s] CIK ticker map load failed: %s", self.name, e)

    def _ticker_for_cik(self, cik: str) -> Optional[str]:
        """Resolve a CIK number to a ticker symbol."""
        return self._cik_to_ticker.get(cik.lstrip("0"))

    # ------------------------------------------------------------------
    # Fetch recent filings via EFTS search API
    # ------------------------------------------------------------------

    def _fetch_recent_filings(self) -> list[dict]:
        """Query EDGAR full-text search for recent 8-K filings."""
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        url = EFTS_SEARCH_URL.format(
            start=yesterday.isoformat(), end=today.isoformat()
        )

        try:
            page = self.fetch_page(url)
            if not page:
                logger.warning("[%s] EFTS search returned no page", self.name)
                return self._fetch_filings_atom_fallback()
            raw = page.text
            if not raw:
                return self._fetch_filings_atom_fallback()
            data = json.loads(raw)
        except Exception as e:
            logger.warning("[%s] EFTS search failed (%s), trying ATOM feed", self.name, e)
            return self._fetch_filings_atom_fallback()

        hits = data.get("hits", {}).get("hits", [])
        filings: list[dict] = []

        for hit in hits:
            src = hit.get("_source", {})
            cik = str(src.get("ciks", [""])[0]) if src.get("ciks") else ""
            company = src.get("display_names", [""])[0] if src.get("display_names") else ""
            filed = src.get("file_date", "")
            # Build the filing index URL from the accession number
            accession = src.get("file_num", "")
            # The _id typically contains the accession number path
            doc_id = hit.get("_id", "")

            filing_url = ""
            if doc_id:
                # doc_id format is usually like "0001234567-24-012345"
                # Convert to URL path
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{doc_id.replace('-', '')}/{doc_id}-index.htm"

            filings.append({
                "cik": cik,
                "company": company,
                "filed": filed,
                "url": filing_url,
                "doc_id": doc_id,
            })

        return filings

    def _fetch_filings_atom_fallback(self) -> list[dict]:
        """Fallback: parse the EDGAR ATOM feed for recent 8-K filings."""
        atom_url = (
            "https://www.sec.gov/cgi-bin/browse-edgar"
            "?action=getcompany&type=8-K&dateb=&owner=include"
            "&count=40&search_text=&action=getcompany&output=atom"
        )

        page = self.fetch_page(atom_url)
        if not page:
            return []

        raw_xml = page.text
        if not raw_xml:
            return []

        filings: list[dict] = []
        try:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            root = ElementTree.fromstring(raw_xml)
            for entry in root.findall("atom:entry", ns):
                title_el = entry.find("atom:title", ns)
                link_el = entry.find("atom:link", ns)
                updated_el = entry.find("atom:updated", ns)
                summary_el = entry.find("atom:summary", ns)

                title_text = title_el.text if title_el is not None else ""
                href = link_el.attrib.get("href", "") if link_el is not None else ""
                updated = updated_el.text if updated_el is not None else ""
                summary = summary_el.text if summary_el is not None else ""

                # Extract CIK from the link URL
                cik_match = re.search(r"CIK=(\d+)", href)
                cik = cik_match.group(1) if cik_match else ""

                # Extract company name from title (format: "8-K - Company Name (0001234)")
                company_match = re.search(r"8-K\s*-\s*(.+?)\s*\(", title_text)
                company = company_match.group(1).strip() if company_match else title_text

                filings.append({
                    "cik": cik,
                    "company": company,
                    "filed": updated[:10] if updated else "",
                    "url": href,
                    "doc_id": "",
                })
        except Exception as e:
            logger.warning("[%s] ATOM feed parsing failed: %s", self.name, e)

        return filings

    # ------------------------------------------------------------------
    # Process individual filings
    # ------------------------------------------------------------------

    def _process_filing(self, filing: dict) -> Optional[ScrapedArticle]:
        """Fetch a filing page and build a ScrapedArticle."""
        url = filing.get("url", "")
        if not url:
            return None

        company = filing.get("company", "")
        cik = filing.get("cik", "")
        filed = filing.get("filed", "")

        # Resolve ticker
        ticker = self._ticker_for_cik(cik) if cik else None
        tickers = [ticker] if ticker else []

        # Fetch the filing index page
        page = self.fetch_page(url)
        if not page:
            return self._build_article_from_metadata(filing, tickers)

        # Try to find the actual 8-K document link on the index page
        doc_url = self._find_8k_document_url(page, url)
        text = ""

        if doc_url:
            doc_page = self.fetch_page(doc_url)
            if doc_page:
                text = self._extract_filing_text(doc_page)

        # Fall back to extracting from the index page itself
        if not text:
            text = self._extract_filing_text(page)

        if not text:
            return self._build_article_from_metadata(filing, tickers)

        # Also try to extract tickers from the filing text
        text_tickers = self.extract_tickers_from_text(text)
        for t in text_tickers:
            if t not in tickers:
                tickers.append(t)

        # Title
        title = f"8-K Filing: {company}" if company else "8-K Filing"
        if ticker:
            title = f"8-K Filing: {company} ({ticker})"

        # Compute age
        pub_date, age = self._parse_filing_date(filed)

        return ScrapedArticle(
            url=url,
            title=title,
            text=text,
            source=self.name,
            published_at=pub_date,
            age_hours=age,
            raw_tickers=tickers,
        )

    def _find_8k_document_url(self, index_page, base_url: str) -> Optional[str]:
        """Find the actual 8-K document link from the filing index page."""
        for link in index_page.css("a[href]"):
            href = link.attrib.get("href", "")
            link_text = (link.text or "").lower()

            # Look for the main 8-K document (usually .htm or .html)
            if any(
                pattern in href.lower()
                for pattern in ["8-k", "8k"]
            ) and href.lower().endswith((".htm", ".html")):
                if href.startswith("/"):
                    return "https://www.sec.gov" + href
                elif href.startswith("http"):
                    return href

        # Also look in table rows for the primary document
        for row in index_page.css("table tr"):
            cells = row.css("td")
            for cell in cells:
                cell_text = (cell.text or "").strip().lower()
                if "8-k" in cell_text:
                    for a in row.css("a[href]"):
                        href = a.attrib.get("href", "")
                        if href.endswith((".htm", ".html")):
                            if href.startswith("/"):
                                return "https://www.sec.gov" + href
                            elif href.startswith("http"):
                                return href

        return None

    def _extract_filing_text(self, page) -> str:
        """Extract text content from a filing HTML page."""
        paragraphs = page.css("p")
        selected: list[str] = []

        for p in paragraphs[:50]:
            text = p.text.strip() if p.text else ""
            if len(text) > 30:
                selected.append(text)

        if not selected:
            # Try divs as fallback
            for div in page.css("div"):
                text = div.text.strip() if div.text else ""
                if len(text) > 50:
                    selected.append(text)
                if len(selected) >= 25:
                    break

        full_text = " ".join(selected)

        # Truncate to MAX_WORDS
        words = full_text.split()[:MAX_WORDS]
        return " ".join(words)

    def _build_article_from_metadata(
        self, filing: dict, tickers: list[str]
    ) -> Optional[ScrapedArticle]:
        """Build a minimal article when the filing page cannot be fetched."""
        company = filing.get("company", "")
        if not company:
            return None

        ticker = tickers[0] if tickers else None
        title = f"8-K Filing: {company}"
        if ticker:
            title += f" ({ticker})"

        text = (
            f"{company} filed an 8-K report with the SEC on {filing.get('filed', 'unknown date')}. "
            f"8-K filings disclose material events including earnings announcements, "
            f"mergers and acquisitions, executive changes, and other significant corporate developments."
        )

        pub_date, age = self._parse_filing_date(filing.get("filed", ""))

        return ScrapedArticle(
            url=filing.get("url", ""),
            title=title,
            text=text,
            source=self.name,
            published_at=pub_date,
            age_hours=age,
            raw_tickers=tickers,
        )

    @staticmethod
    def _parse_filing_date(date_str: str) -> tuple[Optional[str], Optional[float]]:
        """Parse a filing date string and compute age in hours."""
        if not date_str:
            return None, None
        try:
            dt = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d").replace(
                tzinfo=datetime.timezone.utc
            )
            age_hours = (
                datetime.datetime.now(datetime.timezone.utc) - dt
            ).total_seconds() / 3600
            return dt.isoformat(), round(age_hours, 1)
        except Exception:
            return date_str, None
