# tools/data_fetcher.py
# Real data sources — OFAC, NewsAPI, SEC EDGAR, Federal Register
# Zero synthetic data

import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import time

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ── OFAC SDN LIST (Real, Free, Updated Daily) ─────────────────
OFAC_URL = "https://www.treasury.gov/ofac/downloads/sdn.xml"
_ofac_cache = {"data": [], "fetched_at": None}

def fetch_ofac_sanctions(max_entries: int = 50) -> list[dict]:
    """
    Fetch real sanctioned entities from OFAC SDN XML.
    Updated daily by US Treasury. Free, no API key needed.
    Filters for defense/tech/energy relevant entities.
    """
    global _ofac_cache

    if _ofac_cache["fetched_at"] and \
       (datetime.now() - _ofac_cache["fetched_at"]).seconds < 21600 and \
       _ofac_cache["data"]:
        return _ofac_cache["data"][:max_entries]

    print("[OFAC] Fetching SDN list from US Treasury...")
    try:
        resp = requests.get(OFAC_URL, timeout=30)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        ns = {"ofac": "https://tempuri.org/sdnList.xsd"}

        entries_ns = root.findall(".//ofac:sdnEntry", ns)
        entries    = entries_ns if entries_ns else root.findall(".//sdnEntry")

        DEFENSE_TERMS = [
            "military", "defense", "weapon", "arms", "missile",
            "drone", "aircraft", "ship", "nuclear", "chemical",
            "technology", "semiconductor", "electronic", "cyber",
            "intelligence", "security", "energy", "oil", "mining",
            "china", "russia", "iran", "north korea", "syria",
            "india", "pakistan", "israel", "france", "uk", "britain",
            "aerospace", "naval", "armament", "ordnance", "radar",
        ]

        results = []
        for entry in entries:
            def find_text(tag):
                el = entry.find(f"ofac:{tag}", ns) or entry.find(tag)
                return el.text.strip() if el is not None and el.text else ""

            name     = find_text("lastName") or find_text("firstName")
            sdn_type = find_text("sdnType")
            programs_el = entry.find("ofac:programList", ns) or entry.find("programList")
            programs = []
            if programs_el is not None:
                for p in list(programs_el):
                    if p.text:
                        programs.append(p.text.strip())

            remarks = find_text("remarks").lower()
            name_lower = name.lower()

            is_relevant = any(
                term in name_lower or term in remarks or
                any(term in prog.lower() for prog in programs)
                for term in DEFENSE_TERMS
            )

            if is_relevant and name:
                results.append({
                    "name":     name,
                    "type":     sdn_type,
                    "programs": programs,
                    "detail":   remarks[:120] if remarks else f"{sdn_type} — OFAC SDN List",
                    "date":     datetime.now().strftime("%Y-%m-%d"),
                    "source":   "OFAC SDN"
                })

            if len(results) >= max_entries:
                break

        if not results:
            for entry in entries[:max_entries]:
                def find_text_fb(tag):
                    el = entry.find(f"ofac:{tag}", ns) or entry.find(tag)
                    return el.text.strip() if el is not None and el.text else ""
                name = find_text_fb("lastName") or find_text_fb("firstName")
                sdn_type = find_text_fb("sdnType")
                if name:
                    results.append({
                        "name":     name,
                        "type":     sdn_type,
                        "programs": [],
                        "detail":   f"{sdn_type} entity — OFAC SDN List",
                        "date":     datetime.now().strftime("%Y-%m-%d"),
                        "source":   "OFAC SDN"
                    })

        _ofac_cache["data"]       = results
        _ofac_cache["fetched_at"] = datetime.now()
        print(f"[OFAC] Loaded {len(results)} relevant sanctioned entities")
        return results[:max_entries]

    except Exception as e:
        print(f"[OFAC] Error: {e}")
        return []


# ── NEWSAPI (Real Live News) ───────────────────────────────────
_news_cache = {"data": [], "fetched_at": None}

