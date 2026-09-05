"""
foot_traffic_client.py — Pentagon "Pizza Index" & late-night foot-traffic data.

Data sources
------------
1. Outscraper Google Maps API — scrapes live popularity / popular-times data.
2. Google Places API (Nearby Search) — discovers 24-hour food / coffee venues
   near government buildings.

Key function
------------
fetch_foot_traffic() -> pd.DataFrame
    Columns: timestamp, location_name, place_id, lat, lon,
             current_popularity, usual_popularity, anomaly_ratio
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTSCRAPER_API_KEY = os.getenv("OUTSCRAPER_API_KEY", "")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
BESTTIME_API_KEY = os.getenv("BESTTIME_API_KEY", "")

RAW_DATA_DIR = Path("data/raw/foot_traffic")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Geofences — (lat, lon, radius_meters, label)
GEOFENCES = [
    (38.8711,  -77.0559,  1600, "Pentagon"),
    (38.9516,  -77.1467,  1600, "CIA_Langley"),
    (38.8977,  -77.0365,  1600, "White_House"),
    (35.1392,  -79.0061,  2400, "Fort_Bragg"),
    (27.8490,  -82.5280,  2400, "CENTCOM_MacDill"),
]

# Types of places that indicate overnight staffers are in the building
PLACE_TYPES = ["restaurant", "meal_delivery", "cafe", "bar", "convenience_store"]


# ---------------------------------------------------------------------------
# Google Places — discover venues near geofences
# ---------------------------------------------------------------------------
def discover_nearby_places(lat: float, lon: float, radius_m: int = 1600,
                           max_results: int = 20) -> list[dict]:
    """
    Use Google Places Nearby Search to find 24-hour food/coffee venues.
    Returns a list of {name, place_id, lat, lon, types}.
    """
    if not GOOGLE_PLACES_API_KEY:
        print("[foot_traffic] GOOGLE_PLACES_API_KEY not set — skipping discovery.")
        return []

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    results = []

    for ptype in PLACE_TYPES:
        params = {
            "location": f"{lat},{lon}",
            "radius": radius_m,
            "type": ptype,
            "opennow": True,
            "key": GOOGLE_PLACES_API_KEY,
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
            for place in payload.get("results", [])[:max_results]:
                loc = place["geometry"]["location"]
                results.append({
                    "name":     place.get("name", ""),
                    "place_id": place.get("place_id", ""),
                    "lat":      loc["lat"],
                    "lon":      loc["lng"],
                    "types":    place.get("types", []),
                })
        except requests.RequestException as exc:
            print(f"[foot_traffic] Google Places error for type={ptype}: {exc}")

    # Deduplicate by place_id
    seen = set()
    unique = []
    for r in results:
        if r["place_id"] not in seen:
            seen.add(r["place_id"])
            unique.append(r)
    return unique


# ---------------------------------------------------------------------------
# Outscraper — live popularity data
# ---------------------------------------------------------------------------
OUTSCRAPER_BASE_URL = "https://api.outscraper.com/maps/search-v3"

def _fetch_outscraper_popularity(query: str, max_retries: int = 3) -> list[dict]:
    """
    Query Outscraper for Google Maps popularity data.
    """
    if not OUTSCRAPER_API_KEY:
        return []

    headers = {"X-API-KEY": OUTSCRAPER_API_KEY}
    params = {
        "query": query,
        "limit": 1,
        "fields": "name,place_id,latitude,longitude,popular_times,current_popularity",
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(OUTSCRAPER_BASE_URL, headers=headers,
                                params=params, timeout=30)
            resp.raise_for_status()
            return resp.json().get("data", [])
        except requests.RequestException as exc:
            print(f"[foot_traffic] Outscraper attempt {attempt}/{max_retries}: {exc}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    return []


# ---------------------------------------------------------------------------
# BestTime.app — venue foot traffic forecast & live data
# ---------------------------------------------------------------------------
BESTTIME_URL = "https://besttime.app/api/v1/forecasts"

def _fetch_besttime_popularity(venue_name: str, venue_address: str,
                               max_retries: int = 3) -> dict | None:
    """
    Query BestTime.app for foot traffic forecast and live visit data.
    """
    if not BESTTIME_API_KEY:
        return None

    params = {
        "api_key_private": BESTTIME_API_KEY,
        "venue_name": venue_name,
        "venue_address": venue_address,
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(BESTTIME_URL, json=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            print(f"[foot_traffic] BestTime attempt {attempt}/{max_retries}: {exc}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    return None


# ---------------------------------------------------------------------------
# Unified fetch
# ---------------------------------------------------------------------------
def fetch_foot_traffic() -> pd.DataFrame:
    """
    For each geofence, discover nearby venues and pull their live popularity.
    Returns a DataFrame with an **anomaly_ratio** (current / usual) for
    each venue, focusing on the late-night window (22:00–04:00 local).
    """
    records = []
    now = datetime.now(timezone.utc)

    for lat, lon, radius, label in GEOFENCES:
        print(f"[foot_traffic] Scanning {label} ({lat}, {lon}) …")

        # --- Outscraper path ---
        if OUTSCRAPER_API_KEY:
            query = f"restaurants near {label.replace('_', ' ')}"
            data = _fetch_outscraper_popularity(query)
            for item in data:
                current = item.get("current_popularity")
                # Estimate 'usual' from popular_times average if available
                popular_times = item.get("popular_times")
                usual = None
                if popular_times:
                    weekday = now.weekday()  # 0=Mon … 6=Sun
                    day_data = popular_times[weekday] if weekday < len(popular_times) else None
                    if day_data and "data" in day_data:
                        hour = now.hour
                        usual = day_data["data"][hour] if hour < len(day_data["data"]) else None

                ratio = (current / usual) if (current and usual and usual > 0) else None
                records.append({
                    "timestamp":           now.isoformat(),
                    "location_name":       f"{label} — {item.get('name', 'unknown')}",
                    "place_id":            item.get("place_id", ""),
                    "lat":                 item.get("latitude", lat),
                    "lon":                 item.get("longitude", lon),
                    "current_popularity":  current,
                    "usual_popularity":    usual,
                    "anomaly_ratio":       ratio,
                })

        # --- Google Places fallback (metadata only, no live popularity) ---
        elif GOOGLE_PLACES_API_KEY:
            places = discover_nearby_places(lat, lon, radius)
            for p in places:
                records.append({
                    "timestamp":           now.isoformat(),
                    "location_name":       f"{label} — {p['name']}",
                    "place_id":            p["place_id"],
                    "lat":                 p["lat"],
                    "lon":                 p["lon"],
                    "current_popularity":  None,
                    "usual_popularity":    None,
                    "anomaly_ratio":       None,
                })
        else:
            print(f"[foot_traffic] No API keys configured — generating placeholder for {label}.")
            records.append({
                "timestamp":           now.isoformat(),
                "location_name":       label,
                "place_id":            "",
                "lat":                 lat,
                "lon":                 lon,
                "current_popularity":  None,
                "usual_popularity":    None,
                "anomaly_ratio":       None,
            })

    # Persist raw JSON
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    raw_path = RAW_DATA_DIR / f"foot_traffic_{ts}.json"
    raw_path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")

    df = pd.DataFrame(records)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    df = fetch_foot_traffic()
    print(f"\n=== Foot Traffic Summary ===")
    print(f"Venues scanned : {len(df)}")
    anomalies = df.dropna(subset=["anomaly_ratio"])
    if not anomalies.empty:
        print(f"Venues with live data: {len(anomalies)}")
        print(anomalies[["location_name", "current_popularity",
                         "usual_popularity", "anomaly_ratio"]].to_string(index=False))
    else:
        print("No live popularity data available (API keys may not be set).")
