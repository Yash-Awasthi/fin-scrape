"""
Content Extraction Service — Inspired by Trafilatura
Web content extraction with boilerplate removal, readability scoring, and metadata extraction
"""

import re
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class ExtractedContent:
    title: str
    text: str
    author: str = ""
    date: str = ""
    url: str = ""
    site_name: str = ""
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    word_count: int = 0
    reading_time_minutes: float = 0.0
    language: str = "en"
    categories: List[str] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ContentScore:
    readability: float
    quality: float
    noise_ratio: float
    text_density: float
    cohesion: float
    overall: float


class ContentExtractor:
    """Pure function content extraction from HTML text."""

    NOISE_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<style[^>]*>.*?</style>',
        r'<nav[^>]*>.*?</nav>',
        r'<header[^>]*>.*?</header>',
        r'<footer[^>]*>.*?</footer>',
        r'<aside[^>]*>.*?</aside>',
        r'<!--.*?-->',
        r'<form[^>]*>.*?</form>',
        r'<iframe[^>]*>.*?</iframe>',
    ]

    TEXT_SELECTORS = [
        r'<article[^>]*>(.*?)</article>',
        r'<main[^>]*>(.*?)</main>',
        r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
    ]

    FINANCIAL_KEYWORDS = [
        "revenue", "earnings", "profit", "loss", "margin", "growth",
        "dividend", "stock", "equity", "debt", "cash flow", "ebitda",
        "guidance", "outlook", "forecast", "quarter", "annual", "fiscal",
        "market cap", "pe ratio", "eps", "roi", "yield", "interest rate",
        "inflation", "gdp", "unemployment", "fed", "treasury", "bond"
    ]

    @classmethod
    def extract_from_html(cls, html: str, url: str = "") -> ExtractedContent:
        cleaned = cls._remove_noise(html)
        title = cls._extract_title(html)
        text = cls._extract_text(cleaned)
        author = cls._extract_meta(html, "author")
        date = cls._extract_meta(html, "date") or cls._extract_date_from_html(html)
        description = cls._extract_meta(html, "description")
        keywords = cls._extract_keywords(html)
        links = cls._extract_links(cleaned, url)
        images = cls._extract_images(cleaned)
        word_count = len(text.split())
        reading_time = word_count / 200.0
        language = cls._detect_language(text)
        categories = cls._categorize_content(text)
        return ExtractedContent(
            title=title,
            text=text,
            author=author,
            date=date,
            url=url,
            description=description,
            keywords=keywords,
            word_count=word_count,
            reading_time_minutes=round(reading_time, 1),
            language=language,
            categories=categories,
            links=links,
            images=images
        )

    @staticmethod
    def _remove_noise(html: str) -> str:
        cleaned = html
        for pattern in ContentExtractor.NOISE_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        return cleaned

    @staticmethod
    def _extract_title(html: str) -> str:
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
        if match:
            return re.sub(r'<[^>]+>', '', match.group(1)).strip()
        match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
        if match:
            return re.sub(r'<[^>]+>', '', match.group(1)).strip()
        match = re.search(r'og:title[^>]*content="([^"]*)"', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _extract_text(cleaned: str) -> str:
        sentences = re.split(r'[.!?]+', cleaned)
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 10]
        return '. '.join(meaningful)

    @staticmethod
    def _extract_meta(html: str, name: str) -> str:
        patterns = [
            rf'<meta[^>]*name="{name}"[^>]*content="([^"]*)"',
            rf'<meta[^>]*content="([^"]*)"[^>]*name="{name}"',
            rf'<meta[^>]*property="{name}"[^>]*content="([^"]*)"',
            rf'<meta[^>]*content="([^"]*)"[^>]*property="{name}"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    @staticmethod
    def _extract_date_from_html(html: str) -> str:
        patterns = [
            r'<time[^>]*datetime="([^"]*)"',
            r'datePublished["\s:]+["\']?(\d{4}-\d{2}-\d{2})',
            r'dateModified["\s:]+["\']?(\d{4}-\d{2}-\d{2})',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""

    @staticmethod
    def _extract_keywords(html: str) -> List[str]:
        match = re.search(r'<meta[^>]*name="keywords"[^>]*content="([^"]*)"', html, re.IGNORECASE)
        if match:
            return [k.strip() for k in match.group(1).split(',') if k.strip()][:10]
        return []

    @staticmethod
    def _extract_links(text: str, base_url: str) -> List[Dict[str, str]]:
        links = []
        for match in re.finditer(r'href="([^"]*)"', text):
            href = match.group(1)
            if href.startswith(('http://', 'https://')):
                links.append({"url": href, "text": ""})
            elif href.startswith('/') and base_url:
                links.append({"url": base_url.rstrip('/') + href, "text": ""})
        return links[:50]

    @staticmethod
    def _extract_images(text: str) -> List[Dict[str, str]]:
        images = []
        for match in re.finditer(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"', text, re.IGNORECASE):
            images.append({"src": match.group(1), "alt": match.group(2)})
        return images[:20]

    @staticmethod
    def _detect_language(text: str) -> str:
        sample = text[:1000].lower()
        common_words = {
            "en": ["the", "is", "and", "of", "to", "in", "it", "that", "was", "for"],
            "es": ["el", "la", "de", "en", "que", "los", "las", "un", "una", "por"],
            "fr": ["le", "la", "de", "les", "des", "est", "en", "un", "une", "du"],
            "de": ["der", "die", "das", "und", "ist", "von", "den", "des", "ein", "eine"],
        }
        words = re.findall(r'\b\w+\b', sample)
        scores = {}
        for lang, stopwords in common_words.items():
            count = sum(1 for w in words if w in stopwords)
            scores[lang] = count / max(len(words), 1)
        if scores:
            return max(scores, key=scores.get)
        return "en"

    @staticmethod
    def _categorize_content(text: str) -> List[str]:
        categories = []
        text_lower = text.lower()
        if any(kw in text_lower for kw in ["revenue", "earnings", "stock", "market"]):
            categories.append("finance")
        if any(kw in text_lower for kw in ["technology", "software", "ai", "algorithm"]):
            categories.append("technology")
        if any(kw in text_lower for kw in ["health", "medical", "patient", "treatment"]):
            categories.append("health")
        if any(kw in text_lower for kw in ["politics", "election", "government", "policy"]):
            categories.append("politics")
        if any(kw in text_lower for kw in ["sport", "game", "match", "player"]):
            categories.append("sports")
        return categories if categories else ["general"]


class ContentScorer:
    """Score content quality using multiple heuristics."""

    @staticmethod
    def calculate_readability(text: str) -> float:
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = text.split()
        if not sentences or not words:
            return 0.0
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(w) for w in words) / len(words)
        score = 100.0
        score -= max(0, (avg_sentence_length - 15) * 2)
        score -= max(0, (avg_word_length - 5) * 5)
        syllable_count = sum(ContentScorer._count_syllables(w) for w in words)
        avg_syllables = syllable_count / len(words)
        score -= max(0, (avg_syllables - 1.5) * 10)
        return max(0.0, min(100.0, score))

    @staticmethod
    def _count_syllables(word: str) -> int:
        word = word.lower().strip()
        if len(word) <= 2:
            return 1
        vowels = "aeiouy"
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith('e'):
            count -= 1
        return max(1, count)

    @staticmethod
    def calculate_text_density(html: str) -> float:
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'\s+', ' ', text).strip()
        total_chars = len(html)
        text_chars = len(text)
        if total_chars == 0:
            return 0.0
        return text_chars / total_chars

    @staticmethod
    def calculate_noise_ratio(html: str) -> float:
        noise_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<style[^>]*>.*?</style>',
            r'<!--.*?-->',
            r'<nav[^>]*>.*?</nav>',
        ]
        noise_chars = 0
        for pattern in noise_patterns:
            for match in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
                noise_chars += len(match.group(0))
        total_chars = len(html)
        if total_chars == 0:
            return 0.0
        return noise_chars / total_chars

    @staticmethod
    def calculate_cohesion(text: str) -> float:
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip().split() for s in sentences if s.strip()]
        if len(sentences) < 2:
            return 0.5
        overlaps = []
        for i in range(len(sentences) - 1):
            words1 = set(w.lower() for w in sentences[i])
            words2 = set(w.lower() for w in sentences[i + 1])
            if words1 and words2:
                overlap = len(words1 & words2) / min(len(words1), len(words2))
                overlaps.append(overlap)
        return sum(overlaps) / len(overlaps) if overlaps else 0.0

    @classmethod
    def score_content(cls, text: str, html: str = "") -> ContentScore:
        readability = cls.calculate_readability(text)
        text_density = cls.calculate_text_density(html) if html else 0.5
        noise_ratio = cls.calculate_noise_ratio(html) if html else 0.0
        cohesion = cls.calculate_cohesion(text)
        quality = (readability * 0.3 + cohesion * 100 * 0.3 +
                   (1.0 - noise_ratio) * 100 * 0.2 + text_density * 100 * 0.2)
        return ContentScore(
            readability=round(readability, 1),
            quality=round(quality, 1),
            noise_ratio=round(noise_ratio, 3),
            text_density=round(text_density, 3),
            cohesion=round(cohesion, 3),
            overall=round(quality, 1)
        )