DEFENSE_QUERIES = [
    "defense stocks sanctions",
    "geopolitical market risk",
    "NATO defense spending",
    "China military sanctions",
    "Pentagon defense contract",
    "India defense procurement",
    "Israel defense technology",
    "European defense industry",
]

def fetch_defense_news(max_articles: int = 15) -> list[dict]:
    global _news_cache

    if _news_cache["fetched_at"] and \
       (datetime.now() - _news_cache["fetched_at"]).seconds < 900 and \
       _news_cache["data"]:
        return _news_cache["data"][:max_articles]

    if not NEWS_API_KEY:
        print("[NEWS] NEWS_API_KEY not set")
        return []

    print("[NEWS] Fetching live defense news from NewsAPI...")
    articles = []
    seen_titles = set()

    from_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

    for query in DEFENSE_QUERIES[:3]:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":          query,
                    "from":       from_date,
                    "sortBy":     "publishedAt",
                    "language":   "en",
                    "pageSize":   10,
                    "apiKey":     NEWS_API_KEY,
                },
                timeout=10
            )
            data = resp.json()

            if data.get("status") != "ok":
                print(f"[NEWS] API error: {data.get('message', 'unknown')}")
                continue

            for a in data.get("articles", []):
                title = a.get("title", "")
                if not title or title in seen_titles or "[Removed]" in title:
                    continue
                seen_titles.add(title)

                title_lower = title.lower()
                if any(w in title_lower for w in ["sanction", "ban", "attack", "crisis", "war", "strike"]):
                    severity = "HIGH"
                elif any(w in title_lower for w in ["contract", "deal", "spending", "warning", "risk"]):
                    severity = "MED"
                else:
                    severity = "LOW"

                # Expanded ticker name detection for all global companies
                TICKER_NAME_MAP = {
                    "LMT": ["Lockheed"], "RTX": ["Raytheon", "RTX Corp"], "NOC": ["Northrop"],
                    "GD": ["General Dynamics"], "BA": ["Boeing"], "KTOS": ["Kratos"],
                    "AVAV": ["AeroVironment"], "PLTR": ["Palantir"], "HII": ["Huntington Ingalls"],
                    "L3H": ["L3Harris"], "TXT": ["Textron"], "LHX": ["L3Harris"],
                    "LDOS": ["Leidos"], "SAIC": ["SAIC"], "BAH": ["Booz Allen"],
                    "BWXT": ["BWX Technologies"], "DRS": ["Leonardo DRS"],
                    # European
                    "AIR.PA": ["Airbus"], "BA.L": ["BAE Systems", "BAE"],
                    "RR.L": ["Rolls-Royce"], "SAF.PA": ["Safran"],
                    "LDO.MI": ["Leonardo"], "THLEF": ["Thales"],
                    "RHEG": ["Rheinmetall"], "SAAB-B.ST": ["Saab"],
                    # Israeli
                    "ESLT": ["Elbit Systems", "Elbit"],
                    "RRPBY": ["Rafael"], "IAI": ["Israel Aerospace"],
                    # Indian
                    "HAL.NS": ["Hindustan Aeronautics", "HAL"],
                    "BEL.NS": ["Bharat Electronics", "BEL"],
                    # Russian (exchange-listed variants)
                    "RSTLD": ["Rostec", "Rosoboronexport"],
                }
                tickers_mentioned = []
                for ticker, names in TICKER_NAME_MAP.items():
                    if ticker in title.upper() or any(n in title for n in names):
                        tickers_mentioned.append(ticker)

                pub = a.get("publishedAt", "")
                try:
                    pub_dt   = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    delta    = datetime.now(pub_dt.tzinfo) - pub_dt
                    mins     = int(delta.total_seconds() / 60)
                    time_ago = f"{mins}m ago" if mins < 60 else f"{mins//60}h ago"
                except:
                    time_ago = "recently"

                articles.append({
                    "source":   a.get("source", {}).get("name", "NEWS").upper()[:12],
                    "time":     time_ago,
                    "severity": severity,
                    "title":    title[:120],
                    "url":      a.get("url", ""),
                    "tags":     _extract_tags(title),
                    "tickers":  tickers_mentioned,
                })

                if len(articles) >= max_articles:
                    break

            time.sleep(0.5)

        except Exception as e:
            print(f"[NEWS] Query '{query}' failed: {e}")

    _news_cache["data"]       = articles
    _news_cache["fetched_at"] = datetime.now()
    print(f"[NEWS] Loaded {len(articles)} live articles")
    return articles[:max_articles]


