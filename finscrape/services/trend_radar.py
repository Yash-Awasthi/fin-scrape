"""Trend Radar Service.

Extracted from trendradar (inspiration).
News trend analysis, keyword extraction, source aggregation,
and trend scoring for financial intelligence.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class TrendUrgency(Enum):
    BREAKING = "breaking"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NewsSource(Enum):
    TWITTER = "twitter"
    REDDIT = "reddit"
    NEWS = "news"
    RSS = "rss"
    TELEGRAM = "telegram"
    DISCORD = "discord"


@dataclass
class NewsItem:
    title: str
    content: str
    source: NewsSource
    url: str = ""
    author: str = ""
    published_at: datetime = field(default_factory=datetime.now)
    keywords: list[str] = field(default_factory=list)
    sentiment: float = 0.0
    engagement: int = 0


@dataclass
class TrendCluster:
    topic: str
    keywords: list[str]
    item_count: int
    sources: list[NewsSource]
    urgency: TrendUrgency
    avg_sentiment: float
    total_engagement: int
    first_seen: datetime
    last_seen: datetime
    summary: str = ""


@dataclass
class TrendReport:
    generated_at: datetime
    clusters: list[TrendCluster]
    total_items: int
    source_breakdown: dict[str, int]
    top_keywords: list[tuple[str, int]]
    urgency_summary: dict[str, int]


STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "because", "but", "and",
    "or", "if", "while", "this", "that", "these", "those", "it", "its",
    "i", "me", "my", "we", "our", "you", "your", "he", "him", "his",
    "she", "her", "they", "them", "their", "what", "which", "who", "whom",
}


def extract_keywords(text: str, top_n: int = 10) -> list[tuple[str, int]]:
    """Extract keywords from text with frequency counts."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    return Counter(filtered).most_common(top_n)


def calculate_sentiment(text: str) -> float:
    """Calculate simple sentiment score -1 to 1."""
    positive = {"bullish", "surge", "rally", "gain", "profit", "growth", "upgrade", "buy", "strong", "positive", "moon", "pump"}
    negative = {"bearish", "crash", "dump", "loss", "decline", "risk", "sell", "weak", "negative", "rug", "scam", "fear"}
    words = set(text.lower().split())
    pos = len(words & positive)
    neg = len(words & negative)
    total = pos + neg
    return (pos - neg) / total if total > 0 else 0.0


def classify_urgency(text: str, engagement: int = 0, recency_hours: float = 24) -> TrendUrgency:
    """Classify news urgency."""
    breaking_words = {"breaking", "urgent", "alert", "just in", "flash", "emergency"}
    if any(w in text.lower() for w in breaking_words):
        return TrendUrgency.BREAKING
    if engagement > 10000 or recency_hours < 1:
        return TrendUrgency.HIGH
    if engagement > 1000 or recency_hours < 6:
        return TrendUrgency.MEDIUM
    return TrendUrgency.LOW


def cluster_news_items(items: list[NewsItem], similarity_threshold: float = 0.3) -> list[TrendCluster]:
    """Cluster news items by topic similarity."""
    if not items:
        return []
    keyword_sets = {}
    for i, item in enumerate(items):
        kws = set(item.keywords) if item.keywords else set(extract_keywords(item.title + " " + item.content, 5))
        keyword_sets[i] = kws
    clusters: list[list[int]] = []
    assigned: set[int] = set()
    for i in range(len(items)):
        if i in assigned:
            continue
        cluster = [i]
        assigned.add(i)
        for j in range(i + 1, len(items)):
            if j in assigned:
                continue
            overlap = len(keyword_sets[i] & keyword_sets[j])
            total = len(keyword_sets[i] | keyword_sets[j])
            if total > 0 and overlap / total >= similarity_threshold:
                cluster.append(j)
                assigned.add(j)
        clusters.append(cluster)
    result = []
    for cluster_indices in clusters:
        cluster_items = [items[i] for i in cluster_indices]
        all_keywords = []
        for item in cluster_items:
            all_keywords.extend(item.keywords if item.keywords else extract_keywords(item.title, 3))
        topic_keywords = Counter(all_keywords).most_common(5)
        topic = topic_keywords[0][0] if topic_keywords else "general"
        sources = list(set(item.source for item in cluster_items))
        sentiments = [item.sentiment for item in cluster_items if item.sentiment != 0]
        engagement = sum(item.engagement for item in cluster_items)
        dates = [item.published_at for item in cluster_items]
        result.append(TrendCluster(
            topic=topic,
            keywords=[k for k, _ in topic_keywords],
            item_count=len(cluster_items),
            sources=sources,
            urgency=classify_urgency(cluster_items[0].title, engagement),
            avg_sentiment=sum(sentiments) / len(sentiments) if sentiments else 0.0,
            total_engagement=engagement,
            first_seen=min(dates),
            last_seen=max(dates),
        ))
    return sorted(result, key=lambda c: c.total_engagement, reverse=True)


def generate_trend_report(items: list[NewsItem]) -> TrendReport:
    """Generate comprehensive trend report."""
    clusters = cluster_news_items(items)
    source_counts = Counter(item.source.value for item in items)
    all_keywords = []
    for item in items:
        all_keywords.extend(item.keywords if item.keywords else extract_keywords(item.title, 3))
    top_keywords = Counter(all_keywords).most_common(20)
    urgency_counts = Counter(c.urgency.value for c in clusters)
    return TrendReport(
        generated_at=datetime.now(),
        clusters=clusters,
        total_items=len(items),
        source_breakdown=dict(source_counts),
        top_keywords=top_keywords,
        urgency_summary=dict(urgency_counts),
    )


def filter_trending(
    clusters: list[TrendCluster],
    min_engagement: int = 100,
    sources: list[NewsSource] | None = None,
    urgency: TrendUrgency | None = None,
) -> list[TrendCluster]:
    """Filter clusters by criteria."""
    result = clusters
    if min_engagement > 0:
        result = [c for c in result if c.total_engagement >= min_engagement]
    if sources:
        result = [c for c in result if any(s in c.sources for s in sources)]
    if urgency:
        result = [c for c in result if c.urgency == urgency]
    return result


def detect_emerging_topics(
    current_clusters: list[TrendCluster],
    previous_clusters: list[TrendCluster],
    growth_threshold: float = 2.0,
) -> list[TrendCluster]:
    """Detect emerging topics by comparing with previous report."""
    prev_topics = {c.topic: c.item_count for c in previous_clusters}
    emerging = []
    for cluster in current_clusters:
        prev_count = prev_topics.get(cluster.topic, 0)
        if prev_count == 0 and cluster.item_count >= 3:
            emerging.append(cluster)
        elif prev_count > 0 and cluster.item_count / prev_count >= growth_threshold:
            emerging.append(cluster)
    return emerging
