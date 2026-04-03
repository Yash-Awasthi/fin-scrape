"""
backend/entity_extractor.py
============================
High-precision named-entity extraction for financial news articles.

Pipeline
--------
Only the lemmatizer is disabled.  Parser, tagger, tok2vec, and attribute_ruler
all stay active — the ORG quality gates depend on POS tags and dependency
information populated by those components.

Ticker extraction
-----------------
Two tiers: high-confidence (API-supplied related_tickers) and low-confidence
(regex-discovered, validated against the reference ticker set).  Both tiers
are always populated; they are non-overlapping.

Company precision lanes
-----------------------
companies_verified   — CSV-matched or ticker-anchored.  Safe for alerts / strict UIs.
companies_unverified — Passed all NER gates but unanchored.  Useful in research feeds.
companies            — Union of both (backward-compatible).
"""

from __future__ import annotations

import csv
import logging
import multiprocessing
import os
import re
from typing import TypedDict

import spacy
from spacy.language import Language
from spacy.tokens import Doc

__all__ = [
    "EntityResult",
    "LinkedEntity",
    "extract_entities",
    "extract_entities_batch",
]

logger = logging.getLogger(__name__)

_MULTIPROCESS_THRESHOLD: int = 128
_PIPE_BATCH_SIZE: int = 64

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
try:
    nlp: Language = spacy.load("en_core_web_sm", disable=["lemmatizer"])
except OSError as exc:  # pragma: no cover
    raise RuntimeError(
        "spaCy model 'en_core_web_sm' not found. "
        "Run: python -m spacy download en_core_web_sm"
    ) from exc

# ---------------------------------------------------------------------------
# Ticker regex & stopwords
# ---------------------------------------------------------------------------

_TICKER_RE = re.compile(r"(?<!\w)\$?([A-Z]{2,5})(?!\w)")

_TICKER_STOPWORDS: frozenset[str] = frozenset({
    # Function words
    "A", "AN", "AND", "AS", "AT", "BE", "BUT", "BY", "DO", "FOR",
    "IF", "IN", "IS", "IT", "NO", "OF", "ON", "OR", "THE", "TO",
    "ARE", "CAN", "HAS", "HAD", "HAVE", "MAY", "NOT", "WAS", "WERE",
    "WILL", "BEEN",
    # Discourse words
    "ALSO", "BOTH", "EVEN", "FROM", "LAST", "MANY", "MOST", "MUCH",
    "NEXT", "NOW", "ONE", "OUT", "OVER", "SAID", "SAYS", "SUCH",
    "THAN", "THAT", "THIS", "TOLD", "TWO", "WITH",
    # Common nouns that trip the regex
    "ALL", "BANK", "BILL", "BOND", "CASH", "COST", "DATA", "DEAL",
    "DEBT", "FIRM", "FUND", "GAIN", "GO", "GOAL", "GOVT", "LOSS",
    "LAW", "MODEL", "NEW", "PLAN", "POWER", "RATE", "RISK", "ROLE",
    "SALE", "STOCK", "TEAM", "TECH", "TRADE", "UNIT", "UP", "VALUE",
    "YEAR",
    # Financial metrics
    "EPS", "PE", "PB", "ROE", "ROA", "YOY", "QOQ", "MOM", "YTD",
    "TTM", "GAAP", "EBIT", "EBITDA", "FCF", "OCF", "CAPEX", "DPS",
    "NAV", "NIM", "NPL", "FY", "FQ",
    # Market / institution abbreviations
    "IPO", "ETF", "OTC", "DOW", "NYSE", "NASDAQ", "CBOE",
    "FED", "FOMC", "FDIC", "ECB", "IMF", "IRS", "SEC",
    "GDP", "CPI", "PMI",
    # Titles & suffixes
    "CEO", "CFO", "COO", "CTO", "CMO", "CRO", "EVP", "SVP", "VP",
    "AG", "INC", "LLC", "LP", "LTD", "NV", "PLC", "SA",
    # Geography
    "AI", "EU", "UK", "UN", "US", "USA", "UAE",
})