def _extract_tags(text: str) -> list[str]:
    tag_map = {
        "CHINA":        ["china", "chinese", "beijing", "prc", "pla"],
        "RUSSIA":       ["russia", "russian", "kremlin", "moscow", "rostec"],
        "NATO":         ["nato", "alliance"],
        "SANCTIONS":    ["sanction", "ofac", "restrict", "ban"],
        "DRONES":       ["drone", "uav", "unmanned"],
        "SEMICONDUCTOR":["chip", "semiconductor", "tsmc"],
        "TAIWAN":       ["taiwan", "strait"],
        "PENTAGON":     ["pentagon", "dod", "defense department"],
        "CONTRACT":     ["contract", "award", "billion"],
        "UKRAINE":      ["ukraine", "ukrainian"],
        "INDIA":        ["india", "indian", "modi", "hal", "drdo"],
        "ISRAEL":       ["israel", "israeli", "idf", "elbit", "rafael"],
        "IRAN":         ["iran", "iranian", "irgc", "tehran"],
        "FRANCE":       ["france", "french", "airbus", "safran", "thales"],
        "UK":           ["united kingdom", "british", "bae systems", "rolls-royce"],
        "GERMANY":      ["germany", "german", "rheinmetall", "bundeswehr"],
        "PAKISTAN":     ["pakistan", "pakistani", "paf"],
        "NORTH KOREA":  ["north korea", "dprk", "pyongyang"],
        "TURKEY":       ["turkey", "turkish", "bayraktar", "aselsan"],
        "JAPAN":        ["japan", "japanese", "mitsubishi", "kawasaki"],
        "SOUTH KOREA":  ["south korea", "korean", "hanwha", "lg defense"],
        "AUSTRALIA":    ["australia", "australian", "asx defense"],
        "BRAZIL":       ["brazil", "brazilian", "embraer"],
        "SAUDI":        ["saudi", "ksa", "aramco defense"],
    }
    text_lower = text.lower()
    return [tag for tag, keywords in tag_map.items()
            if any(kw in text_lower for kw in keywords)][:5]


# ── SEC EDGAR (Real 10-K Filings) ─────────────────────────────
EDGAR_HEADERS = {"User-Agent": "SENTINEL geopolitical-intelligence@sentinel.ai"}
_edgar_cache  = {}

# ── EXPANDED DEFENSE UNIVERSE ─────────────────────────────────
# US-listed tickers with CIK numbers for SEC EDGAR
DEFENSE_TICKERS = {
    # ── UNITED STATES ──────────────────────────────────────────
    "LMT":  "0000936468",   # Lockheed Martin
    "RTX":  "0000101829",   # RTX Corp (Raytheon)
    "NOC":  "0001133421",   # Northrop Grumman
    "GD":   "0000040533",   # General Dynamics
    "BA":   "0000012927",   # Boeing
    "KTOS": "0001069258",   # Kratos Defense
    "AVAV": "0001134932",   # AeroVironment
    "PLTR": "0001321655",   # Palantir Technologies
    "HII":  "0001501585",   # Huntington Ingalls Industries
    "LHX":  "0001126328",   # L3Harris Technologies
    "TXT":  "0000217346",   # Textron (Bell, Cessna)
    "LDOS": "0001336920",   # Leidos Holdings
    "SAIC": "0001336920",   # Science Applications International
    "BAH":  "0001443646",   # Booz Allen Hamilton
    "BWXT": "0001486703",   # BWX Technologies (nuclear)
    # ── ISRAEL ─────────────────────────────────────────────────
    "ESLT": "0001060349",   # Elbit Systems (NASDAQ-listed)
    # ── INDIA (US-listed ADRs or direct) ───────────────────────
    # HAL, BEL are NSE-listed; no EDGAR CIK but tracked via yfinance suffix
}

