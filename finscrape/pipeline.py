"""
FinScrape Pipeline — orchestrates scraping, AI analysis, validation, and event storage.

Flow: scrape → analyze → validate → score → store → alert → track accuracy
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone
from difflib import SequenceMatcher

from finscrape.scrapers.yahoo import YahooScraper
from finscrape.scrapers.bloomberg import BloombergScraper
from finscrape.scrapers.reuters import ReutersScraper
from finscrape.scrapers.cnbc import CNBCScraper
from finscrape.scrapers.rss import RSSScraperSource
from finscrape.scrapers.marketwatch import MarketWatchScraper
from finscrape.scrapers.seekingalpha import SeekingAlphaScraper
from finscrape.scrapers.benzinga import BenzingaScraper
from finscrape.scrapers.investingcom import InvestingComScraper
from finscrape.scrapers.ft import FTScraper
from finscrape.scrapers.edgar import EdgarScraper
from finscrape.analysis.ai_client import call_ai
from finscrape.analysis.validator import (
    calculate_heuristic_score, check_divergence, clean_tickers,
    apply_source_credibility, apply_recency_decay,
    extract_financial_magnitudes,
)
from finscrape.analysis.prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT
from finscrape.analysis.nlp import FinancialNLP
from finscrape.storage import StateManager
from finscrape.market_data import get_market_data, calculate_market_boost
from finscrape.models import ScrapedArticle, FinEvent, Verdict
from finscrape.dashboard import DashboardClient
from finscrape.agents import AgentCouncil, DEFAULT_AGENTS
from finscrape.alerts import AlertEngine
from finscrape.accuracy import AccuracyTracker
from finscrape.portfolio import PortfolioManager

logger = logging.getLogger(__name__)


class PipelineStats:
    """Tracks per-run pipeline performance metrics."""

    __slots__ = ("started_at", "articles_seen", "articles_skipped",
                 "articles_analyzed", "articles_failed", "events_created",
                 "alerts_fired", "signals_recorded", "stage_timings")

    def __init__(self):
        self.started_at: float = time.monotonic()
        self.articles_seen: int = 0
        self.articles_skipped: int = 0
        self.articles_analyzed: int = 0
        self.articles_failed: int = 0
        self.events_created: int = 0
        self.alerts_fired: int = 0
        self.signals_recorded: int = 0
        self.stage_timings: dict[str, float] = {}

    def time_stage(self, name: str) -> "_StageTimer":
        return _StageTimer(self, name)

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started_at

    def summary(self) -> dict:
        return {
            "elapsed_s": round(self.elapsed, 2),
            "articles_seen": self.articles_seen,
            "articles_skipped": self.articles_skipped,
            "articles_analyzed": self.articles_analyzed,
            "articles_failed": self.articles_failed,
            "events_created": self.events_created,
            "alerts_fired": self.alerts_fired,
            "signals_recorded": self.signals_recorded,
            "stage_timings": {k: round(v, 3) for k, v in self.stage_timings.items()},
        }


class _StageTimer:
    """Context manager for timing pipeline stages."""

    def __init__(self, stats: PipelineStats, name: str):
        self._stats = stats
        self._name = name
        self._start = 0.0

    def __enter__(self):
        self._start = time.monotonic()
        return self

    def __exit__(self, *exc):
        elapsed = time.monotonic() - self._start
        self._stats.stage_timings[self._name] = (
            self._stats.stage_timings.get(self._name, 0.0) + elapsed
        )


class FinScrapePipeline:
    """
    Main pipeline: scrape → analyze → validate → score → store → alert → track.

    Sources are pluggable. Enable/disable via the `sources` parameter.
    Integrates alerts engine, portfolio weighting, and accuracy tracking.
    """

    AVAILABLE_SCRAPERS = {
        "yahoo": YahooScraper,
        "bloomberg": BloombergScraper,
        "reuters": ReutersScraper,
        "cnbc": CNBCScraper,
        "rss": RSSScraperSource,
        "marketwatch": MarketWatchScraper,
        "seekingalpha": SeekingAlphaScraper,
        "benzinga": BenzingaScraper,
        "investingcom": InvestingComScraper,
        "ft": FTScraper,
        "edgar": EdgarScraper,
    }

    def __init__(
        self,
        sources: list[str] | None = None,
        max_articles_per_source: int = 10,
        data_dir: str | None = None,
        use_council: bool = False,
        enable_alerts: bool = True,
        enable_accuracy: bool = True,
        enable_portfolio: bool = True,
    ):
        self.state = StateManager(data_dir=data_dir)
        self.dashboard = DashboardClient()
        self.nlp = FinancialNLP()
        self.use_council = use_council
        self.council = AgentCouncil(agents=DEFAULT_AGENTS) if use_council else None

        # Alert engine integration
        self.alert_engine: AlertEngine | None = None
        if enable_alerts:
            try:
                self.alert_engine = AlertEngine()
            except Exception as e:
                logger.warning("Could not initialize alert engine: %s", e)

        # Accuracy tracker integration
        self.accuracy: AccuracyTracker | None = None
        if enable_accuracy:
            try:
                self.accuracy = AccuracyTracker(data_dir=data_dir)
            except Exception as e:
                logger.warning("Could not initialize accuracy tracker: %s", e)

        # Portfolio manager integration
        self.portfolio: PortfolioManager | None = None
        if enable_portfolio:
            try:
                self.portfolio = PortfolioManager()
            except Exception as e:
                logger.warning("Could not initialize portfolio manager: %s", e)

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
        stats = PipelineStats()

        print(f"\n{'='*60}")
        print(f"  FinScrape Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Sources: {', '.join(self.scrapers.keys())}")
        print(f"{'='*60}\n")

        all_events = []

        for source_name, scraper in self.scrapers.items():
            print(f"[{source_name.upper()}] Scraping...")
            try:
                with stats.time_stage(f"scrape_{source_name}"):
                    articles = scraper.scrape_news()
                print(f"[{source_name.upper()}] Got {len(articles)} articles")
                with stats.time_stage(f"process_{source_name}"):
                    events = self._process_articles(source_name, articles, stats)
                all_events.extend(events)
            except Exception as e:
                logger.error("[%s] Scraper failed: %s", source_name, e, exc_info=True)
                print(f"[{source_name.upper()}] Error: {e}")
                continue

        stats.events_created = len(all_events)

        # --- Post-processing: alerts, portfolio, accuracy ---
        with stats.time_stage("post_processing"):
            self._post_process_events(all_events, stats)

        print(f"\n{'='*60}")
        print(f"  Pipeline Complete — {len(all_events)} new events extracted")
        print(f"  Time: {stats.elapsed:.1f}s | Analyzed: {stats.articles_analyzed} | Failed: {stats.articles_failed}")
        if stats.alerts_fired:
            print(f"  Alerts fired: {stats.alerts_fired}")
        if stats.signals_recorded:
            print(f"  Signals recorded for accuracy: {stats.signals_recorded}")
        print(f"{'='*60}\n")

        # Push to dashboard
        if all_events and self.dashboard.is_configured:
            try:
                result = self.dashboard.push_events([e.to_dict() for e in all_events])
                print(f"  Dashboard: {result}")
            except Exception as e:
                logger.error("Dashboard push failed: %s", e)

        # Print summary
        for event in all_events:
            arrow = "+" if event.signal_score >= 0 else ""
            print(f"  [{event.verdict:8s}] {arrow}{event.signal_score} | {event.subject}")
            print(f"           Tickers: {', '.join(event.tickers)} | Confidence: {event.confidence:.0%}")
            print()

        logger.info("Pipeline stats: %s", stats.summary())
        return all_events

    def _post_process_events(self, events: list[FinEvent], stats: PipelineStats) -> None:
        """Run alerts, portfolio weighting, and accuracy recording on new events."""
        for event in events:
            event_dict = event.to_dict()

            # --- Alert evaluation ---
            if self.alert_engine:
                try:
                    matches = self.alert_engine.evaluate(event_dict)
                    for rule, actions in matches:
                        logger.info("Alert rule '%s' matched event: %s", rule.name, event.subject)
                        self.alert_engine.execute_actions(event_dict, actions)
                        stats.alerts_fired += 1
                except Exception as e:
                    logger.error("Alert evaluation failed for event %s: %s", event.subject[:50], e)

            # --- Portfolio alerts ---
            if self.portfolio:
                try:
                    portfolio_alerts = self.portfolio.check_and_alert([event_dict])
                    if portfolio_alerts:
                        logger.info("Portfolio alerts: %d for event %s",
                                    len(portfolio_alerts), event.subject[:50])
                except Exception as e:
                    logger.error("Portfolio alert check failed: %s", e)

            # --- Accuracy tracking: record signal for later verification ---
            if self.accuracy:
                try:
                    self._record_for_accuracy(event, stats)
                except Exception as e:
                    logger.error("Accuracy recording failed for event %s: %s", event.subject[:50], e)

    def _record_for_accuracy(self, event: FinEvent, stats: PipelineStats) -> None:
        """Record signal with current price for accuracy tracking."""
        if event.verdict not in ("INVEST", "PULL_OUT"):
            return  # Only track actionable verdicts

        market_data = get_market_data(event.tickers)
        price_map = {md["ticker"]: md["price"] for md in market_data}

        for ticker in event.tickers:
            price = price_map.get(ticker)
            if price and price > 0:
                self.accuracy.record_signal(
                    event_id=hash(event.timestamp + ticker) % (2**31),
                    ticker=ticker,
                    signal_score=event.signal_score,
                    confidence=event.confidence,
                    verdict=event.verdict,
                    price_at_signal=price,
                    source=event.sources[0] if event.sources else "",
                    event_type=event.event_type,
                )
                stats.signals_recorded += 1

    def _process_articles(self, source_name: str, articles: list[ScrapedArticle],
                          stats: PipelineStats) -> list[FinEvent]:
        """Process a batch of scraped articles through the AI + validation pipeline."""
        events = []
        visited = self.state.get_visited(source_name)

        for i, article in enumerate(articles):
            stats.articles_seen += 1
            print(f"  [{i+1}/{len(articles)}] {article.url[:80]}...")

            if article.url in visited:
                print(f"    [SKIP] Already visited")
                stats.articles_skipped += 1
                continue

            if not article.has_content:
                print(f"    [SKIP] Insufficient content")
                stats.articles_skipped += 1
                self.state.add_visited(source_name, article.url)
                continue

            if not article.is_fresh:
                age = article.age_hours if article.age_hours is not None else 0
                print(f"    [SKIP] Too old ({age:.1f}h)")
                stats.articles_skipped += 1
                self.state.add_visited(source_name, article.url)
                continue

            try:
                with stats.time_stage("ai_analysis"):
                    event = self._analyze_article(source_name, article)
                if event:
                    events.append(event)
                    stats.articles_analyzed += 1
                else:
                    stats.articles_analyzed += 1  # analyzed but no event produced
            except Exception as e:
                stats.articles_failed += 1
                logger.error("[%s] Article analysis failed for %s: %s",
                             source_name, article.url[:80], e, exc_info=True)
                print(f"    [ERROR] Analysis failed: {e}")

            self.state.add_visited(source_name, article.url)

        return events

    def _analyze_article(self, source_name: str, article: ScrapedArticle) -> FinEvent | None:
        """Run AI analysis + heuristic validation on a single article."""

        # Choose analysis mode: multi-agent council or single AI call
        if self.council:
            result, council_verdict = self._analyze_with_council(source_name, article)
        else:
            result, council_verdict = self._analyze_with_single_ai(article), None

        if not result:
            print(f"    [ERROR] AI analysis failed")
            return None

        if not result.get("relevant", False):
            print(f"    [SKIP] Not market-relevant")
            return None

        # NLP analysis — entity extraction, metrics, sector, breaking news
        full_text = article.title + " " + article.text
        nlp_result = self.nlp.analyze(article.title, article.text)

        # Ticker processing — combine AI, NLP, entity index, and regex extraction
        ai_tickers = result.get("tickers", [])
        nlp_tickers = nlp_result.tickers
        entity_tickers = self.state.resolve_entity_tickers(full_text)
        regex_tickers = article.raw_tickers

        # Also extract tickers from affected_entities
        entity_obj_tickers = [
            e.get("ticker", "")
            for e in result.get("affected_entities", [])
            if e.get("ticker")
        ]

        all_symbols = set(ai_tickers + nlp_tickers + entity_tickers + regex_tickers + entity_obj_tickers)
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
        h_sentiment, h_impact = calculate_heuristic_score(full_text, result.get("event_type", ""))
        divergence = check_divergence(result.get("impact_direction", "neutral"), h_sentiment)

        # Final scoring
        base_score = result.get("signal_score", 0)
        final_score = max(-5, min(5, base_score + market_boost))
        confidence = result.get("confidence", 0.5)

        # Apply divergence penalty
        if divergence:
            confidence = max(0.0, confidence - 0.15)

        # Apply source credibility weighting
        confidence = apply_source_credibility(confidence, source_name)

        # Apply recency decay
        confidence = apply_recency_decay(confidence, article.age_hours)

        # Boost confidence if NLP detects breaking news indicators
        if nlp_result.has_breaking_indicators:
            confidence = min(1.0, confidence + 0.10)

        # Use NLP sector as fallback if AI didn't provide one
        sector = result.get("sector_impact", "") or nlp_result.sector

        # Merge NLP-extracted metrics into key_metrics
        nlp_metrics = {}
        for m in nlp_result.metrics:
            nlp_metrics[m.metric_type] = {"value": m.value, "raw": m.context}
        key_metrics = result.get("key_metrics", {})
        for k, v in nlp_metrics.items():
            if k not in key_metrics:
                key_metrics[k] = v

        # Build event with enriched fields
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
            # New enriched fields from chain-of-thought analysis
            reasoning=result.get("reasoning", ""),
            magnitude=result.get("magnitude", "medium"),
            novelty=result.get("novelty", "standard"),
            actionability=result.get("actionability", "medium"),
            affected_entities=result.get("affected_entities", []),
            second_order_effects=result.get("second_order_effects", []),
            sector_impact=sector,
            key_metrics=key_metrics,
        )

        # Deduplication
        matched = self._find_duplicate(event)
        if matched:
            print(f"    [MERGE] Merging with: {matched.get('subject', '')[:50]}")
            articles_list = matched.get("articles", [])
            sources_list = matched.get("sources", [])
            updated = {}
            if article.url not in articles_list:
                articles_list.append(article.url)
                updated["articles"] = articles_list
            if source_name not in sources_list:
                sources_list.append(source_name)
                updated["sources"] = sources_list
            if updated and matched.get("id"):
                self.state.update_event(matched["id"], **updated)
            return None
        else:
            print(f"    [{event.verdict:8s}] {event.subject}")
            if event.reasoning:
                print(f"           Reasoning: {event.reasoning[:80]}...")
            self.state.add_event(event.to_dict())
            return event

    def _analyze_with_single_ai(self, article: ScrapedArticle) -> dict | None:
        """Standard single-AI analysis."""
        prompt = (
            ANALYSIS_PROMPT
            .replace("{{title}}", article.title)
            .replace("{{article_text}}", article.text)
        )
        return call_ai(prompt, SYSTEM_PROMPT)

    def _analyze_with_council(self, source_name: str, article: ScrapedArticle) -> tuple[dict | None, dict | None]:
        """Multi-agent council analysis. Returns (result_dict, council_verdict_dict)."""
        metadata = {"source": source_name, "age_hours": f"{article.age_hours:.1f}"}
        cv = self.council.deliberate(article.title, article.text, metadata)

        # If no individual verdicts produced anything useful, fail
        if cv.consensus_confidence < 0.05:
            return None, None

        # Convert council verdict into the standard result dict format
        # so downstream ticker/NLP/validation code works unchanged
        result = {
            "relevant": True,
            "event_type": "other",
            "tickers": [],
            "impact_direction": "positive" if cv.consensus_score > 0 else ("negative" if cv.consensus_score < 0 else "neutral"),
            "signal_score": round(cv.consensus_score),
            "confidence": cv.consensus_confidence,
            "subject": article.title,
            "reasoning": f"Council verdict ({cv.agreement_level:.0%} agreement): " + "; ".join(
                f"{v.agent_name}={v.signal_score}" for v in cv.individual_verdicts
            ),
            "magnitude": "medium",
            "novelty": "standard",
            "actionability": "medium",
            "affected_entities": [],
            "second_order_effects": [],
            "sector_impact": "",
            "key_metrics": {},
        }

        # Merge tickers from all agents
        all_tickers = []
        for v in cv.individual_verdicts:
            all_tickers.extend(v.tickers)
        result["tickers"] = list(set(all_tickers))

        # Add council-specific metadata
        council_dict = cv.to_dict()
        council_dict.pop("individual_verdicts", None)  # too large for storage
        result["council"] = council_dict
        result["key_risks"] = cv.key_risks[:5]
        result["key_opportunities"] = cv.key_opportunities[:5]

        return result, council_dict

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
