"""World / geopolitics feed registry — the `Feed` shape + a seed set.

Resolves PLAN.md open-investigation #4 (Feed shape). Each Feed carries the
non-copyrightable facts we need for trust scoring: source `tier` and
`propaganda_risk`. URLs are public RSS endpoints (facts), NOT copied from
worldmonitor source (AGPL). This is a representative SEED subset across tiers;
extend toward the full set as needed — nothing here is load-bearing on count.

Tiers (matches PLAN.md Appendix A SourceType): wire | gov | intel | mainstream
| market | tech | other.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VALID_TIERS = ("wire", "gov", "intel", "mainstream", "market", "tech", "other")
VALID_RISK = ("low", "medium", "high")


@dataclass(frozen=True)
class Feed:
    key: str  # unique, stable id (used as the source tag)
    url: str
    name: str
    tier: str
    region: str = "global"
    propaganda_risk: str = "low"
    topics: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.tier not in VALID_TIERS:
            raise ValueError(f"{self.key}: bad tier {self.tier!r}")
        if self.propaganda_risk not in VALID_RISK:
            raise ValueError(
                f"{self.key}: bad propaganda_risk {self.propaganda_risk!r}"
            )


# Seed registry. Public RSS endpoints; tier/risk are our own classification.
FEEDS: tuple[Feed, ...] = (
    # --- gov / IGO ---
    Feed(
        "un_news",
        "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "UN News",
        "gov",
        propaganda_risk="low",
        topics=("geopolitics", "humanitarian"),
    ),
    Feed(
        "eu_commission",
        "https://ec.europa.eu/commission/presscorner/api/rss?language=en",
        "European Commission",
        "gov",
        region="europe",
    ),
    # --- intel / analysis ---
    Feed(
        "defense_one",
        "https://www.defenseone.com/rss/all/",
        "Defense One",
        "intel",
        region="us",
        topics=("defense", "security"),
    ),
    Feed(
        "war_on_the_rocks",
        "https://warontherocks.com/feed/",
        "War on the Rocks",
        "intel",
        topics=("defense", "strategy"),
    ),
    Feed(
        "csis",
        "https://www.csis.org/analysis/feed",
        "CSIS",
        "intel",
        region="us",
        topics=("strategy", "geopolitics"),
    ),
    # --- mainstream ---
    Feed(
        "bbc_world",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "BBC World",
        "mainstream",
        region="uk",
    ),
    Feed(
        "guardian_world",
        "https://www.theguardian.com/world/rss",
        "The Guardian World",
        "mainstream",
        region="uk",
    ),
    Feed(
        "aljazeera",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "Al Jazeera",
        "mainstream",
        region="mena",
        propaganda_risk="medium",
    ),
    Feed(
        "npr_world",
        "https://feeds.npr.org/1004/rss.xml",
        "NPR World",
        "mainstream",
        region="us",
    ),
    Feed(
        "dw_world",
        "https://rss.dw.com/rdf/rss-en-world",
        "Deutsche Welle",
        "mainstream",
        region="europe",
    ),
    Feed(
        "france24",
        "https://www.france24.com/en/rss",
        "France 24",
        "mainstream",
        region="europe",
    ),
    # --- wire (via aggregators where direct RSS is gated) ---
    Feed(
        "reuters_world_gnews",
        "https://news.google.com/rss/search?q=when:24h+source:reuters+world&hl=en-US&gl=US&ceid=US:en",
        "Reuters (world, via Google News)",
        "wire",
        propaganda_risk="low",
    ),
    Feed(
        "ap_gnews",
        "https://news.google.com/rss/search?q=when:24h+source:%22Associated+Press%22&hl=en-US&gl=US&ceid=US:en",
        "Associated Press (via Google News)",
        "wire",
        propaganda_risk="low",
    ),
    # --- market / finance (geopolitics-adjacent) ---
    Feed(
        "cnbc_world",
        "https://www.cnbc.com/id/100727362/device/rss/rss.html",
        "CNBC World",
        "market",
        region="us",
        topics=("markets", "economy"),
    ),
)

_BY_KEY = {f.key: f for f in FEEDS}


def feed_urls() -> dict[str, str]:
    """{key: url} — the shape RSSScraperSource expects."""
    return {f.key: f.url for f in FEEDS}


def get_feed(key: str) -> Feed | None:
    return _BY_KEY.get(key)


def tier_of(key: str, default: str = "other") -> str:
    f = _BY_KEY.get(key)
    return f.tier if f else default


def propaganda_risk_of(key: str, default: str = "medium") -> str:
    f = _BY_KEY.get(key)
    return f.propaganda_risk if f else default
