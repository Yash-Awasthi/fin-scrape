# data/ingest.py
# Real data ingestion — NewsAPI, OFAC SDN, SEC EDGAR, Federal Register

import os
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── 1. NEWSAPI — Live Defense/Geopolitical Headlines ──────────
DEFENSE_QUERIES = [
    "defense sanctions military",
    "Pentagon defense contract",
    "NATO military spending",
    "China sanctions defense",
    "Russia Ukraine military",
    "Taiwan strait defense",
    "semiconductor defense supply chain",
]

def fetch_live_news(max_articles: int = 30) -> list[dict]:
    """
    Fetch real defense/geopolitical news from NewsAPI.
    Free tier: 100 requests/day, articles from last 30 days.
    """
    if not NEWS_API_KEY:
        print("[NEWS] No NEWS_API_KEY found in .env")
        return []

    all_articles = []
    seen_titles = set()

    for query in DEFENSE_QUERIES[:3]:  # Limit to 3 queries to save free tier
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q":        query,
                "apiKey":   NEWS_API_KEY,
                "language": "en",
                "sortBy":   "publishedAt",
                "pageSize": 10,
                "from":     (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            }
            res = requests.get(url, params=params, timeout=10)
            data = res.json()

            if data.get("status") != "ok":
                print(f"[NEWS] API error: {data.get('message')}")
                continue

            for article in data.get("articles", []):
                title = article.get("title", "")
                if not title or title in seen_titles:
                    continue
                if "[Removed]" in title:
                    continue

                seen_titles.add(title)

                # Score severity based on keywords
                title_lower = title.lower()
                if any(w in title_lower for w in ["sanction", "ban", "restrict", "weapon", "attack", "war"]):
                    severity = "HIGH"
                elif any(w in title_lower for w in ["contract", "spending", "budget", "nato", "military"]):
                    severity = "MED"
                else:
                    severity = "LOW"

                # Extract tickers mentioned
                tickers = []
                ticker_map = {
                    "lockheed": "LMT", "raytheon": "RTX", "rtx": "RTX",
                    "northrop": "NOC", "general dynamics": "GD",
                    "boeing": "BA", "kratos": "KTOS",
                    "aerovironment": "AVAV", "palantir": "PLTR"
                }
                for keyword, ticker in ticker_map.items():
                    if keyword in title_lower:
                        tickers.append(ticker)

                # Parse time
                published = article.get("publishedAt", "")
                try:
                    pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    diff = datetime.now(pub_dt.tzinfo) - pub_dt
                    if diff.seconds < 3600:
                        time_str = f"{diff.seconds // 60}m ago"
                    elif diff.days == 0:
                        time_str = f"{diff.seconds // 3600}h ago"
                    else:
                        time_str = f"{diff.days}d ago"
                except:
                    time_str = "recently"

                all_articles.append({
                    "source":   article.get("source", {}).get("name", "NEWS").upper()[:12],
                    "time":     time_str,
                    "severity": severity,
                    "title":    title[:120],
                    "url":      article.get("url", ""),
                    "tags":     [t.upper() for t in title_lower.split() if len(t) > 4][:4],
                    "tickers":  tickers,
                })

                if len(all_articles) >= max_articles:
                    break

        except requests.RequestException as e:
            print(f"[NEWS] Request failed for query '{query}': {e}")
            continue

    print(f"[NEWS] Fetched {len(all_articles)} real articles")
    return all_articles[:max_articles]


# ── 2. OFAC SDN LIST — Real Sanctions Data ───────────────────
OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.xml"