class FinancialContentExtractor(ContentExtractor):
    """Specialized extractor for financial content."""

    @classmethod
    def extract_financial_content(cls, html: str, url: str = "") -> Dict:
        base = cls.extract_from_html(html, url)
        text_lower = base.text.lower()
        mentioned_keywords = [kw for kw in cls.FINANCIAL_KEYWORDS if kw in text_lower]
        sentiment_words = {
            "positive": ["growth", "profit", "gain", "rise", "increase", "bull", "upgrade", "beat"],
            "negative": ["loss", "decline", "drop", "fall", "bear", "downgrade", "miss", "recession"]
        }
        pos_count = sum(1 for w in sentiment_words["positive"] if w in text_lower)
        neg_count = sum(1 for w in sentiment_words["negative"] if w in text_lower)
        total_sentiment = pos_count + neg_count
        if total_sentiment > 0:
            sentiment_score = (pos_count - neg_count) / total_sentiment
        else:
            sentiment_score = 0.0
        return {
            "title": base.title,
            "text": base.text,
            "word_count": base.word_count,
            "reading_time_minutes": base.reading_time_minutes,
            "financial_keywords": mentioned_keywords,
            "keyword_count": len(mentioned_keywords),
            "sentiment_score": round(sentiment_score, 3),
            "sentiment_label": "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral",
            "categories": base.categories,
            "language": base.language
        }