# Analyst ratings and sentiment words that NER misclassifies as entities.
_RATING_WORD_BLACKLIST: frozenset[str] = frozenset({
    "buy", "sell", "hold", "neutral", "outperform", "underperform",
    "overweight", "underweight", "equalweight", "marketperform",
    "strongbuy", "strongsell", "accumulate", "reduce",
    "probably", "forget", "rising", "falling", "surging", "plunging",
    "beats", "misses", "raises", "cuts", "boosts", "warns",
    "upgrade", "downgrade", "initiates", "reiterates",
    "tumbles", "falls", "hit", "growth"
})

# ---------------------------------------------------------------------------
# Legal suffix stripping
# ---------------------------------------------------------------------------
# Longer / more specific patterns first to avoid partial matches.
# Semantic descriptors (Group, Capital, Bank, etc.) are intentionally excluded;
# stripping them corrupts names like "Capital One" or "The Carlyle Group".
_LEGAL_SUFFIXES: tuple[str, ...] = (
    r"\s*,?\s*Incorporated", r"\s*,?\s*Corporation", r"\s*,?\s*Limited",
    r"\s*,?\s*Inc\.", r"\s*,?\s*Inc",
    r"\s*,?\s*Corp\.", r"\s*,?\s*Corp",
    r"\s*,?\s*Ltd\.", r"\s*,?\s*Ltd",
    r"\s*,?\s*L\.L\.C\.", r"\s*,?\s*LLC",
    r"\s*,?\s*P\.L\.C\.", r"\s*,?\s*PLC",
    r"\s*,?\s*L\.P\.", r"\s*,?\s*LP",
    r"\s*,?\s*N\.V\.", r"\s*,?\s*NV",
    r"\s*,?\s*S\.A\.", r"\s*,?\s*SA",
    r"\s*,?\s*AG", r"\s*,?\s*Co\.", r"\s*,?\s*Co",
)