# All tickers tracked for stock price and risk scoring (including non-US)
ALL_DEFENSE_TICKERS = list(DEFENSE_TICKERS.keys()) + [
    # ── UNITED STATES (additional) ─────────────────────────────
    "DRS",      # Leonardo DRS
    "AXON",     # Axon Enterprise (law enforcement tech)
    "CACI",     # CACI International
    "MANT",     # ManTech International
    # ── UNITED KINGDOM ─────────────────────────────────────────
    "BA.L",     # BAE Systems (LSE)
    "RR.L",     # Rolls-Royce (LSE)
    "COBR.L",   # Cobham (LSE)
    "QQ.L",     # QinetiQ (LSE)
    # ── FRANCE ─────────────────────────────────────────────────
    "AIR.PA",   # Airbus SE (Euronext Paris)
    "SAF.PA",   # Safran SA (Euronext Paris)
    "HO.PA",    # Thales SA (Euronext Paris)
    "DGA.PA",   # MBDA parent — Dassault Aviation
    # ── GERMANY ────────────────────────────────────────────────
    "RHM.DE",   # Rheinmetall AG (XETRA)
    "HEN3.DE",  # Hensoldt AG (XETRA)
    "AIR.DE",   # Airbus (XETRA mirror)
    # ── ITALY ──────────────────────────────────────────────────
    "LDO.MI",   # Leonardo SpA (Borsa Italiana)
    # ── SWEDEN ─────────────────────────────────────────────────
    "SAAB-B.ST",# Saab AB (Stockholm)
    # ── SPAIN ──────────────────────────────────────────────────
    "INDRA.MC", # Indra Sistemas (Madrid)
    # ── ISRAEL ─────────────────────────────────────────────────
    "ESLT",     # Elbit Systems (NASDAQ)
    # ── INDIA ──────────────────────────────────────────────────
    "HAL.NS",   # Hindustan Aeronautics Ltd (NSE)
    "BEL.NS",   # Bharat Electronics Ltd (NSE)
    "BHEL.NS",  # Bharat Heavy Electricals (NSE)
    "DRDO.NS",  # DRDO-adjacent: Solar Industries India (NSE) — SOL.NS
    "SOL.NS",   # Solar Industries (explosives/munitions, NSE)
    "ASTRA.NS", # Astra Microwave Products (NSE)
    # ── SOUTH KOREA ────────────────────────────────────────────
    "010140.KS",# Samsung Techwin / Hanwha Aerospace (KRX)
    "047810.KS",# Korea Aerospace Industries (KRX)
    # ── JAPAN ──────────────────────────────────────────────────
    "7011.T",   # Mitsubishi Heavy Industries (TSE)
    "7012.T",   # Kawasaki Heavy Industries (TSE)
    "6952.T",   # Fujitsu (defense systems, TSE)
    # ── TURKEY ─────────────────────────────────────────────────
    "ASELS.IS", # Aselsan (BIST)
    "ROKET.IS", # Roketsan — private, no listing
    # ── BRAZIL ─────────────────────────────────────────────────
    "EMBR3.SA", # Embraer SA (B3 São Paulo)
    # ── AUSTRALIA ──────────────────────────────────────────────
    "EOS.AX",   # Electro Optic Systems (ASX)
    "BDR.AX",   # Bravura — defense tech (ASX)
]


