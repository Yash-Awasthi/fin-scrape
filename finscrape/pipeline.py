"""
FinScrape Pipeline — orchestrates scraping, AI analysis, validation, and event storage.

Flow: scrape → analyze → validate → score → store → alert → track accuracy
"""

from __future__ import annotations

import logging
import os
import re
import time
from datetime import datetime
from difflib import SequenceMatcher

from finscrape.accuracy import AccuracyTracker
from finscrape.agents import DEFAULT_AGENTS, AgentCouncil
from finscrape.alerts import AlertEngine
from finscrape.analysis.ai_client import call_ai
from finscrape.analysis.nlp import FinancialNLP
from finscrape.analysis.prompts import render_prompt
from finscrape.analysis.validator import (
    calculate_heuristic_score,
    check_divergence,
    clean_tickers,
    fuse_confidence,
    is_market_relevant,
)
from finscrape.dashboard import DashboardClient
from concurrent.futures import ThreadPoolExecutor, as_completed

from finscrape.analysis.embeddings import most_similar
from finscrape.entity_map import resolve_company_tickers, resolve_tickers
from finscrape.market_data import (
    calculate_market_boost,
    get_indicators,
    get_market_data,
)
from finscrape.models import FinEvent, ScrapedArticle, Verdict
from finscrape.portfolio import PortfolioManager
from finscrape.scrapers.benzinga import BenzingaScraper
from finscrape.scrapers.bloomberg import BloombergScraper
from finscrape.scrapers.cnbc import CNBCScraper
from finscrape.scrapers.dev_tools import FirecrawlNewsScraper, SerpNewsScraper
from finscrape.scrapers.edgar import EdgarScraper
from finscrape.scrapers.ft import FTScraper
from finscrape.scrapers.google_news import GoogleNewsScraper
from finscrape.scrapers.google_serp import GoogleSerpScraper
from finscrape.scrapers.investingcom import InvestingComScraper
from finscrape.scrapers.marketwatch import MarketWatchScraper
from finscrape.scrapers.reuters import ReutersScraper
from finscrape.scrapers.rss import RSSScraperSource
from finscrape.scrapers.seekingalpha import SeekingAlphaScraper
from finscrape.scrapers.yahoo import YahooScraper
from finscrape.storage import StateManager

logger = logging.getLogger(__name__)


