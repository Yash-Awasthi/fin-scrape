"""
entity_enricher.py
==================
Stage 2 of the financial NLP pipeline.

Accepts structured ``EntityResult`` output from ``entity_extractor.py`` and
produces an ``EnrichedEntityResult`` — a typed, deduplicated, analytics-ready
representation of financial entities.

Design goals
------------
- Zero external dependencies (standard library only).
- O(n) time complexity; safe for batch processing thousands of articles.
- Deterministic output ordering for reproducibility and diff-stability.
- Purely structural enrichment — no network I/O, no sector lookups (yet).
- Case-insensitive deduplication across all entity types.
- Runtime-safe input coercion; never raises on malformed upstream output.

Verification signal
-------------------
Stage 1 (``entity_extractor.py``) partitions companies into two precision lanes:

* ``companies_verified``   — CSV-matched or ticker-anchored; safe for alerts.
* ``companies_unverified`` — NER-only survivors; useful in research feeds.

Stage 2 consumes this signal **as-is** — it does NOT recompute or validate it.
The ``is_verified`` flag on each ``Company`` object is set by checking whether
the canonical company name appears in ``entity_result["companies_verified"]``.
No CSV files, ticker maps, or external references are loaded here.

Downstream consumers can attach sector/industry/exchange metadata by
extending ``enrich_entities`` or post-processing the returned dict.

Batch usage
-----------
When processing many articles that share a common ``linked_entities`` block,
build the indexes once and pass them directly to avoid redundant work::

    ticker_idx   = _build_ticker_index(shared_linked_entities)
    clean_idx    = _build_clean_name_index(shared_linked_entities)
    verified_set = set(shared_verified_names)

    enriched_articles = [
        enrich_entities(
            er,
            ticker_index=ticker_idx,
            clean_name_index=clean_idx,
            verified_names=verified_set,
        )
        for er in article_entity_results
    ]
"""

from __future__ import annotations

import logging
from typing import TypedDict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------


class LinkedEntity(TypedDict):
    org_name: str    # Original NER surface form  e.g. "Apple Inc."
    clean_name: str  # Legal-suffix-stripped       e.g. "Apple"
    ticker: str      # Matched ticker              e.g. "AAPL"


class EntityResult(TypedDict):
    """
    Output schema produced by ``entity_extractor.py`` (upstream stage).

    Company precision lanes
    ~~~~~~~~~~~~~~~~~~~~~~~
    ``companies_verified`` and ``companies_unverified`` are mutually exclusive
    partitions of ``companies``.  ``companies`` (union) is retained for
    backward compatibility with consumers that predate the precision-lane
    feature.
    """

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


class Company(TypedDict):
    """
    Enriched company object produced by Stage 2.

    Fields
    ------
    name        : Canonical display name (legal suffix stripped).
    ticker      : Exchange ticker if resolvable from ``linked_entities``;
                  ``None`` for private or unlinked companies.
    is_verified : ``True`` when Stage 1 placed this company in the
                  ``companies_verified`` lane (CSV-matched or ticker-anchored).
                  ``False`` for NER-only survivors.  Never recomputed here.
    sector      : Reserved for Stage 3 enrichment; always ``None`` here.
    industry    : Reserved for Stage 3 enrichment; always ``None`` here.
    exchange    : Reserved for Stage 3 enrichment; always ``None`` here.
    """

    name: str
    ticker: str | None
    is_verified: bool
    sector: str | None
    industry: str | None
    exchange: str | None


class Person(TypedDict):
    name: str
    role: str | None     # Populated by downstream leadership-dataset stage.
    company: str | None  # Populated by downstream leadership-dataset stage.


