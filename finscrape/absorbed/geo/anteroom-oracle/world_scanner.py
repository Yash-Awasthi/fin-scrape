"""
ZAI Oracle — World Scanner v3.0
by Zawwar (github.com/Zawwarsami16)

Multi-source price engine with real spot gold/silver via gold-api.com.
Valid ranges updated for March 2026 reality (gold $5000+, silver $80+).
Deduplication, source tiering, narrative momentum tracking.
"""

import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from config import DATA_PATH

# ================================================================
# VALID RANGES — Updated for March 2026 market reality
# Gold has been in a massive bull run — $5000+ is correct
# ================================================================
VALID_RANGES = {
    "sp500":       (500,    12000),
    "nasdaq":      (5000,   25000),
    "dow":         (10000,  65000),
    "gold":        (1500,   8000),    # March 2026: gold at $5000+ is real
    "silver":      (10,     200),     # March 2026: silver at $80 is real
    "oil":         (20,     250),
    "naturalgas":  (1,      20),
    "copper":      (2,      20),
    "vix":         (5,      90),
    "dxy":         (70,     130),
    "tnx":         (0.1,    15),
    "nikkei":      (10000,  60000),
    "ftse":        (5000,   12000),
    "eurusd":      (0.8,    1.5),
    "usdjpy":      (80,     200),
    "btc":         (1000,   250000),
    "eth":         (50,     20000),
    "sol":         (5,      1000),
    "bnb":         (10,     2000),
    "xrp":         (0.1,    10),
}

SOURCE_TIERS = {
    "tier1": ["reuters", "bloomberg", "ft", "wsj", "ap", "bbc", "economist"],
    "tier2": ["aljazeera", "guardian", "cnbc", "marketwatch", "coindesk",
              "cointelegraph", "theblock", "foreignpolicy"],
    "tier3": ["zerohedge", "seeking_alpha", "decrypt", "oilprice", "thehill"],
}

NEWS_FEEDS = {
    "reuters_world":    "https://feeds.reuters.com/Reuters/worldNews",
    "bbc_world":        "https://feeds.bbci.co.uk/news/world/rss.xml",
    "aljazeera":        "https://www.aljazeera.com/xml/rss/all.xml",
    "rfe_rl":           "https://www.rferl.org/api/epiqltbvefu",
    "crisisgroup":      "https://www.crisisgroup.org/rss.xml",
    "foreignpolicy":    "https://foreignpolicy.com/feed/",
    "cfr_global":       "https://www.cfr.org/rss.xml",
    "the_diplomat":     "https://thediplomat.com/feed/",
    "middle_east_eye":  "https://www.middleeasteye.net/rss",
    "bloomberg_markets":"https://feeds.bloomberg.com/markets/news.rss",
    "reuters_finance":  "https://feeds.reuters.com/reuters/businessNews",
    "wsj_markets":      "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "marketwatch":      "https://www.marketwatch.com/rss/topstories",
    "economist":        "https://www.economist.com/latest/rss.xml",
    "zerohedge":        "https://feeds.feedburner.com/zerohedge/feed",
    "coindesk":         "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph":    "https://cointelegraph.com/rss",
    "theblock":         "https://www.theblock.co/rss.xml",
    "oilprice":         "https://oilprice.com/rss/main",
    "eia_energy":       "https://www.eia.gov/rss/news.xml",
    "politico":         "https://www.politico.com/rss/politics08.xml",
    "thehill":          "https://thehill.com/feed/",
    "guardian_politics":"https://www.theguardian.com/politics/rss",
    "mit_tech":         "https://www.technologyreview.com/feed/",
    "wired":            "https://www.wired.com/feed/rss",
    "ars_technica":     "http://feeds.arstechnica.com/arstechnica/index/",
    "reliefweb":        "https://reliefweb.int/updates/rss.xml",
    "who_news":         "https://www.who.int/rss-feeds/news-english.xml",
    "usgs_earthquakes": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.atom",
}

