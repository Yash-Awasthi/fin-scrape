"""
Ticker News Aggregator for fin-scrape
Extracted from: tickertick-api (stock news query language)
Patterns: Multi-source news aggregation, ticker-based queries, relevance scoring,
          deduplication, chronological ordering, source diversity
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class NewsCategory(Enum):
    EARNINGS = "earnings"
    ANALYST = "analyst"
    SEC_FILINGS = "sec_filings"
    INSIDER = "insider"
    MERGER = "merger"
    PRODUCT = "product"
    REGULATION = "regulation"
    MARKET = "market"
    GENERAL = "general"


class NewsSource(Enum):
    REUTERS = "reuters"
    BLOOMBERG = "bloomberg"
    WSJ = "wsj"
    CNBC = "cnbc"
    SEEKING_ALPHA = "seeking_alpha"
    PR_NEWswire = "pr_newswire"
    SEC = "sec"
    TWITTER = "twitter"
    REDDIT = "reddit"
    UNKNOWN = "unknown"


@dataclass
class NewsStory:
    id: str
    title: str
    url: str
    source: NewsSource
    timestamp: datetime
    tickers: list[str] = field(default_factory=list)
    category: NewsCategory = NewsCategory.GENERAL
    sentiment: float = 0.0  # -1 to 1
    relevance: float = 0.0  # 0 to 1
    summary: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class NewsQuery:
    tickers: list[str] = field(default_factory=list)
    categories: list[NewsCategory] = field(default_factory=list)
    sources: list[NewsSource] = field(default_factory=list)
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    keywords: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)
    exclude_sources: list[NewsSource] = field(default_factory=list)
    limit: int = 100
    min_relevance: float = 0.0


@dataclass
class AggregatedFeed:
    stories: list[NewsStory]
    total_count: int
    ticker_coverage: dict[str, int]
    category_breakdown: dict[str, int]
    source_breakdown: dict[str, int]
    avg_sentiment: float
    time_range: tuple[datetime, datetime]


# ─── News Source Configuration ─────────────────────────────────────────

SOURCE_CREDIBILITY = {
    NewsSource.REUTERS: 0.95,
    NewsSource.BLOOMBERG: 0.95,
    NewsSource.WSJ: 0.90,
    NewsSource.CNBC: 0.85,
    NewsSource.SEEKING_ALPHA: 0.70,
    NewsSource.PR_NEWSWIRE: 0.80,
    NewsSource.SEC: 0.99,
    NewsSource.TWITTER: 0.40,
    NewsSource.REDDIT: 0.30,
    NewsSource.UNKNOWN: 0.50,
}

CATEGORY_WEIGHTS = {
    NewsCategory.EARNINGS: 1.0,
    NewsCategory.ANALYST: 0.9,
    NewsCategory.SEC_FILINGS: 0.95,
    NewsCategory.INSIDER: 0.9,
    NewsCategory.MERGER: 0.95,
    NewsCategory.PRODUCT: 0.7,
    NewsCategory.REGULATION: 0.8,
    NewsCategory.MARKET: 0.6,
    NewsCategory.GENERAL: 0.5,
}


# ─── Query Engine ──────────────────────────────────────────────────────

def query_news(stories: list[NewsStory], query: NewsQuery) -> list[NewsStory]:
    """Filter and rank news stories based on query parameters."""
    results = stories

    # Filter by tickers
    if query.tickers:
        ticker_set = set(t.upper() for t in query.tickers)
        results = [s for s in results if any(t in ticker_set for t in s.tickers)]

    # Filter by categories
    if query.categories:
        cat_set = set(query.categories)
        results = [s for s in results if s.category in cat_set]

    # Filter by sources
    if query.sources:
        src_set = set(query.sources)
        results = [s for s in results if s.source in src_set]

    # Exclude sources
    if query.exclude_sources:
        excl_set = set(query.exclude_sources)
        results = [s for s in results if s.source not in excl_set]

    # Filter by time range
    if query.since:
        results = [s for s in results if s.timestamp >= query.since]
    if query.until:
        results = [s for s in results if s.timestamp <= query.until]

    # Filter by keywords
    if query.keywords:
        kw_lower = [k.lower() for k in query.keywords]
        results = [
            s for s in results
            if any(kw in s.title.lower() or kw in s.summary.lower() for kw in kw_lower)
        ]

    # Exclude keywords
    if query.exclude_keywords:
        excl_kw = [k.lower() for k in query.exclude_keywords]
        results = [
            s for s in results
            if not any(kw in s.title.lower() or kw in s.summary.lower() for kw in excl_kw)
        ]

    # Filter by minimum relevance
    if query.min_relevance > 0:
        results = [s for s in results if s.relevance >= query.min_relevance]

    # Compute composite score and sort
    scored = [(compute_story_score(s), s) for s in results]
    scored.sort(key=lambda x: x[0], reverse=True)

    return [s for _, s in scored[:query.limit]]


def compute_story_score(story: NewsStory) -> float:
    """Compute a composite relevance score for ranking."""
    credibility = SOURCE_CREDIBILITY.get(story.source, 0.5)
    category_weight = CATEGORY_WEIGHTS.get(story.category, 0.5)

    # Recency decay (exponential)
    hours_old = (datetime.now() - story.timestamp).total_seconds() / 3600
    recency = math.exp(-hours_old / 24) if hours_old > 0 else 1.0

    return story.relevance * 0.4 + credibility * 0.25 + category_weight * 0.2 + recency * 0.15


# ─── Aggregation ───────────────────────────────────────────────────────

import math

def aggregate_feed(stories: list[NewsStory]) -> AggregatedFeed:
    """Aggregate a list of news stories into a summary feed."""
    if not stories:
        return AggregatedFeed(
            stories=[], total_count=0, ticker_coverage={},
            category_breakdown={}, source_breakdown={},
            avg_sentiment=0, time_range=(datetime.now(), datetime.now()),
        )

    ticker_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    sentiments = []

    for story in stories:
        for ticker in story.tickers:
            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
        category_counts[story.category.value] = category_counts.get(story.category.value, 0) + 1
        source_counts[story.source.value] = source_counts.get(story.source.value, 0) + 1
        sentiments.append(story.sentiment)

    timestamps = [s.timestamp for s in stories]

    return AggregatedFeed(
        stories=stories,
        total_count=len(stories),
        ticker_coverage=ticker_counts,
        category_breakdown=category_counts,
        source_breakdown=source_counts,
        avg_sentiment=sum(sentiments) / len(sentiments) if sentiments else 0,
        time_range=(min(timestamps), max(timestamps)),
    )


# ─── Deduplication ─────────────────────────────────────────────────────

def deduplicate_stories(stories: list[NewsStory], similarity_threshold: float = 0.8) -> list[NewsStory]:
    """Remove duplicate news stories based on title similarity."""
    if not stories:
        return []

    unique = [stories[0]]
    for story in stories[1:]:
        is_dup = False
        for existing in unique:
            similarity = title_similarity(story.title, existing.title)
            if similarity > similarity_threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(story)

    return unique


def title_similarity(a: str, b: str) -> float:
    """Simple Jaccard similarity on word tokens."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return intersection / union if union > 0 else 0.0


