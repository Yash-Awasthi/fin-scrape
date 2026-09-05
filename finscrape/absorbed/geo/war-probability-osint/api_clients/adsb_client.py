"""
adsb_client.py — Military & civilian flight-tracking data ingestion.

Data sources
------------
1. ADS-B Exchange (via RapidAPI)   — unfiltered military aircraft positions.
2. OpenSky Network (free REST API) — civilian airspace anomaly detection.

Key function
------------
fetch_military_flights() -> pd.DataFrame
    Columns: timestamp, icao24, callsign, aircraft_type, lat, lon,
             altitude, velocity, origin_country, is_military
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
ADSB_API_KEY = os.getenv("ADSB_API_KEY", "")
OPENSKY_USERNAME = os.getenv("OPENSKY_USERNAME", "")
OPENSKY_PASSWORD = os.getenv("OPENSKY_PASSWORD", "")

RAW_DATA_DIR = Path("data/raw/flights")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ICAO type designators for aircraft we care about
MILITARY_AIRCRAFT_TYPES = {
    "C17":   "C-17 Globemaster III",
    "C5M":   "C-5M Super Galaxy",
    "C5":    "C-5 Galaxy",
    "K35R":  "KC-135 Stratotanker",
    "KC46":  "KC-46 Pegasus",
    "E4B":   "E-4B Nightwatch (Doomsday)",
    "E6B":   "E-6B Mercury (TACAMO)",
    "B52H":  "B-52H Stratofortress",
    "B1B":   "B-1B Lancer",
    "B2":    "B-2 Spirit",
    "P8":    "P-8A Poseidon",
    "C130":  "C-130 Hercules",
    "C130J": "C-130J Super Hercules",
    "E3CF":  "E-3 Sentry (AWACS)",
    "RQ4":   "RQ-4 Global Hawk",
}

# Callsign prefixes commonly used by the U.S. military
MILITARY_CALLSIGN_PREFIXES = (
    "RCH",   # Reach — Air Mobility Command
    "DUKE",  # C-17 training flights
    "IRON",  # Tanker flights
    "FORTE", # RQ-4 Global Hawk ISR
    "JAKE",  # KC-135/KC-46
    "DOOM",  # E-4B Nightwatch
    "NAVY",
    "ARMY",
    "EVAC",
    "SAM",   # Special Air Mission
    "VENUS",
    "ORDER", # Airborne command
)


# ---------------------------------------------------------------------------
# ADS-B Exchange (RapidAPI)
# ---------------------------------------------------------------------------
ADSB_BASE_URL = "https://adsbexchange-com1.p.rapidapi.com/v2"

def _adsb_headers() -> dict:
    return {
        "X-RapidAPI-Key": ADSB_API_KEY,
        "X-RapidAPI-Host": "adsbexchange-com1.p.rapidapi.com",
    }


def _classify_military(row: dict) -> bool:
    """Heuristic: is this flight military?"""
    callsign = str(row.get("flight", "")).strip().upper()
    ac_type = str(row.get("t", "")).strip().upper()

    if ac_type in MILITARY_AIRCRAFT_TYPES:
        return True
    for prefix in MILITARY_CALLSIGN_PREFIXES:
        if callsign.startswith(prefix):
            return True
    # Flag if the aircraft is registered to a military operator
    if str(row.get("ownOp", "")).upper() in ("USAF", "USN", "USMC", "US ARMY"):
        return True
    return False


def fetch_adsb_military(lat: float = 38.87,
                        lon: float = -77.06,
                        radius_nm: int = 250,
                        max_retries: int = 3) -> pd.DataFrame:
    """
    Pull aircraft positions from ADS-B Exchange within *radius_nm* nautical
    miles of (lat, lon). Defaults to the Washington D.C. area.

    Returns a DataFrame of military-flagged aircraft.
    """
    url = f"{ADSB_BASE_URL}/lat/{lat}/lon/{lon}/dist/{radius_nm}/"
    records = []

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=_adsb_headers(), timeout=30)
            resp.raise_for_status()
            payload = resp.json()

            # Persist raw JSON
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            raw_path = RAW_DATA_DIR / f"adsb_{ts}.json"
            raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            for ac in payload.get("ac", []):
                is_mil = _classify_military(ac)
                records.append({
                    "timestamp":      datetime.now(timezone.utc).isoformat(),
                    "icao24":         ac.get("hex", ""),
                    "callsign":       str(ac.get("flight", "")).strip(),
                    "aircraft_type":  ac.get("t", ""),
                    "lat":            ac.get("lat"),
                    "lon":            ac.get("lon"),
                    "altitude_ft":    ac.get("alt_baro"),
                    "velocity_kts":   ac.get("gs"),
                    "origin_country": ac.get("ownOp", ""),
                    "is_military":    is_mil,
                })
            break  # success

        except requests.RequestException as exc:
            print(f"[adsb_client] ADS-B Exchange attempt {attempt}/{max_retries} failed: {exc}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    df = pd.DataFrame(records)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


# ---------------------------------------------------------------------------
# OpenSky Network (free, rate-limited)
# ---------------------------------------------------------------------------
OPENSKY_BASE_URL = "https://opensky-network.org/api"

def fetch_opensky(bbox: tuple = (24.0, -125.0, 50.0, -66.0),
                  max_retries: int = 3) -> pd.DataFrame:
    """
    Pull all state vectors inside a bounding box from OpenSky.
    Default bbox covers the contiguous United States.

    Returns a DataFrame with an `is_military` flag based on callsign heuristics.
    """
    lamin, lomin, lamax, lomax = bbox
    url = (
        f"{OPENSKY_BASE_URL}/states/all"
        f"?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"
    )
    auth = (OPENSKY_USERNAME, OPENSKY_PASSWORD) if OPENSKY_USERNAME else None
    records = []

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, auth=auth, timeout=30)
            resp.raise_for_status()
            payload = resp.json()

            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            raw_path = RAW_DATA_DIR / f"opensky_{ts}.json"
            raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            for sv in payload.get("states", []):
                callsign = str(sv[1]).strip().upper() if sv[1] else ""
                is_mil = any(callsign.startswith(p) for p in MILITARY_CALLSIGN_PREFIXES)
                records.append({
                    "timestamp":      datetime.fromtimestamp(payload["time"], tz=timezone.utc).isoformat(),
                    "icao24":         sv[0],
                    "callsign":       callsign,
                    "aircraft_type":  "",  # OpenSky doesn't provide this directly
                    "lat":            sv[6],
                    "lon":            sv[5],
                    "altitude_ft":    round(sv[7] * 3.28084) if sv[7] else None,  # m → ft
                    "velocity_kts":   round(sv[9] * 1.94384) if sv[9] else None,  # m/s → kts
                    "origin_country": sv[2],
                    "is_military":    is_mil,
                })
            break

        except requests.RequestException as exc:
            print(f"[adsb_client] OpenSky attempt {attempt}/{max_retries} failed: {exc}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    df = pd.DataFrame(records)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


# ---------------------------------------------------------------------------
# Unified convenience function
# ---------------------------------------------------------------------------
def fetch_all_flights(**kwargs) -> pd.DataFrame:
    """Combine ADS-B Exchange + OpenSky into a single DataFrame."""
    frames = []

    if ADSB_API_KEY:
        print("[adsb_client] Fetching from ADS-B Exchange …")
        frames.append(fetch_adsb_military(**kwargs))
    else:
        print("[adsb_client] ADSB_API_KEY not set — skipping ADS-B Exchange.")

    print("[adsb_client] Fetching from OpenSky Network …")
    frames.append(fetch_opensky())

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined.drop_duplicates(subset=["icao24", "timestamp"], inplace=True)
        return combined
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    df = fetch_all_flights()
    mil = df[df["is_military"]] if not df.empty else df
    print(f"\n=== Flight Data Summary ===")
    print(f"Total aircraft tracked : {len(df)}")
    print(f"Military flagged       : {len(mil)}")
    if not mil.empty:
        print(mil[["callsign", "aircraft_type", "lat", "lon", "altitude_ft"]].to_string(index=False))