SIGNAL_MAP = {
    "war_conflict": {
        "keywords": ["war","attack","missile","invasion","troops","military","nato",
                     "airstrike","bomb","ceasefire","offensive","casualties","siege",
                     "drone strike","naval","warship","escalation","frontline"],
        "affects":  ["gold","oil","vix"],
        "pattern":  "Gold +5-15%, Oil +10-40%, Markets -5-20%",
        "severity": 2.0,
    },
    "geopolitics": {
        "keywords": ["sanction","tariff","trade war","embargo","diplomacy","summit",
                     "treaty","alliance","coup","regime change","protest","revolution"],
        "affects":  ["forex","emerging_markets"],
        "pattern":  "Regional currencies -5-30%",
        "severity": 1.5,
    },
    "oil_energy": {
        "keywords": ["oil","opec","crude","petroleum","natural gas","pipeline",
                     "energy crisis","refinery","lng","shale","saudi","iran",
                     "venezuela","energy supply","oil price","barrel"],
        "affects":  ["oil","inflation","sp500"],
        "pattern":  "Oil +20% → Inflation +2-4% in 8 weeks",
        "severity": 1.8,
    },
    "central_banks": {
        "keywords": ["federal reserve","fed rate","interest rate","powell","fomc",
                     "rate hike","rate cut","quantitative easing","monetary policy",
                     "ecb","bank of england","boj","inflation target","basis points"],
        "affects":  ["bonds","sp500","gold"],
        "pattern":  "Rate hike → Markets -10-25%",
        "severity": 2.0,
    },
    "china_asia": {
        "keywords": ["china","xi jinping","taiwan","prc","yuan","south china sea",
                     "hong kong","brics","belt and road","chinese economy","pmi china"],
        "affects":  ["sp500","copper","commodities"],
        "pattern":  "China slowdown → Global commodities -10-20%",
        "severity": 1.7,
    },
    "crypto_regulation": {
        "keywords": ["bitcoin","ethereum","crypto","blockchain","sec crypto","etf bitcoin",
                     "binance","coinbase","defi","stablecoin","cbdc","crypto ban","tether"],
        "affects":  ["bitcoin","ethereum"],
        "pattern":  "Regulation → Crypto -20-50%",
        "severity": 1.5,
    },
    "recession_economy": {
        "keywords": ["recession","gdp decline","economic slowdown","stagflation",
                     "unemployment surge","layoffs","bankruptcy","default",
                     "debt ceiling","yield curve","inverted yield"],
        "affects":  ["sp500","bonds","gold"],
        "pattern":  "Recession → Markets -20-50%",
        "severity": 2.5,
    },
    "inflation_dollar": {
        "keywords": ["inflation","cpi","pce","consumer price","price rise",
                     "dollar index","usd","de-dollarization","dollar weakness",
                     "hyperinflation","stagflation","purchasing power"],
        "affects":  ["gold","bitcoin","bonds"],
        "pattern":  "High inflation → Gold +20-100%",
        "severity": 1.6,
    },
    "tech_ai": {
        "keywords": ["artificial intelligence","ai model","chatgpt","openai","nvidia",
                     "semiconductor","chip shortage","quantum","tech earnings","big tech"],
        "affects":  ["nasdaq","tech_stocks"],
        "pattern":  "AI boom → Nasdaq +20-80%",
        "severity": 1.4,
    },
    "natural_disaster": {
        "keywords": ["earthquake","hurricane","tsunami","flood","wildfire","volcano",
                     "drought","pandemic","outbreak","famine","extreme weather"],
        "affects":  ["insurance_stocks","commodities"],
        "pattern":  "Major disaster → Insurance -10-30%",
        "severity": 1.3,
    },
    "elections_politics": {
        "keywords": ["election","vote","president","prime minister","parliament",
                     "senate","congress bill","policy","tax reform","stimulus",
                     "fiscal policy","government shutdown"],
        "affects":  ["regional_markets","forex"],
        "pattern":  "Election uncertainty → VIX +10-30%",
        "severity": 1.4,
    },
}