# ─── Ticker-Specific Feed ──────────────────────────────────────────────

def get_ticker_feed(
    stories: list[NewsStory],
    ticker: str,
    limit: int = 50,
    include_related: bool = True,
) -> dict:
    """Get a comprehensive feed for a specific ticker."""
    ticker = ticker.upper()
    direct_stories = [s for s in stories if ticker in s.tickers]

    # Related tickers (appear together in news)
    related_tickers: dict[str, int] = {}
    for story in direct_stories:
        for other_ticker in story.tickers:
            if other_ticker != ticker:
                related_tickers[other_ticker] = related_tickers.get(other_ticker, 0) + 1

    top_related = sorted(related_tickers.items(), key=lambda x: x[1], reverse=True)[:10]

    # Sentiment over time
    daily_sentiment: dict[str, list[float]] = {}
    for story in direct_stories:
        day = story.timestamp.strftime("%Y-%m-%d")
        daily_sentiment.setdefault(day, []).append(story.sentiment)

    sentiment_trend = {
        day: sum(vals) / len(vals) for day, vals in daily_sentiment.items()
    }

    return {
        "ticker": ticker,
        "total_stories": len(direct_stories),
        "stories": direct_stories[:limit],
        "related_tickers": top_related,
        "sentiment_trend": sentiment_trend,
        "avg_sentiment": sum(s.sentiment for s in direct_stories) / len(direct_stories) if direct_stories else 0,
    }
