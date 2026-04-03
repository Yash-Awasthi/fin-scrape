import requests
from bs4 import BeautifulSoup
import re
import yfinance as yf
import math
import datetime
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

MAX_WORDS = 700
TILL_PARA = 25
PRINT_TILL_THIS_AGE = 2 #for main 
AGE_LIMIT = 1 

session = requests.Session()
retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# -----------------------------
# TIME PARSER
# -----------------------------
def parse_time_ago(time_str: str) -> float:
    if not time_str:
        return 999.0

    t = time_str.lower().strip()

    if any(w in t for w in ["just now", "today", "minutes ago", "min ago"]):
        return 0.0

    m = re.search(r'(\d+)\s*(min|m|minutes?)', t)
    if m:
        return int(m.group(1)) / 60.0

    h = re.search(r'(\d+)\s*(h|hr|hours?|hrs?)', t)
    if h:
        return float(h.group(1))

    d = re.search(r'(\d+)\s*(d|day|days?)', t)
    if d:
        return float(d.group(1)) * 24.0

    return 999.0

# -----------------------------
# COLLECT YAHOO NEWS URLS
# -----------------------------
def collect_yahoo_news_urls(limit=20, max_hours_old=AGE_LIMIT):
    urls_to_scrape = [
        "https://finance.yahoo.com/news/",
        "https://finance.yahoo.com/topic/stock-market-news/",
        "https://finance.yahoo.com/",
    ]

    collected = []
    seen = set()

    for page in urls_to_scrape:
        try:
            r = session.get(page, headers=headers, timeout=15)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  [WARN] Could not fetch {page}: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # Broad link sweep — grab ALL links ending in .html from yahoo finance news
        all_links = soup.find_all("a", href=True)

        for a in all_links:
            link = a["href"]

            if link.startswith("/"):
                link = "https://finance.yahoo.com" + link

            link = link.split("?")[0]

            if link in seen:
                continue

            if not link.endswith(".html"):
                continue

            if "finance.yahoo.com" not in link:
                continue

            if not any(p in link for p in ["/news/", "/video/"]):
                continue

            # Try to find time info nearby
            parent = a.find_parent()
            time_str = ""
            if parent:
                text_nearby = parent.get_text(strip=True)
                time_match = re.search(
                    r'(\d+\s*(?:min|minute|hour|hr|day)s?\s*ago|just now)',
                    text_nearby, re.IGNORECASE
                )
                if time_match:
                    time_str = time_match.group(0)

            hours_old = parse_time_ago(time_str)

            # If no time found, include anyway (let scraper filter by pub date)
            if hours_old <= max_hours_old or time_str == "":
                collected.append(link)
                seen.add(link)

        if len(collected) >= limit * 2:
            break

    collected = list(dict.fromkeys(collected))
    print(f"[INFO] Collected {len(collected)} unique URLs")
    return collected[:limit]

# -----------------------------
# SCRAPE ARTICLE
# -----------------------------
def scrape_article(url):
    try:
        r = session.get(url, headers=headers, timeout=15)
    except requests.exceptions.RequestException:
        return "", "", None, None

    if r.status_code != 200:
        return "", "", None, None

    soup = BeautifulSoup(r.text, "html.parser")

    # TITLE
    meta = soup.find("meta", attrs={"property": "og:title"})
    title = meta["content"] if meta and meta.get("content") else ""

    if not title:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

    title = re.sub(r'\s*[-|]\s*Yahoo.*$', '', title).strip()

    # ARTICLE TEXT
    article = soup.find("article") or soup
    paragraphs = article.find_all("p")

    selected = [
        p for p in paragraphs[:TILL_PARA]
        if len(p.get_text(strip=True)) > 40
    ]

    text = " ".join(p.get_text() for p in selected)

    junk_phrases = ["Continue reading", "Sign up", "Advertisement", "Read more", "Related stories"]
    for phrase in junk_phrases:
        text = text.split(phrase)[0]

    article_text = " ".join(text.split()[:MAX_WORDS])

    if len(article_text.strip()) < 150:
        return "", "", None, None

    # ARTICLE AGE
    age_hours = None
    pub_str = None

    meta_date = soup.find("meta", attrs={"property": "article:published_time"})
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
                    pub_str = data.get("datePublished")
                if pub_str:
                    break
            except Exception:
                pass

    if pub_str:
        try:
            dt = datetime.datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            age_hours = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds() / 3600
        except Exception:
            pass

    return title, article_text, soup, round(age_hours, 1) if age_hours is not None else None