def fetch_spot_prices_api():
    """
    Fetches real spot prices from gold-api.com — confirmed working.
    Returns dict with gold and silver spot prices.
    """
    spots = {}
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=8)
        data = r.json()
        if "price" in data:
            spots["gold"] = round(float(data["price"]), 2)
    except Exception:
        pass
    try:
        r = requests.get("https://api.gold-api.com/price/XAG", timeout=8)
        data = r.json()
        if "price" in data:
            spots["silver"] = round(float(data["price"]), 2)
    except Exception:
        pass
    return spots


def fetch_live_prices():
    """
    Fetches all live market prices.
    Gold/Silver: gold-api.com (confirmed working, real spot price)
    Crypto: CoinGecko
    Everything else: yfinance
    """
    prices = {}

    # Gold and Silver from gold-api.com first (most reliable)
    spot_prices = fetch_spot_prices_api()

    # Everything via yfinance
    ticker_map = {
        "sp500":      "^GSPC",
        "nasdaq":     "^IXIC",
        "dow":        "^DJI",
        "gold":       "GC=F",       # fallback only — will be overridden by gold-api
        "silver":     "SI=F",       # fallback only — will be overridden by gold-api
        "oil":        "CL=F",
        "naturalgas": "NG=F",
        "copper":     "HG=F",
        "vix":        "^VIX",
        "dxy":        "DX-Y.NYB",
        "tnx":        "^TNX",
        "nikkei":     "^N225",
        "ftse":       "^FTSE",
        "eurusd":     "EURUSD=X",
        "usdjpy":     "JPY=X",
        "btcusd":     "BTC-USD",
        "ethusd":     "ETH-USD",
    }

    try:
        import yfinance as yf
        for name, ticker in ticker_map.items():
            try:
                df = yf.Ticker(ticker).history(period="5d", interval="1d")
                if df.empty:
                    continue
                price  = float(df["Close"].iloc[-1])
                prev   = float(df["Close"].iloc[-2]) if len(df) > 1 else price
                chg    = ((price - prev) / prev * 100) if prev else 0
                key    = name.replace("usd", "").replace("=x", "")
                lo, hi = VALID_RANGES.get(key, (0, float("inf")))
                prices[key] = {
                    "price":      round(price, 4),
                    "change_pct": round(chg, 2),
                    "ticker":     ticker,
                    "source":     "yfinance",
                    "in_range":   lo <= price <= hi,
                    "trust":      "HIGH" if lo <= price <= hi else "LOW",
                    "warnings":   [] if lo <= price <= hi else [f"outside range ${lo}-${hi}"],
                    "updated":    datetime.now().isoformat(),
                }
            except Exception:
                continue
    except ImportError:
        pass

    # Override gold/silver with real spot prices from gold-api.com
    for asset, spot_price in spot_prices.items():
        lo, hi = VALID_RANGES.get(asset, (0, float("inf")))
        # Get change from yfinance if available, else 0
        chg = prices.get(asset, {}).get("change_pct", 0)
        prices[asset] = {
            "price":        spot_price,
            "change_pct":   chg,
            "source":       "gold-api.com (spot)",
            "ticker":       "XAU" if asset == "gold" else "XAG",
            "in_range":     lo <= spot_price <= hi,
            "trust":        "HIGH",
            "warnings":     [],
            "updated":      datetime.now().isoformat(),
        }

    # Crypto via CoinGecko
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "bitcoin,ethereum,solana,binancecoin,ripple",
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=10
        )
        coin_map = {"bitcoin":"btc","ethereum":"eth","solana":"sol",
                    "binancecoin":"bnb","ripple":"xrp"}
        for coin_id, short in coin_map.items():
            d = r.json().get(coin_id, {})
            if d:
                price  = d["usd"]
                chg    = round(d.get("usd_24h_change", 0), 2)
                lo, hi = VALID_RANGES.get(short, (0, float("inf")))
                prices[short] = {
                    "price":      price,
                    "change_pct": chg,
                    "source":     "CoinGecko",
                    "trust":      "HIGH" if lo <= price <= hi else "LOW",
                    "in_range":   lo <= price <= hi,
                    "warnings":   [],
                    "updated":    datetime.now().isoformat(),
                }
    except Exception:
        pass

    os.makedirs(f"{DATA_PATH}/live", exist_ok=True)
    with open(f"{DATA_PATH}/live/prices.json", "w") as f:
        json.dump(prices, f, indent=2)

    return prices


