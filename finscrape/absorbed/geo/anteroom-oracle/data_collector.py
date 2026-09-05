"""
ZAI World Model — Data Collector
by Zawwar (github.com/Zawwarsami16)

This script downloads historical financial data going back to 1871.
Sources: Federal Reserve (FRED), Yahoo Finance, CoinGecko, World Bank.
Run this once to build your local database, then it auto-updates.

How it works:
1. Downloads all historical CSVs and saves them locally
2. Keeps a live/latest.json that refreshes every few minutes
3. Everything stored on disk — no cloud, no subscriptions, all free
"""

import os
import time
import json
import requests
import pandas as pd
from datetime import datetime
from config import DATA_PATH, DATASETS, HISTORY_FROM_YEAR, UPDATE_INTERVAL

# ================================================================
# SETUP — creates folder structure on first run
# ================================================================
def setup_folders():
    folders = [
        DATA_PATH,
        f"{DATA_PATH}/historical",
        f"{DATA_PATH}/live",
        f"{DATA_PATH}/patterns",
        f"{DATA_PATH}/predictions",
        f"{DATA_PATH}/news",
        f"{DATA_PATH}/logs",
    ]
    for f in folders:
        os.makedirs(f, exist_ok=True)
    print(f"✅ Storage ready: {DATA_PATH}")


# ================================================================
# FRED — Federal Reserve Economic Data
# Free, no API key needed, goes back to the 1800s for some series
# Best source for: inflation, GDP, interest rates, unemployment
# ================================================================
def download_fred_data(series_id, name, start_year=None):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

    try:
        print(f"  📥 {name} (FRED)...")
        df = pd.read_csv(url)

        # Find the date column — FRED uses "DATE"
        date_col = None
        for col in df.columns:
            if "date" in col.lower() or col == df.columns[0]:
                date_col = col
                break

        if date_col is None:
            raise Exception("No date column found")

        df = df.rename(columns={date_col: "date", df.columns[-1]: "value"})
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        if start_year:
            df = df[df["date"].dt.year >= start_year]

        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df["source"] = "FRED"
        df["series"] = name

        path = f"{DATA_PATH}/historical/{name}.csv"
        df.to_csv(path, index=False)
        print(f"  ✅ {name}: {len(df)} records ({df['date'].min().year}–{df['date'].max().year})")
        return df

    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return None


# ================================================================
# YAHOO FINANCE — via yfinance library
# Free, covers stocks, ETFs, commodities, indices
# Best for: S&P500, Nasdaq, Gold, Oil, VIX
# ================================================================
def download_yahoo_data(ticker, name, start_year=None):
    try:
        import yfinance as yf
    except ImportError:
        import subprocess, sys
        print(f"  Installing yfinance...")
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "yfinance", "--break-system-packages", "-q"])
        import yfinance as yf

    safe_year = max(start_year or 1970, 1970)
    start_str = f"{safe_year}-01-01"

    try:
        print(f"  📥 {name} ({ticker}) (Yahoo)...")
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(start=start_str, interval="1d", auto_adjust=True)

        if df.empty:
            print(f"  ❌ {name}: no data returned")
            return None

        df = df.reset_index()
        df = df.rename(columns={"Date": "date", "Close": "value"})
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df = df[["date", "value"]].dropna()
        df["source"] = "Yahoo"
        df["series"] = name

        path = f"{DATA_PATH}/historical/{name}.csv"
        df.to_csv(path, index=False)
        print(f"  ✅ {name}: {len(df)} records ({df['date'].min().year}–{df['date'].max().year})")
        return df

    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return None


