import json
import logging
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher

from src.storage.state_manager import StateManager
from src.ingestion.yahoo_scraper import collect_yahoo_news_urls, scrape_article, extract_tickers, get_market_data
from src.processing.ai_client import call_ai
from src.processing.validator import calculate_heuristic_score, check_divergence, clean_tickers
from src.orchestrator.prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

class ContentPipeline:
    def __init__(self):
        self.state = StateManager()
        self.fetch_count = 5
        self.sources = {
            "yahoo": collect_yahoo_news_urls
        }

    def normalize_subject(self, s):
        s = s.lower()
        s = re.sub(r"[^\w\s]", "", s)
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    def ticker_overlap_ratio(self, a, b):
        if not a or not b:
            return 0
        return len(set(a) & set(b)) / min(len(set(a)), len(set(b)))

    def resolve_entity_tickers(self, text):
        text_lower = text.lower()
        words = set(text_lower.split())
        tickers = []
        for w in words:
            if w in self.state.entity_index:
                for company, ticker in self.state.entity_index[w]:
                    if company in text_lower:
                        tickers.append(ticker)
        return tickers

    def run(self):
        print(f"--- Starting Pipeline Run at {datetime.now()} ---")
        for source_name, collector in self.sources.items():
            print(f"\nProcessing Source: {source_name}")
            urls = collector(self.fetch_count)
            self.process_urls(source_name, urls)
        print("\n--- Pipeline Run Complete ---")

    def process_urls(self, source_name, urls):
        visited = self.state.get_visited(source_name)
        new_events_count = 0

        for i, url in enumerate(urls):
            print(f"\n[{i+1}/{len(urls)}] URL: {url}")
            if url in visited:
                print("  [SKIP] Already visited")
                continue

            try:
                title, article_text, soup, age = scrape_article(url)
                if not title or not article_text:
                    print("  [SKIP] No content extracted")
                    self.state.add_visited(source_name, url)
                    continue

                if age is not None and age > 24: # Increased limit for flexibility
                    print(f"  [SKIP] Too old ({age:.1f}h)")
                    self.state.add_visited(source_name, url)
                    continue

                # AI Analysis
                prompt = ANALYSIS_PROMPT.replace("{{title}}", title).replace("{{article_text}}", article_text)
                ai_response = call_ai(prompt, SYSTEM_PROMPT)
                
                if not ai_response:
                    print("  [ERROR] AI analysis failed")
                    continue

                result_json = json.loads(ai_response)
                if not result_json.get("relevant", False):
                    print("  [SKIP] Irrelevant article")
                    self.state.add_visited(source_name, url)
                    continue

                # Ticker processing
                ai_tickers = result_json.get("tickers", [])
                entity_tickers = self.resolve_entity_tickers(title + " " + article_text)
                regex_tickers = extract_tickers(article_text, soup)
                all_symbols = set(ai_tickers + entity_tickers + regex_tickers)
                
                valid_tickers = clean_tickers([t for t in all_symbols if isinstance(t, str) and 1 < len(t) <= 5 and t.isupper()])
                
                if not valid_tickers:
                   print("  [SKIP] No valid tickers found")
                   self.state.add_visited(source_name, url)
                   continue

                market_data = get_market_data(valid_tickers)
                market_boost = 0
                for md in market_data:
                    if abs(md["change_percent"]) >= 10: market_boost = max(market_boost, 2)
                    elif abs(md["change_percent"]) >= 5: market_boost = max(market_boost, 1)

                # Heuristic Score & Divergence
                h_sentiment, h_impact = calculate_heuristic_score(title + " " + article_text, result_json.get("event_type", ""))
                divergence = check_divergence(result_json.get("impact_direction", "neutral"), h_sentiment)

                # Build Event
                base_score = result_json.get("signal_score", 0)
                final_score = max(-5, min(5, base_score + market_boost))
                
                event = {
                    "subject": self.normalize_subject(result_json.get("subject", title)),
                    "event_type": result_json.get("event_type"),
                    "tickers": valid_tickers,
                    "impact_direction": result_json.get("impact_direction"),
                    "signal_score": final_score,
                    "heuristic_impact": h_impact,
                    "divergence_flag": divergence,
                    "confidence": result_json.get("confidence", 0.5),
                    "sources": [source_name],
                    "articles": [url],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                # Deduplication
                matched = self.find_duplicate(event)
                if matched:
                    print(f"  [MERGE] Merging with existing event: {matched['subject']}")
                    if url not in matched["articles"]: matched["articles"].append(url)
                    if source_name not in matched["sources"]: matched["sources"].append(source_name)
                else:
                    print(f"  [EVENT] New Event: {event['subject']}")
                    self.state.events.append(event)
                    new_events_count += 1

                self.state.add_visited(source_name, url)
                self.state.save_events(self.state.events)

            except Exception as e:
                print(f"  [ERROR] Pipeline error: {e}")
                continue

    def find_duplicate(self, new_event):
        for e in self.state.events[-100:]:
            # Check ticker overlap
            if self.ticker_overlap_ratio(new_event["tickers"], e.get("tickers", [])) >= 0.5:
                if e.get("event_type") == new_event["event_type"]:
                    # Semantic subject check
                    similarity = SequenceMatcher(None, e.get("subject", ""), new_event["subject"]).ratio()
                    if similarity >= 0.85:
                        return e
        return None
