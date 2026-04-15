"""Quick scrape test — grab live news, display headlines. No AI scoring."""

import sys, os, json, logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.WARNING)

def scrape_rss():
    """Grab articles from RSS feeds (fastest, no browser needed)."""
    from finscrape.scrapers.rss import RSSScraperSource
    scraper = RSSScraperSource(max_articles=5)
    return "RSS", scraper.scrape_news()

def scrape_yahoo():
    """Grab articles from Yahoo Finance (HTTP, no browser)."""
    from finscrape.scrapers.yahoo import YahooScraper
    scraper = YahooScraper(max_articles=5)
    return "Yahoo", scraper.scrape_news()

def scrape_cnbc():
    """Grab articles from CNBC (HTTP)."""
    from finscrape.scrapers.cnbc import CNBCScraper
    scraper = CNBCScraper(max_articles=5)
    return "CNBC", scraper.scrape_news()

def scrape_benzinga():
    """Grab articles from Benzinga (HTTP)."""
    from finscrape.scrapers.benzinga import BenzingaScraper
    scraper = BenzingaScraper(max_articles=5)
    return "Benzinga", scraper.scrape_news()

def display_articles(source_name, articles):
    """Pretty-print articles."""
    print(f"\n{'='*70}")
    print(f"  {source_name} — {len(articles)} articles fetched")
    print(f"{'='*70}")

    if not articles:
        print("  (no articles found)")
        return

    for i, a in enumerate(articles, 1):
        age = f"{a.age_hours:.1f}h ago" if a.age_hours is not None else "unknown age"
        tickers = ", ".join(a.raw_tickers) if a.raw_tickers else "—"
        text_preview = a.text[:200].replace("\n", " ") if a.text else "(no text)"

        print(f"\n  [{i}] {a.title}")
        print(f"      Source: {a.source} | {age}")
        print(f"      Tickers: {tickers}")
        print(f"      URL: {a.url}")
        print(f"      Text: {text_preview}...")
        print(f"      Content length: {len(a.text or '')} chars | Fresh: {a.is_fresh}")

if __name__ == "__main__":
    print(f"\nFinScrape Live News Test — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"(AI scoring bypassed — raw scrape only)\n")

    total = 0
    # Try each source, skip on failure
    for scrape_fn in [scrape_rss, scrape_yahoo, scrape_cnbc, scrape_benzinga]:
        try:
            name, articles = scrape_fn()
            display_articles(name, articles)
            total += len(articles)
        except Exception as e:
            print(f"\n  [{scrape_fn.__name__}] Failed: {e}")

    print(f"\n{'='*70}")
    print(f"  Total: {total} articles grabbed across all sources")
    print(f"{'='*70}\n")
