"""
Content Quality Scorer
Extracted from trafilatura's extraction heuristics

Scores HTML content for quality and relevance using multiple signals:
- Text density analysis
- Link density analysis
- Boilerplate detection
- Content extraction confidence scoring
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import re
import math


@dataclass
class ContentScore:
    """Content quality score with breakdown"""
    overall: float          # 0-1 overall quality score
    text_density: float     # Text-to-HTML ratio
    link_density: float     # Link-to-text ratio
    boilerplate_score: float # 0-1 (1 = no boilerplate)
    confidence: float       # Extraction confidence


@dataclass
class TextBlock:
    """Text block with metadata"""
    text: str
    length: int
    word_count: int
    sentence_count: int
    link_count: int
    element_type: str       # p, div, article, etc.
    depth: int              # DOM depth


def calculate_text_density(html: str) -> float:
    """
    Calculate text density (text-to-HTML ratio)
    
    High text density indicates content-rich pages.
    Low density indicates navigation-heavy or boilerplate pages.
    
    Args:
        html: Raw HTML
    
    Returns:
        Text density ratio (0-1)
    """
    # Remove all tags
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(html) == 0:
        return 0.0
    
    return len(text) / len(html)


def calculate_link_density(html: str) -> float:
    """
    Calculate link density (link text to total text ratio)
    
    High link density indicates navigation or directory pages.
    Low link density indicates content pages.
    
    Args:
        html: Raw HTML
    
    Returns:
        Link density ratio (0-1)
    """
    # Extract link text
    link_text = re.findall(r'<a[^>]*>(.*?)</a>', html, re.DOTALL)
    link_text = ' '.join(link_text)
    link_text = re.sub(r'<[^>]+>', '', link_text)
    link_text = re.sub(r'\s+', ' ', link_text).strip()
    
    # Extract all text
    all_text = re.sub(r'<[^>]+>', '', html)
    all_text = re.sub(r'\s+', ' ', all_text).strip()
    
    if len(all_text) == 0:
        return 0.0
    
    return len(link_text) / len(all_text)


def detect_boilerplate(html: str) -> float:
    """
    Detect boilerplate content (headers, footers, navigation, sidebars)
    
    Returns score from 0-1 where 1 = no boilerplate detected.
    
    Args:
        html: Raw HTML
    
    Returns:
        Boilerplate score (0-1)
    """
    boilerplate_signals = 0
    total_signals = 0
    
    # Check for common boilerplate elements
    boilerplate_patterns = [
        (r'<nav[^>]*>', 'navigation'),
        (r'<header[^>]*>', 'header'),
        (r'<footer[^>]*>', 'footer'),
        (r'<aside[^>]*>', 'sidebar'),
        (r'class="[^"]*(?:menu|nav|sidebar|widget|ad)[^"]*"', 'widget'),
        (r'id="[^"]*(?:menu|nav|sidebar|widget|ad)[^"]*"', 'widget'),
    ]
    
    for pattern, signal_type in boilerplate_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            boilerplate_signals += 1
        total_signals += 1
    
    # Check for excessive link density (navigation indicator)
    link_density = calculate_link_density(html)
    if link_density > 0.5:
        boilerplate_signals += 1
    total_signals += 1
    
    # Check for short content (likely boilerplate)
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) < 200:
        boilerplate_signals += 1
    total_signals += 1
    
    return 1.0 - (boilerplate_signals / total_signals if total_signals > 0 else 0)


def extract_text_blocks(html: str) -> List[TextBlock]:
    """
    Extract text blocks from HTML with metadata
    
    Args:
        html: Raw HTML
    
    Returns:
        List of TextBlock objects
    """
    blocks = []
    
    # Simple extraction of paragraph-like elements
    # In production, use proper HTML parser like BeautifulSoup or lxml
    elements = re.findall(r'<(p|div|article|section|li)[^>]*>(.*?)</\1>', html, re.DOTALL | re.IGNORECASE)
    
    for element_type, content in elements:
        # Clean content
        text = re.sub(r'<[^>]+>', '', content)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 10:  # Skip very short blocks
            continue
        
        # Count words and sentences
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        # Count links
        links = re.findall(r'<a[^>]*>', content)
        
        blocks.append(TextBlock(
            text=text,
            length=len(text),
            word_count=len(words),
            sentence_count=len(sentences),
            link_count=len(links),
            element_type=element_type,
            depth=0  # Would need proper parsing for real depth
        ))
    
    return blocks


def calculate_content_quality(blocks: List[TextBlock]) -> ContentScore:
    """
    Calculate content quality from text blocks
    
    Uses heuristics inspired by trafilatura's extraction confidence:
    - Text length and word count
    - Sentence structure
    - Link density within blocks
    - Block consistency
    
    Args:
        blocks: List of TextBlock objects
    
    Returns:
        ContentScore with quality metrics
    """
    if not blocks:
        return ContentScore(
            overall=0.0,
            text_density=0.0,
            link_density=1.0,
            boilerplate_score=0.0,
            confidence=0.0
        )
    
    # Calculate metrics
    total_text = ' '.join(b.text for b in blocks)
    total_words = sum(b.word_count for b in blocks)
    total_sentences = sum(b.sentence_count for b in blocks)
    total_links = sum(b.link_count for b in blocks)
    
    # Text density score (optimal: 200-2000 words)
    if total_words < 50:
        text_density_score = total_words / 50
    elif total_words > 2000:
        text_density_score = max(0.5, 1.0 - (total_words - 2000) / 5000)
    else:
        text_density_score = 1.0
    
    # Link density score (optimal: < 0.1 links per word)
    link_ratio = total_links / total_words if total_words > 0 else 0
    link_density_score = max(0, 1.0 - link_ratio * 10)
    
    # Sentence structure score (optimal: 5-30 words per sentence)
    if total_sentences > 0:
        words_per_sentence = total_words / total_sentences
        if 5 <= words_per_sentence <= 30:
            sentence_score = 1.0
        elif words_per_sentence < 5:
            sentence_score = words_per_sentence / 5
        else:
            sentence_score = max(0.3, 1.0 - (words_per_sentence - 30) / 50)
    else:
        sentence_score = 0.0
    
    # Block consistency score (similar block sizes indicate content)
    block_sizes = [b.word_count for b in blocks]
    if len(block_sizes) > 1:
        mean_size = sum(block_sizes) / len(block_sizes)
        variance = sum((s - mean_size) ** 2 for s in block_sizes) / len(block_sizes)
        cv = math.sqrt(variance) / mean_size if mean_size > 0 else 0
        consistency_score = max(0, 1.0 - cv)
    else:
        consistency_score = 0.5
    
    # Overall score (weighted combination)
    overall = (
        text_density_score * 0.3 +
        link_density_score * 0.2 +
        sentence_score * 0.25 +
        consistency_score * 0.25
    )
    
    return ContentScore(
        overall=overall,
        text_density=text_density_score,
        link_density=link_density_score,
        boilerplate_score=consistency_score,  # Simplified
        confidence=overall
    )


def score_html_content(html: str) -> ContentScore:
    """
    Score HTML content quality in one call
    
    Args:
        html: Raw HTML
    
    Returns:
        ContentScore with quality metrics
    """
    # Extract text blocks
    blocks = extract_text_blocks(html)
    
    # Calculate quality
    score = calculate_content_quality(blocks)
    
    # Adjust with HTML-level metrics
    text_density = calculate_text_density(html)
    link_density = calculate_link_density(html)
    boilerplate = detect_boilerplate(html)
    
    # Blend scores
    score.text_density = text_density
    score.link_density = link_density
    score.boilerplate_score = boilerplate
    
    # Recalculate overall with HTML metrics
    score.overall = (
        score.overall * 0.6 +
        text_density * 0.2 +
        boilerplate * 0.2
    )
    
    score.confidence = score.overall
    
    return score


def compare_content_quality(html1: str, html2: str) -> Dict[str, any]:
    """
    Compare quality of two HTML content pieces
    
    Args:
        html1: First HTML content
        html2: Second HTML content
    
    Returns:
        Comparison results
    """
    score1 = score_html_content(html1)
    score2 = score_html_content(html2)
    
    return {
        'content1': {
            'overall': score1.overall,
            'text_density': score1.text_density,
            'link_density': score1.link_density,
            'confidence': score1.confidence
        },
        'content2': {
            'overall': score2.overall,
            'text_density': score2.text_density,
            'link_density': score2.link_density,
            'confidence': score2.confidence
        },
        'winner': 'content1' if score1.overall > score2.overall else 'content2',
        'difference': abs(score1.overall - score2.overall)
    }