import asyncio
import logging

from news_api import fetch_company_news
from entity_extractor import extract_entities_batch
from entity_enricher import enrich_entities
from event_detector import detect_events
from signal_extractor import extract_signals

# Setup basic logging for better visibility
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def process_article(article, extracted_entities):
    """Processes a single article through Stages 2, 3, and 4."""
    try:
        # Stage 2: Enrichment
        enriched = enrich_entities(extracted_entities)
        
        # Stage 3: Event Detection
        # Use .get() with defaults to prevent AttributeErrors
        headline = article.get('headline', '')
        summary = article.get('summary', '')
        text = f"{headline}. {summary}".strip()
        
        events_result = detect_events(text, enriched)
        
        # Stage 4: Signal Extraction
        signals_result = extract_signals(events_result)
        
        return {
            "headline": headline,
            "events": events_result.events,
            "signals": signals_result.signals,
            "stats": signals_result.stats
        }
    except Exception as e:
        logger.error(f"Error processing article '{article.get('headline')}': {e}")
        return None

async def run_pipeline(ticker: str = "AAPL", limit: int = 5):
    print("\n" + "="*40)
    print(f"🚀 STARTING PIPELINE: {ticker}")
    print("="*40)

    # Stage 0: Fetch news
    news = await fetch_company_news(ticker)
    if not news:
        logger.warning("No news returned.")
        return
    
    news = news[:limit]
    logger.info(f"Processing {len(news)} articles...")

    # Stage 1: Batch Entity extraction (Keep this outside the loop as it's already optimized)
    print("\n[Stage 1] Batch Extracting Entities...")
    extracted_list = extract_entities_batch(news)

    # Stages 2-4: Process articles concurrently
    print("[Stages 2-4] Running Enrichment, Detection, and Signals...")
    tasks = [
        process_article(article, extracted) 
        for article, extracted in zip(news, extracted_list)
    ]
    
    results = await asyncio.gather(*tasks)

    # Final Reporting
    total_signals = 0
    print("\n" + "="*40)
    print("📊 PIPELINE RESULTS SUMMARY")
    print("="*40)

    for i, res in enumerate(results):
        if not res:
            continue
            
        print(f"\n📰 Article {i+1}: {res['headline']}")
        
        if res['events']:
            print(f"   ✅ Detected {len(res['events'])} Events")
            for sig in res['signals']:
                sentiment_color = "🟢" if sig.sentiment.is_positive else "🔴" if sig.sentiment.is_negative else "⚪"
                print(f"      {sentiment_color} {sig.entity}: {sig.event_type.value} "
                      f"(Impact: {sig.impact_score:.2f}, Conf: {sig.confidence:.2f})")
            total_signals += len(res['signals'])
        else:
            print("   ⚠️ No events detected.")

    print("\n" + "="*40)
    print(f"✅ PIPELINE COMPLETE | Total Signals: {total_signals}")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(run_pipeline("AAPL", limit=5))