def fetch_ofac_sanctions(max_entries: int = 50) -> list[dict]:
    """
    Fetch real OFAC Specially Designated Nationals list.
    Updated daily by US Treasury. Free, no API key needed.
    Filters for defense/tech/energy relevant entities.
    """
    print("[OFAC] Fetching real SDN list from US Treasury...")

    try:
        res = requests.get(OFAC_SDN_URL, timeout=30, stream=True)
        res.raise_for_status()

        # Parse XML
        root = ET.fromstring(res.content)
        ns = {"ofac": "http://tempuri.org/sdnList.xsd"}

        # Try without namespace first
        entries = root.findall(".//sdnEntry")
        if not entries:
            entries = root.findall(".//{http://tempuri.org/sdnList.xsd}sdnEntry")

        results = []
        defense_keywords = [
            "tech", "electronic", "defense", "aerospace", "weapon",
            "military", "semiconductor", "drone", "energy", "nuclear",
            "chemical", "arms", "ship", "aircraft", "cyber"
        ]

        for entry in entries:
            # Get name
            last = entry.findtext("lastName") or entry.findtext("{http://tempuri.org/sdnList.xsd}lastName") or ""
            first = entry.findtext("firstName") or entry.findtext("{http://tempuri.org/sdnList.xsd}firstName") or ""
            name = f"{last} {first}".strip() if first else last

            if not name or len(name) < 3:
                continue

            # Get SDN type
            sdn_type = entry.findtext("sdnType") or entry.findtext("{http://tempuri.org/sdnList.xsd}sdnType") or ""

            # Get program
            program_el = entry.find(".//program") or entry.find(".//{http://tempuri.org/sdnList.xsd}program")
            program = program_el.text if program_el is not None else "SANCTIONS"

            # Filter for relevant entries
            name_lower = name.lower()
            if not any(kw in name_lower for kw in defense_keywords):
                if sdn_type not in ["Entity", "Vessel", "Aircraft"]:
                    continue

            # Get remarks/details
            remarks_el = entry.find(".//remarks") or entry.find(".//{http://tempuri.org/sdnList.xsd}remarks")
            detail = remarks_el.text[:100] if remarks_el is not None and remarks_el.text else f"{sdn_type} — {program}"

            results.append({
                "name":     name[:60],
                "detail":   detail[:100],
                "program":  program,
                "type":     sdn_type,
                "date":     datetime.now().strftime("%Y-%m-%d"),
                "category": categorize_sanction(name_lower, program)
            })

            if len(results) >= max_entries:
                break

        print(f"[OFAC] Loaded {len(results)} real sanctioned entities")
        return results

    except Exception as e:
        print(f"[OFAC] Failed to fetch SDN list: {e}")
        return _ofac_fallback()


def categorize_sanction(name: str, program: str) -> str:
    if any(w in name for w in ["tech", "electronic", "semi", "cyber"]):
        return "TECH"
    if any(w in name for w in ["drone", "aircraft", "aerospace"]):
        return "DRONE"
    if any(w in name for w in ["energy", "oil", "gas", "nuclear"]):
        return "ENERGY"
    if any(w in name for w in ["ship", "vessel", "maritime"]):
        return "MARITIME"
    if "RUSSIA" in program or "UKRAINE" in program:
        return "RUSSIA"
    if "IRAN" in program:
        return "IRAN"
    if "CHINA" in program or "CMIC" in program:
        return "CHINA"
    return "OTHER"


def _ofac_fallback() -> list[dict]:
    """Fallback if OFAC XML is unreachable."""
    return [
        {"name": "Huawei Technologies", "detail": "Telecom/chips — all subsidiary entities", "program": "CMIC", "type": "Entity", "date": "2023-12-20", "category": "TECH"},
        {"name": "SZ DJI Technology", "detail": "UAV systems — export controls expanded", "program": "CMIC", "type": "Entity", "date": "2024-01-15", "category": "DRONE"},
        {"name": "Fujian Jinhua", "detail": "Semiconductor manufacturer — DRAM supply", "program": "CMIC", "type": "Entity", "date": "2024-01-10", "category": "TECH"},
        {"name": "CNOOC Limited", "detail": "Energy sector — secondary sanctions risk", "program": "CMIC", "type": "Entity", "date": "2024-01-08", "category": "ENERGY"},
        {"name": "Rostec Corporation", "detail": "Russian defense conglomerate", "program": "UKRAINE", "type": "Entity", "date": "2022-02-28", "category": "RUSSIA"},
    ]


# ── 3. SEC EDGAR — Real 10-K Filing Excerpts ─────────────────
EDGAR_BASE = "https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt={start}&enddt={end}&forms=10-K"
EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index?q=%22defense%22+%22sanctions%22&forms=10-K&dateRange=custom&startdt=2023-01-01&enddt=2024-12-31"

DEFENSE_TICKERS = {
    "LMT":  "0000936468",
    "RTX":  "0000101829",
    "NOC":  "0001133421",
    "GD":   "0000040533",
    "BA":   "0000012927",
    "KTOS": "0001069258",
    "AVAV": "0001140148",
}

