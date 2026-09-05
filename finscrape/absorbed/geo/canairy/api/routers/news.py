"""
News router - fetches real news articles from RSS feeds
"""

from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
import httpx
import feedparser
from datetime import datetime, timedelta
import asyncio
import re

router = APIRouter()

# RSS feeds by category - these are real, public feeds
NEWS_FEEDS = {
    "breaking": [
        ("Reuters Top News", "https://www.reutersagency.com/feed/?best-topics=top-news"),
        ("AP News", "https://rsshub.app/apnews/topics/apf-topnews"),
    ],
    "economy": [
        ("Reuters Business", "https://www.reutersagency.com/feed/?best-topics=business-finance"),
        ("Fed News", "https://www.federalreserve.gov/feeds/press_all.xml"),
        ("Treasury News", "https://home.treasury.gov/system/files/136/rss.xml"),
    ],
    "security": [
        ("CISA Alerts", "https://www.cisa.gov/cybersecurity-advisories/all.xml"),
        ("WHO Disease Outbreaks", "https://www.who.int/feeds/entity/csr/don/en/rss.xml"),
    ],
    "world": [
        ("Reuters World", "https://www.reutersagency.com/feed/?best-topics=world"),
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ],
    "conflict": [
        ("Google News - Conflict", "https://news.google.com/rss/search?q=military+conflict&hl=en-US&gl=US&ceid=US:en"),
        ("Reuters Europe", "https://www.reutersagency.com/feed/?best-regions=europe"),
    ],
}

async def fetch_feed(client: httpx.AsyncClient, name: str, url: str) -> List[Dict[str, Any]]:
    """Fetch and parse a single RSS feed."""
    try:
        response = await client.get(url, timeout=10.0)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            articles = []
            for entry in feed.entries[:5]:  # Limit per feed
                # Get publication date
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6]).isoformat() + 'Z'
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6]).isoformat() + 'Z'

                # Clean up title and description
                title = entry.get('title', '').strip()
                description = entry.get('summary', entry.get('description', '')).strip()
                # Remove HTML tags
                description = re.sub(r'<[^>]+>', '', description)[:200]

                link = entry.get('link', '')

                if title and link:
                    articles.append({
                        "title": title,
                        "description": description,
                        "url": link,
                        "source": name,
                        "published": pub_date,
                    })
            return articles
    except Exception as e:
        print(f"Error fetching {name}: {e}")
    return []

@router.get("/")
async def get_news(
    categories: Optional[str] = Query(None, description="Comma-separated categories: breaking,economy,security,world,conflict")
) -> List[Dict[str, Any]]:
    """
    Get real news articles from RSS feeds.

    Categories: breaking, economy, security, world, conflict
    """
    # Parse categories
    if categories:
        selected = [c.strip() for c in categories.split(",")]
    else:
        selected = ["breaking", "world"]  # Default

    # Collect feeds to fetch
    feeds_to_fetch = []
    for cat in selected:
        if cat in NEWS_FEEDS:
            feeds_to_fetch.extend(NEWS_FEEDS[cat])

    # If no valid categories, use breaking
    if not feeds_to_fetch:
        feeds_to_fetch = NEWS_FEEDS["breaking"]

    # Fetch all feeds concurrently
    async with httpx.AsyncClient(
        headers={"User-Agent": "Canairy/1.0 (household-resilience-monitor)"},
        follow_redirects=True
    ) as client:
        tasks = [fetch_feed(client, name, url) for name, url in feeds_to_fetch]
        results = await asyncio.gather(*tasks)

    # Flatten and dedupe by URL
    seen_urls = set()
    all_articles = []
    for articles in results:
        for article in articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                all_articles.append(article)

    # Sort by date (newest first), handling None dates
    all_articles.sort(key=lambda x: x.get("published") or "", reverse=True)

    # Return top 15
    return all_articles[:15]

@router.get("/by-domain")
async def get_news_by_domain(
    domain: str = Query(..., description="Domain to get news for: economy, global_conflict, security_infrastructure, etc.")
) -> List[Dict[str, Any]]:
    """Get news articles relevant to a specific indicator domain."""

    # Map domains to categories
    domain_to_categories = {
        "economy": ["economy"],
        "jobs_labor": ["economy"],
        "global_conflict": ["conflict", "world"],
        "security_infrastructure": ["security"],
        "domestic_control": ["breaking"],
        "energy": ["economy"],
        "supply_chain": ["economy", "world"],
        "travel_mobility": ["world"],
    }

    categories = domain_to_categories.get(domain, ["breaking"])
    return await get_news(categories=",".join(categories))

@router.get("/intelligence")
async def get_news_intelligence() -> Dict[str, Any]:
    """Get news intelligence analysis with articles."""
    articles = await get_news(categories="breaking,world,conflict")

    # Simple threat assessment based on keywords
    threat_keywords = ["war", "attack", "crisis", "emergency", "threat", "conflict"]
    threat_count = sum(
        1 for a in articles
        if any(kw in (a.get("title", "") + a.get("description", "")).lower() for kw in threat_keywords)
    )

    if threat_count >= 5:
        threat_level = "red"
        summary = "Multiple concerning news events detected"
    elif threat_count >= 2:
        threat_level = "amber"
        summary = "Some elevated news activity"
    else:
        threat_level = "green"
        summary = "Normal news activity"

    return {
        "summary": summary,
        "threat_level": threat_level,
        "threat_article_count": threat_count,
        "articles": articles[:10]
    }