def fetch_sec_filing(ticker: str, max_chars: int = 3000) -> dict:
    if ticker in _edgar_cache:
        return _edgar_cache[ticker]

    cik = DEFENSE_TICKERS.get(ticker)
    if not cik:
        return {}

    try:
        url  = f"https://data.sec.gov/submissions/CIK{cik}.json"
        resp = requests.get(url, headers=EDGAR_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        filings = data.get("filings", {}).get("recent", {})
        forms   = filings.get("form", [])
        dates   = filings.get("filingDate", [])
        accnums = filings.get("accessionNumber", [])

        for i, form in enumerate(forms):
            if form == "10-K":
                accession = accnums[i].replace("-", "")
                date      = dates[i]

                result = {
                    "ticker":       ticker,
                    "filing_type":  "10-K",
                    "filing_date":  date,
                    "company":      data.get("name", ticker),
                    "description":  f"{data.get('name', ticker)} annual report filed {date}. "
                                    f"SIC: {data.get('sic', 'N/A')} — {data.get('sicDescription', '')}. "
                                    f"Employees: {data.get('ein', 'N/A')}.",
                    "source":       "SEC EDGAR 10-K",
                    "url":          f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K"
                }
                _edgar_cache[ticker] = result
                return result

    except Exception as e:
        print(f"[EDGAR] Error fetching {ticker}: {e}")

    return {}

def fetch_all_sec_filings() -> list[dict]:
    print("[EDGAR] Fetching SEC 10-K filings...")
    results = []
    for ticker in DEFENSE_TICKERS:
        filing = fetch_sec_filing(ticker)
        if filing:
            results.append(filing)
            time.sleep(0.3)
    print(f"[EDGAR] Loaded {len(results)} SEC filings")
    return results


# ── FEDERAL REGISTER (Real Defense Procurement) ───────────────
_fed_cache = {"data": [], "fetched_at": None}

def fetch_federal_register_notices(max_results: int = 10) -> list[dict]:
    global _fed_cache

    if _fed_cache["fetched_at"] and \
       (datetime.now() - _fed_cache["fetched_at"]).seconds < 3600 and \
       _fed_cache["data"]:
        return _fed_cache["data"][:max_results]

    print("[FED-REG] Fetching defense procurement notices...")
    try:
        resp = requests.get(
            "https://www.federalregister.gov/api/v1/documents.json",
            params={
                "conditions[term]":    "defense procurement weapons systems",
                "conditions[type][]":  "Notice",
                "per_page":            max_results,
                "order":               "newest",
                "fields[]": [
                    "title", "publication_date", "abstract",
                    "agencies", "document_number"
                ]
            },
            timeout=15
        )
        data = resp.json()

        results = []
        for doc in data.get("results", []):
            agencies = [a.get("name","") for a in doc.get("agencies", [])]
            results.append({
                "title":   doc.get("title", "")[:150],
                "date":    doc.get("publication_date", ""),
                "abstract": doc.get("abstract", "")[:300] if doc.get("abstract") else "",
                "agencies": agencies[:2],
                "source":  "Federal Register",
                "url":     f"https://www.federalregister.gov/documents/{doc.get('document_number','')}"
            })

        _fed_cache["data"]       = results
        _fed_cache["fetched_at"] = datetime.now()
        print(f"[FED-REG] Loaded {len(results)} procurement notices")
        return results

    except Exception as e:
        print(f"[FED-REG] Error: {e}")
        return []


# ── Combined Context Builder ───────────────────────────────────
def build_real_context(query: str) -> str:
    context_parts = []

    filings = fetch_all_sec_filings()
    query_lower = query.lower()
    for f in filings:
        if any(w in query_lower for w in [
            f["ticker"].lower(),
            f["company"].lower().split()[0],
            "defense", "military", "stock"
        ]):
            context_parts.append(
                f"[SEC 10-K — {f['ticker']} — {f['filing_date']}]\n{f['description']}"
            )

    notices = fetch_federal_register_notices()
    for n in notices[:3]:
        context_parts.append(
            f"[Federal Register — {n['date']}]\n{n['title']}\n{n['abstract']}"
        )

    return "\n\n".join(context_parts[:8])
