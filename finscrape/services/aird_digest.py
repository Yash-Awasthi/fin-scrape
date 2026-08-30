"""
AIRD Digest — Extracted from AIRD patterns.

AI-powered RSS digest with:
- Interest-based filtering
- Local deduplication
- Article summarization
- Configurable output formats
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set


@dataclass
class Article:
    title: str
    url: str
    source: str
    published: str = ""
    content: str = ""
    summary: str = ""
    tags: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    fingerprint: str = ""

    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = self._compute_fingerprint()

    def _compute_fingerprint(self) -> str:
        content = f"{self.title}:{self.url}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class DigestConfig:
    rss_urls: List[str] = field(default_factory=list)
    interest_tags: List[str] = field(default_factory=list)
    noise_tags: List[str] = field(default_factory=list)
    max_articles: int = 50
    filter_model: str = "gpt-4"
    summary_model: str = "gpt-3.5-turbo"
    language: str = "en"
    batch_size: int = 10


class DeduplicationCache:
    """Local deduplication using fingerprints."""

    def __init__(self) -> None:
        self._seen: Set[str] = set()
        self._db: Dict[str, float] = {}

    def is_duplicate(self, fingerprint: str) -> bool:
        return fingerprint in self._seen

    def add(self, fingerprint: str) -> None:
        self._seen.add(fingerprint)
        self._db[fingerprint] = time.time()

    def cleanup(self, max_age_days: int = 7) -> int:
        cutoff = time.time() - max_age_days * 86400
        to_remove = [fp for fp, ts in self._db.items() if ts < cutoff]
        for fp in to_remove:
            self._seen.discard(fp)
            del self._db[fp]
        return len(to_remove)

    def size(self) -> int:
        return len(self._seen)


class ArticleFilter:
    """Filter articles by interest tags."""

    def __init__(self, interest_tags: List[str], noise_tags: List[str]) -> None:
        self.interest_tags = [t.lower() for t in interest_tags]
        self.noise_tags = [t.lower() for t in noise_tags]

    def score(self, article: Article) -> float:
        text = f"{article.title} {article.content}".lower()
        interest_score = sum(1 for tag in self.interest_tags if tag in text)
        noise_penalty = sum(1 for tag in self.noise_tags if tag in text)
        score = interest_score - noise_penalty
        return max(0.0, min(1.0, score / max(len(self.interest_tags), 1)))

    def should_include(self, article: Article, threshold: float = 0.1) -> bool:
        return self.score(article) >= threshold


class ArticleSummarizer:
    """Summarize articles using AI."""

    def __init__(self, model: str = "gpt-3.5-turbo") -> None:
        self.model = model

    def summarize(self, article: Article, max_words: int = 100) -> str:
        # Pattern extraction — actual API call would go here
        content = article.content[:500]
        sentences = content.split('.')
        summary = '. '.join(sentences[:3]) + '.'
        return summary[:max_words * 5] if summary else article.title


class AIRDDigest:
    """AI RSS Daily digest engine."""

    def __init__(self, config: DigestConfig) -> None:
        self.config = config
        self.cache = DeduplicationCache()
        self.filter = ArticleFilter(config.interest_tags, config.noise_tags)
        self.summarizer = ArticleSummarizer(config.summary_model)
        self.articles: List[Article] = []

    def fetch_articles(self, rss_urls: Optional[List[str]] = None) -> List[Article]:
        """Fetch articles from RSS feeds."""
        urls = rss_urls or self.config.rss_urls
        articles: List[Article] = []

        for url in urls:
            # Pattern extraction — actual feedparser call would go here
            pass

        return articles

    def process_articles(self, articles: List[Article]) -> List[Article]:
        """Filter, deduplicate, and summarize articles."""
        processed: List[Article] = []

        for article in articles:
            if self.cache.is_duplicate(article.fingerprint):
                continue

            if not self.filter.should_include(article):
                continue

            article.summary = self.summarizer.summarize(article)
            article.relevance_score = self.filter.score(article)
            self.cache.add(article.fingerprint)
            processed.append(article)

        processed.sort(key=lambda a: a.relevance_score, reverse=True)
        return processed[:self.config.max_articles]

    def format_markdown(self, articles: List[Article]) -> str:
        """Format articles as Markdown digest."""
        lines = [f"# Daily Digest — {datetime.now().strftime('%Y-%m-%d')}", ""]

        for i, article in enumerate(articles, 1):
            lines.append(f"## {i}. {article.title}")
            lines.append(f"**Source:** {article.source} | **Relevance:** {article.relevance_score:.1%}")
            lines.append(f"**Link:** {article.url}")
            lines.append("")
            lines.append(article.summary)
            lines.append("")

        return "\n".join(lines)

    def format_text(self, articles: List[Article]) -> str:
        """Format articles as plain text digest."""
        lines = [f"DAILY DIGEST — {datetime.now().strftime('%Y-%m-%d')}", "=" * 50, ""]

        for i, article in enumerate(articles, 1):
            lines.append(f"{i}. {article.title}")
            lines.append(f"   Source: {article.source} | Score: {article.relevance_score:.1%}")
            lines.append(f"   {article.summary}")
            lines.append("")

        return "\n".join(lines)