_LEGAL_SUFFIX_RE = re.compile(
    r"(?:" + "|".join(_LEGAL_SUFFIXES) + r")+$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Company → ticker reference map
# ---------------------------------------------------------------------------
# CSV format: two columns, no header — lowercase company name, uppercase ticker.
# Lines beginning with '#' are treated as comments and skipped.
# Resolution order:
#   1. COMPANY_TICKER_CSV env var
#   2. <module_dir>/data/company_tickers.csv
#   3. Empty dict — entity linking degrades gracefully with a WARNING.

def _load_company_ticker_map() -> dict[str, str]:
    candidates = [
        os.environ.get("COMPANY_TICKER_CSV", ""),
        os.path.join(os.path.dirname(__file__), "data", "company_tickers.csv"),
    ]
    for path in candidates:
        if not path or not os.path.isfile(path):
            continue
        mapping: dict[str, str] = {}
        try:
            with open(path, newline="", encoding="utf-8") as fh:
                for row in csv.reader(fh):
                    if not row or row[0].startswith("#"):
                        continue
                    if len(row) >= 2:
                        company, ticker = row[0].strip().lower(), row[1].strip().upper()
                        if company and ticker:
                            mapping[company] = ticker
            logger.info("Loaded %d company→ticker entries from %s", len(mapping), path)
            return mapping
        except OSError:
            logger.exception("Failed to read company ticker file at %s", path)

    logger.warning(
        "No company_tickers.csv found. Entity linking will rely on ticker symbol "
        "matching only. Set COMPANY_TICKER_CSV or place file at "
        "<module_dir>/data/company_tickers.csv."
    )
    return {}


_COMPANY_TICKER_MAP: dict[str, str] = _load_company_ticker_map()

# Validated ticker set — regex candidates must appear here (or be $-prefixed)
# to be accepted as low-confidence.  Empty when CSV is missing; see module
# docstring for the precision tradeoff this implies.
_KNOWN_TICKERS: frozenset[str] = frozenset(_COMPANY_TICKER_MAP.values())

# Asset-class words used by ORG gate 4.
# A span whose every PROPN/NOUN token is in this set is a fund/index descriptor,
# not a company name.
_ASSET_CLASS_WORDS: frozenset[str] = frozenset({
    "equity", "equities", "fund", "funds", "index", "indices",
    "trust", "etf", "reit", "bond", "bonds", "note", "notes",
    "rate", "rates", "yield", "yields", "portfolio", "basket",
    "security", "securities", "asset", "assets", "commodity",
    "futures", "options", "swap", "derivative",
})

# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

class LinkedEntity(TypedDict):
    org_name: str    # Original NER surface form  e.g. "Apple Inc."
    clean_name: str  # Legal-suffix-stripped       e.g. "Apple"
    ticker: str      # Matched ticker              e.g. "AAPL"


class EntityResult(TypedDict):
    companies: list[str]               # Union of both lanes (backward compat)
    companies_verified: list[str]      # CSV-matched or ticker-anchored
    companies_unverified: list[str]    # NER-only survivors
    organizations: list[str]           # Legal names for all ORG entities
    people: list[str]
    products: list[str]
    locations: list[str]               # GPE + LOC
    tickers: list[str]                 # High-confidence (API-supplied)
    tickers_low_confidence: list[str]  # Regex-discovered, reference-validated
    linked_entities: list[LinkedEntity]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_result() -> EntityResult:
    return EntityResult(
        companies=[], companies_verified=[], companies_unverified=[],
        organizations=[], people=[], products=[], locations=[],
        tickers=[], tickers_low_confidence=[], linked_entities=[],
    )


def _normalize_entity_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _strip_legal_suffix(name: str) -> str:
    return _LEGAL_SUFFIX_RE.sub("", name).strip(" ,")


def _dedup_exact(entities: list[str]) -> list[str]:
    """Case-insensitive dedup preserving first-mention order."""
    seen: set[str] = set()
    out: list[str] = []
    for ent in entities:
        key = ent.lower()
        if key not in seen:
            seen.add(key)
            out.append(ent)
    return out


def _dedup_people(entities: list[str]) -> list[str]:
    """
    Case-insensitive dedup for PERSON entities with substring suppression.
    "Musk" is dropped when "Elon Musk" is present.
    Scoped to PERSON only — "Apple" and "Apple Daily" are distinct companies.
    """
    seen: set[str] = set()
    unique: list[str] = []
    for ent in entities:
        key = ent.lower()
        if key not in seen:
            seen.add(key)
            unique.append(ent)

    lower_unique = [e.lower() for e in unique]
    retained: list[str] = []
    for i, (ent, el) in enumerate(zip(unique, lower_unique)):
        subsumed = any(
            j != i and el != lower_unique[j] and el in lower_unique[j]
            for j in range(len(lower_unique))
        )
        if not subsumed:
            retained.append(ent)
    return retained


def _extract_tickers(
    text: str,
    related_tickers: list[str],
) -> tuple[list[str], list[str]]:
    """
    Returns (high_confidence, low_confidence) ticker lists.
    Always scans free text even when related_tickers is non-empty, so that
    secondary tickers in multi-company articles are not missed.
    """
    high_set: dict[str, None] = {}
    for ticker in related_tickers or []:
        if isinstance(ticker, str) and (t := ticker.strip().upper()):
            high_set.setdefault(t, None)

    low_set: dict[str, None] = {}
    for match in _TICKER_RE.finditer(text or ""):
        raw = match.group(0)
        candidate = match.group(1).upper()
        if candidate in _TICKER_STOPWORDS or candidate in high_set:
            continue
        if raw.startswith("$") or candidate in _KNOWN_TICKERS:
            low_set.setdefault(candidate, None)

    return list(high_set), list(low_set)


def _link_entities(
    org_names: list[str],
    high_tickers: list[str],
    low_tickers: list[str] | None = None,
) -> list[LinkedEntity]:
    """
    Match ORG names to tickers.  Priority:
      1. CSV map lookup on clean name.
      2. Direct name==ticker match, high-confidence first, then low-confidence.
    """
    high_set = frozenset(high_tickers)
    low_set  = frozenset(low_tickers or [])

    linked: list[LinkedEntity] = []
    seen: set[str] = set()

    for org in org_names:
        clean = _strip_legal_suffix(org)
        mapped = _COMPANY_TICKER_MAP.get(clean.lower())

        if mapped and mapped not in seen:
            linked.append(LinkedEntity(org_name=org, clean_name=clean, ticker=mapped))
            seen.add(mapped)
        elif not mapped:
            for ticker in (*high_set, *low_set):
                if ticker.lower() == clean.lower() and ticker not in seen:
                    linked.append(LinkedEntity(org_name=org, clean_name=clean, ticker=ticker))
                    seen.add(ticker)
                    break

    return linked


def _partition_companies(
    clean_names: list[str],
    high_tickers: list[str],
    low_tickers: list[str],
) -> tuple[list[str], list[str]]:
    """
    Split company names into verified and unverified lanes.
    Verified if: direct CSV hit, reverse ticker→name match, or name==known ticker.
    Unverified if: passed all NER gates but not anchored to any reference data.
    """
    all_tickers: frozenset[str] = frozenset(
        t.upper() for t in (*high_tickers, *low_tickers)
    )
    reverse_map: dict[str, str] = {v.upper(): k for k, v in _COMPANY_TICKER_MAP.items()}

    verified: list[str] = []
    unverified: list[str] = []

    for name in clean_names:
        name_lower = name.lower()

        if name_lower in _COMPANY_TICKER_MAP:
            verified.append(name)
        elif any(reverse_map.get(t, "") == name_lower for t in all_tickers):
            verified.append(name)
        elif name.upper() in all_tickers and name.upper() in _KNOWN_TICKERS:
            verified.append(name)
        else:
            unverified.append(name)

    return verified, unverified


def _build_result(doc: Doc, related_tickers: list[str], raw_text: str) -> EntityResult:
    orgs: list[str] = []
    people: list[str] = []
    products: list[str] = []
    locations: list[str] = []

    for ent in doc.ents:
        normalized = _normalize_entity_text(ent.text)
        if not normalized:
            continue

        # Gate 1: minimum length.
        if len(normalized) < 2:
            continue

        # Gate 2: analyst rating / sentiment words.
        if normalized.lower() in _RATING_WORD_BLACKLIST:
            continue

        label = ent.label_

        if label == "ORG":
            # Gate 3: root POS — reject spans headed by ADV or VERB.
            # e.g. "Retirees Probably" (root=ADV), "Rising Rates" (root=VERB).
            if ent.root.pos_ in ("ADV", "VERB"):
                logger.debug("ORG gate 3 rejected %r (root=%r pos=%s)",
                             normalized, ent.root.text, ent.root.pos_)
                continue

            # Gate 4: noun-presence — span must contain at least one PROPN or NOUN.
            # Secondary: if every such token is a generic asset-class descriptor,
            # the span is a fund/index label, not a company.
            # e.g. "The ESG US Equity" → PROPN tokens = {"equity"} ⊆ _ASSET_CLASS_WORDS.
            span_noun_pos = {tok.pos_ for tok in ent} & {"PROPN", "NOUN"}
            if not span_noun_pos:
                logger.debug("ORG gate 4 rejected %r — no PROPN/NOUN token", normalized)
                continue
            noun_tokens = {tok.text.lower() for tok in ent if tok.pos_ in ("PROPN", "NOUN")}
            if noun_tokens and noun_tokens.issubset(_ASSET_CLASS_WORDS):
                logger.debug("ORG gate 4 rejected %r — asset descriptors only: %s",
                             normalized, noun_tokens)
                continue
            if len(ent.text.split()) > 4:
                continue
            # Gate 5: reject if any token in the span is a VERB.
            # Catches run-on headline fragments like
            # "Ramsey Theory Group Expand Creative and Technology"
            # where the length-cap heuristic would be both imprecise and fragile.
            if any(tok.pos_ == "VERB" for tok in ent):
                logger.debug("ORG gate 5 rejected %r — span contains VERB token", normalized)
                continue

            orgs.append(normalized)

        elif label == "PERSON":
            if normalized in orgs:
                continue
            if normalized.lower() in _COMPANY_TICKER_MAP:
                continue
            people.append(normalized)
        elif label == "PRODUCT":
            products.append(normalized)
        elif label in ("GPE", "LOC"):
            locations.append(normalized)

    deduped_orgs = _dedup_exact(orgs)
    clean_companies = _dedup_exact([_strip_legal_suffix(org) for org in orgs])
    high_tickers, low_tickers = _extract_tickers(raw_text, related_tickers)
    verified, unverified = _partition_companies(clean_companies, high_tickers, low_tickers)

    return EntityResult(
        companies=clean_companies,
        companies_verified=verified,
        companies_unverified=unverified,
        organizations=deduped_orgs,
        people=_dedup_people(people),
        products=_dedup_exact(products),
        locations=_dedup_exact(locations),
        tickers=high_tickers,
        tickers_low_confidence=low_tickers,
        linked_entities=_link_entities(deduped_orgs, high_tickers, low_tickers),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_entities(article: dict) -> EntityResult:
    """
    Extract entities from a single article dict.
    Keys: headline (str), summary (str), related_tickers (list[str]).
    All keys are optional; missing/None values are handled gracefully.
    """
    headline: str = article.get("headline") or ""
    summary: str  = article.get("summary") or ""
    related: list[str] = article.get("related_tickers") or []
    raw_text = f"{headline} {summary}".strip()

    if not raw_text:
        result = _empty_result()
        result["tickers"], result["tickers_low_confidence"] = _extract_tickers("", related)
        return result

    return _build_result(nlp(raw_text), related, raw_text)


def extract_entities_batch(
    news: list[dict],
    *,
    batch_size: int = _PIPE_BATCH_SIZE,
) -> list[EntityResult]:
    """
    Extract entities from a list of article dicts using nlp.pipe().
    Returns a parallel list; len(output) == len(news) always.
    Batches exceeding _MULTIPROCESS_THRESHOLD use n_process=max(1, cpu_count-1).
    Falls back to serial processing if nlp.pipe() raises.
    """
    if not news:
        return []

    texts: list[str] = []
    meta: list[tuple[list[str], str]] = []

    for article in news:
        headline: str  = article.get("headline") or ""
        summary: str   = article.get("summary") or ""
        related: list[str] = article.get("related_tickers") or []
        raw_text = f"{headline} {summary}".strip()
        texts.append(raw_text)
        meta.append((related, raw_text))

    non_empty_idx   = [i for i, t in enumerate(texts) if t]
    non_empty_texts = [texts[i] for i in non_empty_idx]
    n_articles      = len(non_empty_texts)

    if n_articles > _MULTIPROCESS_THRESHOLD:
        n_process = max(1, multiprocessing.cpu_count() - 1)
        logger.info("Batch %d > threshold %d — using n_process=%d.",
                    n_articles, _MULTIPROCESS_THRESHOLD, n_process)
    else:
        n_process = 1

    processed: list[Doc | None] = [None] * n_articles
    try:
        for pos, doc in enumerate(
            nlp.pipe(non_empty_texts, batch_size=batch_size, n_process=n_process)
        ):
            processed[pos] = doc
    except Exception:
        logger.exception("nlp.pipe() failed (n_process=%d); retrying serially.", n_process)
        for pos, text in enumerate(non_empty_texts):
            try:
                processed[pos] = nlp(text)
            except Exception:
                logger.warning("NER failed on article index %d; skipping.", non_empty_idx[pos])

    all_docs: list[Doc | None] = [None] * len(news)
    for pos, doc in enumerate(processed):
        if doc is not None:
            all_docs[non_empty_idx[pos]] = doc

    results: list[EntityResult] = []
    for i, (related, raw_text) in enumerate(meta):
        try:
            if all_docs[i] is not None:
                results.append(_build_result(all_docs[i], related, raw_text))
            else:
                result = _empty_result()
                result["tickers"], result["tickers_low_confidence"] = (
                    _extract_tickers("", related)
                )
                results.append(result)
        except Exception:
            logger.exception("Extraction failed for article index %d (headline=%r).",
                             i, news[i].get("headline", ""))
            results.append(_empty_result())

    return results