class EnrichedEntityResult(TypedDict):
    """Enriched, deduplicated entity graph ready for downstream analytics."""

    companies: list[Company]
    people: list[Person]
    products: list[str]
    locations: list[str]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _coerce_str_list(value: object) -> list[str]:
    """
    Safely coerce an arbitrary value to a flat list of non-empty strings.

    Protects against upstream emitting ``None``, a scalar, or a mixed-type
    list in place of the expected ``list[str]``.

    Parameters
    ----------
    value:
        Raw value retrieved from an ``EntityResult`` field.

    Returns
    -------
    list[str]
        Each element is a stripped, non-empty string; malformed items are
        silently dropped.
    """
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _build_verified_set(verified_names: list[str]) -> set[str]:
    """
    Build a lowercased set of verified company names for O(1) lookup.

    Mirrors the index-building pattern of ``_build_ticker_index`` and
    ``_build_clean_name_index``.  Lowercasing ensures the membership test
    in ``_normalize_companies`` is case-insensitive, guarding against
    casing drift between Stage 1 and Stage 2.

    The verified signal is consumed directly from Stage 1 output — no CSV
    files, ticker maps, or external references are loaded here.

    Parameters
    ----------
    verified_names:
        ``entity_result["companies_verified"]`` from the extractor.  These
        are already legal-suffix-stripped clean names.

    Returns
    -------
    set[str]
        Lowercased canonical names that Stage 1 has marked as verified.
    """
    return {name.strip().lower() for name in verified_names if name.strip()}


def _build_ticker_index(linked_entities: list[LinkedEntity]) -> dict[str, str]:
    """
    Build a lowercased-name → ticker lookup from ``linked_entities``.

    Both ``org_name`` and ``clean_name`` are indexed so that raw extractor
    names (which may differ from the canonical form) still resolve to a
    ticker.  When a name appears in multiple entries the last writer wins,
    consistent with the extractor's own resolution semantics.

    Parameters
    ----------
    linked_entities:
        The ``linked_entities`` list from an ``EntityResult``.

    Returns
    -------
    dict[str, str]
        Keys are lowercased name strings; values are non-empty ticker symbols.
    """
    index: dict[str, str] = {}
    for entry in linked_entities:
        ticker = entry.get("ticker", "").strip()
        if not ticker:
            continue
        for field in ("org_name", "clean_name"):
            name = entry.get(field, "").strip()
            if name:
                index[name.lower()] = ticker
    return index


def _build_clean_name_index(linked_entities: list[LinkedEntity]) -> dict[str, str]:
    """
    Build a lowercased-``org_name`` → canonical ``clean_name`` lookup.

    Enables alias collapse before deduplication: ``"Apple Inc"`` and
    ``"Apple"`` both resolve to the same canonical display name when the
    extractor has linked them.

    Parameters
    ----------
    linked_entities:
        The ``linked_entities`` list from an ``EntityResult``.

    Returns
    -------
    dict[str, str]
        Keys are lowercased ``org_name`` strings; values are canonical names
        (original casing preserved from ``clean_name``).
    """
    index: dict[str, str] = {}
    for entry in linked_entities:
        org = entry.get("org_name", "").strip()
        clean = entry.get("clean_name", "").strip()
        if org and clean:
            index[org.lower()] = clean
    return index


