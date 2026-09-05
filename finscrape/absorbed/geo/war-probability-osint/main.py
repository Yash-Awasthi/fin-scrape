#!/usr/bin/env python3
"""
main.py — Master pipeline for the War-Probability OSINT system.

Workflow
--------
1. Load environment variables.
2. Fetch data from each API client (flights, foot traffic, news, markets).
3. Clean and normalise via data_cleaner.
4. Compute anomaly features via feature_engineering.
5. Run the Random Forest model via model_inference.
6. Print a human-readable dashboard with the escalation probability.

Usage
-----
    python main.py                 # Full live run (requires API keys)
    python main.py --dry-run       # Synthetic data, no API calls
    python main.py --train         # Train/re-train the model first
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="War-Probability OSINT — Military Escalation Predictor",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use synthetic/random data instead of calling live APIs.",
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Train (or re-train) the ML model before running inference.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Data acquisition (live)
# ---------------------------------------------------------------------------
def _fetch_live_data() -> dict:
    """Call every API client and return raw DataFrames."""
    from api_clients.adsb_client import fetch_all_flights
    from api_clients.foot_traffic_client import fetch_foot_traffic
    from api_clients.gdelt_client import fetch_gdelt_articles
    from api_clients.finance_client import fetch_market_data

    print("\n" + "=" * 60)
    print("  PHASE 1 — DATA ACQUISITION")
    print("=" * 60)

    print("\n[1/4] Flight tracking (ADS-B + OpenSky) …")
    flights_df = fetch_all_flights()
    print(f"       → {len(flights_df)} aircraft positions")

    print("[2/4] Foot traffic (Pentagon Pizza Index) …")
    foot_traffic_df = fetch_foot_traffic()
    print(f"       → {len(foot_traffic_df)} venue readings")

    print("[3/4] Geopolitical news (GDELT) …")
    gdelt_df = fetch_gdelt_articles(timespan="24h", max_records=50)
    print(f"       → {len(gdelt_df)} articles")

    print("[4/4] Financial markets (yfinance) …")
    finance_df = fetch_market_data()
    print(f"       → {len(finance_df)} ticker snapshots")

    return {
        "flights":      flights_df,
        "foot_traffic": foot_traffic_df,
        "gdelt":        gdelt_df,
        "finance":      finance_df,
    }


# ---------------------------------------------------------------------------
# Data acquisition (synthetic / dry-run)
# ---------------------------------------------------------------------------
def _fetch_synthetic_data() -> dict:
    """Generate random DataFrames that mimic API outputs for testing."""
    import pandas as pd

    rng = np.random.default_rng(0)
    now = datetime.now(timezone.utc).isoformat()

    print("\n" + "=" * 60)
    print("  PHASE 1 — DATA ACQUISITION  [DRY-RUN — synthetic data]")
    print("=" * 60)

    # Flights
    n_flights = rng.integers(50, 200)
    flights_df = pd.DataFrame({
        "timestamp":     [now] * n_flights,
        "icao24":        [f"A{i:05d}" for i in range(n_flights)],
        "callsign":      [f"RCH{rng.integers(100,999)}" if rng.random() < 0.15 else f"UAL{rng.integers(100,999)}" for _ in range(n_flights)],
        "aircraft_type": [rng.choice(["C17", "B738", "A320", "KC46", "E4B", "B77W"]) for _ in range(n_flights)],
        "lat":           rng.uniform(25, 50, n_flights),
        "lon":           rng.uniform(-125, -66, n_flights),
        "altitude_ft":   rng.integers(5000, 45000, n_flights),
        "velocity_kts":  rng.integers(200, 550, n_flights),
        "origin_country": ["United States"] * n_flights,
        "is_military":   rng.random(n_flights) < 0.15,
    })
    flights_df["timestamp"] = pd.to_datetime(flights_df["timestamp"], utc=True)
    print(f"  [1/4] Synthetic flights:      {len(flights_df)} aircraft")

    # Foot traffic
    foot_traffic_df = pd.DataFrame({
        "timestamp":          [now] * 5,
        "location_name":      ["Pentagon", "CIA_Langley", "White_House", "Fort_Bragg", "CENTCOM"],
        "place_id":           [f"place_{i}" for i in range(5)],
        "lat":                [38.87, 38.95, 38.90, 35.14, 27.85],
        "lon":                [-77.06, -77.15, -77.04, -79.01, -82.53],
        "current_popularity": rng.integers(10, 90, 5),
        "usual_popularity":   rng.integers(20, 50, 5),
        "anomaly_ratio":      rng.uniform(0.5, 3.0, 5),
    })
    foot_traffic_df["timestamp"] = pd.to_datetime(foot_traffic_df["timestamp"], utc=True)
    print(f"  [2/4] Synthetic foot traffic: {len(foot_traffic_df)} venues")

    # GDELT
    n_articles = rng.integers(20, 80)
    gdelt_df = pd.DataFrame({
        "timestamp": [now] * n_articles,
        "title":     [f"Synthetic article {i}" for i in range(n_articles)],
        "source":    [f"source{i}.com" for i in range(n_articles)],
        "url":       [f"https://source{i}.com/article" for i in range(n_articles)],
        "tone":      rng.normal(-2.0, 3.0, n_articles),
        "theme":     ["MILITARY"] * n_articles,
        "locations": [""] * n_articles,
        "language":  ["English"] * n_articles,
    })
    gdelt_df["timestamp"] = pd.to_datetime(gdelt_df["timestamp"], utc=True)
    print(f"  [3/4] Synthetic GDELT:        {len(gdelt_df)} articles")

    # Finance
    finance_df = pd.DataFrame({
        "timestamp":       [now] * 5,
        "symbol":          ["BZ=F", "GC=F", "LMT", "RTX", "^VIX"],
        "name":            ["Brent Crude", "Gold", "Lockheed", "Raytheon", "VIX"],
        "price":           [82.5, 2050.0, 480.0, 105.0, 22.5],
        "pct_change_24h":  rng.normal(0, 2, 5),
        "rolling_mean_30d": [80.0, 2020.0, 470.0, 102.0, 20.0],
        "z_score":         rng.normal(0, 1, 5),
    })
    finance_df["timestamp"] = pd.to_datetime(finance_df["timestamp"], utc=True)
    print(f"  [4/4] Synthetic finance:      {len(finance_df)} tickers")

    return {
        "flights":      flights_df,
        "foot_traffic": foot_traffic_df,
        "gdelt":        gdelt_df,
        "finance":      finance_df,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def _print_dashboard(result: dict, feature_explanations: list[dict]) -> None:
    """Pretty-print the escalation probability and per-signal breakdown."""
    prob = result["probability"]
    risk = result["risk_level"]

    # Color-coded risk bar
    bar_len = 40
    filled = int(prob * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║   WAR-PROBABILITY OSINT — ESCALATION DASHBOARD            ║")
    print("╠" + "═" * 58 + "╣")
    print(f"║  Timestamp : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'):>42s}  ║")
    print(f"║  Risk Level: {risk:>42s}  ║")
    print(f"║  Probability: {prob:>6.1%}{' ' * 35}║")
    print(f"║  [{bar}] {prob:>5.1%}   ║")
    print(f"║  Confidence : {result['confidence']:>6.1%}{' ' * 35}║")
    print("╠" + "═" * 58 + "╣")
    print("║  SIGNAL BREAKDOWN                                         ║")
    print("╠" + "═" * 58 + "╣")

    for feat in feature_explanations:
        name  = feat["name"]
        val   = feat["value"]
        interp = feat["interpretation"]
        mini_bar = "█" * min(int(abs(val) * 4), 20)
        line = f"  {name:25s} {val:+7.3f}  {interp:12s}  {mini_bar}"
        print(f"║{line:<57s} ║")

    print("╠" + "═" * 58 + "╣")
    print("║  FEATURE IMPORTANCES (model weights)                      ║")
    print("╠" + "═" * 58 + "╣")

    for fname, imp in sorted(result["feature_importances"].items(),
                              key=lambda x: -x[1]):
        imp_bar = "█" * int(imp * 50)
        line = f"  {fname:25s} {imp:.4f}  {imp_bar}"
        print(f"║{line:<57s} ║")

    print("╚" + "═" * 58 + "╝")
    print()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args()

    # --- Optional: train model ---
    if args.train:
        print("[main] Training model …")
        from models.train_model import train_and_save
        train_and_save()
        print()

    # --- Ensure model exists ---
    model_path = Path("models/random_forest_v1.pkl")
    if not model_path.exists():
        print("[main] Model not found. Training now …")
        from models.train_model import train_and_save
        train_and_save()
        print()

    # --- Phase 1: Data acquisition ---
    if args.dry_run:
        raw_data = _fetch_synthetic_data()
    else:
        raw_data = _fetch_live_data()

    # --- Phase 2: Cleaning ---
    from src.data_cleaner import (
        clean_flight_data,
        clean_foot_traffic_data,
        clean_gdelt_data,
        clean_finance_data,
        merge_all_sources,
    )

    print("\n" + "=" * 60)
    print("  PHASE 2 — DATA CLEANING & MERGING")
    print("=" * 60)

    flights_clean      = clean_flight_data(raw_data["flights"])
    foot_traffic_clean = clean_foot_traffic_data(raw_data["foot_traffic"])
    gdelt_clean        = clean_gdelt_data(raw_data["gdelt"])
    finance_clean      = clean_finance_data(raw_data["finance"])

    summary = merge_all_sources(
        flights_df=flights_clean,
        foot_traffic_df=foot_traffic_clean,
        gdelt_df=gdelt_clean,
        finance_df=finance_clean,
    )

    print("  Merged summary:")
    for k, v in summary.items():
        if k != "timestamp":
            print(f"    {k:30s}: {v}")

    # --- Phase 3: Feature engineering ---
    from src.feature_engineering import compute_features, explain_features

    print("\n" + "=" * 60)
    print("  PHASE 3 — FEATURE ENGINEERING")
    print("=" * 60)

    features = compute_features(summary)
    explanations = explain_features(features)
    for e in explanations:
        print(f"  {e['name']:25s}  {e['value']:+8.4f}  [{e['interpretation']}]")

    # --- Phase 4: Model inference ---
    from src.model_inference import predict_escalation

    print("\n" + "=" * 60)
    print("  PHASE 4 — MODEL INFERENCE")
    print("=" * 60)

    result = predict_escalation(features)

    # --- Dashboard ---
    _print_dashboard(result, explanations)

    # --- Save processed output ---
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    import json
    output = {
        "timestamp":    ts,
        "probability":  result["probability"],
        "risk_level":   result["risk_level"],
        "confidence":   result["confidence"],
        "features":     {e["name"]: e["value"] for e in explanations},
        "importances":  result["feature_importances"],
        "raw_summary":  {k: (str(v) if not isinstance(v, (int, float)) else v)
                         for k, v in summary.items()},
    }
    out_path = processed_dir / f"prediction_{ts}.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"[main] Prediction saved → {out_path}")


if __name__ == "__main__":
    main()