def validate_prices(prices):
    """Validates all prices and builds trust report."""
    verified = errors = fixed = 0
    warn_list = []
    err_list  = []
    fix_list  = []

    for asset, data in prices.items():
        if not isinstance(data, dict):
            continue
        if data.get("source","").startswith("gold-api"):
            fixed += 1
            fix_list.append(f"{asset}: real spot price from gold-api.com")
        if data.get("in_range", True):
            verified += 1
        else:
            errors += 1
            err_list.append(f"{asset}: ${data.get('price',0):,.2f} outside expected range")

    total     = len(prices)
    trust_pct = round((verified / total * 100) if total else 0)

    return {
        "total_assets":   total,
        "verified":       verified,
        "trust_pct":      trust_pct,
        "fixed":          fix_list,
        "fixed_count":    len(fix_list),
        "warnings":       warn_list,
        "warnings_count": len(warn_list),
        "errors":         err_list,
        "errors_count":   errors,
    }


def get_source_tier(source_name):
    src = source_name.lower()
    for tier, sources in SOURCE_TIERS.items():
        if any(s in src for s in sources):
            return tier, {"tier1":1.0,"tier2":0.7,"tier3":0.4}[tier]
    return "tier3", 0.4


def fetch_rss(url, source_name, timeout=8):
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0 ZAI-Oracle/3.0"}, timeout=timeout)
        r.raise_for_status()
        root  = ET.fromstring(r.content)
        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        articles = []
        for item in items[:8]:
            title = (item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
            desc  = (item.findtext("description") or item.findtext("{http://www.w3.org/2005/Atom}summary") or "").strip()[:200]
            pub   = (item.findtext("pubDate") or item.findtext("{http://www.w3.org/2005/Atom}updated") or "").strip()
            if title:
                articles.append({"title":title,"desc":desc,"source":source_name,"published":pub})
        return articles
    except Exception:
        return []


def scan_world_news(max_feeds=30):
    """Scans news with deduplication, source tiering, narrative momentum."""
    print(f"  Scanning {min(max_feeds, len(NEWS_FEEDS))} news sources...")

    all_articles = []
    seen_titles  = set()
    sources_hit  = 0
    feed_list    = list(NEWS_FEEDS.items())[:max_feeds]

    for name, url in feed_list:
        articles = fetch_rss(url, name)
        if articles:
            sources_hit += 1
        for a in articles:
            key = a["title"][:60].lower().strip()
            if key not in seen_titles:
                seen_titles.add(key)
                all_articles.append(a)
        time.sleep(0.1)

    print(f"  {len(all_articles)} unique articles from {sources_hit} sources")

    triggered = {}
    for article in all_articles:
        text = (article["title"] + " " + article["desc"]).lower()
        src  = article["source"]
        tier_key, tier_weight = get_source_tier(src)

        for category, info in SIGNAL_MAP.items():
            if not any(kw in text for kw in info["keywords"]):
                continue
            if category not in triggered:
                triggered[category] = {
                    "count": 0, "severity": 0.0,
                    "unique_sources": set(),
                    "source_breakdown": {},
                    "tier_breakdown": {"tier1":0,"tier2":0,"tier3":0},
                    "headlines": [],
                    "affects": info["affects"],
                    "pattern": info["pattern"],
                }
            triggered[category]["count"]    += 1
            triggered[category]["severity"] += info["severity"] * tier_weight
            triggered[category]["unique_sources"].add(src)
            triggered[category]["source_breakdown"][src] = triggered[category]["source_breakdown"].get(src, 0) + 1
            triggered[category]["tier_breakdown"][tier_key] += 1
            if len(triggered[category]["headlines"]) < 5:
                triggered[category]["headlines"].append({"title":article["title"],"source":src,"tier":tier_key})

    for cat in triggered:
        unique_set = triggered[cat]["unique_sources"]
        triggered[cat]["unique_sources"] = len(unique_set)
        t1 = triggered[cat]["tier_breakdown"]["tier1"]
        t2 = triggered[cat]["tier_breakdown"]["tier2"]
        triggered[cat]["consensus"] = "HIGH" if t1 >= 2 else "MEDIUM" if (t1+t2) >= 2 else "LOW"

    triggered = dict(sorted(triggered.items(), key=lambda x: x[1]["severity"], reverse=True))

    total_sev = sum(v["severity"] for v in triggered.values())
    risk_level = (
        "CRITICAL"  if total_sev > 50 else
        "HIGH"      if total_sev > 30 else
        "ELEVATED"  if total_sev > 15 else
        "MODERATE"  if total_sev > 5  else "LOW"
    )

    result = {
        "scanned_at":      datetime.now().isoformat(),
        "total_articles":  len(all_articles),
        "unique_articles": len(all_articles),
        "total_sources":   sources_hit,
        "risk_level":      risk_level,
        "total_severity":  round(total_sev, 1),
        "signals":         triggered,
        "top_headlines":   [a["title"] for a in all_articles[:20]],
    }

    os.makedirs(f"{DATA_PATH}/news", exist_ok=True)
    with open(f"{DATA_PATH}/news/latest.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    return result


def assess_world_situation(prices, news):
    signals   = news.get("signals", {})
    situation = {
        "timestamp":     datetime.now().isoformat(),
        "risk_level":    news.get("risk_level", "UNKNOWN"),
        "active_crises": [],
        "market_stress": [],
        "key_numbers":   {},
    }
    for cat, data in signals.items():
        if data["count"] >= 5:
            situation["active_crises"].append({
                "type":      cat,
                "intensity": data["count"],
                "consensus": data.get("consensus","LOW"),
                "affects":   data["affects"],
                "pattern":   data["pattern"],
            })
    p = prices
    if p.get("vix",{}).get("price",0) > 25:
        situation["market_stress"].append(f"VIX elevated at {p['vix']['price']:.1f}")
    if p.get("oil",{}).get("change_pct",0) > 3:
        situation["market_stress"].append(f"Oil surging +{p['oil']['change_pct']:.1f}% today")
    if p.get("oil",{}).get("price",0) > 100:
        situation["market_stress"].append("Oil above $100 — inflation trigger breached")
    if p.get("gold",{}).get("change_pct",0) > 2:
        situation["market_stress"].append(f"Gold flight +{p['gold']['change_pct']:.1f}% — fear buying")
    if p.get("btc",{}).get("change_pct",0) < -5:
        situation["market_stress"].append(f"BTC selling off {p['btc']['change_pct']:.1f}%")
    if p.get("dxy",{}).get("change_pct",0) > 0.5:
        situation["market_stress"].append(f"Dollar strengthening +{p['dxy']['change_pct']:.1f}% — risk-off")
    for asset in ["oil","gold","btc","sp500","vix","dxy"]:
        if asset in p:
            situation["key_numbers"][asset] = {
                "price": p[asset]["price"],
                "chg":   p[asset]["change_pct"],
                "trust": p[asset].get("trust","HIGH"),
            }
    return situation
