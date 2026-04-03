import requests
from bs4 import BeautifulSoup
import re
import yfinance as yf
import math
import datetime
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from zoneinfo import ZoneInfo  # for IST if needed

MAX_WORDS = 700
TILL_PARA = 25
PRINT_TILL_THIS_AGE = 2   # final display filter (hours)
AGE_LIMIT = 4             # looser during URL collection (Moneycontrol has good "ago")

session = requests.Session()
retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# -----------------------------
# TIME PARSER (works great on Moneycontrol)
# -----------------------------
def parse_time_ago(time_str: str) -> float:
    if not time_str:
        return 999.0
    t = time_str.lower().strip()
    if any(w in t for w in ["just now", "today", "minutes ago", "min ago", "moments ago"]):
        return 0.0
    m = re.search(r'(\d+)\s*(min|m|minutes?)', t)
    if m:
        return int(m.group(1)) / 60.0
    h = re.search(r'(\d+)\s*(h|hr|hours?|hrs?)', t)
    if h:
        return float(h.group(1))
    d = re.search(r'(\d+)\s*(d|day|days?|yesterday)', t)
    if d:
        return float(d.group(1)) * 24.0 if "yesterday" not in t else 24.0
    return 999.0

# -----------------------------
# COLLECT MONEYCONTROL NEWS URLS
# -----------------------------
def collect_moneycontrol_news_urls(limit=60, max_hours_old=AGE_LIMIT):
    start_urls = [
        "https://www.moneycontrol.com/news/business/stocks/",
        "https://www.moneycontrol.com/news/business/markets/",
        "https://www.moneycontrol.com/news/tags/companies.html",
        "https://www.moneycontrol.com/editors-picks/companies/",
        "https://www.moneycontrol.com/news/business/companies/",
        "https://www.moneycontrol.com/news/business/",
    ]

    collected = []
    seen = set()

    for page_url in start_urls:
        try:
            r = session.get(page_url, headers=headers, timeout=15)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  [WARN] Could not fetch {page_url}: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        all_links = soup.find_all("a", href=True)

        for a in all_links:
            link = a["href"]
            if link.startswith("/"):
                link = "https://www.moneycontrol.com" + link
            link = link.split("?")[0].rstrip("/")
            
            if link in seen:
                continue

            # Article filter
            if not link.endswith(".html"):
                continue
            if not any(p in link for p in [
                "/news/business/stocks/",
                "/news/business/markets/",
                "/news/business/companies/",
                "/editors-picks/",
                "/news/business/moneycontrol-research/",
                "/news/business/"
            ]):
                continue

            # reject known non-article substrings (tag/podcast/gallery/liveblog/etc)
            if any(x in link for x in ["/video/", "/gallery/", "/liveblog/","liveblog", "/mutual-funds/", "/ipo/", "/tags/", "/podcast/"]):
                continue
            
            slug = link.split("/")[-1].replace(".html", "")
            if len(slug) < 20:   # real articles have long slugs; tag pages are short
                continue

            # Time heuristic near link (Moneycontrol often has it)
            parent = a.find_parent(["li", "div", "span", "p"])
            time_str = ""
            if parent:
                text_nearby = parent.get_text(strip=True)
                time_match = re.search(
                    r'(\d+\s*(?:min|minute|hour|hr)s?\s*ago|just now|yesterday|\d+\s*(?:min|hrs?|days?)\s*ago)',
                    text_nearby, re.IGNORECASE
                )
                if time_match:
                    time_str = time_match.group(0)

            hours_old = parse_time_ago(time_str)

            if hours_old <= max_hours_old or time_str == "":
                collected.append(link)
                seen.add(link)

        if len(collected) >= limit * 2:
            break

    collected = list(dict.fromkeys(collected))
    print(f"[INFO] Collected {len(collected)} unique Moneycontrol URLs")
    return collected[:limit]

# -----------------------------
# SCRAPE ARTICLE
# -----------------------------