def _normalize_companies(
    raw_names: list[str],
    ticker_index: dict[str, str],
    clean_name_index: dict[str, str],
    verified_names: set[str],
) -> list[Company]:
    """
    Convert raw company name strings into deduplicated ``Company`` objects.

    Processing order (per design rules)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. **Normalize** — resolve each raw name to its canonical ``clean_name``
       via ``clean_name_index`` (identity fallback when not found).
    2. **Deduplicate** — key the seen-set on the lowercased canonical name so
       that ``"Apple"`` / ``"Apple Inc"`` / ``"APPLE"`` collapse to one entry.
       First-seen wins; subsequent duplicates are logged at DEBUG and dropped.
    3. **Ticker** — attach ticker from ``ticker_index`` if available.
    4. **Verify** — set ``is_verified`` by checking whether ``canonical_name``
       (lowercased) is present in ``verified_names``.  The signal is consumed
       directly from Stage 1 output; it is never recomputed here.

    Parameters
    ----------
    raw_names:
        ``entity_result["companies"]`` strings from the extractor.  These are
        already legal-suffix-stripped clean names as of the current extractor.
    ticker_index:
        Name → ticker mapping produced by ``_build_ticker_index``.
    clean_name_index:
        ``org_name`` → ``clean_name`` mapping produced by
        ``_build_clean_name_index``.
    verified_names:
        Lowercased set of company names Stage 1 placed in the
        ``companies_verified`` lane, produced by ``_build_verified_set``.

    Returns
    -------
    list[Company]
        Deduplicated ``Company`` objects in first-seen order with
        ``is_verified`` tagged, and ``sector`` / ``industry`` / ``exchange``
        as ``None`` (reserved for Stage 3).
    """
    seen: dict[str, Company] = {}  # canonical_key → Company

    for raw in raw_names:
        raw = raw.strip()
        if not raw:
            continue

        # Step 1 — normalize to canonical display name.
        canonical_name: str = clean_name_index.get(raw.lower(), raw)
        canonical_key: str = canonical_name.lower()

        # Step 2 — deduplicate before any tagging.
        if canonical_key in seen:
            logger.debug("Deduplicating company: %r → %r", raw, canonical_name)
            continue

        # Step 3 — attach ticker if resolvable.
        ticker: str | None = (
            ticker_index.get(raw.lower())
            or ticker_index.get(canonical_key)
            or None
        )

        # Step 4 — consume verification signal from Stage 1; do not recompute.
        is_verified: bool = canonical_key in verified_names

        seen[canonical_key] = Company(
            name=canonical_name,
            ticker=ticker,
            is_verified=is_verified,
            sector=None,
            industry=None,
            exchange=None,
        )

    return list(seen.values())


def _normalize_people(raw_names: list[str]) -> list[Person]:
    """
    Convert raw person name strings into deduplicated ``Person`` objects.

    Deduplication is case-insensitive; the original casing of the first
    occurrence is preserved as the display name.  ``role`` and ``company``
    are ``None`` — populated by a downstream leadership-dataset stage.

    Parameters
    ----------
    raw_names:
        ``entity_result["people"]`` strings from the extractor.

    Returns
    -------
    list[Person]
        Deduplicated ``Person`` objects in first-seen order.
    """
    seen: dict[str, Person] = {}  # lowercased name → Person

    for raw in raw_names:
        raw = raw.strip()
        if not raw:
            continue
        key = raw.lower()
        if key not in seen:
            seen[key] = Person(name=raw, role=None, company=None)

    return list(seen.values())


