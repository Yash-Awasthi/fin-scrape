"""
finance_client.py — Oil, gold, and defense-stock market trackers.

Data sources
------------
1. yfinance — free Yahoo Finance wrapper (Brent Crude, Gold, defense stocks).
2. Alpha Vantage API — real-time intraday quotes (optional, more granular).

Key function
------------
fetch_market_data() -> pd.DataFrame
    Columns: timestamp, symbol, name, price, pct_change_24h,
             rolling_mean_30d, z_score
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

RAW_DATA_DIR = Path("data/raw/finance")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Tickers we care about
TICKERS = {
    # Commodities
    "BZ=F":  "Brent Crude Oil Futures",
    "CL=F":  "WTI Crude Oil Futures",
    "GC=F":  "Gold Futures",

    # Major defense contractors
    "LMT":   "Lockheed Martin",
    "RTX":   "Raytheon Technologies",
    "NOC":   "Northrop Grumman",
    "GD":    "General Dynamics",
    "BA":    "Boeing",
    "LHX":   "L3Harris Technologies",

    # Volatility & safe-haven
    "^VIX":  "CBOE Volatility Index",
    "TLT":   "iShares 20+ Year Treasury Bond ETF",
}

# How many trading days of history to pull for baseline statistics
LOOKBACK_DAYS = 60


# ---------------------------------------------------------------------------
# yfinance-based ingestion
# ---------------------------------------------------------------------------
def fetch_market_data(tickers: dict | None = None,
                      lookback_days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """
    Pull historical close prices via yfinance for the configured tickers.
    Compute:
        - 24 h % change
        - 30-day rolling mean
        - Z-score vs rolling window

    Returns
    -------
    pd.DataFrame with one row per ticker containing the latest stats.
    """
    try:
        import yfinance as yf
    except ImportError:
        print("[finance_client] yfinance not installed. Run: pip install yfinance")
        return pd.DataFrame()

    if tickers is None:
        tickers = TICKERS

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)

    records = []
    for symbol, name in tickers.items():
        try:
            ticker_obj = yf.Ticker(symbol)
            hist = ticker_obj.history(start=start.strftime("%Y-%m-%d"),
                                     end=end.strftime("%Y-%m-%d"))
            if hist.empty:
                print(f"[finance_client] No data for {symbol}")
                continue

            # Persist raw
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            raw_path = RAW_DATA_DIR / f"{symbol.replace('=', '').replace('^', '')}_{ts}.json"
            raw_path.write_text(hist.tail(5).to_json(date_format="iso", indent=2), encoding="utf-8")

            latest_close = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2] if len(hist) >= 2 else latest_close

            pct_change_24h = ((latest_close - prev_close) / prev_close) * 100

            rolling_mean = hist["Close"].rolling(window=30, min_periods=5).mean().iloc[-1]
            rolling_std = hist["Close"].rolling(window=30, min_periods=5).std().iloc[-1]

            z_score = ((latest_close - rolling_mean) / rolling_std
                       if rolling_std and rolling_std > 0 else 0.0)

            records.append({
                "timestamp":       end.isoformat(),
                "symbol":          symbol,
                "name":            name,
                "price":           round(latest_close, 2),
                "pct_change_24h":  round(pct_change_24h, 4),
                "rolling_mean_30d": round(rolling_mean, 2),
                "z_score":         round(z_score, 4),
            })

        except Exception as exc:
            print(f"[finance_client] Error fetching {symbol}: {exc}")

    df = pd.DataFrame(records)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


# ---------------------------------------------------------------------------
# Alpha Vantage — intraday quotes (optional, higher granularity)
# ---------------------------------------------------------------------------
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

def fetch_alpha_vantage_intraday(symbol: str,
                                  interval: str = "60min",
                                  max_retries: int = 3) -> pd.DataFrame:
    """
    Pull intraday time-series from Alpha Vantage for a single ticker.
    """
    if not ALPHA_VANTAGE_API_KEY:
        print("[finance_client] ALPHA_VANTAGE_API_KEY not set — skipping.")
        return pd.DataFrame()

    params = {
        "function":   "TIME_SERIES_INTRADAY",
        "symbol":     symbol,
        "interval":   interval,
        "apikey":     ALPHA_VANTAGE_API_KEY,
        "outputsize": "compact",
        "datatype":   "json",
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=20)
            resp.raise_for_status()
            payload = resp.json()

            ts_key = f"Time Series ({interval})"
            ts_data = payload.get(ts_key, {})
            if not ts_data:
                print(f"[finance_client] No intraday data for {symbol}")
                return pd.DataFrame()

            rows = []
            for dt_str, ohlcv in ts_data.items():
                rows.append({
                    "timestamp": dt_str,
                    "open":      float(ohlcv["1. open"]),
                    "high":      float(ohlcv["2. high"]),
                    "low":       float(ohlcv["3. low"]),
                    "close":     float(ohlcv["4. close"]),
                    "volume":    int(ohlcv["5. volume"]),
                })

            df = pd.DataFrame(rows)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["symbol"] = symbol
            return df.sort_values("timestamp").reset_index(drop=True)

        except requests.RequestException as exc:
            print(f"[finance_client] Alpha Vantage attempt {attempt}/{max_retries}: {exc}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Convenience: defense-sector anomaly score
# ---------------------------------------------------------------------------
def compute_defense_anomaly(df: pd.DataFrame | None = None) -> dict:
    """
    From the market data DataFrame, compute aggregate anomaly indicators:
        - avg_defense_z   : mean z-score across defense stocks
        - oil_z           : Brent Crude z-score
        - gold_z          : Gold z-score
        - vix_z           : VIX z-score
    """
    if df is None:
        df = fetch_market_data()

    if df.empty:
        return {"avg_defense_z": 0, "oil_z": 0, "gold_z": 0, "vix_z": 0}

    defense_symbols = {"LMT", "RTX", "NOC", "GD", "BA", "LHX"}
    defense_rows = df[df["symbol"].isin(defense_symbols)]
    avg_defense_z = defense_rows["z_score"].mean() if not defense_rows.empty else 0.0

    def _z(sym):
        row = df[df["symbol"] == sym]
        return row["z_score"].iloc[0] if not row.empty else 0.0

    return {
        "avg_defense_z": round(avg_defense_z, 4),
        "oil_z":         round(_z("BZ=F"), 4),
        "gold_z":        round(_z("GC=F"), 4),
        "vix_z":         round(_z("^VIX"), 4),
    }


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Market Data Fetch ===")
    df = fetch_market_data()
    if not df.empty:
        print(df[["symbol", "name", "price", "pct_change_24h", "z_score"]].to_string(index=False))
        print("\n=== Defense Anomaly Scores ===")
        anomaly = compute_defense_anomaly(df)
        for k, v in anomaly.items():
            print(f"  {k:20s}: {v:+.4f}")
    else:
        print("No market data available.")