# ================================================================
# COINGECKO — Free crypto historical data
# No API key for basic use, covers Bitcoin from 2010
# ================================================================
def download_coingecko_data(coin_id, name):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "max"}

    try:
        print(f"  📥 {name} (CoinGecko)...")
        r = requests.get(url, params=params, headers=headers, timeout=60)

        if r.status_code == 429:
            print(f"  ⏳ Rate limited — waiting 60s...")
            time.sleep(60)
            r = requests.get(url, params=params, headers=headers, timeout=60)

        data = r.json()
        prices = data.get("prices", [])

        if not prices:
            print(f"  ❌ {name}: empty response")
            return None

        df = pd.DataFrame(prices, columns=["timestamp", "value"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df[["date", "value"]].dropna()
        df["source"] = "CoinGecko"
        df["series"] = name

        path = f"{DATA_PATH}/historical/{name}.csv"
        df.to_csv(path, index=False)
        print(f"  ✅ {name}: {len(df)} records ({df['date'].min().year}–{df['date'].max().year})")
        return df

    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return None


# ================================================================
# WORLD BANK — Global economic data
# Free API, covers GDP and macro data for all countries
# ================================================================
def download_world_bank_data(indicator, country, name):
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    params = {"format": "json", "per_page": 10000, "mrv": 100}

    try:
        print(f"  📥 {name} (World Bank)...")
        r = requests.get(url, params=params, timeout=30)
        data = r.json()

        if len(data) < 2:
            return None

        records = data[1]
        rows = []
        for rec in records:
            if rec.get("value") is not None:
                rows.append({
                    "date": pd.to_datetime(f"{rec['date']}-01-01"),
                    "value": float(rec["value"]),
                    "source": "WorldBank",
                    "series": name
                })

        df = pd.DataFrame(rows).sort_values("date")
        path = f"{DATA_PATH}/historical/{name}.csv"
        df.to_csv(path, index=False)
        print(f"  ✅ {name}: {len(df)} records ({df['date'].min().year}–{df['date'].max().year})")
        return df

    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return None


# ================================================================
# DOWNLOAD EVERYTHING
# ================================================================
def download_all_historical():
    print("\n" + "="*60)
    print("📚 DOWNLOADING HISTORICAL DATA")
    print("="*60)
    print(f"Storage: {DATA_PATH}")
    print(f"Starting from: {HISTORY_FROM_YEAR}\n")

    results = {}

    # --- FRED (Federal Reserve) ---
    print("🏦 Federal Reserve (FRED):")
    if DATASETS.get("inflation"):
        results["inflation"] = download_fred_data("CPIAUCNS", "inflation", 1871)
        time.sleep(1)
    if DATASETS.get("interest"):
        results["interest"] = download_fred_data("FEDFUNDS", "interest_rate", 1954)
        time.sleep(1)
    if DATASETS.get("unemployment"):
        results["unemployment"] = download_fred_data("UNRATE", "unemployment", 1948)
        time.sleep(1)
    if DATASETS.get("gdp"):
        results["gdp"] = download_fred_data("GDP", "gdp_usa", 1947)
        time.sleep(1)
    if DATASETS.get("bonds"):
        results["bonds"] = download_fred_data("GS10", "treasury_10y", 1962)
        time.sleep(1)
    results["m2"] = download_fred_data("M2SL", "money_supply_m2", 1959)
    time.sleep(1)
    results["sentiment"] = download_fred_data("UMCSENT", "consumer_sentiment", 1952)
    time.sleep(1)

    # --- Yahoo Finance ---
    print("\n📈 Yahoo Finance:")
    if DATASETS.get("sp500"):
        results["sp500"] = download_yahoo_data("^GSPC", "sp500", 1970)
        time.sleep(2)
    if DATASETS.get("nasdaq"):
        results["nasdaq"] = download_yahoo_data("^IXIC", "nasdaq", 1971)
        time.sleep(2)
    if DATASETS.get("gold"):
        results["gold"] = download_yahoo_data("GC=F", "gold", 1970)
        time.sleep(2)
    if DATASETS.get("oil"):
        results["oil"] = download_yahoo_data("CL=F", "oil_crude", 1983)
        time.sleep(2)
    if DATASETS.get("vix"):
        results["vix"] = download_yahoo_data("^VIX", "vix_fear", 1990)
        time.sleep(2)
    if DATASETS.get("copper"):
        results["copper"] = download_yahoo_data("HG=F", "copper", 1988)
        time.sleep(2)

    # --- CoinGecko ---
    print("\n🪙 CoinGecko:")
    if DATASETS.get("bitcoin"):
        results["bitcoin"] = download_coingecko_data("bitcoin", "bitcoin")
        time.sleep(3)
    results["ethereum"] = download_coingecko_data("ethereum", "ethereum")
    time.sleep(3)

    # --- World Bank ---
    print("\n🌍 World Bank:")
    results["world_gdp"] = download_world_bank_data("NY.GDP.MKTP.CD", "WLD", "world_gdp")
    time.sleep(2)
    results["china_gdp"] = download_world_bank_data("NY.GDP.MKTP.CD", "CHN", "china_gdp")
    time.sleep(2)

    # Summary
    success = sum(1 for v in results.values() if v is not None)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"✅ Done: {success}/{total} datasets downloaded")
    print(f"📁 Saved to: {DATA_PATH}/historical/")
    print(f"{'='*60}")

    log = {
        "downloaded_at": datetime.now().isoformat(),
        "datasets": {k: (v is not None) for k, v in results.items()}
    }
    with open(f"{DATA_PATH}/logs/download_log.json", "w") as f:
        json.dump(log, f, indent=2)

    return results


# ================================================================
# LIVE DATA — runs every UPDATE_INTERVAL seconds
# Keeps prices fresh without re-downloading full history
# ================================================================
def update_live_data():
    print(f"\n🔄 Live update: {datetime.now().strftime('%H:%M:%S')}")

    live_data = {}

    # Market tickers to keep live
    tickers = {
        "sp500":  "^GSPC",
        "nasdaq": "^IXIC",
        "gold":   "GC=F",
        "oil":    "CL=F",
        "vix":    "^VIX",
    }

    for name, ticker in tickers.items():
        try:
            import yfinance as yf
            df = yf.Ticker(ticker).history(period="5d", interval="1d")
            if not df.empty:
                latest = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2]) if len(df) > 1 else latest
                change_pct = ((latest - prev) / prev) * 100
                live_data[name] = {
                    "price": latest,
                    "change_pct": round(change_pct, 2),
                    "updated": datetime.now().isoformat()
                }
        except:
            pass

    # Bitcoin and Ethereum via CoinGecko
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum", "vs_currencies": "usd",
                    "include_24hr_change": "true"},
            timeout=10
        )
        data = r.json()
        live_data["bitcoin"] = {
            "price": data["bitcoin"]["usd"],
            "change_pct": round(data["bitcoin"].get("usd_24h_change", 0), 2),
            "updated": datetime.now().isoformat()
        }
        live_data["ethereum"] = {
            "price": data["ethereum"]["usd"],
            "change_pct": round(data["ethereum"].get("usd_24h_change", 0), 2),
            "updated": datetime.now().isoformat()
        }
    except:
        pass

    path = f"{DATA_PATH}/live/latest.json"
    with open(path, "w") as f:
        json.dump(live_data, f, indent=2)

    return live_data


def check_existing_data():
    historical_path = f"{DATA_PATH}/historical"
    if not os.path.exists(historical_path):
        return []
    return [f.replace(".csv", "") for f in os.listdir(historical_path) if f.endswith(".csv")]


# ================================================================
# RUN
# ================================================================
if __name__ == "__main__":
    setup_folders()

    existing = check_existing_data()

    if existing:
        print(f"\n📂 Found existing data: {', '.join(existing)}")
        ans = input("Re-download everything? (y/n): ").strip().lower()
        if ans == "y":
            download_all_historical()
    else:
        print("\n🆕 First run — downloading all historical data...")
        download_all_historical()

    print("\n🔄 Starting live updates (Ctrl+C to stop)...\n")

    while True:
        try:
            live = update_live_data()
            for name, d in live.items():
                arrow = "↑" if d["change_pct"] > 0 else "↓"
                print(f"  {name:<12} ${d['price']:>12,.2f}  {arrow} {abs(d['change_pct']):.2f}%")
            print(f"  Next update in {UPDATE_INTERVAL}s...")
            time.sleep(UPDATE_INTERVAL)
        except KeyboardInterrupt:
            print("\n👋 Live updates stopped.")
            break