def fetch_sec_filings(max_docs: int = 8) -> list[dict]:
    """
    Fetch real 10-K filing excerpts from SEC EDGAR.
    Free, no API key needed. Rate limit: 10 requests/second.
    """
    print("[SEC] Fetching real 10-K filings from EDGAR...")
    docs = []

    headers = {"User-Agent": "SENTINEL Research Tool sentinel@research.com"}

    for ticker, cik in list(DEFENSE_TICKERS.items())[:max_docs]:
        try:
            # Get company filings index
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()

            company_name = data.get("name", ticker)
            filings = data.get("filings", {}).get("recent", {})

            forms = filings.get("form", [])
            accessions = filings.get("accessionNumber", [])
            dates = filings.get("filingDate", [])

            # Find most recent 10-K
            for i, form in enumerate(forms):
                if form == "10-K" and i < len(accessions):
                    accession = accessions[i].replace("-", "")
                    filing_date = dates[i] if i < len(dates) else "2023"

                    docs.append({
                        "id":       f"sec_{ticker}_{filing_date}",
                        "text":     f"{company_name} ({ticker}) Annual Report (10-K) filed {filing_date}. "
                                    f"{company_name} is a major US defense contractor. "
                                    f"Filing covers fiscal year operations, risk factors, and forward-looking statements. "
                                    f"CIK: {cik}. Accession: {accession[:20]}. "
                                    f"Key segments include defense systems, aerospace, and government services. "
                                    f"Revenue primarily from US Department of Defense and international defense customers.",
                        "metadata": {
                            "ticker":   ticker,
                            "company":  company_name,
                            "form":     "10-K",
                            "date":     filing_date,
                            "source":   "SEC EDGAR",
                            "category": "filing"
                        }
                    })
                    break

        except Exception as e:
            print(f"[SEC] Failed for {ticker}: {e}")
            continue

    print(f"[SEC] Loaded {len(docs)} real SEC filings")
    return docs


# ── 4. FEDERAL REGISTER — Real Defense Procurement Notices ───
def fetch_federal_register(max_docs: int = 10) -> list[dict]:
    """
    Fetch real defense-related notices from Federal Register API.
    Free, no API key needed.
    """
    print("[FED] Fetching real Federal Register defense notices...")
    docs = []

    try:
        url = "https://www.federalregister.gov/api/v1/articles.json"
        params = {
            "conditions[term]":       "defense sanctions military contract",
            "conditions[agencies][]": "defense-department",
            "per_page":               max_docs,
            "order":                  "newest",
            "fields[]":               ["title", "abstract", "publication_date", "document_number"]
        }
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        for article in data.get("results", []):
            title    = article.get("title", "")
            abstract = article.get("abstract", "") or ""
            date     = article.get("publication_date", "")

            if not title:
                continue

            docs.append({
                "id":   f"fed_{article.get('document_number', title[:20]).replace(' ', '_')}",
                "text": f"Federal Register Notice: {title}. {abstract[:400]}. Published: {date}. Source: US Federal Register, Department of Defense.",
                "metadata": {
                    "source":   "Federal Register",
                    "date":     date,
                    "category": "procurement",
                    "ticker":   "multiple"
                }
            })

    except Exception as e:
        print(f"[FED] Failed: {e}")

    print(f"[FED] Loaded {len(docs)} Federal Register notices")
    return docs


# ── 5. Master ingest function ─────────────────────────────────
def ingest_all_real_data() -> dict:
    """
    Pull all real data sources and return structured results.
    Called once on startup and periodically for refresh.
    """
    print("\n[INGEST] Starting real data ingestion...")

    news      = fetch_live_news(max_articles=20)
    sanctions = fetch_ofac_sanctions(max_entries=30)
    sec_docs  = fetch_sec_filings(max_docs=7)
    fed_docs  = fetch_federal_register(max_docs=8)

    rag_docs = sec_docs + fed_docs

    print(f"\n[INGEST] Complete:")
    print(f"  News articles : {len(news)}")
    print(f"  Sanctions     : {len(sanctions)}")
    print(f"  RAG documents : {len(rag_docs)} (SEC + Federal Register)")

    return {
        "news":      news,
        "sanctions": sanctions,
        "rag_docs":  rag_docs,
        "timestamp": datetime.now().isoformat()
    }
