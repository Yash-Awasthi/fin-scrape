"""
News intelligence from global-news-intel-platform — article analysis.
"""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class NewsArticle:
    title: str
    source: str
    url: str = ""
    published: str = ""
    summary: str = ""
    sentiment: float = 0.0
    topics: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    region: str = ""
    importance: float = 0.0


@dataclass
class NewsDigest:
    articles: List[NewsArticle]
    top_topics: List[Dict[str, int]]
    avg_sentiment: float = 0.0
    region_breakdown: Dict[str, int] = field(default_factory=dict)
    alert_count: int = 0


def analyze_article(article: NewsArticle) -> NewsArticle:
    words = article.title.lower().split()
    positive_words = {"surge", "gain", "rise", "profit", "growth", "boom", "rally", "upgrade"}
    negative_words = {"crash", "drop", "loss", "decline", "crisis", "recession", "downgrade", "default"}
    pos = sum(1 for w in words if w in positive_words)
    neg = sum(1 for w in words if w in negative_words)
    total = pos + neg
    article.sentiment = (pos - neg) / total if total > 0 else 0.0
    article.importance = min(1.0, len(article.entities) * 0.2 + abs(article.sentiment) * 0.3 + len(article.topics) * 0.1)
    return article


def build_digest(articles: List[NewsArticle]) -> NewsDigest:
    analyzed = [analyze_article(a) for a in articles]
    avg_sentiment = sum(a.sentiment for a in analyzed) / len(analyzed) if analyzed else 0
    topics: Dict[str, int] = {}
    regions: Dict[str, int] = {}
    for a in analyzed:
        for t in a.topics: topics[t] = topics.get(t, 0) + 1
        if a.region: regions[a.region] = regions.get(a.region, 0) + 1
    top_topics = [{"topic": k, "count": v} for k, v in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]]
    alerts = sum(1 for a in analyzed if abs(a.sentiment) > 0.7)
    return NewsDigest(articles=analyzed, top_topics=top_topics, avg_sentiment=avg_sentiment, region_breakdown=regions, alert_count=alerts)
