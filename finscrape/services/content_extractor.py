"""
Web Content Extraction Service
Inspired by trafilatura - structured text extraction from HTML

Pure functions for extracting meaningful content from web pages:
- HTML parsing and noise removal
- Text extraction with metadata
- Content classification (article, product, etc.)
- Language detection
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
import re


@dataclass
class ExtractedContent:
    """Extracted web content with metadata"""
    title: str
    text: str
    author: Optional[str]
    date: Optional[str]
    language: str
    content_type: str  # article, product, forum, etc.
    word_count: int
    reading_time: float  # minutes
    keywords: List[str]
    summary: str


@dataclass
class ExtractionConfig:
    """Configuration for content extraction"""
    include_tables: bool = True
    include_links: bool = False
    include_images: bool = False
    min_text_length: int = 100
    max_text_length: int = 100000
    deduplicate: bool = True


def extract_content(html: str, url: str = "", config: Optional[ExtractionConfig] = None) -> ExtractedContent:
    """
    Extract structured content from HTML
    
    Args:
        html: Raw HTML content
        url: Source URL (for context)
        config: Extraction configuration
    
    Returns:
        ExtractedContent with structured data
    """
    if config is None:
        config = ExtractionConfig()
    
    # Remove noise (scripts, styles, navigation, etc.)
    cleaned_html = remove_noise(html)
    
    # Extract title
    title = extract_title(cleaned_html)
    
    # Extract main text content
    text = extract_text_content(cleaned_html, config)
    
    # Extract metadata
    author = extract_author(cleaned_html)
    date = extract_date(cleaned_html)
    language = detect_language(text)
    content_type = classify_content(cleaned_html, text)
    
    # Calculate statistics
    word_count = len(text.split())
    reading_time = word_count / 200.0  # Average reading speed: 200 wpm
    
    # Extract keywords
    keywords = extract_keywords(text)
    
    # Generate summary
    summary = generate_summary(text)
    
    return ExtractedContent(
        title=title,
        text=text,
        author=author,
        date=date,
        language=language,
        content_type=content_type,
        word_count=word_count,
        reading_time=reading_time,
        keywords=keywords,
        summary=summary
    )


def remove_noise(html: str) -> str:
    """
    Remove noise from HTML (scripts, styles, navigation, etc.)
    
    Args:
        html: Raw HTML
    
    Returns:
        Cleaned HTML with noise removed
    """
    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    
    # Remove navigation elements
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove ads and sidebars
    html = re.sub(r'<aside[^>]*>.*?</aside>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<div[^>]*class="[^"]*(?:ad|sidebar|widget)[^"]*"[^>]*>.*?</div>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    
    return html


def extract_title(html: str) -> str:
    """
    Extract page title from HTML
    
    Args:
        html: Cleaned HTML
    
    Returns:
        Extracted title
    """
    # Try og:title first (most reliable)
    og_title = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', html, re.IGNORECASE)
    if og_title:
        return clean_text(og_title.group(1))
    
    # Try <title> tag
    title_tag = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if title_tag:
        return clean_text(title_tag.group(1))
    
    # Try first <h1>
    h1_tag = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
    if h1_tag:
        return clean_text(h1_tag.group(1))
    
    return "Untitled"


def extract_text_content(html: str, config: ExtractionConfig) -> str:
    """
    Extract main text content from HTML
    
    Args:
        html: Cleaned HTML
        config: Extraction configuration
    
    Returns:
        Extracted text content
    """
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters
    text = re.sub(r'[^\w\s.,!?;:\-\'"]', '', text)
    
    # Apply length limits
    if len(text) < config.min_text_length:
        return ""
    
    if len(text) > config.max_text_length:
        text = text[:config.max_text_length]
    
    return text


def extract_author(html: str) -> Optional[str]:
    """
    Extract author from HTML
    
    Args:
        html: Cleaned HTML
    
    Returns:
        Author name or None
    """
    # Try meta author
    meta_author = re.search(r'<meta[^>]*name="author"[^>]*content="([^"]*)"', html, re.IGNORECASE)
    if meta_author:
        return clean_text(meta_author.group(1))
    
    # Try og:author
    og_author = re.search(r'<meta[^>]*property="og:author"[^>]*content="([^"]*)"', html, re.IGNORECASE)
    if og_author:
        return clean_text(og_author.group(1))
    
    # Try common author patterns
    author_patterns = [
        r'(?i)by\s+([A-Z][a-z]+ [A-Z][a-z]+)',
        r'(?i)author:\s*([A-Z][a-z]+ [A-Z][a-z]+)',
        r'(?i)written by\s+([A-Z][a-z]+ [A-Z][a-z]+)'
    ]
    
    for pattern in author_patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    
    return None


def extract_date(html: str) -> Optional[str]:
    """
    Extract publication date from HTML
    
    Args:
        html: Cleaned HTML
    
    Returns:
        Date string or None
    """
    # Try meta date
    meta_date = re.search(r'<meta[^>]*name="date"[^>]*content="([^"]*)"', html, re.IGNORECASE)
    if meta_date:
        return meta_date.group(1)
    
    # Try og:published_time
    og_date = re.search(r'<meta[^>]*property="og:published_time"[^>]*content="([^"]*)"', html, re.IGNORECASE)
    if og_date:
        return og_date.group(1)
    
    # Try common date patterns
    date_patterns = [
        r'(?i)published:\s*(\d{4}-\d{2}-\d{2})',
        r'(?i)date:\s*(\d{4}-\d{2}-\d{2})',
        r'(?i)(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    
    return None


def detect_language(text: str) -> str:
    """
    Detect language of text
    
    Args:
        text: Input text
    
    Returns:
        Language code (e.g., 'en', 'es', 'fr')
    """
    # Simple language detection based on common words
    text_lower = text.lower()
    
    # English indicators
    english_words = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'for']
    english_count = sum(1 for word in english_words if word in text_lower)
    
    # Spanish indicators
    spanish_words = ['el', 'la', 'de', 'en', 'y', 'que', 'los', 'del', 'las', 'por']
    spanish_count = sum(1 for word in spanish_words if word in text_lower)
    
    # French indicators
    french_words = ['le', 'la', 'de', 'et', 'en', 'les', 'des', 'du', 'un', 'une']
    french_count = sum(1 for word in french_words if word in text_lower)
    
    # German indicators
    german_words = ['der', 'die', 'das', 'und', 'ist', 'in', 'den', 'von', 'zu', 'mit']
    german_count = sum(1 for word in german_words if word in text_lower)
    
    # Determine language
    counts = {
        'en': english_count,
        'es': spanish_count,
        'fr': french_count,
        'de': german_count
    }
    
    max_lang = max(counts, key=counts.get)
    if counts[max_lang] > 2:
        return max_lang
    
    return 'en'  # Default to English


def classify_content(html: str, text: str) -> str:
    """
    Classify content type
    
    Args:
        html: Cleaned HTML
        text: Extracted text
    
    Returns:
        Content type (article, product, forum, etc.)
    """
    text_lower = text.lower()
    
    # Check for product indicators
    product_indicators = ['price', 'buy', 'cart', 'add to', 'shop', 'product']
    if any(indicator in text_lower for indicator in product_indicators):
        return 'product'
    
    # Check for forum indicators
    forum_indicators = ['reply', 'comment', 'posted by', 'thread', 'topic']
    if any(indicator in text_lower for indicator in forum_indicators):
        return 'forum'
    
    # Check for news indicators
    news_indicators = ['breaking', 'report', 'according to', 'sources', 'officials']
    if any(indicator in text_lower for indicator in news_indicators):
        return 'news'
    
    # Check for blog indicators
    blog_indicators = ['posted on', 'written by', 'author', 'category', 'tags']
    if any(indicator in text_lower for indicator in blog_indicators):
        return 'blog'
    
    return 'article'


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text
    
    Args:
        text: Input text
        max_keywords: Maximum number of keywords to extract
    
    Returns:
        List of keywords
    """
    # Simple keyword extraction based on word frequency
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                  'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'can', 'shall', 'this', 'that', 'these', 'those'}
    
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count word frequency
    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]


def generate_summary(text: str, max_sentences: int = 3) -> str:
    """
    Generate a summary of the text
    
    Args:
        text: Input text
        max_sentences: Maximum number of sentences in summary
    
    Returns:
        Text summary
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    if not sentences:
        return ""
    
    # Take first N sentences as summary
    summary_sentences = sentences[:max_sentences]
    return '. '.join(summary_sentences) + '.'


def clean_text(text: str) -> str:
    """
    Clean extracted text
    
    Args:
        text: Raw text
    
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters
    text = re.sub(r'[^\w\s.,!?;:\-\'"]', '', text)
    
    return text