def scrape_article(url):
    try:
        r = session.get(url, headers=headers, timeout=20)
        r.raise_for_status()
    except requests.exceptions.RequestException:
        return "", "", None, None

    soup = BeautifulSoup(r.text, "html.parser")

    # TITLE (robust fallbacks)
    title = ""
    for sel in [
        ("meta", {"property": "og:title"}),
        ("meta", {"name": "twitter:title"}),
    ]:
        meta = soup.find(sel[0], attrs=sel[1])
        if meta and meta.get("content"):
            title = meta["content"].strip()
            break
    if not title:
        h1 = soup.find(["h1"])
        title = h1.get_text(strip=True) if h1 else ""
    for suffix in [" | Moneycontrol", " - Moneycontrol", " | MC", " Moneycontrol News"]:
        title = title.replace(suffix, "").strip()

    # ARTICLE BODY — multiple fallbacks
    body_candidates = []
    # schema articleBody
    body_candidates += soup.select("div[itemprop='articleBody'] p")
    # common Moneycontrol container patterns (try class contains 'story'/'article'/'content')
    body_candidates += soup.select("div[class*='story'] p")
    body_candidates += soup.select("div[class*='article'] p")
    body_candidates += soup.select("div[class*='content'] p")
    # straight <article> fallback
    body_candidates += soup.find_all("article")
    # last resort: all <p> on page
    if not body_candidates:
        body_candidates = soup.find_all("p")

    # build text from first meaningful paragraphs
    paras = []
    for p in body_candidates:
        txt = p.get_text(" ", strip=True)
        if len(txt) > 30:           # lower threshold, less aggressive
            paras.append(txt)
        if len(paras) >= TILL_PARA:
            break

    article_text = " ".join(paras)
    # trim and remove junk
    junk = ["Continue reading", "Sign up", "Advertisement", "Read more", "Also read", "Disclaimer"]
    for phrase in junk:
        article_text = article_text.split(phrase)[0]
    article_text = " ".join(article_text.split()[:MAX_WORDS])

    if len(article_text.strip()) < 120:   # small drop to avoid false negatives
        return "", "", None, None

    # PUB DATE: try meta, ld+json, or visible date string
    age_hours = None
    pub_str = None
    meta_date = soup.find("meta", attrs={"property": "article:published_time"}) or soup.find("meta", attrs={"name":"ptime"})
    if meta_date and meta_date.get("content"):
        pub_str = meta_date["content"]
    if not pub_str:
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                if isinstance(data, dict):
                    pub_str = data.get("datePublished") or data.get("dateModified")
                if pub_str:
                    break
            except:
                pass
    # last resort: regex search for lines like "March 12, 2026 / 12:26 IST"
    if not pub_str:
        m = re.search(r'[A-Z][a-z]+ \d{1,2}, \s*\d{4}.*?IST', r.text)
        if m:
            pub_str = m.group(0)

    if pub_str:
        try:
            dt_str = pub_str.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            now_ist = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
            age_hours = (now_ist - dt).total_seconds() / 3600
        except:
            pass

    return title, article_text, soup, round(age_hours, 1) if age_hours is not None else None

# -----------------------------
# TICKER EXTRACTION (tuned a bit for MC patterns)
# -----------------------------
def extract_tickers(text, soup):
    if soup is None:
        return []

    text_tickers = set()
    # Classic (RELIANCE), (TCS), (NIFTY 50)
    matches = re.findall(r'\(([A-Z]{1,5}(?:\s*[A-Z0-9]+)?)\)', text)
    # ^NSEI, NIFTY=F etc.
    indexes = re.findall(r'\^[A-Z]{2,5}\b', text)
    futures = re.findall(r'\b[A-Z]{1,5}=F\b', text)

    for m in matches:
        clean = m.upper().replace(" ", "").replace("&", "")
        if 2 <= len(clean) <= 6:
            text_tickers.add(clean)
    for i in indexes + futures:
        text_tickers.add(i)

    # Optional extra: all-caps near price/%
    extra = re.findall(r'\b([A-Z]{3,6})\b(?=.*(?:₹|Rs|shares|stock|CMP|rose|fell|up|down|gain|loss))', text)
    for e in extra:
        if 3 <= len(e) <= 6:
            text_tickers.add(e)

    BLACKLIST = {
        "CEO", "CFO", "MD", "ETF", "GDP", "EPS", "IPO", "RBI", "SEBI", "GST", "NSE", "BSE",
        "FII", "DII", "QIP", "UK", "US", "ET", "AI", "ON", "IN", "AT", "BY", "IT"
    }

    valid = [t for t in text_tickers if t not in BLACKLIST]

    return list(dict.fromkeys(valid))

