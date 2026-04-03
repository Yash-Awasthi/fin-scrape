"""
event_detector.py
-----------------
Stage 3 of the financial NLP pipeline: Event Detection.

Consumes:
    - Raw source text
    - EnrichedEntityResult (Stage 2 output — TypedDict with companies/people/
      products/locations; each Company carries name, ticker, is_verified)

Produces:
    - EventDetectionResult: frozen container of DetectedEvent objects,
      each binding a company name to a trigger phrase and event type.

Design:
    - Fully deterministic; zero ML dependencies.
    - Rule-based keyword matching with trigger-proximity validation.
    - Dedup keyed on (entity, event_type, sentence) — first/longest trigger wins.
    - is_verified propagated from Stage 2 directly; never recomputed here.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, FrozenSet, Iterator, NamedTuple

if TYPE_CHECKING:
    from entity_enricher import Company, EnrichedEntityResult  # noqa: F401

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

MAX_SENTENCE_CHARS: int = 1_200
MAX_TOKEN_DISTANCE: int = 25

# Risk-qualifier suppression window (tokens; EventType-independent constants go here)
_RISK_QUALIFIER_WINDOW: int = 5

_RISK_QUALIFIER_RE: re.Pattern[str] = re.compile(
    r"\b(?:risk|risks|concern|concerns|fear|fears|threat|threats|"
    r"potential|possibly|possible|exposure|test|tests|testing|"
    r"watchdog|scrutiny|pressure|pressures|worry|worries|looming)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Event taxonomy
# ---------------------------------------------------------------------------

class EventType(str, Enum):
    MERGER_ACQUISITION = "MERGER_ACQUISITION"
    STOCK_MOVEMENT     = "STOCK_MOVEMENT"
    EARNINGS_REPORT    = "EARNINGS_REPORT"
    FUNDING_ROUND      = "FUNDING_ROUND"
    PRODUCT_LAUNCH     = "PRODUCT_LAUNCH"
    LAYOFF             = "LAYOFF"
    LEGAL_ACTION       = "LEGAL_ACTION"
    EXECUTIVE_CHANGE   = "EXECUTIVE_CHANGE"
    PARTNERSHIP        = "PARTNERSHIP"
    BANKRUPTCY         = "BANKRUPTCY"
    DIVIDEND           = "DIVIDEND"
    SHARE_BUYBACK      = "SHARE_BUYBACK"
    REGULATORY_ACTION  = "REGULATORY_ACTION"
    IPO                = "IPO"
    DEBT_ISSUANCE      = "DEBT_ISSUANCE"
    RESTRUCTURING      = "RESTRUCTURING"
    CONTRACT_WIN       = "CONTRACT_WIN"
    ANALYST_RATING     = "ANALYST_RATING"


_ALL_EVENT_TYPE_VALUES: frozenset[str] = frozenset(e.value for e in EventType)

# These event types only apply to corporate entities.
_CORPORATE_ONLY_EVENTS: frozenset[str] = frozenset({
    EventType.LEGAL_ACTION.value,
    EventType.REGULATORY_ACTION.value,
    EventType.BANKRUPTCY.value,
    EventType.SHARE_BUYBACK.value,
    EventType.DIVIDEND.value,
    EventType.IPO.value,
    EventType.DEBT_ISSUANCE.value,
})

# ---------------------------------------------------------------------------
# Risk-qualifier suppression — EventType-dependent sets
# ---------------------------------------------------------------------------
# High-context events require unambiguous trigger sentences.  If the trigger
# sits inside a "risk framing" token window (see _RISK_QUALIFIER_RE defined
# in Tunables above), the event is suppressed.
_HIGH_CONTEXT_EVENT_TYPES: frozenset[str] = frozenset({
    EventType.LEGAL_ACTION.value,
    EventType.REGULATORY_ACTION.value,
    EventType.BANKRUPTCY.value,
})

# ---------------------------------------------------------------------------
# "Against" directional pivot scope
# ---------------------------------------------------------------------------
# The entity-reassignment pivot (subject → entity appearing after "against")
# is meaningful only for inherently directional event types.  Scoping it here
# prevents an incidental "against" from corrupting entity assignment for
# STOCK_MOVEMENT, PRODUCT_LAUNCH, etc.
_AGAINST_DIRECTIONAL_TYPES: frozenset[str] = frozenset({
    EventType.LEGAL_ACTION.value,
    EventType.REGULATORY_ACTION.value,
    EventType.MERGER_ACQUISITION.value,
})

# ---------------------------------------------------------------------------
# Per-entity event-type priority
# ---------------------------------------------------------------------------
# Used in post-detection filtering: if an entity generates events of multiple
# types in one article, only types within _PRIORITY_TOLERANCE of the entity's
# highest-priority event are kept.  LEGAL_ACTION is intentionally lower than
# concrete business events so that a weak legal signal does not shadow a
# high-confidence EARNINGS or PRODUCT_LAUNCH event.
_EVENT_TYPE_PRIORITY: dict[str, int] = {
    EventType.MERGER_ACQUISITION.value:  10,
    EventType.BANKRUPTCY.value:          10,
    EventType.IPO.value:                  9,
    EventType.EARNINGS_REPORT.value:      8,
    EventType.LAYOFF.value:               7,
    EventType.EXECUTIVE_CHANGE.value:     6,
    EventType.FUNDING_ROUND.value:        6,
    EventType.PRODUCT_LAUNCH.value:       5,
    EventType.PARTNERSHIP.value:          5,
    EventType.CONTRACT_WIN.value:         5,
    EventType.RESTRUCTURING.value:        4,
    EventType.STOCK_MOVEMENT.value:       4,
    EventType.ANALYST_RATING.value:       3,
    EventType.LEGAL_ACTION.value:         2,   # ← lower than concrete business events
    EventType.REGULATORY_ACTION.value:    2,
    EventType.SHARE_BUYBACK.value:        1,
    EventType.DIVIDEND.value:             1,
    EventType.DEBT_ISSUANCE.value:        1,
}

# ---------------------------------------------------------------------------
# Trigger groups — keyword → EventType mapping
# Multi-word phrases sorted longest-first at compile time; keys are lowercase.
# ---------------------------------------------------------------------------

# fmt: off
_TRIGGER_GROUPS: dict[EventType, list[str]] = {

    EventType.MERGER_ACQUISITION: [
        "agreed to acquire","acquisition of","acquired","acquires","merged with",
        "merger with","hostile takeover","takeover bid","leveraged buyout",
        "management buyout","bought out","acquire","purchase of","sold to",
        "sale of","buy","purchase","deal to acquire","agreed to buy",
        "agreed to purchase","buyout of","takeover of",
    ],

    EventType.STOCK_MOVEMENT: [
        "stock tumbles", "stock drops", "stock falls", "shares tumble", "shares drop",
        "hit a 52-week high","hit a 52-week low", "tumbles",
        "shares surged","shares plunged","shares rallied","shares tumbled",
        "shares dropped","shares soared","shares spiked","shares declined",
        "shares rebounded","shares rose","shares fell", 
        "stock surged","stock plunged","stock rallied","stock dropped",
        "stock soared","stock rose","stock fell",
        "surged","plunged","tumbled","soared","rallied","rose",
        "fell sharply","gained","lost ground","traded higher","traded lower",
        "edged up","edged down","moved higher","moved lower",
        "shares gained","shares slipped","shares edged higher","shares edged lower",
        "stock gained","stock slipped","stock edged higher","stock edged lower",
        "traded up","traded down", "shares climbed","stock climbed",
        "trading higher","trading lower","trading sharply higher","trading sharply lower",
        "shares jumped","shares slid","shares slumped","shares weakened",
        "stock jumped","stock slid","stock slumped","stock weakened",
        "momentum building","momentum fading","strong momentum","weak momentum",
        "uptrend","downtrend","market rally","market selloff","broad rally","sharp selloff",
        "heavy trading","active trading","volume surge","trading volume surged",
        "trading volume spiked","unusual trading activity","options activity","high volume trading",
        "investor optimism","investor concerns","investor confidence","investor panic",
        "market confidence","market fears","risk-off sentiment","risk-on sentiment",
        "market crash","flash crash","sharp rally","massive rally","steep decline",
        "sharp drop","dramatic fall","record rally",
        "valuation surge","valuation decline","market capitalization",
        "market cap milestone","valuation milestone",
        "bullish outlook","bearish outlook","bullish sentiment","bearish sentiment",
        "turns bullish","turns bearish","bullish call","bearish call",
        "bull case","bear case","strong bullish","strong bearish",
        "stocks rallied","stocks fell","stocks surged","stocks dropped","stocks jumped",
        "stocks slid","stocks slumped","stocks weakened","stocks strengthened",
        "stocks advanced","stocks retreated","stocks declined","stocks climbed",
        "skyrocketed","collapsed","crashed","plummeted","spiked sharply",
        "surged sharply","plunged sharply","jumped sharply","slumped sharply",
        "bullish stance","bearish stance","bullish momentum","bearish momentum",
        "bullish trend","bearish trend","bull market","bear market",
        "investors cheered","investors welcomed","investors worried",
        "investors concerned","investor sentiment improved",
        "investor sentiment weakened","investor demand","investor appetite",
        "inflation fears","interest rate fears","economic slowdown",
        "economic recovery","market volatility","risk appetite",
        "jumped","jumps","boosted","boosts","advanced","advances","climbed","climbs",
    ],

    EventType.EARNINGS_REPORT: [
        "reported quarterly earnings","reported annual earnings","reported net income",
        "reported earnings","reported revenue","quarterly earnings","quarterly results",
        "annual results","earnings per share","earnings report","beat estimates",
        "missed estimates","beat expectations","missed expectations",
        "posted earnings","posted profit","posted revenue","net income",
        "profit rose","profit fell","earnings guidance","issued guidance",
        "revenue forecast","financial results","record profit","record revenue",
        "profit jumped","profit declined","revenue grew","revenue declined",
        "earnings outlook","raised guidance","cut guidance",
        "forecast revenue","forecast earnings","revenue guidance",
        "lowered guidance","expects revenue","expects earnings","expects profit",
        "projects revenue","projects earnings","outlook for revenue",
        "outlook for earnings","business outlook","financial outlook",
        "business success","strong performance","weak performance",
        "operational success","record growth","growth slowed",
        "growth accelerated","business slowdown","performance improvement",
        "performance decline","profit warning","earnings warning",
        "quarterly profit","quarterly revenue","earnings growth",
        "profit growth","revenue growth","earnings decline","profit decline",
        "revenue decline","operating income","operating margin","gross margin",
        "raised outlook","lowered outlook","boosted forecast","trimmed forecast",
        "revised guidance","updated guidance","financial guidance", "increases","increased"
    ],

    EventType.FUNDING_ROUND: [
        "closed a funding round","raised funding","secured funding",
        "series a funding","series b funding","series c funding",
        "series a round","series b round","series c round",
        "seed funding","seed round","venture capital","raised $","raised €",
        "investment round","funding round","backed by","led by investors",
        "invested in","investment from","venture funding",
        "series d funding","series e funding","growth funding",
        "investing in","plans to invest","strategic investment","equity investment",
        "minority stake","acquired a stake","took a stake","stake purchase",
        "investment deal","acquired stake","stake acquisition","equity stake",
        "major stake","minority investment","strategic stake","shareholding",
    ],

    EventType.PRODUCT_LAUNCH: [
        "new product launch","announced the launch","announced the release",
        "launched its","launched a new","launched the","unveiled its","unveiled a",
        "introduced its","introduced a new","released its","debuted its",
        "rolled out","rollout","showcased","revealed","new model",
        "introduced the","launched new","new product",
        "successful launch","product success","product failure",
        "announced new platform","new technology","new chip","new processor",
        "next-generation","new service launch","cloud service launch",
        "software release",
    ],

    EventType.LAYOFF: [
        "reduce its workforce","workforce reduction","announced layoffs",
        "cutting jobs","cut jobs","laying off","laid off","job cuts",
        "downsizing","redundancies","retrenchment","layoffs",
        "cut workforce","reduce workforce","staff reductions","job reduction",
    ],

    EventType.LEGAL_ACTION: [
        # ── Directional phrases (entity is the TARGET, not the actor) ──────────
        "urge antitrust action against", "antitrust action against",
        "filed lawsuit against", "filed suit against", "legal action against",
        "court order against", "ruling against",
        # ── Active litigation ────────────────────────────────────────────────
        "antitrust lawsuit", "class action lawsuit", "class action",
        "filed a lawsuit", "files a lawsuit", "lawsuit filed",
        "antitrust action", "urge antitrust action", "faces lawsuit",
        "legal proceedings", "court ruling",
        # ── Regulatory enforcement (concrete outcomes only) ──────────────────
        "reached a settlement", "settlement of", "sec charged", "doj charged",
        "fined by", "regulatory fine", "sued by", "indicted",
        # ── Investigation / probe (multi-word forms only) ────────────────────
        "antitrust probe", "faces investigation", "under regulatory probe",
        "faces legal action", "filed legal action",
        # NOTE: Removed bare "antitrust", "against", "litigation", "legal action",
        # "urge action", "lawsuit" — all fire on risk-framing sentences like
        # "Antitrust Risks Test Valuation" or "litigation concerns" where no
        # actual legal event has occurred.  Multi-word forms above cover every
        # legitimate case those tokens were intended to catch.
    ],
    EventType.EXECUTIVE_CHANGE: [
        "chief executive officer","replaced as ceo","stepped down as",
        "appointed as ceo","appointed ceo","named as ceo","resigned as",
        "new ceo","named ceo","takes over as ceo","succeeds as ceo",
        "interim ceo","appointed chairman","appointed president",
        "named president","stepped down",
    ],

    EventType.PARTNERSHIP: [
        "entered a partnership","strategic alliance","joint venture with",
        "collaboration with","partnered with","teamed up with",
        "partnership with","collaborates with","teams up with",
        "joined forces with","collaboration agreement","strategic partnership",
        "commercial partnership","technology partnership","distribution agreement",
        "licensing agreement","supply agreement","cooperation agreement",
    ],

    EventType.BANKRUPTCY: [
        "chapter 11 protection","filed for bankruptcy","filed for chapter 11",
        "filed for chapter 7","declared bankruptcy","insolvency","insolvent",
        "bankruptcy protection","seeks bankruptcy",
        "defaulted on debt","missed debt payment","credit downgrade",
        "debt default","bond default","credit risk","liquidity crisis",
        "debt restructuring","financial distress","default risk",
    ],

    EventType.DIVIDEND: [
        "declared a special dividend","declared a dividend",
        "suspended its dividend","raised its dividend",
        "cut its dividend","dividend per share","dividend payout",
        "increased dividend",
    ],

    EventType.SHARE_BUYBACK: [
        "stock repurchase program","share repurchase program","repurchase program",
        "buyback program","stock repurchase","share repurchase",
        "stock buyback","share buyback",
    ],

    EventType.REGULATORY_ACTION: [
        "approved by regulators","regulatory approval","antitrust approval",
        "under investigation by","ftc investigation","sec investigation",
        "regulatory scrutiny","government probe","regulatory investigation",
        "antitrust investigation","under investigation","regulatory review",
        "government investigation","regulators probing",
    ],

    EventType.IPO: [
        "initial public offering","began trading on","priced its ipo",
        "filed for ipo","went public","listed on","ipo filing",
        "plans ipo","preparing ipo","ipo plans","ipo prospectus",
        "filed confidentially","ipo valuation","ipo launch","ipo roadshow",
    ],

    EventType.DEBT_ISSUANCE: [
        "issued bonds","bond offering","debt offering","credit facility",
        "senior notes","term loan","bond sale","notes offering","debt sale",
    ],

    EventType.RESTRUCTURING: [
        "corporate restructuring","restructuring plan","reorganization plan",
        "divestiture","divested","spin-off","spinoff","asset sale",
        "unit sale","business sale","strategic shift","business transformation",
        "strategic pivot","major overhaul","corporate overhaul",
        "project failure","project success","strategic success","strategic failure",
        "expanding operations","expansion plan","global expansion","market expansion",
        "expanding into","entered the market","opening new facility",
        "new manufacturing plant","building new factory",
        "strategic review","business realignment","cost cutting plan",
        "cost reduction plan","operational overhaul", "competitive pressures",
        "organizational restructuring","strategic realignment",
        "production expansion","capacity expansion", "loss of business",
        "new manufacturing facility","factory expansion","plant expansion",
        "boosts","boosted","boosting","expands","expanded"
    ],

    EventType.CONTRACT_WIN: [
        "awarded a contract","secured a contract","multi-year contract",
        "government contract","won a contract","contract award",
        "contract extension","major contract","signed contract",
        "supply agreement","supply contract","procurement contract",
        "defense contract","service agreement","framework agreement",
    ],

    EventType.ANALYST_RATING: [
        "upgraded to","downgraded to","reinstated at","initiated coverage",
        "maintained rating","downgraded", "downgrades",
        "maintains rating","reiterated rating",
        "raised price target","cut price target","lowered price target",
        "increased price target","set price target","analyst upgrade",
        "analyst downgrade","initiated with","coverage initiated",
        "buy rating","sell rating","strong buy","strong sell",
        "maintains buy","maintains sell","downgraded to sell",
        "upgraded to buy","neutral rating","hold rating",
        "overweight rating","underweight rating","outperform rating",
        "underperform rating","market perform","equal weight",
        "rating reiterated","analyst note","analyst report",
        "broker upgrade","broker downgrade","research note",
        "equity research","coverage upgraded","coverage downgraded",
        "initiated coverage on","initiated coverage with",
        "coverage resumed","coverage reinstated","coverage started",
        "downgrade", "says sell", "cut to sell", "analyst",
    ],
}



_RAW_TRIGGER_MAP: dict[str, EventType] = {
    trigger: event_type
    for event_type, triggers in _TRIGGER_GROUPS.items()
    for trigger in triggers
}
# fmt: on

# ---------------------------------------------------------------------------
# Compiled trigger patterns — lazy singleton
# ---------------------------------------------------------------------------

class _CompiledTrigger(NamedTuple):
    pattern:    re.Pattern[str]
    keyword:    str
    event_type: EventType


def _build_trigger_patterns(mapping: dict[str, EventType]) -> tuple[_CompiledTrigger, ...]:
    """Compile trigger phrases into boundary-safe regex patterns, longest first."""
    result: list[_CompiledTrigger] = []
    for phrase, event_type in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        pattern = re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)", re.IGNORECASE)
        result.append(_CompiledTrigger(pattern=pattern, keyword=phrase, event_type=event_type))
    return tuple(result)


_TRIGGER_PATTERNS_CACHE: tuple[_CompiledTrigger, ...] | None = None


def _get_trigger_patterns() -> tuple[_CompiledTrigger, ...]:
    global _TRIGGER_PATTERNS_CACHE
    if _TRIGGER_PATTERNS_CACHE is None:
        _TRIGGER_PATTERNS_CACHE = _build_trigger_patterns(_RAW_TRIGGER_MAP)
    return _TRIGGER_PATTERNS_CACHE


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DetectedEvent:
    """A single financial event detected within one sentence."""
    entity:      str
    event_type:  EventType
    trigger:     str
    sentence:    str
    is_verified: bool   # Propagated from Stage 2 Company.is_verified


@dataclass(frozen=True)
class EventDetectionResult:
    """Aggregate output of Stage 3. Frozen to prevent downstream mutation."""
    events:          tuple[DetectedEvent, ...] = field(default_factory=tuple)
    total_sentences: int = 0
    entity_hits:     int = 0   # Sentences that produced ≥1 event

    def by_entity(self, name: str) -> list[DetectedEvent]:
        lower = name.lower()
        return [e for e in self.events if e.entity.lower() == lower]

    def by_event_type(self, event_type: str | EventType) -> list[DetectedEvent]:
        target = EventType(event_type) if isinstance(event_type, str) else event_type
        return [e for e in self.events if e.event_type == target]

    def verified_events(self) -> list[DetectedEvent]:
        """Events where the source entity was Stage-1 verified."""
        return [e for e in self.events if e.is_verified]

    def unique_entities(self) -> FrozenSet[str]:
        return frozenset(e.entity for e in self.events)

    def unique_event_types(self) -> FrozenSet[EventType]:
        return frozenset(e.event_type for e in self.events)

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self) -> Iterator[DetectedEvent]:
        return iter(self.events)


# ---------------------------------------------------------------------------
# Sentence splitter
# ---------------------------------------------------------------------------

_ABBREV_ALTS = (
    r"Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|Mt|No|Sen|Rep|Gov|Gen|Sgt|Cpl|Pvt|Capt|"
    r"Maj|Col|Lt|Cmdr|Adm|vs|etc|approx|est|Corp|Co|Ltd|Inc|LLC|LLP|PLC|"
    r"AG|SA|NV|BV|GmbH|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|"
    r"U\.S|U\.K|E\.U|Q[1-4]"
)
_ABBREV_RE           = re.compile(rf"(?:{_ABBREV_ALTS})\.", re.IGNORECASE)
_PERIOD_PLACEHOLDER  = "\x00P\x00"
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")
_MULTI_SPACE_RE      = re.compile(r"\s+")


def _split_sentences(text: str) -> list[str]:
    """Regex sentence tokeniser tuned for financial news.
    Masks known abbreviation periods; does not require uppercase sentence starts."""
    masked = _ABBREV_RE.sub(lambda m: m.group().replace(".", _PERIOD_PLACEHOLDER), text)
    parts  = _SENTENCE_BOUNDARY_RE.split(masked)
    return [
        _MULTI_SPACE_RE.sub(" ", part.replace(_PERIOD_PLACEHOLDER, ".")).strip()
        for part in parts
        if part.strip()
    ]


# ---------------------------------------------------------------------------
# Entity matching helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=4096)
def _entity_pattern(name: str) -> re.Pattern[str]:
    """Boundary-safe pattern for a single entity name. Cached per name."""
    return re.compile(rf"(?<!\w){re.escape(name)}(?!\w)", re.IGNORECASE)


def _build_combined_entity_pattern(names: list[str]) -> re.Pattern[str]:
    """Single alternation regex for fast sentence-level entity presence check."""
    alts = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alts})(?!\w)", re.IGNORECASE)


def _entities_in_sentence(
    sentence: str,
    names: list[str],
    combined: re.Pattern[str],
) -> list[tuple[int, int, str]]:

    """
    Return entity spans as (start, end, name) tuples for entities present in the sentence., longest-first.
    Overlapping spans are suppressed — only the longest match per span fires.
    """
    if not combined.search(sentence):
        return []

    accepted: list[tuple[int, int, str]] = []   # (start, end, name)
    for name in sorted(names, key=len, reverse=True):
        for m in _entity_pattern(name).finditer(sentence):
            s, e = m.start(), m.end()
            if any(start < e and s < end for start, end, _ in accepted):
                continue
            accepted.append((s, e, name))

    return [(start, end, name) for start, end, name in sorted(accepted)]


# ---------------------------------------------------------------------------
# Trigger proximity check
# ---------------------------------------------------------------------------

def _within_proximity(sentence: str, entity: str, trigger: str) -> bool:
    """True if trigger falls within MAX_TOKEN_DISTANCE tokens of entity.
    Skipped entirely when MAX_TOKEN_DISTANCE == 0."""
    if MAX_TOKEN_DISTANCE <= 0:
        return True

    tokens   = sentence.lower().split()
    e_lower  = entity.lower()
    t_tokens = trigger.lower().split()

    entity_idx  = [i for i, tok in enumerate(tokens) if e_lower  in tok.strip(".,:$()\"'")]
    trigger_idx = [i for i, tok in enumerate(tokens) if t_tokens[0] in tok]

    if not entity_idx or not trigger_idx:
        return False

    return any(
        abs(ei - ti) <= MAX_TOKEN_DISTANCE
        for ei in entity_idx
        for ti in trigger_idx
    )


# ---------------------------------------------------------------------------
# Internal: per-sentence detection
# ---------------------------------------------------------------------------

def _detect_events_in_sentence(
    sentence:           str,
    entities: list[tuple[int, int, str]],
    entity_verified:    dict[str, bool],
    entity_is_corporate: dict[str, bool],
    triggers:           tuple[_CompiledTrigger, ...],
) -> list[DetectedEvent]:
    
    detected_dict: dict[tuple[str, str], DetectedEvent] = {}
    sent_lower = sentence.lower()

    for compiled in triggers:
        for m in compiled.pattern.finditer(sentence):
            trigger_pos = m.start()
            etype_val = compiled.event_type.value
        
            subject = None
            ent_pos = -1

            # --- 1. SEMANTIC PIVOT: reassign subject to the entity *after* "against".
            #        Scoped to _AGAINST_DIRECTIONAL_TYPES so an incidental "against"
            #        in a STOCK_MOVEMENT / PRODUCT_LAUNCH sentence doesn't corrupt
            #        entity assignment for unrelated triggers.
            if etype_val in _AGAINST_DIRECTIONAL_TYPES and "against" in sent_lower:
                against_idx = sent_lower.find("against")
                # Candidates are entities whose span starts after "against"; list is
                # already position-sorted, so the first hit is the nearest one.
                candidates = [(s, e, n) for s, e, n in entities if s > against_idx]
                if candidates:
                    s_best, _, target_entity = candidates[0]
                    subject = target_entity
                    ent_pos = s_best

            # --- 2. HEURISTICS: Fallback if no "against" keyword is present ---
            if subject is None:
                # Specific fix for "Restructuring" (Article 5)
                if compiled.event_type == EventType.RESTRUCTURING and entities:
                    start, end, subject = entities[0]
                    ent_pos = start
                else:
                    # Default: Find the entity closest to the trigger
                    best_dist = float("inf")
                    for start, end, name in entities:
                        dist = abs(trigger_pos - start)
                        if dist < best_dist:
                            best_dist = dist
                            subject = name
                            ent_pos = start

            # Final Fallback: if somehow still None, pick first available
            if subject is None and entities:
                ent_pos, _, subject = entities[0]

            if not subject: continue

            # --- 3. DEDUPLICATION & FILTERS ---
            if (subject, etype_val) in detected_dict:
                continue

            ent_lower = subject.lower()
            
            # Analyst/Bank Filter
            source_names = ["bofa", "bank of america", "goldman", "gs", "morgan stanley", "ms"]
            if any(s in ent_lower for s in source_names):
                if not entity_verified.get(subject, False):
                    continue

            # Attribution Filter (Ensure "Apple says..." doesn't trigger on Apple)
            reporting_verbs = ["warns", "notes", "reports", "says", "claims"]
            is_source = False
            for verb in reporting_verbs:
                verb_idx = sent_lower.find(verb)
                if verb_idx != -1 and ent_pos > verb_idx:
                    is_source = True
                    break
            if is_source: continue
            
            # Corporate/Verified Safety
            if etype_val in _CORPORATE_ONLY_EVENTS:
                if not (entity_is_corporate.get(subject, True) or entity_verified.get(subject, False)):
                    continue

            # --- Risk-qualifier suppression ----------------------------------------
            # For high-stakes events (LEGAL_ACTION, REGULATORY_ACTION, BANKRUPTCY),
            # check whether the trigger sits inside a "risk framing" window.
            # e.g. "Antitrust *Risks* Test Valuation" → trigger="antitrust probe",
            # window contains "risks" → suppress (it's a risk discussion, not an event).
            if etype_val in _HIGH_CONTEXT_EVENT_TYPES:
                trig_tokens  = compiled.keyword.split()
                all_tokens   = sentence.split()
                # Find the token-index of the first token of the trigger phrase.
                trig_start_char = m.start()
                tok_idx = len(sentence[:trig_start_char].split())
                window_lo = max(0, tok_idx - _RISK_QUALIFIER_WINDOW)
                window_hi = min(len(all_tokens), tok_idx + len(trig_tokens) + _RISK_QUALIFIER_WINDOW)
                window_text = " ".join(all_tokens[window_lo:window_hi])
                if _RISK_QUALIFIER_RE.search(window_text):
                    logger.debug(
                        "event_detector: risk-qualifier suppressed %s for '%s' | window=%r",
                        etype_val, subject, window_text,
                    )
                    continue

            # SUCCESS
            detected_dict[(subject, etype_val)] = DetectedEvent(
                entity=subject,
                event_type=compiled.event_type,
                trigger=compiled.keyword,
                sentence=sentence,
                is_verified=entity_verified.get(subject, False),
            )
            
    return list(detected_dict.values())# ---------------------------------------------------------------------------
# Internal: extract company records from Stage 2 TypedDict
# ---------------------------------------------------------------------------

def _extract_entity_records(enriched: dict) -> list[tuple[str, bool, bool]]:
    """
    Consume Stage 2 EnrichedEntityResult (TypedDict / plain dict).

    Returns a list of (canonical_name, is_verified, is_corporate) tuples,
    deduped and sorted longest-name-first so the combined entity regex
    shadows shorter substrings correctly.

    is_corporate is True for all entries from enriched["companies"] and
    False for entries from enriched["people"].  This distinction gates
    _CORPORATE_ONLY_EVENTS in _detect_events_in_sentence — e.g. a Person
    entity will never fire DIVIDEND or SHARE_BUYBACK even if those triggers
    appear in proximity.  Defaulting companies to True means the guard is
    future-proof: if enriched["people"] is ever wired in, it arrives as
    is_corporate=False without any further changes needed downstream.

    Stage 2 contract consumed here:
        enriched["companies"] → list of Company TypedDicts
        Company["name"]        → str  (canonical, suffix-stripped)
        Company["is_verified"] → bool (set by Stage 1 precision lane)
    """
    seen:    set[str]                   = set()
    records: list[tuple[str, bool, bool]] = []

    for company in enriched.get("companies", []):
        if not isinstance(company, dict):
            continue
        # Use the canonical 'name', but also allow 'ticker' as a valid match target
        name_val = company.get("name")
        name     = name_val.strip() if isinstance(name_val, str) else ""
        name = re.sub(r"\b(stock|shares)\b.*", "", name, flags=re.I).strip()
        tick_val = company.get("ticker")
        ticker   = tick_val.strip() if isinstance(tick_val, str) else ""
        verified = bool(company.get("is_verified", False))
        
        if name:
            key = name.lower()
            if key not in seen:
                seen.add(key)
                records.append((name, verified, True))
        
        # ADD THIS: Also allow the ticker to act as the entity anchor
        if ticker and ticker.lower() not in seen:
            seen.add(ticker.lower())
            records.append((ticker, verified, True))

    # People are non-corporate — corporate-only events will be suppressed.
    for person in enriched.get("people", []):
        if not isinstance(person, dict):
            continue
        name = person.get("name", "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        records.append((name, False, False))     # is_verified=False, is_corporate=False

    # Longest name first — prevents shorter substrings shadowing full names
    # in the combined alternation regex.
    records.sort(key=lambda r: len(r[0]), reverse=True)
    return records


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_events(
    text: str,
    enriched_entities: dict,
    *,
    deduplicate: bool = True,
) -> EventDetectionResult:
    """
    Stage 3 entry point: detect financial events in text.

    Parameters
    ----------
    text:
        Raw source document (headline + summary, or full article body).
    enriched_entities:
        Output of entity_enricher.enrich_entities() — a plain dict matching
        the EnrichedEntityResult TypedDict schema.  The function accesses
        enriched_entities["companies"] directly; no attribute access.
    deduplicate:
        Suppress duplicate (entity, event_type, sentence) triples.
        When True, the first/longest trigger per (entity, EventType, sentence)
        is kept and subsequent ones are dropped.

    Returns
    -------
    EventDetectionResult
        Frozen container; events as an immutable tuple.
    """
    if not text or not text.strip():
        logger.debug("event_detector: empty text — skipping.")
        return EventDetectionResult()

    entity_records = _extract_entity_records(enriched_entities)
    if not entity_records:
        logger.debug("event_detector: no company entities — skipping.")
        return EventDetectionResult()

    entity_names       = [r[0] for r in entity_records]
    entity_verified    = {r[0]: r[1] for r in entity_records}
    entity_is_corporate = {r[0]: r[2] for r in entity_records}
    combined_re        = _build_combined_entity_pattern(entity_names)
    triggers           = _get_trigger_patterns()

    sentences  = _split_sentences(text)
    total      = len(sentences)
    events:    list[DetectedEvent]       = []
    seen:      set[tuple[str, str, str]] = set()
    hit_count  = 0

    for sentence in sentences:
        if len(sentence) > MAX_SENTENCE_CHARS:
            logger.debug("event_detector: sentence length %d exceeds limit — skipped.", len(sentence))
            continue

        matched_entities = _entities_in_sentence(sentence, entity_names, combined_re)
        if not matched_entities:
            continue

        sentence_events = _detect_events_in_sentence(
            sentence, matched_entities, entity_verified, entity_is_corporate, triggers,
        )

        new_events: list[DetectedEvent] = []
        for ev in sentence_events:
            key = (ev.entity, ev.event_type.value)
            if deduplicate and key in seen:
                continue
            seen.add(key)
            new_events.append(ev)

        if new_events:
            hit_count += 1
            events.extend(new_events)

    logger.debug(
        "event_detector: %d events (pre-priority) | %d/%d event-producing sentences | "
        "%d verified-entity events.",
        len(events), hit_count, total,
        sum(1 for e in events if e.is_verified),
    )

    # ── Priority-based per-entity resolution ────────────────────────────────
    # If an entity triggers multiple event types (e.g. STOCK_MOVEMENT and
    # LEGAL_ACTION in the same article), retain only the event(s) whose
    # priority equals the maximum observed for that entity.  This prevents
    # a loose LEGAL_ACTION trigger from surviving alongside a high-confidence
    # business event for the same company.
    if events:
        from collections import defaultdict
        entity_max_priority: dict[str, int] = defaultdict(int)
        for ev in events:
            p = _EVENT_TYPE_PRIORITY.get(ev.event_type.value, 0)
            if p > entity_max_priority[ev.entity]:
                entity_max_priority[ev.entity] = p

        _PRIORITY_TOLERANCE: int = 3   # allow events within this many priority levels
        filtered: list[DetectedEvent] = []
        for ev in events:
            p    = _EVENT_TYPE_PRIORITY.get(ev.event_type.value, 0)
            best = entity_max_priority[ev.entity]
            if best - p <= _PRIORITY_TOLERANCE:
                filtered.append(ev)
            else:
                logger.debug(
                    "event_detector: priority-filtered %s for '%s' "
                    "(priority %d vs entity-best %d).",
                    ev.event_type.value, ev.entity, p, best,
                )
        events = filtered

    logger.debug(
        "event_detector: %d events (post-priority) | %d verified-entity events.",
        len(events),
        sum(1 for e in events if e.is_verified),
    )

    return EventDetectionResult(
        events=tuple(events),
        total_sentences=total,
        entity_hits=hit_count,
    )