"""
SEC filing content parser.

Extracts structured financial data from 10-K, 10-Q, 8-K, and Form 4 filings.
Handles both HTML-formatted and plain-text filings using regex-based extraction.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def _clean_number(text: str) -> Optional[float]:
    """Parse a number string, handling commas, parentheses (negatives), and $ signs."""
    if not text:
        return None
    text = text.strip()
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]
    text = text.replace("$", "").replace(",", "").strip()
    try:
        val = float(text)
        return -val if negative else val
    except (ValueError, TypeError):
        return None


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class FilingParser:
    """Parse SEC filing content and extract structured financial data.

    Handles both HTML and plain text formats using regex patterns
    tuned to common SEC filing structures.
    """

    # ------------------------------------------------------------------
    # 10-K parsing
    # ------------------------------------------------------------------

    def parse_10k(self, text: str) -> dict:
        """Parse a 10-K annual report and extract key financials.

        Args:
            text: Raw text content of the 10-K filing.

        Returns:
            Dict with keys: revenue, net_income, total_assets,
            total_liabilities, risk_factors, business_description.
        """
        clean = _strip_html(text)

        return {
            "revenue": self._extract_financial_value(clean, _REVENUE_PATTERNS),
            "net_income": self._extract_financial_value(clean, _NET_INCOME_PATTERNS),
            "total_assets": self._extract_financial_value(clean, _TOTAL_ASSETS_PATTERNS),
            "total_liabilities": self._extract_financial_value(clean, _TOTAL_LIABILITIES_PATTERNS),
            "risk_factors": self._extract_risk_factors(clean),
            "business_description": self._extract_business_description(clean),
        }

    # ------------------------------------------------------------------
    # 10-Q parsing
    # ------------------------------------------------------------------

    def parse_10q(self, text: str) -> dict:
        """Parse a 10-Q quarterly report.

        Args:
            text: Raw text content of the 10-Q filing.

        Returns:
            Dict with keys: quarterly_revenue, quarterly_eps, key_financials.
        """
        clean = _strip_html(text)

        quarterly_revenue = self._extract_financial_value(clean, _REVENUE_PATTERNS)
        eps = self._extract_eps(clean)

        key_financials: dict = {}
        for label, patterns in [
            ("revenue", _REVENUE_PATTERNS),
            ("net_income", _NET_INCOME_PATTERNS),
            ("total_assets", _TOTAL_ASSETS_PATTERNS),
            ("operating_income", _OPERATING_INCOME_PATTERNS),
        ]:
            val = self._extract_financial_value(clean, patterns)
            if val is not None:
                key_financials[label] = val

        return {
            "quarterly_revenue": quarterly_revenue,
            "quarterly_eps": eps,
            "key_financials": key_financials,
        }

    # ------------------------------------------------------------------
    # 8-K parsing
    # ------------------------------------------------------------------

    def parse_8k(self, text: str) -> dict:
        """Parse an 8-K current report (material event disclosure).

        Args:
            text: Raw text content of the 8-K filing.

        Returns:
            Dict with keys: event_type, event_description, material_event.
        """
        clean = _strip_html(text)
        event_type = self._classify_8k_event(clean)
        description = self._extract_8k_description(clean)
        material = self._is_material_event(event_type, clean)

        return {
            "event_type": event_type,
            "event_description": description,
            "material_event": material,
        }

    # ------------------------------------------------------------------
    # Form 4 parsing
    # ------------------------------------------------------------------

    def parse_form4(self, text: str) -> dict:
        """Parse a Form 4 insider trading disclosure.

        Args:
            text: Raw text (often XML) content of the Form 4 filing.

        Returns:
            Dict with keys: insider_name, insider_title, transaction_type,
            shares, price_per_share, total_value, is_10b5_plan.
        """
        clean = _strip_html(text)

        insider_name = self._extract_form4_name(text, clean)
        insider_title = self._extract_form4_title(text, clean)
        txn_type = self._extract_form4_transaction_type(text, clean)
        shares = self._extract_form4_shares(text, clean)
        price = self._extract_form4_price(text, clean)
        total_value = round(shares * price, 2) if shares and price else None
        is_10b5 = self._detect_10b5_plan(text, clean)

        return {
            "insider_name": insider_name,
            "insider_title": insider_title,
            "transaction_type": txn_type,
            "shares": shares,
            "price_per_share": price,
            "total_value": total_value,
            "is_10b5_plan": is_10b5,
        }

    # ==================================================================
    # Financial value extraction helpers
    # ==================================================================

    @staticmethod
    def _extract_financial_value(
        text: str, patterns: list[re.Pattern]
    ) -> Optional[float]:
        """Try multiple regex patterns to extract a financial value."""
        for pat in patterns:
            match = pat.search(text)
            if match:
                val = _clean_number(match.group(1))
                if val is not None:
                    return val
        return None

    @staticmethod
    def _extract_eps(text: str) -> Optional[float]:
        """Extract earnings per share from filing text."""
        for pat in _EPS_PATTERNS:
            m = pat.search(text)
            if m:
                val = _clean_number(m.group(1))
                if val is not None:
                    return val
        return None

    # ------------------------------------------------------------------
    # 10-K section extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_risk_factors(text: str) -> list[str]:
        """Extract risk factor headings from a 10-K filing."""
        risks: list[str] = []

        # Look for the Risk Factors section
        rf_match = re.search(
            r'(?:Item\s*1A|RISK\s+FACTORS)[.\s:—\-]*(.*?)(?:Item\s*1B|Item\s*2|UNRESOLVED\s+STAFF|PROPERTIES)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not rf_match:
            return risks

        section = rf_match.group(1)

        # Extract individual risk headings (bold/capitalized lines or bullet items)
        # Risks are often short sentences/phrases before longer descriptions
        risk_patterns = [
            re.compile(r'(?:^|\.\s+)([A-Z][^.]{20,120}\.)', re.MULTILINE),
            re.compile(r'[-•]\s*([A-Z][^.]{15,150}\.?)'),
        ]

        for pat in risk_patterns:
            for m in pat.finditer(section):
                risk_text = m.group(1).strip()
                if len(risk_text) > 15 and risk_text not in risks:
                    risks.append(risk_text)
                if len(risks) >= 20:
                    break
            if risks:
                break

        return risks

    @staticmethod
    def _extract_business_description(text: str) -> str:
        """Extract business description from Item 1 of a 10-K."""
        # Item 1 - Business section
        biz_match = re.search(
            r'(?:Item\s*1[.\s:—\-]+(?:Business)?)(.*?)(?:Item\s*1A|Item\s*2|RISK\s+FACTORS)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if biz_match:
            desc = biz_match.group(1).strip()
            # Truncate to first ~500 chars
            if len(desc) > 500:
                desc = desc[:500].rsplit(" ", 1)[0] + "..."
            return desc

        return ""

    # ------------------------------------------------------------------
    # 8-K event classification
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_8k_event(text: str) -> str:
        """Classify the type of 8-K event based on item numbers and content."""
        text_lower = text.lower()

        event_map = {
            "entry_into_agreement": [r"item\s*1\.01", r"entry into.*material.*agreement"],
            "bankruptcy": [r"item\s*1\.03", r"bankruptcy"],
            "results_of_operations": [r"item\s*2\.02", r"results of operations"],
            "acquisition_or_disposition": [r"item\s*2\.01", r"acquisition", r"disposition of assets"],
            "creation_of_obligation": [r"item\s*2\.03", r"direct financial obligation"],
            "costs_associated_with_exit": [r"item\s*2\.05", r"restructuring"],
            "material_impairment": [r"item\s*2\.06", r"material impairment"],
            "delisting": [r"item\s*3\.01", r"delisting"],
            "unregistered_sale": [r"item\s*3\.02", r"unregistered.*sale"],
            "director_departure": [r"item\s*5\.02", r"departure of director", r"appointment of.*officer"],
            "amendments_to_articles": [r"item\s*5\.03"],
            "regulation_fd": [r"item\s*7\.01", r"regulation fd"],
            "other_events": [r"item\s*8\.01"],
            "financial_statements": [r"item\s*9\.01", r"financial statements"],
        }

        for event_type, patterns in event_map.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return event_type

        return "other"

    @staticmethod
    def _extract_8k_description(text: str) -> str:
        """Extract event description from 8-K filing."""
        # Look for the narrative after item number references
        desc_match = re.search(
            r'(?:Item\s*\d+\.\d+.*?)\n(.*?)(?:SIGNATURE|EXHIBIT|Item\s*\d+\.\d+|\Z)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if desc_match:
            desc = desc_match.group(1).strip()
            if len(desc) > 1000:
                desc = desc[:1000].rsplit(" ", 1)[0] + "..."
            return desc

        # Fallback: first substantial paragraph
        sentences = re.split(r'(?<=[.!?])\s+', text)
        substantial = [s for s in sentences if len(s) > 50]
        if substantial:
            return " ".join(substantial[:3])

        return text[:500] if len(text) > 500 else text

    @staticmethod
    def _is_material_event(event_type: str, text: str) -> bool:
        """Determine if an 8-K event is material."""
        material_types = {
            "results_of_operations",
            "acquisition_or_disposition",
            "bankruptcy",
            "entry_into_agreement",
            "director_departure",
            "delisting",
            "material_impairment",
        }
        if event_type in material_types:
            return True

        # Check for material keywords
        material_kw = re.search(
            r'material|significant|substantial|major',
            text,
            re.IGNORECASE,
        )
        return bool(material_kw)

    # ------------------------------------------------------------------
    # Form 4 extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_form4_name(raw: str, clean: str) -> str:
        """Extract insider name from Form 4."""
        # XML format
        xml_match = re.search(
            r'<rptOwnerName>(.*?)</rptOwnerName>', raw, re.IGNORECASE
        )
        if xml_match:
            return _strip_html(xml_match.group(1)).strip()

        # Plain text / HTML
        name_match = re.search(
            r'(?:Reporting\s+(?:Person|Owner)\s*(?:Name)?[:\s]+)([A-Z][A-Za-z\s,.\'-]+?)(?:\s+(?:Relationship|Title|Transaction|Date|Issuer|Form)|$)',
            clean,
            re.IGNORECASE,
        )
        if name_match:
            return name_match.group(1).strip()

        name_match = re.search(
            r'(?:Name\s+of\s+Reporting\s+Person)[:\s]+([A-Z][A-Za-z\s,.\'-]+?)(?:\s+(?:Relationship|Title|Transaction|Date|Issuer|Form)|$)',
            clean,
            re.IGNORECASE,
        )
        if name_match:
            return name_match.group(1).strip()

        return ""

    @staticmethod
    def _extract_form4_title(raw: str, clean: str) -> str:
        """Extract insider title/relationship from Form 4."""
        xml_match = re.search(
            r'<officerTitle>(.*?)</officerTitle>', raw, re.IGNORECASE
        )
        if xml_match:
            return _strip_html(xml_match.group(1)).strip()

        title_match = re.search(
            r'(?:Relationship|Title)[:\s]+((?:CEO|CFO|COO|CTO|Director|VP|President|'
            r'Officer|Chairman|Secretary|Treasurer|General\s+Counsel|SVP|EVP)[A-Za-z\s,]*)',
            clean,
            re.IGNORECASE,
        )
        if title_match:
            return title_match.group(1).strip()

        return ""

    @staticmethod
    def _extract_form4_transaction_type(raw: str, clean: str) -> str:
        """Determine buy/sell/gift from Form 4 transaction code."""
        # XML transactionCode
        code_match = re.search(
            r'<transactionCode>(.*?)</transactionCode>', raw, re.IGNORECASE
        )
        if code_match:
            code = code_match.group(1).strip().upper()
            if code == "P":
                return "buy"
            elif code in ("S", "F"):
                return "sell"
            elif code == "G":
                return "gift"
            elif code in ("A", "M"):
                return "buy"  # award/exercise
            elif code == "D":
                return "sell"  # disposition

        # XML transactionAcquiredDisposedCode
        ad_match = re.search(
            r'<transactionAcquiredDisposedCode>.*?<value>(.*?)</value>',
            raw,
            re.IGNORECASE | re.DOTALL,
        )
        if ad_match:
            code = ad_match.group(1).strip().upper()
            if code == "A":
                return "buy"
            elif code == "D":
                return "sell"

        # Plain text fallback
        text_lower = clean.lower()
        if "purchase" in text_lower or "acquired" in text_lower:
            return "buy"
        elif "sale" in text_lower or "sold" in text_lower or "disposed" in text_lower:
            return "sell"
        elif "gift" in text_lower:
            return "gift"

        return "unknown"

    @staticmethod
    def _extract_form4_shares(raw: str, clean: str) -> Optional[float]:
        """Extract number of shares from Form 4."""
        # XML transactionShares
        xml_match = re.search(
            r'<transactionShares>.*?<value>([\d,.]+)</value>',
            raw,
            re.IGNORECASE | re.DOTALL,
        )
        if xml_match:
            return _clean_number(xml_match.group(1))

        # Plain text
        shares_match = re.search(
            r'(?:shares?|amount)\s*(?:of\s+common\s+stock\s*)?[:\s]+([\d,]+(?:\.\d+)?)',
            clean,
            re.IGNORECASE,
        )
        if shares_match:
            return _clean_number(shares_match.group(1))

        return None

    @staticmethod
    def _extract_form4_price(raw: str, clean: str) -> Optional[float]:
        """Extract price per share from Form 4."""
        # XML transactionPricePerShare
        xml_match = re.search(
            r'<transactionPricePerShare>.*?<value>([\d,.]+)</value>',
            raw,
            re.IGNORECASE | re.DOTALL,
        )
        if xml_match:
            return _clean_number(xml_match.group(1))

        # Plain text
        price_match = re.search(
            r'(?:price|per\s+share)\s*[:\s]*\$?([\d,.]+)',
            clean,
            re.IGNORECASE,
        )
        if price_match:
            return _clean_number(price_match.group(1))

        return None

    @staticmethod
    def _detect_10b5_plan(raw: str, clean: str) -> bool:
        """Detect if transaction is part of a Rule 10b5-1 trading plan."""
        combined = raw + " " + clean
        return bool(re.search(r'10b5-?1', combined, re.IGNORECASE))


# ==================================================================
# Compiled regex patterns for financial data extraction
# ==================================================================

_REVENUE_PATTERNS = [
    re.compile(
        r'(?:(?:Total|Net)\s+)?(?:Revenue|Sales|Net\s+(?:Revenue|Sales))\s*[\$:]?\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|billion|thousand)?',
        re.IGNORECASE,
    ),
    re.compile(
        r'Revenue[s]?\s*(?:were|was|of|totaled)\s*\$?([\d,]+(?:\.\d+)?)',
        re.IGNORECASE,
    ),
    re.compile(
        r'Total\s+revenue\s+\$\s*([\d,]+(?:\.\d+)?)',
        re.IGNORECASE,
    ),
]

_NET_INCOME_PATTERNS = [
    re.compile(
        r'Net\s+(?:Income|Earnings|Profit)\s*[\$:]?\s*\$?\s*([\d,()]+(?:\.\d+)?)',
        re.IGNORECASE,
    ),
    re.compile(
        r'Net\s+(?:income|earnings|profit)\s*(?:was|were|of|totaled)\s*\$?([\d,()]+(?:\.\d+)?)',
        re.IGNORECASE,
    ),
]

_TOTAL_ASSETS_PATTERNS = [
    re.compile(
        r'Total\s+[Aa]ssets\s*[\$:]?\s*\$?\s*([\d,]+(?:\.\d+)?)',
    ),
    re.compile(
        r'Total\s+assets\s*(?:were|was|of|totaled)\s*\$?([\d,]+(?:\.\d+)?)',
        re.IGNORECASE,
    ),
]

_TOTAL_LIABILITIES_PATTERNS = [
    re.compile(
        r'Total\s+[Ll]iabilities\s*[\$:]?\s*\$?\s*([\d,]+(?:\.\d+)?)',
    ),
    re.compile(
        r'Total\s+liabilities\s*(?:were|was|of|totaled)\s*\$?([\d,]+(?:\.\d+)?)',
        re.IGNORECASE,
    ),
]

_OPERATING_INCOME_PATTERNS = [
    re.compile(
        r'Operating\s+(?:Income|Profit)\s*[\$:]?\s*\$?\s*([\d,()]+(?:\.\d+)?)',
        re.IGNORECASE,
    ),
]

_EPS_PATTERNS = [
    re.compile(
        r'(?:Earnings|EPS|Diluted\s+EPS|(?:Net\s+)?(?:Earnings|Income)\s+per\s+share)\s*[\$:]?\s*\$?\s*([\d,.()]+)',
        re.IGNORECASE,
    ),
    re.compile(
        r'(?:Basic|Diluted)\s+(?:earnings|net\s+income)\s+per\s+(?:common\s+)?share\s*[\$:]?\s*\$?\s*([\d,.()]+)',
        re.IGNORECASE,
    ),
]
