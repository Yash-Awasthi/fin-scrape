"""
Web Content Extractor — Extracted from Trafilatura patterns.

Web content extraction with:
- HTML noise removal
- Main content extraction
- Metadata extraction
- Deduplication
- Language detection
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from html.parser import HTMLParser


@dataclass
class ExtractedContent:
    title: str = ""
    text: str = ""
    author: str = ""
    date: str = ""
    url: str = ""
    language: str = "en"
    keywords: List[str] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)
    fingerprint: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "text": self.text,
            "author": self.author,
            "date": self.date,
            "url": self.url,
            "language": self.language,
            "keywords": self.keywords,
        }


class HTMLCleaner:
    """Remove noise from HTML documents."""

    UNWANTED_TAGS = {
        "script", "style", "nav", "footer", "header", "aside",
        "form", "button", "input", "select", "textarea",
        "iframe", "noscript", "svg", "canvas",
    }

    UNWANTED_CLASSES = {
        "sidebar", "widget", "advertisement", "ad", "banner",
        "popup", "modal", "cookie", "consent", "newsletter",
        "social", "share", "comment", "related",
    }

    def clean(self, html: str) -> str:
        """Remove unwanted elements from HTML."""
        cleaned = html

        # Remove script and style tags
        cleaned = re.sub(r'<script[^>]*>.*?</script>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<style[^>]*>.*?</style>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Remove comments
        cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)

        # Remove unwanted tags
        for tag in self.UNWANTED_TAGS:
            cleaned = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Remove elements with unwanted classes
        for cls in self.UNWANTED_CLASSES:
            cleaned = re.sub(
                f'<[^>]*class=["\'][^"\']*{cls}[^"\']*["\'][^>]*>.*?</[^>]+>',
                '',
                cleaned,
                flags=re.DOTALL | re.IGNORECASE,
            )

        return cleaned


class ContentExtractor:
    """Extract main content from HTML."""

    def __init__(self) -> None:
        self.cleaner = HTMLCleaner()

    def extract(self, html: str, url: str = "") -> ExtractedContent:
        """Extract content from HTML."""
        cleaned = self.cleaner.clean(html)

        title = self._extract_title(cleaned)
        text = self._extract_text(cleaned)
        author = self._extract_author(cleaned)
        date = self._extract_date(cleaned)
        keywords = self._extract_keywords(cleaned)

        content = ExtractedContent(
            title=title,
            text=text,
            author=author,
            date=date,
            url=url,
            keywords=keywords,
        )
        content.fingerprint = self._fingerprint(text)
        return content

    def _extract_title(self, html: str) -> str:
        """Extract title from HTML."""
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return self._clean_text(match.group(1))

        match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return self._clean_text(match.group(1))

        match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE)
        if match:
            return self._clean_text(match.group(1))

        return ""

    def _extract_text(self, html: str) -> str:
        """Extract main text content."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Decode entities
        import html as html_module
        text = html_module.unescape(text)
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove short segments (likely noise)
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        return '. '.join(sentences)

    def _extract_author(self, html: str) -> str:
        """Extract author from HTML."""
        patterns = [
            r'<meta[^>]*name=["\']author["\'][^>]*content=["\'](.*?)["\']',
            r'<meta[^>]*property=["\']article:author["\'][^>]*content=["\'](.*?)["\']',
            r'class=["\'][^"\']*author[^"\']*["\'][^>]*>(.*?)<',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))
        return ""

    def _extract_date(self, html: str) -> str:
        """Extract publication date."""
        patterns = [
            r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\'](.*?)["\']',
            r'<time[^>]*datetime=["\'](.*?)["\']',
            r'class=["\'][^"\']*date[^"\']*["\'][^>]*>(.*?)<',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))
        return ""

    def _extract_keywords(self, html: str) -> List[str]:
        """Extract keywords from HTML."""
        match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE)
        if match:
            return [k.strip() for k in match.group(1).split(',')]
        return []

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        text = re.sub(r'<[^>]+>', '', text)
        import html as html_module
        text = html_module.unescape(text)
        return re.sub(r'\s+', ' ', text).strip()

    def _fingerprint(self, text: str) -> str:
        """Generate content fingerprint for deduplication."""
        import hashlib
        # Normalize text
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()


class DeduplicationCache:
    """LRU cache for content deduplication."""

    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self.cache: Dict[str, str] = {}

    def is_duplicate(self, fingerprint: str) -> bool:
        """Check if content is a duplicate."""
        return fingerprint in self.cache

    def add(self, fingerprint: str, url: str = "") -> None:
        """Add content fingerprint to cache."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[fingerprint] = url

    def clear(self) -> None:
        self.cache.clear()