# -----------------------------
# MARKET DATA (.NS default)
# -----------------------------
def get_market_data(tickers):
    data = []
    if not tickers:
        return data

    tickers_ns = [t + ".NS" if not any(t.endswith(s) for s in (".NS", ".BO", "=F", "^")) else t for t in tickers]

    try:
        df = yf.download(
            tickers=" ".join(set(tickers_ns)),  # dedup
            period="5d",
            interval="1d",
            progress=False,
            threads=True
        )

        if df.empty or "Close" not in df.columns:
            return data

        for orig_t, ns_t in zip(tickers, tickers_ns):
            try:
                if len(tickers_ns) > 1 and ns_t in df["Close"].columns:
                    close = df["Close"][ns_t]
                else:
                    close = df["Close"]

                if len(close.dropna()) < 2:
                    continue

                price = float(close.iloc[-1])
                prev = float(close.iloc[-2])

                if math.isnan(price) or math.isnan(prev):
                    continue

                change = ((price - prev) / prev) * 100
                data.append({
                    "ticker": orig_t,
                    "price": round(price, 2),
                    "change_percent": round(change, 2)
                })
            except:
                continue
    except Exception as e:
        print(f"  [WARN] yfinance error: {e}")

    return data

# -----------------------------
# MAIN
# -----------------------------
def main():
    print("=" * 60)
    print("  Moneycontrol Stocks & Markets News Scraper")
    print("=" * 60)

    print("\n[STEP 1] Collecting article URLs...")
    urls = collect_moneycontrol_news_urls(limit=60, max_hours_old=AGE_LIMIT)

    if not urls:
        print("[ERROR] No URLs found. Moneycontrol layout may have changed.")
        return

    print(f"[INFO] Found {len(urls)} URLs to scrape\n")

    results = []
    skip_count = 0
    MAX_SKIPS = 5

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Scraping: {url}")

        try:
            title, text, soup, age_hours = scrape_article(url)
            if not title or not text:
                print("  [SKIP] Could not extract content.\n")
                skip_count += 1
                continue
            if age_hours is not None and age_hours > PRINT_TILL_THIS_AGE:
                print(f"  [SKIP] Too old ({age_hours:.1f}h)\n")
                skip_count += 1
                continue
        except Exception as e:
            print(f"  [ERROR] Scraping failed for {url}: {e}\n")
            skip_count += 1
            continue

        if skip_count >= MAX_SKIPS:
            print(f"[STOP] {MAX_SKIPS} consecutive skips — stopping early.\n")
            break

        age_str = f"{age_hours:.1f}h old" if age_hours is not None else "age unknown"

        print(f"  Title : {title}")
        print(f"  Age   : {age_str}")

        tickers = extract_tickers(text, soup)
        print(f"  Tickers found: {tickers if tickers else 'None'}")

        market_data = get_market_data(tickers) if tickers else []

        if market_data:
            for md in market_data:
                arrow = "▲" if md["change_percent"] >= 0 else "▼"
                print(f"  {md['ticker']:6s} ₹{md['price']:.2f}  {arrow} {md['change_percent']:+.2f}%")

        print(f"  Snippet: {text[:200]}...")
        print()

        results.append({
            "url": url,
            "title": title,
            "age_hours": age_hours,
            "tickers": tickers,
            "market_data": market_data,
            "text_snippet": text[:300]
        })

        skip_count = 0  # reset on success

    print("=" * 60)
    print(f"  Done. Successfully scraped {len(results)}/{len(urls)} articles.")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()