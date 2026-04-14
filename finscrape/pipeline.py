"""
FinScrape Pipeline — orchestrates scraping, AI analysis, validation, and event storage.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher

from finscrape.scrapers.yahoo import YahooScraper
from finscrape.scrapers.bloomberg import BloombergScraper
from finscrape.scrapers.reuters import ReutersScraper
from finscrape.scrapers.cnbc import CNBCScraper
from finscrape.scrapers.rss import RSSScraperSource
from finscrape.analysis.ai_client import call_ai
from finscrape.analysis.validator import calculate_heuristic_score, check_divergence, clean_tickers
from finscrape.analysis.prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT
from finscrape.storage import StateManager
from finscrape.market_data import get_market_data, calculate_market_boost
from finscrape.models import ScrapedArticle, FinEvent, Verdict

logger = logging.getLogger(__name__)


class FinScrapePipeline:
    """
    Main pipeline: scrape → analyze → validate → score → store.

    Sources are pluggable. Enable/disable via the `sources` parameter.
    """

    AVAILABLE_SCRAPERS = {
        "yahoo": YahooScraper,
        "bloomberg": BloombergScraper,
        "reuters": ReutersScraper,
        "cnbc": CNBCScraper,
        "rss": RSSScraperSource,
    }

    def __init__(
        self,
        sources: list[str] | None = None,
        max_articles_per_source: int = 10,
        data_dir: str | None = None,
    ):
        self.state = StateManager(data_dir=data_dir)

        # Default: only yahoo (most reliable). Add others as needed.
        source_names = sources or ["yahoo"]

        self.scrapers = {}
        for name in source_names:
            cls = self.AVAILABLE_SCRAPERS.get(name)
            if cls:
                self.scrapers[name] = cls(max_articles=max_articles_per_source)
            else:
                logger.warning("Unknown source '%s' — skipping", name)

    def run(self) -> list[FinEvent]:
        """Run the full pipeline across all configured sources."""
        print(f"\n{'='*60}")
        print(f"  FinScrape Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Sources: {', '.join(self.scrapers.keys())}")
        print(f"{'='*60}\n")

        all_events = []

        for source_name, scraper in self.scrapers.items():
            print(f"[{source_name.upper()}] Scraping...")
            try:
                articles = scraper.scrape_news()
                print(f"[{source_name.upper()}] Got {len(articles)} articles")
                events = self._process_articles(source_name, articles)
                all_events.extend(events)
            except Exception as e:
                logger.error("[%s] Scraper failed: %s", source_name, e)
                print(f"[{source_name.upper()}] Error: {e}")
                continue

        print(f"\n{'='*60}")
        print(f"  Pipeline Complete — {len(all_events)} new events extracted")
        print(f"{'='*60}\n")

        # Print summary
        for event in all_events:
            arrow = "+" if event.signal_score >= 0 else ""
            print(f"  [{event.verdict:8s}] {arrow}{event.signal_score} | {event.subject}")
            print(f"           Tickers: {', '.join(event.tickers)} | Confidence: {event.confidence:.0%}")
            print()

        return all_events

    def _process_articles(self, source_name: str, articles: list[ScrapedArticle]) -> list[FinEvent]:
        """Process a batch of scraped articles through the AI + validation pipeline."""
        events = []
        visited = self.state.get_visited(source_name)

        for i, article in enumerate(articles):
            print(f"  [{i+1}/{len(articles)}] {article.url[:80]}...")

            if article.url in visited:
                print(f"    [SKIP] Already visited")
                continue

            if not article.has_content:
                print(f"    [SKIP] Insufficient content")
                self.state.add_visited(source_name, article.url)
                continue

            if not article.is_fresh:
                print(f"    [SKIP] Too old ({article.age_hours:.1f}h)")
                self.state.add_visited(source_name, article.url)
                continue

            event = self._analyze_article(source_name, article)
            if event:
                events.append(event)

            self.state.add_visited(source_name, article.url)

        return events

    def _analyze_article(self, source_name: str, article: ScrapedArticle) -> FinEvent | None:
        """Run AI analysis + heuristic validation on a single article."""

        # AI Analysis
        prompt = (
            ANALYSIS_PROMPT
            .replace("{{title}}", article.title)
            .replace("{{article_text}}", article.text)
        )
        result = call_ai(prompt, SYSTEM_PROMPT)

        if not result:
            print(f"    [ERROR] AI analysis failed")
            return None

        if not result.get("relevant", False):
            print(f"    [SKIP] Not market-relevant")
            return None

        # Ticker processing — combine AI, entity index, and regex extraction
        ai_tickers = result.get("tickers", [])
        entity_tickers = self.state.resolve_entity_tickers(article.title + " " + article.text)
        regex_tickers = article.raw_tickers

        all_symbols = set(ai_tickers + entity_tickers + regex_tickers)
        valid_tickers = clean_tickers([
            t for t in all_symbols
            if isinstance(t, str) and 1 < len(t) <= 5 and t.isupper()
        ])

        if not valid_tickers:
            print(f"    [SKIP] No valid tickers found")
            return None

        # Market data
        market_data = get_market_data(valid_tickers)
        market_boost = calculate_market_boost(market_data)

        # Heuristic validation
        full_text = article.title + " " + article.text
        h_sentiment, h_impact = calculate_heuristic_score(full_text, result.get("event_type", ""))
        divergence = check_divergence(result.get("impact_direction", "neutral"), h_sentiment)

        # Final scoring
        base_score = result.get("signal_score", 0)
        final_score = max(-5, min(5, base_score + market_boost))
        confidence = result.get("confidence", 0.5)

        # Apply divergence penalty
        if divergence:
            confidence = max(0.0, confidence - 0.15)

        # Build event
        subject = self._normalize_subject(result.get("subject", article.title))
        verdict = Verdict.from_score(final_score)

        event = FinEvent(
            subject=subject,
            event_type=result.get("event_type", "other"),
            tickers=valid_tickers,
            impact_direction=result.get("impact_direction", "neutral"),
            signal_score=final_score,
            confidence=round(confidence, 2),
            verdict=verdict.value,
            heuristic_impact=h_impact,
            divergence_flag=divergence,
            sources=[source_name],
            articles=[article.url],
        )

        # Deduplication
        matched = self._find_duplicate(event)
        if matched:
            print(f"    [MERGE] Merging with: {matched.get('subject', '')[:50]}")
            if article.url not in matched.get("articles", []):
                matched["articles"].append(article.url)
            if source_name not in matched.get("sources", []):
                matched["sources"].append(source_name)
            self.state.save_events()
            return None
        else:
            print(f"    [{event.verdict:8s}] {event.subject}")
            self.state.add_event(event.to_dict())
            return event

    def _normalize_subject(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r"[^\w\s]", "", s)
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    def _find_duplicate(self, new_event: FinEvent) -> dict | None:
        """Check if this event already exists in recent history."""
        for e in self.state.events[-100:]:
            # Ticker overlap
            existing_tickers = e.get("tickers", [])
            if not existing_tickers or not new_event.tickers:
                continue

            overlap = len(set(new_event.tickers) & set(existing_tickers))
            ratio = overlap / min(len(set(new_event.tickers)), len(set(existing_tickers)))

            if ratio >= 0.5 and e.get("event_type") == new_event.event_type:
                similarity = SequenceMatcher(
                    None, e.get("subject", ""), new_event.subject
                ).ratio()
                if similarity >= 0.85:
                    return e

        return None
