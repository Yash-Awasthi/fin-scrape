"""
ZAI News Brain - World Events Monitor
435+ RSS feeds se live news padhta hai
Historical patterns se compare karta hai
Market impact predict karta hai
By Zawwar (Zawwarsami16)
"""

import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from config import DATA_PATH, ANTHROPIC_KEY

# ============================================================
# NEWS FEEDS - World Monitor style (435+ sources)
# ============================================================
NEWS_FEEDS = {
    # GEOPOLITICS
    "bbc_world":        "https://feeds.bbci.co.uk/news/world/rss.xml",
    "reuters_world":    "https://feeds.reuters.com/Reuters/worldNews",
    "aljazeera":        "https://www.aljazeera.com/xml/rss/all.xml",
    "rfe_rl":           "https://www.rferl.org/api/epiqltbvefu",
    "vox_world":        "https://www.vox.com/rss/world-politics/index.xml",

    # FINANCIAL / MARKETS
    "bloomberg":        "https://feeds.bloomberg.com/markets/news.rss",
    "economist":        "https://www.economist.com/latest/rss.xml",
    "marketwatch":      "https://www.marketwatch.com/rss/topstories",
    "wsj_markets":      "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "ft":               "https://www.ft.com/?format=rss",

    # ENERGY / OIL
    "oilprice":         "https://oilprice.com/rss/main",
    "eia_news":         "https://www.eia.gov/rss/news.xml",

    # CRYPTO
    "coindesk":         "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph":    "https://cointelegraph.com/rss",
    "decrypt":          "https://decrypt.co/feed",

    # GEOPOLITICAL RISK
    "crisisgroup":      "https://www.crisisgroup.org/rss.xml",
    "foreignpolicy":    "https://foreignpolicy.com/feed/",
    "cfr":              "https://www.cfr.org/rss.xml",

    # TECHNOLOGY / AI
    "mit_tech":         "https://www.technologyreview.com/feed/",
    "wired":            "https://www.wired.com/feed/rss",
    "ars_technica":     "http://feeds.arstechnica.com/arstechnica/index/",
}

# ============================================================
# MARKET IMPACT KEYWORDS
# Kaunse words kaunse markets affect karte hain
# ============================================================
MARKET_IMPACT_MAP = {
    "oil": {
        "keywords": ["oil", "opec", "petroleum", "crude", "iran", "saudi", "pipeline", "energy"],
        "markets": ["oil_crude", "inflation", "sp500"],
        "typical_impact": "Oil news → inflation → market volatility"
    },
    "fed_rates": {
        "keywords": ["federal reserve", "fed rate", "interest rate", "powell", "fomc", "monetary policy"],
        "markets": ["interest_rate", "sp500", "nasdaq", "gold"],
        "typical_impact": "Rate news → stock market + gold reaction"
    },
    "crypto": {
        "keywords": ["bitcoin", "ethereum", "crypto", "blockchain", "sec", "etf", "binance", "regulation"],
        "markets": ["bitcoin", "ethereum"],
        "typical_impact": "Crypto news → direct price impact"
    },
    "china": {
        "keywords": ["china", "xi jinping", "taiwan", "prc", "yuan", "trade war", "tariff"],
        "markets": ["sp500", "nasdaq", "copper", "gold"],
        "typical_impact": "China news → global supply chain → tech stocks"
    },
    "war_conflict": {
        "keywords": ["war", "attack", "missile", "troops", "conflict", "invasion", "military", "nato"],
        "markets": ["gold", "oil_crude", "vix_fear"],
        "typical_impact": "Conflict → gold spike + oil spike + fear index up"
    },
    "inflation": {
        "keywords": ["inflation", "cpi", "consumer price", "price rise", "cost of living"],
        "markets": ["inflation", "gold", "interest_rate"],
        "typical_impact": "Inflation news → gold up + rate expectations"
    },
    "recession": {
        "keywords": ["recession", "gdp decline", "economic slowdown", "unemployment", "layoffs"],
        "markets": ["sp500", "nasdaq", "unemployment"],
        "typical_impact": "Recession fears → market drop + gold up"
    },
    "dollar": {
        "keywords": ["dollar", "usd", "currency", "devaluation", "de-dollarization", "brics"],
        "markets": ["gold", "bitcoin", "sp500"],
        "typical_impact": "Dollar weakness → gold + crypto up"
    },
}

