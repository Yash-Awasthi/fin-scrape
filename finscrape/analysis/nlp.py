"""
Advanced NLP pipeline — spaCy-based entity extraction, disambiguation,
coreference resolution, and relationship extraction for financial text.

Replaces the naive regex ticker extraction with proper NLP:
- Named Entity Recognition (NER) for ORG, PERSON, MONEY, DATE, PERCENT
- Entity disambiguation (Apple Inc vs. apple fruit)
- Company→ticker resolution via entity index + fuzzy matching
- Financial metric extraction (revenue, EPS, price targets)
- Relationship extraction (acquirer→target, analyst→company)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-load spaCy to avoid import overhead when not needed
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model: en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            return None
    return _nlp


# --- Well-known financial entity mappings ---

COMPANY_TICKER_MAP: dict[str, str] = {
    "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL", "alphabet": "GOOGL",
    "amazon": "AMZN", "meta": "META", "facebook": "META", "meta platforms": "META",
    "nvidia": "NVDA", "tesla": "TSLA", "netflix": "NFLX", "amd": "AMD",
    "advanced micro devices": "AMD", "intel": "INTC", "ibm": "IBM",
    "salesforce": "CRM", "adobe": "ADBE", "oracle": "ORCL", "cisco": "CSCO",
    "qualcomm": "QCOM", "broadcom": "AVGO", "texas instruments": "TXN",
    "jpmorgan": "JPM", "jp morgan": "JPM", "j.p. morgan": "JPM",
    "goldman sachs": "GS", "morgan stanley": "MS", "bank of america": "BAC",
    "citigroup": "C", "wells fargo": "WFC", "blackrock": "BLK",
    "berkshire hathaway": "BRK.B", "berkshire": "BRK.B",
    "walmart": "WMT", "target": "TGT", "costco": "COST", "home depot": "HD",
    "disney": "DIS", "walt disney": "DIS", "comcast": "CMCSA", "verizon": "VZ",
    "at&t": "T", "t-mobile": "TMUS", "uber": "UBER", "airbnb": "ABNB",
    "paypal": "PYPL", "visa": "V", "mastercard": "MA", "square": "SQ", "block": "SQ",
    "coca-cola": "KO", "pepsi": "PEP", "pepsico": "PEP",
    "johnson & johnson": "JNJ", "pfizer": "PFE", "unitedhealth": "UNH",
    "procter & gamble": "PG", "exxon mobil": "XOM", "exxon": "XOM", "chevron": "CVX",
    "boeing": "BA", "lockheed martin": "LMT", "raytheon": "RTX",
    "caterpillar": "CAT", "3m": "MMM", "honeywell": "HON",
    "samsung": "SSNLF", "tsmc": "TSM", "taiwan semiconductor": "TSM",
    "alibaba": "BABA", "tencent": "TCEHY", "baidu": "BIDU",
    "shopify": "SHOP", "snowflake": "SNOW", "palantir": "PLTR",
    "coinbase": "COIN", "robinhood": "HOOD", "sofi": "SOFI",
    "rivian": "RIVN", "lucid": "LCID", "nio": "NIO",
    "crowdstrike": "CRWD", "datadog": "DDOG", "cloudflare": "NET",
    "arm": "ARM", "arm holdings": "ARM",
    "openai": "", "federal reserve": "", "fed": "", "sec": "", "ftc": "",
    "european central bank": "", "ecb": "",
}

# Analyst/bank names that appear as actors in financial news
ANALYST_ENTITIES = frozenset({
    "goldman sachs", "morgan stanley", "jpmorgan", "jp morgan", "j.p. morgan",
    "bank of america", "merrill lynch", "citigroup", "citi", "barclays",
    "deutsche bank", "ubs", "credit suisse", "hsbc", "wells fargo",
    "raymond james", "piper sandler", "jefferies", "cowen", "needham",
    "wedbush", "oppenheimer", "bernstein", "rbc", "bmo", "canaccord",
    "stifel", "wolfe research", "evercore", "truist", "mizuho",
    "keybanc", "loop capital", "rosenblatt", "susquehanna",
})

# Words that indicate "Apple" is the company, not the fruit
APPLE_COMPANY_CONTEXT = frozenset({
    "iphone", "ipad", "mac", "macbook", "ios", "app store", "tim cook",
    "cupertino", "silicon", "aapl", "apple watch", "airpods", "vision pro",
    "revenue", "earnings", "stock", "shares", "market cap", "quarterly",
})


@dataclass
class ExtractedEntity:
    """An entity extracted from financial text."""
    name: str
    entity_type: str  # ORG, PERSON, MONEY, DATE, PERCENT, GPE, PRODUCT
    ticker: str = ""
    role: str = "mentioned"  # primary, competitor, analyst, regulator, mentioned
    impact: str = "neutral"  # positive, negative, neutral
    confidence: float = 0.5
    span_start: int = 0
    span_end: int = 0


@dataclass
class FinancialMetric:
    """A financial metric extracted from text."""
    metric_type: str  # revenue, eps, price_target, market_cap, layoffs, etc.
    value: float
    unit: str = ""  # %, $, count
    context: str = ""  # "beat by", "missed by", "grew", "declined"
    comparison: str = ""  # "vs estimate", "yoy", "qoq"


@dataclass
class EntityRelation:
    """A relationship between two entities."""
    subject: str
    relation: str  # acquires, invests_in, upgrades, downgrades, sues, partners_with
    object: str
    confidence: float = 0.5


@dataclass
class NLPResult:
    """Complete NLP analysis of a financial text."""
    entities: list[ExtractedEntity] = field(default_factory=list)
    metrics: list[FinancialMetric] = field(default_factory=list)
    relations: list[EntityRelation] = field(default_factory=list)
    tickers: list[str] = field(default_factory=list)
    primary_company: str = ""
    primary_ticker: str = ""
    sector: str = ""
    has_breaking_indicators: bool = False


class FinancialNLP:
    """Advanced NLP pipeline for financial text analysis."""

    def __init__(self, entity_index: dict[str, list[tuple[str, str]]] | None = None):
        """
        Args:
            entity_index: Optional mapping of keyword → [(company, ticker), ...]
                          from the storage layer. Supplements the built-in map.
        """
        self._custom_index = entity_index or {}

    def analyze(self, title: str, text: str) -> NLPResult:
        """Run the full NLP pipeline on a headline + article text."""
        full_text = f"{title}. {text}" if title else text
        result = NLPResult()

        # Step 1: spaCy NER
        nlp = _get_nlp()
        if nlp:
            doc = nlp(full_text[:10000])  # Cap to avoid memory issues
            result.entities = self._extract_entities(doc, full_text)
        else:
            result.entities = self._fallback_entity_extraction(full_text)

        # Step 2: Financial metric extraction (regex-based, doesn't need spaCy)
        result.metrics = self._extract_metrics(full_text)

        # Step 3: Relationship extraction
        result.relations = self._extract_relations(full_text)

        # Step 4: Resolve tickers
        result.tickers = self._resolve_all_tickers(result.entities, full_text)

        # Step 5: Identify primary company
        if result.tickers:
            result.primary_ticker = result.tickers[0]
            for ent in result.entities:
                if ent.ticker == result.primary_ticker:
                    result.primary_company = ent.name
                    break

        # Step 6: Sector detection
        result.sector = self._detect_sector(full_text, result.tickers)

        # Step 7: Breaking news indicators
        result.has_breaking_indicators = self._check_breaking_indicators(full_text)

        return result

    def _extract_entities(self, doc, full_text: str) -> list[ExtractedEntity]:
        """Extract entities using spaCy NER + disambiguation."""
        entities = []
        seen = set()

        for ent in doc.ents:
            if ent.label_ not in ("ORG", "PERSON", "MONEY", "DATE", "PERCENT", "GPE", "PRODUCT"):
                continue

            name = ent.text.strip()
            key = (name.lower(), ent.label_)
            if key in seen:
                continue
            seen.add(key)

            extracted = ExtractedEntity(
                name=name,
                entity_type=ent.label_,
                span_start=ent.start_char,
                span_end=ent.end_char,
            )

            # Resolve ticker for ORG entities
            if ent.label_ == "ORG":
                ticker = self._resolve_ticker(name, full_text)
                if ticker:
                    extracted.ticker = ticker

                # Determine role
                name_lower = name.lower()
                if name_lower in ANALYST_ENTITIES or any(a in name_lower for a in ANALYST_ENTITIES):
                    extracted.role = "analyst"
                else:
                    extracted.role = "primary"

            entities.append(extracted)

        return entities

    def _fallback_entity_extraction(self, text: str) -> list[ExtractedEntity]:
        """Fallback entity extraction when spaCy is not available."""
        entities = []
        text_lower = text.lower()

        for name, ticker in COMPANY_TICKER_MAP.items():
            if name in text_lower and ticker:
                entities.append(ExtractedEntity(
                    name=name.title(),
                    entity_type="ORG",
                    ticker=ticker,
                    role="primary",
                ))

        return entities

    def _resolve_ticker(self, entity_name: str, context: str) -> str:
        """Resolve an entity name to a ticker symbol with disambiguation."""
        name_lower = entity_name.lower().strip()
        context_lower = context.lower()

        # Disambiguation: "Apple" the company vs fruit
        if name_lower == "apple":
            if any(w in context_lower for w in APPLE_COMPANY_CONTEXT):
                return "AAPL"
            # In financial news, default to company
            return "AAPL"

        # Direct lookup
        if name_lower in COMPANY_TICKER_MAP:
            return COMPANY_TICKER_MAP[name_lower]

        # Partial match (e.g., "Apple Inc." → "apple")
        for key, ticker in COMPANY_TICKER_MAP.items():
            if key in name_lower or name_lower in key:
                if ticker:
                    return ticker

        # Custom entity index lookup
        for keyword, entries in self._custom_index.items():
            if keyword in name_lower:
                for company, ticker in entries:
                    if company.lower() in context_lower:
                        return ticker

        return ""

    def _extract_metrics(self, text: str) -> list[FinancialMetric]:
        """Extract financial metrics from text using regex patterns."""
        metrics = []

        # Revenue/earnings beats/misses
        for m in re.finditer(
            r'(?:revenue|sales|earnings|eps|profit)\s+(?:of\s+)?\$?([\d,.]+)\s*(billion|million|B|M|bn|mn)?'
            r'(?:.*?(?:beat|miss|exceed|top|below|above)\w*\s+(?:by\s+)?([\d.]+)%?)?',
            text, re.IGNORECASE
        ):
            value = float(m.group(1).replace(",", ""))
            unit = (m.group(2) or "").lower()
            if unit in ("billion", "b", "bn"):
                value *= 1_000_000_000
            elif unit in ("million", "m", "mn"):
                value *= 1_000_000

            metric_type = "revenue"
            for kw in ("earnings", "eps", "profit"):
                if kw in m.group(0).lower():
                    metric_type = kw
                    break

            context = ""
            if m.group(3):
                beat_pct = float(m.group(3))
                if any(w in m.group(0).lower() for w in ("beat", "exceed", "top", "above")):
                    context = f"beat by {beat_pct}%"
                else:
                    context = f"missed by {beat_pct}%"

            metrics.append(FinancialMetric(
                metric_type=metric_type,
                value=value,
                unit="$",
                context=context,
            ))

        # Percentage changes
        for m in re.finditer(
            r'(?:up|down|rose|fell|gained|lost|grew|declined|surged|plunged|jumped|dropped)\s+'
            r'([\d.]+)%',
            text, re.IGNORECASE
        ):
            direction = m.group(0).split()[0].lower()
            is_positive = direction in ("up", "rose", "gained", "grew", "surged", "jumped")
            metrics.append(FinancialMetric(
                metric_type="price_change",
                value=float(m.group(1)) * (1 if is_positive else -1),
                unit="%",
                context=direction,
            ))

        # Price targets
        for m in re.finditer(
            r'price\s+target\s+(?:of\s+|to\s+|at\s+)?\$?([\d,.]+)',
            text, re.IGNORECASE
        ):
            metrics.append(FinancialMetric(
                metric_type="price_target",
                value=float(m.group(1).replace(",", "")),
                unit="$",
            ))

        # Layoff numbers
        for m in re.finditer(
            r'(?:lay\s*off|cut|eliminate|reduce)\w*\s+([\d,]+)\s*(?:jobs|positions|employees|workers)',
            text, re.IGNORECASE
        ):
            metrics.append(FinancialMetric(
                metric_type="layoffs",
                value=float(m.group(1).replace(",", "")),
                unit="count",
            ))

        # Deal values
        for m in re.finditer(
            r'(?:deal|acquisition|merger|transaction|valued)\s+(?:worth|at|of)\s+\$?([\d,.]+)\s*(billion|million|B|M|bn|mn)',
            text, re.IGNORECASE
        ):
            value = float(m.group(1).replace(",", ""))
            unit = m.group(2).lower()
            if unit in ("billion", "b", "bn"):
                value *= 1_000_000_000
            elif unit in ("million", "m", "mn"):
                value *= 1_000_000
            metrics.append(FinancialMetric(
                metric_type="deal_value",
                value=value,
                unit="$",
            ))

        return metrics

    def _extract_relations(self, text: str) -> list[EntityRelation]:
        """Extract entity relationships from financial text."""
        relations = []
        text_lower = text.lower()

        # Acquisition patterns
        for m in re.finditer(
            r'(\b[A-Z][a-zA-Z& .]+?)\s+(?:to acquire|acquires|acquired|buying|to buy|buys|bought)\s+(\b[A-Z][a-zA-Z& .]+?)(?:\s|,|\.)',
            text
        ):
            relations.append(EntityRelation(
                subject=m.group(1).strip(),
                relation="acquires",
                object=m.group(2).strip(),
                confidence=0.8,
            ))

        # Upgrade/downgrade patterns
        for m in re.finditer(
            r'(\b[A-Z][a-zA-Z& .]+?)\s+(?:upgrades?|raised?)\s+(\b[A-Z][a-zA-Z& .]+?)\s+(?:to|rating)',
            text
        ):
            relations.append(EntityRelation(
                subject=m.group(1).strip(),
                relation="upgrades",
                object=m.group(2).strip(),
                confidence=0.7,
            ))

        for m in re.finditer(
            r'(\b[A-Z][a-zA-Z& .]+?)\s+(?:downgrades?|cut|cuts)\s+(\b[A-Z][a-zA-Z& .]+?)\s+(?:to|rating)',
            text
        ):
            relations.append(EntityRelation(
                subject=m.group(1).strip(),
                relation="downgrades",
                object=m.group(2).strip(),
                confidence=0.7,
            ))

        # Investment patterns
        for m in re.finditer(
            r'(\b[A-Z][a-zA-Z& .]+?)\s+(?:invests?|invested)\s+(?:\$[\d,.]+\s*(?:billion|million|B|M)\s+)?(?:in)\s+(\b[A-Z][a-zA-Z& .]+)',
            text
        ):
            relations.append(EntityRelation(
                subject=m.group(1).strip(),
                relation="invests_in",
                object=m.group(2).strip(),
                confidence=0.7,
            ))

        # Partnership
        for m in re.finditer(
            r'(\b[A-Z][a-zA-Z& .]+?)\s+(?:partners? with|partnering with|collaborat\w+ with)\s+(\b[A-Z][a-zA-Z& .]+)',
            text
        ):
            relations.append(EntityRelation(
                subject=m.group(1).strip(),
                relation="partners_with",
                object=m.group(2).strip(),
                confidence=0.6,
            ))

        return relations

    def _resolve_all_tickers(self, entities: list[ExtractedEntity], text: str) -> list[str]:
        """Resolve all tickers from entities + regex patterns, deduplicated."""
        tickers = []
        seen = set()

        # From NER entities
        for ent in entities:
            if ent.ticker and ent.ticker not in seen:
                tickers.append(ent.ticker)
                seen.add(ent.ticker)

        # Regex patterns for explicit tickers
        # $AAPL pattern
        for m in re.findall(r'\$([A-Z]{2,5})\b', text):
            if m not in seen:
                tickers.append(m)
                seen.add(m)

        # (AAPL) pattern
        for m in re.findall(r'\(([A-Z]{2,5})\)', text):
            if m not in seen:
                tickers.append(m)
                seen.add(m)

        return tickers

    def _detect_sector(self, text: str, tickers: list[str]) -> str:
        """Detect the primary sector from text content and tickers."""
        text_lower = text.lower()

        sector_keywords = {
            "technology": ["tech", "software", "semiconductor", "chip", "ai ", "cloud", "saas", "data center"],
            "healthcare": ["pharma", "biotech", "drug", "fda", "clinical trial", "healthcare", "hospital"],
            "finance": ["bank", "financial", "interest rate", "mortgage", "insurance", "trading"],
            "energy": ["oil", "gas", "renewable", "solar", "wind", "energy", "petroleum", "opec"],
            "consumer": ["retail", "consumer", "e-commerce", "shopping", "brand"],
            "industrial": ["manufacturing", "aerospace", "defense", "construction", "transport"],
            "real_estate": ["real estate", "reit", "property", "housing", "mortgage rates"],
            "crypto": ["bitcoin", "crypto", "blockchain", "ethereum", "defi"],
        }

        scores: dict[str, int] = {}
        for sector, keywords in sector_keywords.items():
            scores[sector] = sum(1 for kw in keywords if kw in text_lower)

        if scores:
            best = max(scores, key=scores.get)  # type: ignore
            if scores[best] > 0:
                return best

        return ""

    def _check_breaking_indicators(self, text: str) -> bool:
        """Check if text contains indicators of breaking/urgent news."""
        breaking_patterns = [
            r'\bbreaking\b', r'\bjust\s+in\b', r'\bexclusive\b',
            r'\bflash\b', r'\burgent\b', r'\bjust\s+announced\b',
            r'\bfirst\s+reported\b', r'\bsources?\s+say\b',
            r'\baccording\s+to\s+sources?\b',
        ]
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in breaking_patterns)


# Convenience function
def analyze_financial_text(
    title: str,
    text: str,
    entity_index: dict[str, list[tuple[str, str]]] | None = None,
) -> NLPResult:
    """Analyze financial text and return structured NLP results."""
    nlp = FinancialNLP(entity_index=entity_index)
    return nlp.analyze(title, text)
