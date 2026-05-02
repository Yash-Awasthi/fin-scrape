"""
FinScrape -> Dashboard Push Script
Scrapes news from all sources and pushes them directly to the dashboard API.
AI scoring is bypassed -- events get a basic heuristic score instead.
"""

import sys, os, logging, json, argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.WARNING)

from finscrape.scrapers.bloomberg import BloombergScraper
from finscrape.scrapers.reuters import ReutersScraper
from finscrape.scrapers.marketwatch import MarketWatchScraper
from finscrape.scrapers.investingcom import InvestingComScraper
from finscrape.scrapers.seekingalpha import SeekingAlphaScraper
from finscrape.scrapers.ft import FTScraper
from finscrape.scrapers.yahoo import YahooScraper
from finscrape.scrapers.cnbc import CNBCScraper
from finscrape.scrapers.benzinga import BenzingaScraper
from finscrape.scrapers.google_news import GoogleNewsScraper
from finscrape.analysis.validator import calculate_heuristic_score
import requests

# Defaults
DEFAULT_URL = os.getenv("FINSCRAPE_DASHBOARD_URL", "https://fin-scrape-qhuij2.apps.camelai.dev")
DEFAULT_KEY = os.getenv("FINSCRAPE_API_KEY", "finscrape-default-key")

SOURCES = [
    ("bloomberg", BloombergScraper),
    ("reuters", ReutersScraper),
    ("marketwatch", MarketWatchScraper),
    ("investingcom", InvestingComScraper),
    ("seekingalpha", SeekingAlphaScraper),
    ("ft", FTScraper),
    ("yahoo", YahooScraper),
    ("cnbc", CNBCScraper),
    ("benzinga", BenzingaScraper),
    ("google_news", GoogleNewsScraper),
]

def heuristic_verdict(score):
    if score >= 3: return "INVEST"
    if score >= 1: return "OBSERVE"
    if score >= -1: return "CAUTIOUS"
    return "PULL_OUT"

def guess_direction(title, text):
    """Simple keyword-based direction guess."""
    combined = (title + " " + text).lower()
    pos = ["rally", "surge", "jump", "climb", "gain", "rise", "higher", "beat", "record",
           "upgrade", "buy", "bullish", "soar", "boom", "positive", "growth", "profit"]
    neg = ["fall", "drop", "slip", "decline", "crash", "plunge", "loss", "cut", "downgrade",
           "sell", "bearish", "slump", "negative", "fear", "risk", "warn", "crisis", "block"]
    pos_count = sum(1 for w in pos if w in combined)
    neg_count = sum(1 for w in neg if w in combined)
    if pos_count > neg_count: return "positive"
    if neg_count > pos_count: return "negative"
    return "neutral"

def guess_event_type(title, text):
    combined = (title + " " + text).lower()
    if any(w in combined for w in ["earnings", "revenue", "profit", "quarterly"]): return "earnings"
    if any(w in combined for w in ["merger", "acqui", "deal", "buyout"]): return "merger_acquisition"
    if any(w in combined for w in ["upgrade", "downgrade", "target", "rating"]): return "analyst_upgrade"
    if any(w in combined for w in ["launch", "product", "announce"]): return "product_launch"
    if any(w in combined for w in ["fed", "rate", "inflation", "gdp", "economic"]): return "market_movement"
    return "market_movement"

def article_to_event(article, source_name):
    """Convert a scraped article to a dashboard event dict with heuristic scoring."""
    title = article.title or ""
    text = article.text or ""
    tickers = article.raw_tickers or []

    direction = guess_direction(title, text)
    event_type = guess_event_type(title, text)

    h_sentiment, h_impact = calculate_heuristic_score(title + " " + text, event_type)
    sent_map = {"positive": 1, "negative": -1, "neutral": 0}
    sent_num = sent_map.get(h_sentiment, 0)
    score = max(-5, min(5, round(sent_num * 2 + h_impact)))

    # Clamp to reasonable range
    if direction == "positive" and score < 0: score = abs(score)
    if direction == "negative" and score > 0: score = -abs(score)

    confidence = min(1.0, 0.4 + abs(score) * 0.1)
    verdict = heuristic_verdict(score)

    return {
        "subject": title,
        "event_type": event_type,
        "tickers": [t for t in tickers if isinstance(t, str) and 1 <= len(t) <= 6 and t.replace(".", "").isupper()],
        "impact_direction": direction,
        "signal_score": score,
        "confidence": round(confidence, 2),
        "verdict": verdict,
        "heuristic_impact": round(h_impact, 2),
        "divergence_flag": False,
        "sources": [source_name],
        "articles": [article.url] if article.url else [],
        "timestamp": article.published_at or datetime.now(timezone.utc).isoformat(),
        "reasoning": f"Heuristic analysis (AI bypassed). Direction: {direction}, type: {event_type}",
        "magnitude": "medium",
        "sector_impact": "",
    }


def main():
    parser = argparse.ArgumentParser(description="FinScrape -> Dashboard Push")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Dashboard URL (default: {DEFAULT_URL})")
    parser.add_argument("--api-key", default=DEFAULT_KEY, help="API Key for ingestion")
    parser.add_argument("--limit", type=int, default=8, help="Max articles per source")
    args = parser.parse_args()

    dashboard_url = args.url.rstrip("/")
    api_key = args.api_key

    print(f"\nFinScrape -> Dashboard Push -- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dashboard: {dashboard_url}\n")

    all_events = []

    for source_name, Cls in SOURCES:
        try:
            print(f"  Scraping {source_name}...", end=" ", flush=True)
            articles = Cls(max_articles=args.limit).scrape_news()
            print(f"{len(articles)} articles")

            for a in articles:
                event = article_to_event(a, source_name)
                if event["subject"]:  # skip empty
                    all_events.append(event)
        except Exception as e:
            print(f"FAILED: {e}")

    print(f"\n  Total events: {len(all_events)}")

    if not all_events:
        print("  No events to push.")
        return

    # Push to dashboard
    print(f"  Pushing to dashboard...", end=" ", flush=True)
    try:
        resp = requests.post(
            f"{dashboard_url}/api/events",
            json={"events": all_events},
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key,
            },
            timeout=30,
        )
        print(f"HTTP {resp.status_code}")
        print(f"  Response: {resp.text[:300]}")
    except Exception as e:
        print(f"FAILED: {e}")

    # Print summary
    print(f"\n{'='*60}")
    for ev in sorted(all_events, key=lambda e: e["timestamp"], reverse=True)[:10]:
        tickers = ", ".join(ev["tickers"]) if ev["tickers"] else "---"
        arrow = "+" if ev["signal_score"] >= 0 else ""
        print(f"  [{ev['verdict']:8s}] {arrow}{ev['signal_score']} | {ev['subject'][:70]}")
        print(f"           {ev['sources'][0]:12s} | {tickers}")
    if len(all_events) > 10:
        print(f"  ... and {len(all_events) - 10} more")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
