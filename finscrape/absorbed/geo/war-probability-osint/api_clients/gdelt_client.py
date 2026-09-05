"""
gdelt_client.py — Geopolitical news sentiment & event ingestion.

Data sources
------------
1. GDELT 2.0 DOC API  — full-text article search with tone/sentiment.
2. GDELT 2.0 GEO API  — geographic heat-map of event mentions.

Key function
------------
fetch_gdelt_articles() -> pd.DataFrame
    Columns: timestamp, title, source, url, tone, theme, locations, language
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RAW_DATA_DIR = Path("data/raw/gdelt")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# GDELT DOC API (free, no key required)
GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# Conflict-related search themes
CONFLICT_QUERIES = [
    "military escalation",
    "troop deployment",
    "missile strike",
    "naval blockade",
    "airspace closure",
    "diplomatic expulsion",
    "sanctions threat",
    "nuclear threat",
    "carrier strike group",
    "defense readiness",
]

# Country pairs we monitor for bilateral tension
COUNTRY_PAIRS = [
    ("United States", "Iran"),
    ("United States", "China"),
    ("United States", "Russia"),
    ("United States", "North Korea"),
    ("Israel", "Iran"),
    ("NATO", "Russia"),
    ("India", "Pakistan"),
    ("China", "Taiwan"),
]


# ---------------------------------------------------------------------------
# GDELT 2.0 DOC API
# ---------------------------------------------------------------------------
def fetch_gdelt_articles(query: str | None = None,
                         timespan: str = "24h",
                         max_records: int = 75,
                         max_retries: int = 3) -> pd.DataFrame:
    """
    Query the GDELT DOC 2.0 API for conflict-related articles.

    Parameters
    ----------
    query     : Custom search string. If None, uses built-in conflict queries.
    timespan  : Lookback window, e.g. "24h", "7d".
    max_records : Max articles to retrieve.

    Returns
    -------
    pd.DataFrame with columns:
        timestamp, title, source, url, tone, theme, locations, language
    """
    if query is None:
        query = " OR ".join(f'"{q}"' for q in CONFLICT_QUERIES)

    params = {
        "query":      query,
        "mode":       "artlist",
        "maxrecords": max_records,
        "timespan":   timespan,
        "format":     "json",
        "sort":       "datedesc",
    }

    records = []
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(GDELT_DOC_URL, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()

            # Persist raw response
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            raw_path = RAW_DATA_DIR / f"gdelt_articles_{ts}.json"
            raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            for article in payload.get("articles", []):
                records.append({
                    "timestamp":  article.get("seendate", ""),
                    "title":      article.get("title", ""),
                    "source":     article.get("domain", ""),
                    "url":        article.get("url", ""),
                    "tone":       article.get("tone", 0.0),
                    "theme":      article.get("theme", ""),
                    "locations":  article.get("sourcelocationname", ""),
                    "language":   article.get("language", ""),
                })
            break

        except requests.RequestException as exc:
            print(f"[gdelt_client] Attempt {attempt}/{max_retries} failed: {exc}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    df = pd.DataFrame(records)
    if not df.empty:
        # GDELT seendate format: YYYYMMDDTHHmmSSZ
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed", utc=True, errors="coerce")
        # Parse tone — GDELT returns "tone,pos,neg,polarity,…" as a comma-separated string
        if df["tone"].dtype == object:
            df["tone"] = df["tone"].apply(_parse_tone)
    return df


def _parse_tone(tone_str) -> float:
    """Extract the primary tone score from GDELT's comma-separated tone field."""
    try:
        if isinstance(tone_str, str):
            return float(tone_str.split(",")[0])
        return float(tone_str)
    except (ValueError, IndexError):
        return 0.0


# ---------------------------------------------------------------------------
# GDELT Tone timeline (for trend detection)
# ---------------------------------------------------------------------------
def fetch_gdelt_tone_timeline(query: str | None = None,
                              timespan: str = "7d",
                              max_retries: int = 3) -> pd.DataFrame:
    """
    Pull the tone timeline from GDELT to detect sentiment shifts over time.

    Returns
    -------
    pd.DataFrame with columns: date, tone_avg, article_count
    """
    if query is None:
        query = " OR ".join(f'"{q}"' for q in CONFLICT_QUERIES[:5])

    params = {
        "query":    query,
        "mode":     "timelinetone",
        "timespan": timespan,
        "format":   "json",
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(GDELT_DOC_URL, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()

            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            raw_path = RAW_DATA_DIR / f"gdelt_tone_timeline_{ts}.json"
            raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            timeline = payload.get("timeline", [])
            if timeline and isinstance(timeline[0], dict):
                data_series = timeline[0].get("data", [])
            elif timeline:
                data_series = timeline
            else:
                data_series = []

            rows = []
            for point in data_series:
                rows.append({
                    "date":          point.get("date", ""),
                    "tone_avg":      point.get("value", 0.0),
                    "article_count": point.get("norm", 0),
                })

            df = pd.DataFrame(rows)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], format="mixed", utc=True, errors="coerce")
            return df

        except requests.RequestException as exc:
            print(f"[gdelt_client] Timeline attempt {attempt}/{max_retries}: {exc}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Country-pair tension scanner
# ---------------------------------------------------------------------------
def scan_bilateral_tensions(timespan: str = "24h") -> pd.DataFrame:
    """
    For each monitored country pair, fetch article tone to produce a tension score.
    """
    rows = []
    for country_a, country_b in COUNTRY_PAIRS:
        query = f'"{country_a}" "{country_b}" ("military" OR "conflict" OR "sanctions")'
        df = fetch_gdelt_articles(query=query, timespan=timespan, max_records=25)
        if not df.empty:
            avg_tone = df["tone"].mean()
            count = len(df)
        else:
            avg_tone = 0.0
            count = 0
        rows.append({
            "country_a":     country_a,
            "country_b":     country_b,
            "avg_tone":      avg_tone,
            "article_count": count,
            "tension_flag":  avg_tone < -3.0 and count > 5,  # heuristic threshold
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== GDELT Article Fetch ===")
    articles = fetch_gdelt_articles(timespan="24h", max_records=10)
    print(f"Articles retrieved: {len(articles)}")
    if not articles.empty:
        print(articles[["timestamp", "title", "tone"]].head(10).to_string(index=False))

    print("\n=== Bilateral Tension Scan ===")
    tensions = scan_bilateral_tensions(timespan="7d")
    print(tensions.to_string(index=False))