def _deduplicate_strings(items: list[str]) -> list[str]:
    """
    Deduplicate a string list with case-insensitive comparison.

    The original casing of the first occurrence is preserved in the output.
    Empty and whitespace-only strings are removed.

    Parameters
    ----------
    items:
        Arbitrary string list (products, locations, …).

    Returns
    -------
    list[str]
        Unique strings in first-seen order, casing from first occurrence.
    """
    seen_keys: set[str] = set()
    result: list[str] = []

    for item in items:
        item = item.strip()
        if not item:
            continue
        key = item.lower()
        if key not in seen_keys:
            seen_keys.add(key)
            result.append(item)

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def enrich_entities(
    entity_result: EntityResult,
    *,
    ticker_index: dict[str, str] | None = None,
    clean_name_index: dict[str, str] | None = None,
    verified_names: set[str] | None = None,
) -> EnrichedEntityResult:
    """
    Enrich a raw ``EntityResult`` into a structured ``EnrichedEntityResult``.

    This is the sole public entry-point of the module.  It performs:

    1. **Company normalization** — maps raw name strings to ``Company``
       objects and attaches tickers from ``linked_entities``.
    2. **Alias collapse** — canonical name resolution deduplicates variants
       such as ``"Apple"`` / ``"Apple Inc."`` into a single entry.
    3. **Verification tagging** — sets ``is_verified`` on each ``Company``
       by consuming the ``companies_verified`` lane from Stage 1 output.
       No CSV files or ticker maps are loaded; the signal is never recomputed.
    4. **People normalization** — wraps name strings in ``Person`` objects
       with ``None`` role/company fields (for later enrichment).
    5. **Pass-through deduplication** — ``products`` and ``locations`` are
       case-insensitively deduplicated and forwarded unchanged.

    The function is stateless and side-effect-free, making it safe for
    concurrent batch processing.

    Batch optimisation
    ------------------
    When processing many articles that share a common entity graph, build all
    indexes once and inject them to avoid redundant per-call work::

        ti  = _build_ticker_index(shared_linked)
        ci  = _build_clean_name_index(shared_linked)
        vs  = _build_verified_set(shared_verified_names)

        results = [
            enrich_entities(er, ticker_index=ti, clean_name_index=ci, verified_names=vs)
            for er in entity_results
        ]

    Parameters
    ----------
    entity_result:
        Output dict produced by ``entity_extractor.py``.  Missing or
        ``None``-valued fields are coerced to empty lists rather than
        raising; malformed input is handled defensively throughout.
    ticker_index:
        Optional pre-built name → ticker index.  If ``None``, built
        automatically from ``entity_result["linked_entities"]``.
    clean_name_index:
        Optional pre-built org_name → clean_name index.  If ``None``, built
        automatically from ``entity_result["linked_entities"]``.
    verified_names:
        Optional pre-built lowercased set of verified company names.
        If ``None``, built automatically from
        ``entity_result["companies_verified"]``.

    Returns
    -------
    EnrichedEntityResult
        Typed dict ready for downstream analytics or serialization.

    Examples
    --------
    >>> result = enrich_entities({
    ...     "companies": ["Apple", "Ramsey Theory Group"],
    ...     "companies_verified": ["Apple"],
    ...     "companies_unverified": ["Ramsey Theory Group"],
    ...     "organizations": ["Apple Inc.", "Ramsey Theory Group"],
    ...     "people": [],
    ...     "products": [],
    ...     "locations": ["India"],
    ...     "tickers": ["AAPL"],
    ...     "tickers_low_confidence": [],
    ...     "linked_entities": [
    ...         {"org_name": "Apple Inc.", "clean_name": "Apple", "ticker": "AAPL"},
    ...     ],
    ... })
    >>> result["companies"][0]["ticker"]
    'AAPL'
    >>> result["companies"][0]["is_verified"]
    True
    >>> result["companies"][1]["is_verified"]
    False
    """
    linked: list[LinkedEntity] = entity_result.get("linked_entities") or []
    if not isinstance(linked, list):
        linked = []

    if ticker_index is None:
        ticker_index = _build_ticker_index(linked)
    if clean_name_index is None:
        clean_name_index = _build_clean_name_index(linked)
    if verified_names is None:
        verified_names = _build_verified_set(
            _coerce_str_list(entity_result.get("companies_verified"))
        )

    companies = _normalize_companies(
        _coerce_str_list(entity_result.get("companies")),
        ticker_index,
        clean_name_index,
        verified_names,
    )
    people = _normalize_people(
        _coerce_str_list(entity_result.get("people"))
    )
    products = _deduplicate_strings(
        _coerce_str_list(entity_result.get("products"))
    )
    locations = _deduplicate_strings(
        _coerce_str_list(entity_result.get("locations"))
    )

    logger.debug(
        "enrich_entities: %d companies (%d verified), %d people, "
        "%d products, %d locations",
        len(companies),
        sum(1 for c in companies if c["is_verified"]),
        len(people),
        len(products),
        len(locations),
    )

    return EnrichedEntityResult(
        companies=companies,
        people=people,
        products=products,
        locations=locations,
    )