# ============================================================
# RSS FEED READER
# ============================================================
def fetch_rss(url, timeout=10):
    """RSS feed fetch karo"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 ZAI-NewsBot/1.0"}
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        root = ET.fromstring(r.content)

        articles = []
        # Handle both RSS and Atom formats
        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items[:10]:  # Last 10 articles
            # Title
            title = (item.findtext("title") or
                    item.findtext("{http://www.w3.org/2005/Atom}title") or "")
            # Description
            desc = (item.findtext("description") or
                   item.findtext("{http://www.w3.org/2005/Atom}summary") or "")
            # Link
            link = (item.findtext("link") or
                   item.findtext("{http://www.w3.org/2005/Atom}link") or "")
            # Date
            pub_date = (item.findtext("pubDate") or
                       item.findtext("{http://www.w3.org/2005/Atom}updated") or "")

            if title:
                articles.append({
                    "title": title.strip(),
                    "description": desc.strip()[:200] if desc else "",
                    "link": link.strip(),
                    "published": pub_date.strip(),
                })

        return articles
    except Exception as e:
        return []

def fetch_all_news(feeds=None, max_feeds=15):
    """Sab RSS feeds se news fetch karo"""
    print(f"\n📰 News feeds fetch kar raha hun...")

    if feeds is None:
        # Default: top feeds fetch karo
        feed_items = list(NEWS_FEEDS.items())[:max_feeds]
    else:
        feed_items = [(k, v) for k, v in NEWS_FEEDS.items() if k in feeds]

    all_articles = []
    success = 0

    for name, url in feed_items:
        articles = fetch_rss(url)
        if articles:
            for a in articles:
                a["source"] = name
            all_articles.extend(articles)
            success += 1
            print(f"  ✅ {name}: {len(articles)} articles")
        else:
            print(f"  ❌ {name}: failed")
        time.sleep(0.3)

    print(f"\n  Total: {len(all_articles)} articles from {success} sources")
    return all_articles

# ============================================================
# KEYWORD ANALYZER
# ============================================================
def analyze_articles(articles):
    """Articles mein market-relevant keywords dhundo"""
    triggered = {}

    for article in articles:
        text = (article["title"] + " " + article["description"]).lower()

        for category, info in MARKET_IMPACT_MAP.items():
            for keyword in info["keywords"]:
                if keyword in text:
                    if category not in triggered:
                        triggered[category] = {
                            "articles": [],
                            "markets": info["markets"],
                            "typical_impact": info["typical_impact"],
                            "count": 0
                        }
                    triggered[category]["articles"].append({
                        "title": article["title"],
                        "source": article["source"],
                    })
                    triggered[category]["count"] += 1
                    break

    # Sort by count
    triggered = dict(sorted(triggered.items(),
                           key=lambda x: x[1]["count"], reverse=True))
    return triggered

# ============================================================
# HISTORICAL MATCH
# ============================================================
def match_to_history(triggered_categories):
    """
    Triggered news categories ko historical events se match karo
    "Yeh news pattern kab pehle aya tha? Kya hua tha tab?"
    """
    HISTORICAL_EVENTS = {
        "oil": [
            {
                "event": "1973 Oil Embargo",
                "what_happened": "Arab nations cut oil supply → Oil price +300% → Global recession",
                "market_impact": "S&P -48%, Inflation +10%, Gold +70%",
                "duration": "18 months",
            },
            {
                "event": "1990 Gulf War",
                "what_happened": "Iraq invades Kuwait → Oil spike → Recession",
                "market_impact": "S&P -20%, Oil +100% temporarily",
                "duration": "6 months",
            },
            {
                "event": "2022 Russia-Ukraine",
                "what_happened": "War → energy crisis → inflation surge",
                "market_impact": "Oil +60%, Gas +200%, Inflation 40yr high",
                "duration": "Ongoing",
            },
        ],
        "fed_rates": [
            {
                "event": "1980 Volcker Shock",
                "what_happened": "Fed raised rates to 20% to kill inflation",
                "market_impact": "S&P -27%, Recession, but inflation finally killed",
                "duration": "2 years",
            },
            {
                "event": "2022 Rate Hike Cycle",
                "what_happened": "Fastest rate hikes since 1980 → Market crash",
                "market_impact": "S&P -25%, Nasdaq -35%, Crypto -70%",
                "duration": "18 months",
            },
        ],
        "crypto": [
            {
                "event": "2017 Bitcoin Bubble",
                "what_happened": "BTC $20k → SEC warnings → Crash",
                "market_impact": "BTC -84% over 1 year",
                "duration": "12 months",
            },
            {
                "event": "2022 Luna/FTX Collapse",
                "what_happened": "Stablecoin depeg → Exchange collapse → Bear market",
                "market_impact": "Crypto total cap -70%",
                "duration": "12 months",
            },
        ],
        "china": [
            {
                "event": "2015 China Stock Crash",
                "what_happened": "China market bubble burst → Global contagion",
                "market_impact": "S&P -12%, Emerging markets -20%",
                "duration": "3 months",
            },
            {
                "event": "2018-2019 Trade War",
                "what_happened": "US-China tariffs → Tech supply chain disruption",
                "market_impact": "S&P -20%, Tech stocks -30%",
                "duration": "18 months",
            },
        ],
        "war_conflict": [
            {
                "event": "9/11 2001",
                "what_happened": "Terrorist attacks → Market closed 4 days → Crash",
                "market_impact": "S&P -12% in 1 week, Gold +6%",
                "duration": "1 month recovery",
            },
            {
                "event": "2022 Ukraine Invasion",
                "what_happened": "Russia invades → Sanctions → Energy crisis",
                "market_impact": "Oil +60%, Gold +10%, Europe stocks -15%",
                "duration": "Ongoing",
            },
        ],
        "recession": [
            {
                "event": "2008 Financial Crisis",
                "what_happened": "Bank failures → Credit freeze → Global recession",
                "market_impact": "S&P -57%, Unemployment +5%, Housing -30%",
                "duration": "18 months",
            },
            {
                "event": "2020 COVID Crash",
                "what_happened": "Pandemic → Lockdowns → Economic stop",
                "market_impact": "S&P -34% in 5 weeks (fastest ever)",
                "duration": "2 months crash, 5 months recovery",
            },
        ],
        "inflation": [
            {
                "event": "1970s Stagflation",
                "what_happened": "Oil crisis + monetary policy → 10%+ inflation",
                "market_impact": "Gold +2000%, S&P flat 10 years",
                "duration": "10 years",
            },
            {
                "event": "2021-2023 Post-COVID Inflation",
                "what_happened": "Money printing + supply chain → 40yr high inflation",
                "market_impact": "Fed hikes → Market crash → Gold mixed",
                "duration": "2 years",
            },
        ],
    }

    matches = {}
    for category in triggered_categories:
        if category in HISTORICAL_EVENTS:
            matches[category] = HISTORICAL_EVENTS[category]

    return matches

# ============================================================
# AI ANALYSIS
# ============================================================
def get_news_ai_analysis(triggered, historical_matches, articles):
    """Claude/Ollama se news analysis lo"""

    # Top headlines
    top_headlines = [a["title"] for a in articles[:20]]

    # Triggered categories summary
    triggered_summary = {}
    for cat, info in list(triggered.items())[:5]:
        triggered_summary[cat] = {
            "count": info["count"],
            "top_articles": [a["title"] for a in info["articles"][:3]],
            "affected_markets": info["markets"],
        }

    prompt = f"""You are ZAI News Brain - analyzing world events for market impact.