class PipelineStats:
    """Tracks per-run pipeline performance metrics."""

    __slots__ = (
        "alerts_fired",
        "articles_analyzed",
        "articles_failed",
        "articles_seen",
        "articles_skipped",
        "events_created",
        "signals_recorded",
        "stage_timings",
        "started_at",
    )

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

    def time_stage(self, name: str) -> _StageTimer:
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
        "google_news": GoogleNewsScraper,
        "google_serp": GoogleSerpScraper,
        # Dev-mode tools (secrets/dev_tools.json) — no-op with a clear warning
        # until an API key is configured via `main.py devtools set`.
        "firecrawl": FirecrawlNewsScraper,
        "serp": SerpNewsScraper,
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
        self.council = AgentCouncil(agents=DEFAULT_AGENTS, judge=True) if use_council else None

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
        """Run the full pipeline across all configured sources.

        Sources scrape in PARALLEL (wall time ≈ slowest source, not their sum);
        processing stays sequential afterwards because it mutates shared SQLite
        state. Results are merged in deterministic source order.
        """
        stats = PipelineStats()

        print(f"\n{'='*60}")
        print(f"  FinScrape Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Sources: {', '.join(self.scrapers.keys())}")
        print(f"{'='*60}\n")

        def _scrape_source(source_name: str, scraper) -> tuple[str, list, Exception | None]:
            try:
                with stats.time_stage(f"scrape_{source_name}"):
                    articles = scraper.scrape_news()
                return source_name, articles, None
            except Exception as e:  # noqa: BLE001 — one dead source never kills the run
                return source_name, [], e

        scraped: dict[str, tuple[list, Exception | None]] = {}
        max_workers = min(4, max(1, len(self.scrapers)))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [
                pool.submit(_scrape_source, name, scraper)
                for name, scraper in self.scrapers.items()
            ]
            for future in as_completed(futures):
                name, articles, error = future.result()
                scraped[name] = (articles, error)
                if error is not None:
                    logger.error("[%s] Scraper failed: %s", name, error, exc_info=error)
                    print(f"[{name.upper()}] Error: {error}")
                else:
                    print(f"[{name.upper()}] Got {len(articles)} articles")

        all_events = []
        for source_name, scraper in self.scrapers.items():
            articles, error = scraped.get(source_name, ([], None))
            if error is not None or not articles:
                continue
            with stats.time_stage(f"process_{source_name}"):
                events = self._process_articles(source_name, articles, stats)
            all_events.extend(events)

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
                print("    [SKIP] Already visited")
                stats.articles_skipped += 1
                continue

            if not article.has_content:
                print("    [SKIP] Insufficient content")
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

        # Pre-LLM relevance gate: junk lifestyle pieces and transient event
        # briefs (minor quakes, forming storms) never reach the AI or the DB.
        if not is_market_relevant(article.title, article.text):
            print("    [SKIP] Not market-relevant (off-topic or transient brief)")
            return None

        # Choose analysis mode: multi-agent council or single AI call
        if self.council:
            result, council_verdict = self._analyze_with_council(source_name, article)
        else:
            result, council_verdict = self._analyze_with_single_ai(article), None

        if not result:
            # Zero-cost mode: LLM unavailable / budget-capped → heuristic + entity-map
            # tickers so ingestion never stalls (opt-in: FINSCRAPE_HEURISTIC_FALLBACK).
            # The event lands with a heuristic verdict, enrichable on demand (/api/ai/analyze).
            if os.getenv("FINSCRAPE_HEURISTIC_FALLBACK", "").lower() in ("1", "true", "yes"):
                result = self._heuristic_only(article)
            if not result:
                print("    [ERROR] AI analysis failed")
                return None

        if not result.get("relevant", False):
            print("    [SKIP] Not market-relevant")
            return None

        # NLP analysis — entity extraction, metrics, sector, breaking news
        full_text = article.title + " " + article.text
        nlp_result = self.nlp.analyze(article.title, article.text)

        # Ticker processing — combine AI, NLP, entity index, regex, and sector-map
        ai_tickers = result.get("tickers", [])
        nlp_tickers = nlp_result.tickers
        entity_tickers = self.state.resolve_entity_tickers(full_text)
        regex_tickers = article.raw_tickers
        # Sector/geopolitics keyword → tickers (Phase 12): rescues world headlines that
        # name a sector/region but no company, where the LLM left tickers blank.
        # Company-name resolution (SEC list) catches articles naming the company outright.
        sector_tickers = resolve_tickers(full_text)
        company_tickers = resolve_company_tickers(full_text)

        # Also extract tickers from affected_entities
        entity_obj_tickers = [
            e.get("ticker", "")
            for e in result.get("affected_entities", [])
            if e.get("ticker")
        ]

        all_symbols = set(
            ai_tickers
            + nlp_tickers
            + entity_tickers
            + regex_tickers
            + entity_obj_tickers
            + sector_tickers
            + company_tickers
        )
        valid_tickers = clean_tickers([
            t for t in all_symbols
            if isinstance(t, str) and 1 < len(t) <= 5 and t.isupper()
        ], text=full_text)

        if not valid_tickers:
            print("    [SKIP] No valid tickers found")
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
        confidence = fuse_confidence(
            result.get("confidence", 0.5),
            source_name,
            article.age_hours,
            divergence,
            nlp_result.has_breaking_indicators,
        )

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

    def _heuristic_only(self, article: ScrapedArticle) -> dict | None:
        """LLM-free analysis (zero-cost mode): heuristic verdict + entity-map/regex tickers,
        shaped like a call_ai result. Returns None when no tickers resolve (can't place it).
        Tagged key_metrics.prompt_variant='heuristic' so it's distinguishable + enrichable."""
        full_text = article.title + " " + article.text
        symbols = sorted(
            set(resolve_tickers(full_text) + resolve_company_tickers(full_text) + list(article.raw_tickers or []))
        )
        tickers = [t for t in symbols if isinstance(t, str) and 1 < len(t) <= 5 and t.isupper()]
        if not tickers:
            return None
        sentiment, impact = calculate_heuristic_score(full_text, "")
        mag = round(impact * 5)
        score = mag if sentiment == "positive" else -mag if sentiment == "negative" else 0
        return {
            "relevant": True,
            "event_type": "other",
            "subject": article.title[:120],
            "impact_direction": sentiment if sentiment in ("positive", "negative") else "neutral",
            "tickers": tickers,
            "affected_entities": [],
            "signal_score": int(max(-5, min(5, score))),
            "confidence": 0.4,
            "magnitude": "high" if impact >= 0.66 else "low" if impact < 0.33 else "medium",
            "novelty": "standard",
            "actionability": "low",
            "reasoning": "Heuristic analysis (LLM unavailable) — click to enrich with AI.",
            "key_metrics": {"prompt_variant": "heuristic"},
            "sector_impact": "",
            "second_order_effects": [],
        }

    def _analyze_with_single_ai(self, article: ScrapedArticle) -> dict | None:
        """Standard single-AI analysis. Picks a prompt variant (A/B, opt-in) and stamps
        it into key_metrics so accuracy can be compared per variant."""
        from finscrape.analysis.prompt_registry import get_prompts, pick_variant

        variant = pick_variant(article.title)
        system_prompt, analysis_prompt = get_prompts(variant)
        prompt = render_prompt(analysis_prompt, article.title, article.text)
        result = call_ai(prompt, system_prompt)
        if result is not None:
            result.setdefault("key_metrics", {})["prompt_variant"] = variant
        return result

    def _analyze_with_council(self, source_name: str, article: ScrapedArticle) -> tuple[dict | None, dict | None]:
        """Multi-agent council analysis. Returns (result_dict, council_verdict_dict).

        Tickers resolve before deliberation (same resolve_tickers used by
        _heuristic_only) so real computed indicators can go into the council as
        GROUND TRUTH facts — the council itself fetches nothing, stays pure.
        """
        metadata = {"source": source_name, "age_hours": f"{article.age_hours:.1f}"}
        full_text = article.title + " " + article.text
        tickers = sorted(set(resolve_tickers(full_text) + resolve_company_tickers(full_text)))
        market_facts = get_indicators(tickers) if tickers else {}

        # Grounded past performance for the judge only — debators stay naive.
        lessons: dict = {}
        if self.accuracy:
            try:
                lessons = self.accuracy.get_lessons(tickers=tickers, source=source_name)
            except Exception as e:
                logger.warning("Could not fetch lessons for judge: %s", e)

        cv = self.council.deliberate(article.title, article.text, metadata, market_facts, lessons)

        # If no individual verdicts produced anything useful, fail
        if cv.consensus_confidence < 0.05:
            return None, None

        # Convert council verdict into the standard result dict format
        # so downstream ticker/NLP/validation code works unchanged
        reasoning = f"Council verdict ({cv.agreement_level:.0%} agreement): " + "; ".join(
            f"{v.agent_name}={v.signal_score}" for v in cv.individual_verdicts
        )
        if cv.judged:
            reasoning += f" | Judge override (raw mean {cv.consensus_score_raw}): {cv.judge_rationale}"

        result = {
            "relevant": True,
            "event_type": "other",
            "tickers": [],
            "impact_direction": "positive" if cv.consensus_score > 0 else ("negative" if cv.consensus_score < 0 else "neutral"),
            "signal_score": round(cv.consensus_score),
            "confidence": cv.consensus_confidence,
            "subject": article.title,
            "reasoning": reasoning,
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
        """Check if this event already exists in recent history.

        Gate 1: ticker overlap + same event type. Gate 2: subject similarity —
        first by character ratio, then (Phase 13) by embedding cosine, which
        catches paraphrased coverage of the same story across sources.
        """
        recent = self.state.events[-100:]
        candidates: list[tuple[int, str]] = []
        for idx, e in enumerate(recent):
            existing_tickers = e.get("tickers", [])
            if not existing_tickers or not new_event.tickers:
                continue

            overlap = len(set(new_event.tickers) & set(existing_tickers))
            ratio = overlap / min(len(set(new_event.tickers)), len(set(existing_tickers)))

            if ratio >= 0.5 and e.get("event_type") == new_event.event_type:
                candidates.append((idx, e.get("subject", "")))

        for idx, existing_subject in candidates:
            if SequenceMatcher(None, existing_subject, new_event.subject).ratio() >= 0.85:
                return recent[idx]

        # Embedding fallback: paraphrased duplicates the character ratio misses.
        # 0.62 is calibrated for nomic-embed-text (same-story paraphrases ~0.70,
        # unrelated ~0.44); the structural gate above keeps false merges away.
        # No-ops (returns None) whenever Ollama is unavailable.
        if candidates:
            match = most_similar(
                new_event.subject,
                [(subject, subject) for _, subject in candidates],
                threshold=0.62,
            )
            if match:
                matched_subject, _score = match
                for idx, subject in candidates:
                    if subject == matched_subject:
                        return recent[idx]

        return None