# -----------------------------
# TICKER EXTRACTION
# -----------------------------
def extract_tickers(text, soup):
    if soup is None:
        return []

    text_tickers = set()
    matches = re.findall(r'\(([A-Z]{1,5})\)', text)
    futures = re.findall(r'\b[A-Z]{1,2}=F\b', text)
    indexes = re.findall(r'\^[A-Z]{2,5}\b', text)

    for m in matches:
        text_tickers.add(m)
    for f in futures:
        text_tickers.add(f)
    for i in indexes:
        text_tickers.add(i)

    meta_tickers = set()
    for script in soup.find_all("script"):
        if script.string and "hashtag" in script.string:
            m = re.search(r'"hashtag":"([^"]+)"', script.string)
            if m:
                tags = m.group(1).split(";")
                for t in tags:
                    if t.startswith("$"):
                        meta_tickers.add(t[1:].upper())

    BLACKLIST = {
        "CEO", "ETF", "GDP", "EPS", "AI", "RPO", "IEA", "UK", "US", "ET",
        "FREE", "GTA", "VI", "NYSEA", "SHRM", "ARR", "ON", "IN", "AT", "BY", "IT"
    }

    valid_tickers = []
    for t in (text_tickers | meta_tickers):
        if len(t) < 2 or len(t) > 5 or not t.isupper():
            continue
        if t in BLACKLIST:
            continue
        valid_tickers.append(t)

    return list(dict.fromkeys(valid_tickers))

# -----------------------------
# MARKET DATA
# -----------------------------
def get_market_data(tickers):
    data = []
    if not tickers:
        return data

    try:
        tickers = [t for t in tickers if isinstance(t, str) and t]
        df = yf.download(
            tickers=" ".join(tickers),
            period="2d",
            interval="1d",
            progress=False
        )

        if df is None or df.empty:
            return data

        if "Close" not in df.columns:
            return data

        for t in tickers:
            try:
                if len(tickers) > 1:
                    close = df["Close"][t]
                else:
                    close = df["Close"]

                if len(close) < 2:
                    continue

                price = float(close.iloc[-1])
                prev = float(close.iloc[-2])

                if math.isnan(price) or math.isnan(prev):
                    continue

                change = ((price - prev) / prev) * 100
                data.append({
                    "ticker": t,
                    "price": round(price, 2),
                    "change_percent": round(change, 2)
                })
            except Exception:
                continue

    except Exception as e:
        print(f"  [WARN] Market data error: {e}")

    return data

# -----------------------------
# MAIN — THIS WAS MISSING
# -----------------------------
def main():
    print("=" * 60)
    print("  Yahoo Finance News Scraper")
    print("=" * 60)

    print("\n[STEP 1] Collecting article URLs...")
    urls = collect_yahoo_news_urls(limit=50, max_hours_old=AGE_LIMIT)

    if not urls:
        print("[ERROR] No URLs found. Yahoo Finance may have changed its layout.")
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
                continue
            if age_hours is not None and age_hours > PRINT_TILL_THIS_AGE:
                print(f"  [SKIP] Too old ({age_hours:.1f}h)\n")
                skip_count += 1
                continue
        except Exception as e:
            print(f"  [ERROR] Scraping failed for {url}: {e}\n")
            continue
        if skip_count >= MAX_SKIPS:
            print(f"[STOP] {MAX_SKIPS} consecutive skips hit — stopping early.\n")
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
                print(f"  {md['ticker']:6s} ${md['price']:.2f}  {arrow} {md['change_percent']:+.2f}%")

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

    print("=" * 60)
    print(f"  Done. Successfully scraped {len(results)}/{len(urls)} articles.")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()