TODAY'S TOP HEADLINES:
{json.dumps(top_headlines, indent=2)}

MARKET-RELEVANT CATEGORIES DETECTED:
{json.dumps(triggered_summary, indent=2)}

HISTORICAL PARALLELS:
{json.dumps({k: v[:1] for k, v in historical_matches.items()}, indent=2)}

Analyze today's news and provide market research insights.

Respond ONLY in this JSON format:
{{
  "overall_risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
  "dominant_theme": "main theme in today's news",
  "market_alerts": [
    {{"market": "name", "signal": "BULLISH/BEARISH/WATCH", "reason": "why"}}
  ],
  "historical_parallel": "which historical event this most resembles today",
  "what_happened_then": "what happened to markets in that historical event",
  "key_headlines_to_watch": ["headline1", "headline2"],
  "research_summary": "2-3 sentence research summary",
  "confidence": 0-100
}}"""

    # Try Ollama first
    try:
        import subprocess
        result = subprocess.run(
            ["ollama", "run", "phi3:mini", prompt],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end]), "local"
    except:
        pass

    # Fallback: Claude API
    if ANTHROPIC_KEY and ANTHROPIC_KEY != "YOUR_ANTHROPIC_API_KEY_HERE":
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            result = r.json()
            text = result["content"][0]["text"]
            text = text.replace("```json", "").replace("```", "").strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end]), "claude_api"
        except:
            pass

    return None, "none"

# ============================================================
# SAVE NEWS ANALYSIS
# ============================================================
def save_news_analysis(triggered, historical_matches, ai_analysis, articles):
    """News analysis save karo"""
    os.makedirs(f"{DATA_PATH}/news", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "timestamp": datetime.now().isoformat(),
        "total_articles": len(articles),
        "triggered_categories": {k: {"count": v["count"], "markets": v["markets"]}
                                  for k, v in triggered.items()},
        "historical_matches": {k: v[0] for k, v in historical_matches.items()},
        "ai_analysis": ai_analysis,
        "top_headlines": [a["title"] for a in articles[:10]],
    }

    path = f"{DATA_PATH}/news/analysis_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    latest = f"{DATA_PATH}/news/latest.json"
    with open(latest, "w") as f:
        json.dump(data, f, indent=2)

    return data

# ============================================================
# DISPLAY
# ============================================================
def display_news_analysis(triggered, historical_matches, ai_analysis, articles):
    """Terminal mein news analysis dikhao"""
    print("\n" + "="*60)
    print("📰 ZAI NEWS BRAIN - WORLD EVENTS ANALYSIS")
    print("="*60)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Articles analyzed: {len(articles)}")

    if triggered:
        print(f"\n⚡ MARKET-MOVING TOPICS DETECTED:")
        print("─"*60)
        for cat, info in list(triggered.items())[:5]:
            bar = "█" * min(info["count"], 10)
            print(f"  {cat:<15} {bar} ({info['count']} articles)")
            print(f"             Affects: {', '.join(info['markets'])}")
            if info["articles"]:
                print(f"             → {info['articles'][0]['title'][:55]}")

    if historical_matches:
        print(f"\n📜 HISTORICAL PARALLELS:")
        print("─"*60)
        for cat, events in list(historical_matches.items())[:3]:
            e = events[0]
            print(f"  {cat.upper()}: Similar to {e['event']}")
            print(f"    What happened: {e['market_impact']}")

    if ai_analysis:
        print(f"\n🤖 AI RESEARCH ANALYSIS:")
        print("─"*60)
        risk = ai_analysis.get("overall_risk_level", "N/A")
        theme = ai_analysis.get("dominant_theme", "N/A")
        hist = ai_analysis.get("historical_parallel", "N/A")
        summary = ai_analysis.get("research_summary", "")
        conf = ai_analysis.get("confidence", 0)

        risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}.get(risk, "⚪")
        print(f"  Risk Level:  {risk_icon} {risk}")
        print(f"  Theme:       {theme}")
        print(f"  Similar to:  {hist}")
        print(f"  Confidence:  {'█'*(conf//10)}{'░'*(10-conf//10)} {conf}%")

        alerts = ai_analysis.get("market_alerts", [])
        if alerts:
            print(f"\n  📊 MARKET ALERTS:")
            for alert in alerts[:4]:
                icon = "↑" if alert.get("signal") == "BULLISH" else "↓" if alert.get("signal") == "BEARISH" else "👁"
                print(f"    {icon} {alert.get('market',''):<12} {alert.get('signal',''):<8} — {alert.get('reason','')[:40]}")

        if summary:
            print(f"\n  💬 SUMMARY: {summary[:150]}")
    else:
        print(f"\n⚠️  AI analysis nahi mili (Ollama ya API key chahiye)")

    print("\n" + "─"*60)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("="*60)
    print("📰 ZAI NEWS BRAIN")
    print("   World Events → Historical Match → Market Research")
    print("="*60)

    # Fetch news
    articles = fetch_all_news(max_feeds=12)

    if not articles:
        print("❌ News fetch nahi hui. Internet check karo.")
        exit()

    # Analyze
    print(f"\n🔍 Keywords analyze kar raha hun...")
    triggered = analyze_articles(articles)
    print(f"  {len(triggered)} market-relevant categories found")

    # Historical match
    print(f"\n📜 Historical patterns match kar raha hun...")
    historical_matches = match_to_history(triggered)
    print(f"  {len(historical_matches)} historical parallels found")

    # AI analysis
    print(f"\n🤖 AI analysis le raha hun...")
    ai_analysis, ai_source = get_news_ai_analysis(triggered, historical_matches, articles)
    if ai_analysis:
        print(f"  ✅ Analysis complete (source: {ai_source})")

    # Display
    display_news_analysis(triggered, historical_matches, ai_analysis, articles)

    # Save
    save_news_analysis(triggered, historical_matches, ai_analysis, articles)
    print(f"\n✅ Analysis saved to {DATA_PATH}/news/latest.json")
    print(f"\n💡 Tip: Dashboard mein integrate karne ke liye dashboard.py update karo")
