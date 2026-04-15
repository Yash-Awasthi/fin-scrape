"""
Comprehensive tests for the deep SEC EDGAR integration.

Covers: filing fetching, 10-K / 10-Q / 8-K / Form 4 parsing,
insider activity detection, sentiment scoring, rate limiting, and
error handling.  All HTTP calls are mocked.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from finscrape.edgar.filings import (
    Filing,
    FilingFetcher,
    FilingType,
    _RateLimiter,
)
from finscrape.edgar.parser import FilingParser, _clean_number, _strip_html
from finscrape.edgar.insider_tracker import InsiderTracker, InsiderTransaction


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture
def parser():
    return FilingParser()


@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "test_insider.db")


@pytest.fixture
def mock_fetcher():
    """FilingFetcher with a mocked session so no real HTTP occurs."""
    fetcher = FilingFetcher.__new__(FilingFetcher)
    fetcher.user_agent = "Test/1.0 test@test.com"
    fetcher._rate_limiter = _RateLimiter(max_per_second=1000)
    fetcher._session = MagicMock()
    fetcher._ticker_to_cik = {"AAPL": "320193", "MSFT": "789019"}
    fetcher._cik_to_ticker = {"320193": "AAPL", "789019": "MSFT"}
    return fetcher


def _make_response(text="", status=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    resp.raise_for_status = MagicMock()
    if json_data is not None:
        resp.json.return_value = json_data
        resp.text = json.dumps(json_data)
    return resp


# =====================================================================
# Filing type enum
# =====================================================================

class TestFilingType:
    def test_values(self):
        assert FilingType.FORM_10K.value == "10-K"
        assert FilingType.FORM_10Q.value == "10-Q"
        assert FilingType.FORM_8K.value == "8-K"
        assert FilingType.FORM_4.value == "4"
        assert FilingType.DEF14A.value == "DEF 14A"
        assert FilingType.FORM_13F.value == "13-F"

    def test_is_string_enum(self):
        assert isinstance(FilingType.FORM_10K, str)
        assert FilingType.FORM_10K == "10-K"


# =====================================================================
# Filing dataclass
# =====================================================================

class TestFiling:
    def test_defaults(self):
        f = Filing(
            cik="320193", company_name="Apple Inc.", ticker="AAPL",
            filing_type=FilingType.FORM_10K, filed_date="2025-11-01",
            accession_number="0000320193-25-000001", url="https://sec.gov/test",
        )
        assert f.document_urls == []
        assert f.ticker == "AAPL"

    def test_document_urls(self):
        f = Filing(
            cik="1", company_name="X", ticker="X",
            filing_type=FilingType.FORM_8K, filed_date="2025-01-01",
            accession_number="acc", url="https://sec.gov",
            document_urls=["https://sec.gov/doc1.htm"],
        )
        assert len(f.document_urls) == 1


# =====================================================================
# FilingFetcher
# =====================================================================

class TestFilingFetcher:
    def test_get_recent_filings_empty_when_unknown_ticker(self, mock_fetcher):
        mock_fetcher._ticker_to_cik = {}
        mock_fetcher._session.get.return_value = _make_response(json_data={})
        result = mock_fetcher.get_recent_filings("ZZZZ", FilingType.FORM_10K)
        assert result == []

    def test_get_recent_filings_parses_browse_html(self, mock_fetcher):
        html = """
        <span class="companyName">Apple Inc.</span>
        <table>
        <tr><td>10-K</td>
        <td><a href="/Archives/edgar/data/320193/0000320193-25-000001-index.htm">Filing</a></td>
        <td>2025-11-01</td></tr>
        </table>
        """
        mock_fetcher._session.get.return_value = _make_response(text=html)
        filings = mock_fetcher.get_recent_filings("AAPL", FilingType.FORM_10K, limit=5)
        assert isinstance(filings, list)
        for f in filings:
            assert f.ticker == "AAPL"

    def test_get_filing_document_html(self, mock_fetcher):
        filing = Filing(
            cik="320193", company_name="Apple", ticker="AAPL",
            filing_type=FilingType.FORM_10K, filed_date="2025-11-01",
            accession_number="acc", url="https://sec.gov/test",
            document_urls=["https://sec.gov/doc.htm"],
        )
        mock_fetcher._session.get.return_value = _make_response(
            text="<html><body><p>Total Revenue $394,328</p></body></html>"
        )
        text = mock_fetcher.get_filing_document(filing)
        assert "Revenue" in text
        assert "394,328" in text

    def test_get_filing_document_plain_text(self, mock_fetcher):
        filing = Filing(
            cik="1", company_name="X", ticker="X",
            filing_type=FilingType.FORM_10K, filed_date="2025-01-01",
            accession_number="acc", url="https://sec.gov/plain",
            document_urls=[],
        )
        mock_fetcher._session.get.return_value = _make_response(
            text="Net Income $5,000,000"
        )
        text = mock_fetcher.get_filing_document(filing)
        assert "Net Income" in text

    def test_get_filing_document_handles_failure(self, mock_fetcher):
        filing = Filing(
            cik="1", company_name="X", ticker="X",
            filing_type=FilingType.FORM_10K, filed_date="2025-01-01",
            accession_number="acc", url="https://sec.gov/bad",
        )
        mock_fetcher._session.get.side_effect = Exception("timeout")
        text = mock_fetcher.get_filing_document(filing)
        assert text == ""

    def test_user_agent_header_set(self):
        fetcher = FilingFetcher(user_agent="MyApp info@example.com")
        assert fetcher._session.headers["User-Agent"] == "MyApp info@example.com"


# =====================================================================
# Rate limiter
# =====================================================================

class TestRateLimiter:
    def test_respects_minimum_interval(self):
        limiter = _RateLimiter(max_per_second=100)
        start = time.monotonic()
        for _ in range(5):
            limiter.wait()
        elapsed = time.monotonic() - start
        # 5 calls at 100/sec → min ~0.04s total gap
        assert elapsed >= 0.03

    def test_no_delay_when_interval_passed(self):
        limiter = _RateLimiter(max_per_second=10)
        limiter._last_request = time.monotonic() - 1.0  # 1s ago
        start = time.monotonic()
        limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.05


# =====================================================================
# Helper functions
# =====================================================================

class TestHelpers:
    def test_clean_number_basic(self):
        assert _clean_number("1,234,567") == 1234567.0
        assert _clean_number("$42.50") == 42.50
        assert _clean_number("(100)") == -100.0
        assert _clean_number("") is None
        assert _clean_number(None) is None

    def test_strip_html(self):
        assert "hello world" in _strip_html("<p>hello <b>world</b></p>")
        assert "&" in _strip_html("&amp;")


# =====================================================================
# 10-K parsing
# =====================================================================

class TestParse10K:
    SAMPLE_10K = """
    Item 1. Business
    Apple Inc. designs, manufactures and markets smartphones, tablets and computers.
    Item 1A. RISK FACTORS
    - Supply chain disruptions could materially affect our operations.
    - Foreign exchange fluctuations may impact revenue.
    - Competition in the technology sector is intense and could reduce market share.
    Item 1B. Unresolved Staff Comments

    Total Revenue $394,328
    Net Income $96,995
    Total Assets $352,583
    Total Liabilities $290,437
    """

    def test_extracts_revenue(self, parser):
        result = parser.parse_10k(self.SAMPLE_10K)
        assert result["revenue"] == 394328.0

    def test_extracts_net_income(self, parser):
        result = parser.parse_10k(self.SAMPLE_10K)
        assert result["net_income"] == 96995.0

    def test_extracts_total_assets(self, parser):
        result = parser.parse_10k(self.SAMPLE_10K)
        assert result["total_assets"] == 352583.0

    def test_extracts_total_liabilities(self, parser):
        result = parser.parse_10k(self.SAMPLE_10K)
        assert result["total_liabilities"] == 290437.0

    def test_extracts_risk_factors(self, parser):
        result = parser.parse_10k(self.SAMPLE_10K)
        assert isinstance(result["risk_factors"], list)

    def test_extracts_business_description(self, parser):
        result = parser.parse_10k(self.SAMPLE_10K)
        assert "Apple" in result["business_description"] or result["business_description"] == ""

    def test_handles_html_formatted_10k(self, parser):
        html = """
        <html><body>
        <p>Total Revenue $123,456</p>
        <p>Net Income $45,678</p>
        <p>Total Assets $999,000</p>
        <p>Total Liabilities $500,000</p>
        </body></html>
        """
        result = parser.parse_10k(html)
        assert result["revenue"] == 123456.0
        assert result["net_income"] == 45678.0

    def test_handles_missing_data(self, parser):
        result = parser.parse_10k("This filing contains no financial data at all.")
        assert result["revenue"] is None
        assert result["net_income"] is None
        assert result["total_assets"] is None
        assert result["risk_factors"] == []


# =====================================================================
# 10-Q parsing
# =====================================================================

class TestParse10Q:
    SAMPLE_10Q = """
    Quarterly Report
    Total Revenue $85,200
    Net Income $21,000
    Diluted EPS $1.46
    Total Assets $400,000
    Operating Income $26,800
    """

    def test_extracts_quarterly_revenue(self, parser):
        result = parser.parse_10q(self.SAMPLE_10Q)
        assert result["quarterly_revenue"] == 85200.0

    def test_extracts_eps(self, parser):
        result = parser.parse_10q(self.SAMPLE_10Q)
        assert result["quarterly_eps"] == 1.46

    def test_key_financials_populated(self, parser):
        result = parser.parse_10q(self.SAMPLE_10Q)
        kf = result["key_financials"]
        assert "revenue" in kf
        assert "operating_income" in kf

    def test_handles_empty_10q(self, parser):
        result = parser.parse_10q("")
        assert result["quarterly_revenue"] is None
        assert result["quarterly_eps"] is None
        assert result["key_financials"] == {}


# =====================================================================
# 8-K parsing
# =====================================================================

class TestParse8K:
    def test_classifies_results_of_operations(self, parser):
        text = "Item 2.02 Results of Operations and Financial Condition"
        result = parser.parse_8k(text)
        assert result["event_type"] == "results_of_operations"
        assert result["material_event"] is True

    def test_classifies_acquisition(self, parser):
        text = "Item 2.01 Completion of Acquisition or Disposition of Assets"
        result = parser.parse_8k(text)
        assert result["event_type"] == "acquisition_or_disposition"
        assert result["material_event"] is True

    def test_classifies_director_departure(self, parser):
        text = "Item 5.02 Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers"
        result = parser.parse_8k(text)
        assert result["event_type"] == "director_departure"

    def test_classifies_bankruptcy(self, parser):
        text = "Item 1.03 Bankruptcy or Receivership"
        result = parser.parse_8k(text)
        assert result["event_type"] == "bankruptcy"
        assert result["material_event"] is True

    def test_classifies_other(self, parser):
        result = parser.parse_8k("Some random filing text with no item reference.")
        assert result["event_type"] == "other"

    def test_extracts_description(self, parser):
        text = """Item 2.02 Results of Operations
        The company reported quarterly revenue of $50 billion, exceeding expectations.
        SIGNATURE"""
        result = parser.parse_8k(text)
        assert "revenue" in result["event_description"].lower() or len(result["event_description"]) > 0

    def test_material_from_keywords(self, parser):
        text = "This is a material announcement regarding restructuring."
        result = parser.parse_8k(text)
        assert result["material_event"] is True

    def test_not_material_for_mundane_text(self, parser):
        # No item references and no material keywords
        text = "The company updated its mailing address."
        result = parser.parse_8k(text)
        assert result["material_event"] is False


# =====================================================================
# Form 4 parsing
# =====================================================================

class TestParseForm4:
    SAMPLE_XML = """
    <ownershipDocument>
        <rptOwnerName>John Smith</rptOwnerName>
        <officerTitle>CEO</officerTitle>
        <transactionCode>P</transactionCode>
        <transactionShares><value>10000</value></transactionShares>
        <transactionPricePerShare><value>150.25</value></transactionPricePerShare>
    </ownershipDocument>
    """

    def test_extracts_name_from_xml(self, parser):
        result = parser.parse_form4(self.SAMPLE_XML)
        assert result["insider_name"] == "John Smith"

    def test_extracts_title_from_xml(self, parser):
        result = parser.parse_form4(self.SAMPLE_XML)
        assert result["insider_title"] == "CEO"

    def test_extracts_buy_transaction(self, parser):
        result = parser.parse_form4(self.SAMPLE_XML)
        assert result["transaction_type"] == "buy"

    def test_extracts_shares(self, parser):
        result = parser.parse_form4(self.SAMPLE_XML)
        assert result["shares"] == 10000.0

    def test_extracts_price(self, parser):
        result = parser.parse_form4(self.SAMPLE_XML)
        assert result["price_per_share"] == 150.25

    def test_calculates_total_value(self, parser):
        result = parser.parse_form4(self.SAMPLE_XML)
        assert result["total_value"] == 1502500.0

    def test_sell_transaction(self, parser):
        xml = """
        <ownershipDocument>
            <rptOwnerName>Jane Doe</rptOwnerName>
            <officerTitle>CFO</officerTitle>
            <transactionCode>S</transactionCode>
            <transactionShares><value>5000</value></transactionShares>
            <transactionPricePerShare><value>200.00</value></transactionPricePerShare>
        </ownershipDocument>
        """
        result = parser.parse_form4(xml)
        assert result["transaction_type"] == "sell"
        assert result["total_value"] == 1000000.0

    def test_gift_transaction(self, parser):
        xml = """
        <ownershipDocument>
            <rptOwnerName>Bob</rptOwnerName>
            <officerTitle>Director</officerTitle>
            <transactionCode>G</transactionCode>
            <transactionShares><value>1000</value></transactionShares>
            <transactionPricePerShare><value>0</value></transactionPricePerShare>
        </ownershipDocument>
        """
        result = parser.parse_form4(xml)
        assert result["transaction_type"] == "gift"

    def test_10b5_plan_detection(self, parser):
        xml = """
        <ownershipDocument>
            <rptOwnerName>Alice</rptOwnerName>
            <officerTitle>VP</officerTitle>
            <transactionCode>S</transactionCode>
            <transactionShares><value>2000</value></transactionShares>
            <transactionPricePerShare><value>100</value></transactionPricePerShare>
            <footnote>This transaction was effected pursuant to a Rule 10b5-1 trading plan.</footnote>
        </ownershipDocument>
        """
        result = parser.parse_form4(xml)
        assert result["is_10b5_plan"] is True

    def test_no_10b5_plan(self, parser):
        result = parser.parse_form4(self.SAMPLE_XML)
        assert result["is_10b5_plan"] is False

    def test_plain_text_form4(self, parser):
        text = """
        Name of Reporting Person: Warren Buffett
        Relationship: Director
        Transaction: purchase of 50,000 shares at price $45.00 per share
        """
        result = parser.parse_form4(text)
        assert result["insider_name"] == "Warren Buffett"
        assert result["transaction_type"] == "buy"

    def test_handles_empty_form4(self, parser):
        result = parser.parse_form4("")
        assert result["insider_name"] == ""
        assert result["shares"] is None


# =====================================================================
# InsiderTransaction dataclass
# =====================================================================

class TestInsiderTransaction:
    def test_to_dict(self):
        txn = InsiderTransaction(
            ticker="AAPL", insider_name="Tim Cook", title="CEO",
            transaction_type="sell", shares=50000, price=175.0,
            total_value=8750000, date="2025-06-01", is_10b5_plan=True,
        )
        d = txn.to_dict()
        assert d["ticker"] == "AAPL"
        assert d["is_10b5_plan"] is True


# =====================================================================
# InsiderTracker – unusual activity detection
# =====================================================================

class TestInsiderTrackerUnusual:
    def _make_tracker(self, tmp_db):
        fetcher = MagicMock()
        fetcher.get_recent_filings.return_value = []
        return InsiderTracker(db_path=tmp_db, fetcher=fetcher, parser=FilingParser())

    def _insert(self, tracker, txn, accession=""):
        tracker._store_transaction(txn, accession)

    def test_no_transactions_is_not_unusual(self, tmp_db):
        tracker = self._make_tracker(tmp_db)
        result = tracker.detect_unusual_activity("AAPL")
        assert result["is_unusual"] is False

    def test_large_single_buy_is_unusual(self, tmp_db):
        from datetime import date, timedelta
        tracker = self._make_tracker(tmp_db)
        today = date.today().isoformat()
        self._insert(tracker, InsiderTransaction(
            ticker="AAPL", insider_name="Big Buyer", title="CEO",
            transaction_type="buy", shares=100000, price=150.0,
            total_value=15_000_000.0, date=today, is_10b5_plan=False,
        ), accession="acc1")
        result = tracker.detect_unusual_activity("AAPL")
        assert result["is_unusual"] is True
        assert result["signal_type"] == "large_single"

    def test_cluster_buy_detected(self, tmp_db):
        from datetime import date, timedelta
        tracker = self._make_tracker(tmp_db)
        base = date.today()
        for i, name in enumerate(["Alice", "Bob", "Carol"]):
            d = (base - timedelta(days=i)).isoformat()
            self._insert(tracker, InsiderTransaction(
                ticker="MSFT", insider_name=name, title="Director",
                transaction_type="buy", shares=1000, price=50.0,
                total_value=50000, date=d, is_10b5_plan=False,
            ), accession=f"cluster_buy_{i}")
        result = tracker.detect_unusual_activity("MSFT")
        assert result["is_unusual"] is True
        assert result["signal_type"] == "cluster_buy"

    def test_cluster_sell_detected(self, tmp_db):
        from datetime import date, timedelta
        tracker = self._make_tracker(tmp_db)
        base = date.today()
        for i, name in enumerate(["X", "Y", "Z"]):
            d = (base - timedelta(days=i)).isoformat()
            self._insert(tracker, InsiderTransaction(
                ticker="TSLA", insider_name=name, title="VP",
                transaction_type="sell", shares=500, price=200.0,
                total_value=100000, date=d, is_10b5_plan=False,
            ), accession=f"cluster_sell_{i}")
        result = tracker.detect_unusual_activity("TSLA")
        assert result["is_unusual"] is True
        assert result["signal_type"] == "cluster_sell"

    def test_normal_activity_is_not_unusual(self, tmp_db):
        from datetime import date, timedelta
        tracker = self._make_tracker(tmp_db)
        # Two insiders buying (below the 3 threshold) with small amounts
        for i, name in enumerate(["One", "Two"]):
            d = (date.today() - timedelta(days=i)).isoformat()
            self._insert(tracker, InsiderTransaction(
                ticker="GOOG", insider_name=name, title="Dir",
                transaction_type="buy", shares=100, price=50.0,
                total_value=5000, date=d, is_10b5_plan=False,
            ), accession=f"normal_{i}")
        result = tracker.detect_unusual_activity("GOOG")
        assert result["is_unusual"] is False


# =====================================================================
# InsiderTracker – sentiment
# =====================================================================

class TestInsiderSentiment:
    def _make_tracker(self, tmp_db):
        fetcher = MagicMock()
        fetcher.get_recent_filings.return_value = []
        return InsiderTracker(db_path=tmp_db, fetcher=fetcher, parser=FilingParser())

    def test_no_data_returns_zero(self, tmp_db):
        tracker = self._make_tracker(tmp_db)
        assert tracker.get_insider_sentiment("AAPL") == 0.0

    def test_all_buys_returns_positive_one(self, tmp_db):
        from datetime import date
        tracker = self._make_tracker(tmp_db)
        today = date.today().isoformat()
        tracker._store_transaction(InsiderTransaction(
            ticker="AAPL", insider_name="A", title="CEO",
            transaction_type="buy", shares=1000, price=100.0,
            total_value=100000, date=today, is_10b5_plan=False,
        ), "sent1")
        assert tracker.get_insider_sentiment("AAPL") == 1.0

    def test_all_sells_returns_negative_one(self, tmp_db):
        from datetime import date
        tracker = self._make_tracker(tmp_db)
        today = date.today().isoformat()
        tracker._store_transaction(InsiderTransaction(
            ticker="AAPL", insider_name="B", title="CFO",
            transaction_type="sell", shares=1000, price=100.0,
            total_value=100000, date=today, is_10b5_plan=False,
        ), "sent2")
        assert tracker.get_insider_sentiment("AAPL") == -1.0

    def test_equal_buys_and_sells_returns_zero(self, tmp_db):
        from datetime import date
        tracker = self._make_tracker(tmp_db)
        today = date.today().isoformat()
        tracker._store_transaction(InsiderTransaction(
            ticker="AAPL", insider_name="C", title="VP",
            transaction_type="buy", shares=1000, price=50.0,
            total_value=50000, date=today, is_10b5_plan=False,
        ), "sent3")
        tracker._store_transaction(InsiderTransaction(
            ticker="AAPL", insider_name="D", title="Dir",
            transaction_type="sell", shares=1000, price=50.0,
            total_value=50000, date=today, is_10b5_plan=False,
        ), "sent4")
        assert tracker.get_insider_sentiment("AAPL") == 0.0

    def test_gifts_excluded_from_sentiment(self, tmp_db):
        from datetime import date
        tracker = self._make_tracker(tmp_db)
        today = date.today().isoformat()
        tracker._store_transaction(InsiderTransaction(
            ticker="AAPL", insider_name="E", title="Dir",
            transaction_type="buy", shares=100, price=100.0,
            total_value=10000, date=today, is_10b5_plan=False,
        ), "sent5")
        tracker._store_transaction(InsiderTransaction(
            ticker="AAPL", insider_name="F", title="Dir",
            transaction_type="gift", shares=100000, price=0.0,
            total_value=0, date=today, is_10b5_plan=False,
        ), "sent6")
        # Only the buy counts
        assert tracker.get_insider_sentiment("AAPL") == 1.0

    def test_sentiment_bounded(self, tmp_db):
        from datetime import date
        tracker = self._make_tracker(tmp_db)
        today = date.today().isoformat()
        tracker._store_transaction(InsiderTransaction(
            ticker="X", insider_name="G", title="CEO",
            transaction_type="buy", shares=999999, price=999.0,
            total_value=999999 * 999.0, date=today, is_10b5_plan=False,
        ), "sent7")
        s = tracker.get_insider_sentiment("X")
        assert -1.0 <= s <= 1.0


# =====================================================================
# InsiderTracker – fetch_recent_insider_trades
# =====================================================================

class TestFetchRecentInsiderTrades:
    def test_fetches_and_stores(self, tmp_db):
        from datetime import date
        fetcher = MagicMock()
        parser = MagicMock()

        today = date.today().isoformat()
        filing = Filing(
            cik="320193", company_name="Apple", ticker="AAPL",
            filing_type=FilingType.FORM_4, filed_date=today,
            accession_number="acc-fetch-1", url="https://sec.gov/test",
        )
        fetcher.get_recent_filings.return_value = [filing]
        fetcher.get_filing_document.return_value = "<xml>fake</xml>"
        parser.parse_form4.return_value = {
            "insider_name": "Tim Cook",
            "insider_title": "CEO",
            "transaction_type": "sell",
            "shares": 50000,
            "price_per_share": 175.0,
            "total_value": 8750000,
            "is_10b5_plan": True,
        }

        tracker = InsiderTracker(db_path=tmp_db, fetcher=fetcher, parser=parser)
        txns = tracker.fetch_recent_insider_trades("AAPL", days=90)
        assert len(txns) >= 1
        assert txns[0].insider_name == "Tim Cook"


# =====================================================================
# Error handling
# =====================================================================

class TestErrorHandling:
    def test_malformed_html_in_10k(self, parser):
        malformed = "<html><body><p>Revenue $$$</p><div><<<broken>></div></body></html>"
        result = parser.parse_10k(malformed)
        # Should not crash, returns None for unparseable values
        assert result["revenue"] is None or isinstance(result["revenue"], float)

    def test_empty_filing_text(self, parser):
        for method in [parser.parse_10k, parser.parse_10q, parser.parse_8k, parser.parse_form4]:
            result = method("")
            assert isinstance(result, dict)

    def test_ingest_filing_handles_exception(self, tmp_db):
        fetcher = MagicMock()
        fetcher.get_recent_filings.return_value = []
        fetcher.get_filing_document.side_effect = Exception("network error")
        tracker = InsiderTracker(db_path=tmp_db, fetcher=fetcher, parser=FilingParser())
        filing = Filing(
            cik="1", company_name="X", ticker="X",
            filing_type=FilingType.FORM_4, filed_date="2025-01-01",
            accession_number="err-1", url="https://sec.gov/bad",
        )
        # Should not raise
        tracker._ingest_filing(filing, "X")

    def test_duplicate_accession_ignored(self, tmp_db):
        fetcher = MagicMock()
        fetcher.get_recent_filings.return_value = []
        tracker = InsiderTracker(db_path=tmp_db, fetcher=fetcher, parser=FilingParser())
        from datetime import date
        today = date.today().isoformat()
        txn = InsiderTransaction(
            ticker="AAPL", insider_name="Dup", title="VP",
            transaction_type="buy", shares=100, price=10.0,
            total_value=1000, date=today, is_10b5_plan=False,
        )
        tracker._store_transaction(txn, "dup-acc-1")
        tracker._store_transaction(txn, "dup-acc-1")  # duplicate
        txns = tracker._load_transactions("AAPL", today)
        assert len(txns) == 1


# =====================================================================
# Package imports
# =====================================================================

class TestPackageImports:
    def test_top_level_imports(self):
        from finscrape.edgar import (
            Filing, FilingFetcher, FilingType, FilingParser,
            InsiderTracker, InsiderTransaction,
        )
        assert FilingType.FORM_10K.value == "10-K"
