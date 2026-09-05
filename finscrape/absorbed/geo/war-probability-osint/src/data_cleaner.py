"""
data_cleaner.py — Normalizes timestamps, handles missing data, and merges
multi-source DataFrames into a single time-indexed feature table.

Public API
----------
clean_flight_data(df)        -> pd.DataFrame
clean_foot_traffic_data(df)  -> pd.DataFrame
clean_gdelt_data(df)         -> pd.DataFrame
clean_finance_data(df)       -> pd.DataFrame
merge_all_sources(...)       -> pd.DataFrame
"""

from datetime import datetime, timezone

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Timestamp normalisation
# ---------------------------------------------------------------------------
def _normalise_timestamps(df: pd.DataFrame,
                          col: str = "timestamp") -> pd.DataFrame:
    """Ensure the timestamp column is tz-aware UTC datetime64."""
    df = df.copy()
    if col not in df.columns:
        df[col] = datetime.now(timezone.utc)
    df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    df.dropna(subset=[col], inplace=True)
    return df


# ---------------------------------------------------------------------------
# Per-source cleaners
# ---------------------------------------------------------------------------
def clean_flight_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw ADS-B / OpenSky DataFrame.

    Steps:
        1. Normalise timestamps.
        2. Drop rows with missing lat/lon.
        3. Coerce altitude and velocity to numeric.
        4. Remove exact duplicates.
    """
    if df.empty:
        return df

    df = _normalise_timestamps(df)
    df = df.dropna(subset=["lat", "lon"])

    for col in ("altitude_ft", "velocity_kts"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["callsign"] = df["callsign"].astype(str).str.strip().str.upper()
    df["aircraft_type"] = df["aircraft_type"].astype(str).str.strip().str.upper()

    df.drop_duplicates(subset=["icao24", "timestamp"], inplace=True)
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def clean_foot_traffic_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the foot-traffic / Pentagon pizza DataFrame.

    Steps:
        1. Normalise timestamps.
        2. Coerce popularity columns to float.
        3. Recompute anomaly_ratio where inputs allow.
    """
    if df.empty:
        return df

    df = _normalise_timestamps(df)

    for col in ("current_popularity", "usual_popularity"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Recompute ratio to ensure consistency
    mask = (df["usual_popularity"].notna()) & (df["usual_popularity"] > 0)
    df.loc[mask, "anomaly_ratio"] = (
        df.loc[mask, "current_popularity"] / df.loc[mask, "usual_popularity"]
    )

    df.drop_duplicates(subset=["place_id", "timestamp"], inplace=True)
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def clean_gdelt_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the GDELT articles DataFrame.

    Steps:
        1. Normalise timestamps.
        2. Ensure tone is numeric.
        3. Drop duplicate URLs.
    """
    if df.empty:
        return df

    df = _normalise_timestamps(df)
    df["tone"] = pd.to_numeric(df["tone"], errors="coerce").fillna(0.0)

    if "url" in df.columns:
        df.drop_duplicates(subset=["url"], inplace=True)

    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def clean_finance_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the market / finance DataFrame.

    Steps:
        1. Normalise timestamps.
        2. Coerce numeric columns.
        3. Drop rows with missing price.
    """
    if df.empty:
        return df

    df = _normalise_timestamps(df)

    for col in ("price", "pct_change_24h", "rolling_mean_30d", "z_score"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=["price"], inplace=True)
    df.drop_duplicates(subset=["symbol", "timestamp"], inplace=True)
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


# ---------------------------------------------------------------------------
# Merge all sources into a single row of features
# ---------------------------------------------------------------------------
def merge_all_sources(
    flights_df: pd.DataFrame | None = None,
    foot_traffic_df: pd.DataFrame | None = None,
    gdelt_df: pd.DataFrame | None = None,
    finance_df: pd.DataFrame | None = None,
) -> dict:
    """
    Collapse each cleaned source into summary statistics and return a single
    flat dictionary suitable for feature engineering.

    This is the bridge between raw cleaned tables and the feature vector
    expected by the ML model.
    """
    summary: dict = {"timestamp": datetime.now(timezone.utc).isoformat()}

    # --- Flights ---
    if flights_df is not None and not flights_df.empty:
        mil = flights_df[flights_df["is_military"] == True]
        summary["total_aircraft"]     = len(flights_df)
        summary["military_aircraft"]  = len(mil)
        summary["military_ratio"]     = len(mil) / max(len(flights_df), 1)

        # Count tankers / refuelers specifically
        tanker_types = {"K35R", "KC46"}
        tanker_mask = mil["aircraft_type"].isin(tanker_types)
        summary["tanker_count"]       = int(tanker_mask.sum())
        summary["tanker_ratio"]       = summary["tanker_count"] / max(len(mil), 1)
    else:
        summary.update(total_aircraft=0, military_aircraft=0,
                       military_ratio=0, tanker_count=0, tanker_ratio=0)

    # --- Foot traffic ---
    if foot_traffic_df is not None and not foot_traffic_df.empty:
        ratios = foot_traffic_df["anomaly_ratio"].dropna()
        summary["foot_traffic_mean_ratio"] = ratios.mean() if not ratios.empty else 0.0
        summary["foot_traffic_max_ratio"]  = ratios.max() if not ratios.empty else 0.0
        summary["foot_traffic_venues"]     = len(foot_traffic_df)
    else:
        summary.update(foot_traffic_mean_ratio=0, foot_traffic_max_ratio=0,
                       foot_traffic_venues=0)

    # --- GDELT ---
    if gdelt_df is not None and not gdelt_df.empty:
        summary["gdelt_article_count"]  = len(gdelt_df)
        summary["gdelt_mean_tone"]      = gdelt_df["tone"].mean()
        summary["gdelt_min_tone"]       = gdelt_df["tone"].min()
        summary["gdelt_negative_pct"]   = (gdelt_df["tone"] < 0).mean()
    else:
        summary.update(gdelt_article_count=0, gdelt_mean_tone=0,
                       gdelt_min_tone=0, gdelt_negative_pct=0)

    # --- Finance ---
    if finance_df is not None and not finance_df.empty:
        defense_syms = {"LMT", "RTX", "NOC", "GD", "BA", "LHX"}
        defense = finance_df[finance_df["symbol"].isin(defense_syms)]
        summary["defense_stock_avg_z"]  = defense["z_score"].mean() if not defense.empty else 0.0

        def _z(sym):
            r = finance_df[finance_df["symbol"] == sym]
            return r["z_score"].iloc[0] if not r.empty else 0.0

        summary["oil_z"]   = _z("BZ=F")
        summary["gold_z"]  = _z("GC=F")
        summary["vix_z"]   = _z("^VIX")
    else:
        summary.update(defense_stock_avg_z=0, oil_z=0, gold_z=0, vix_z=0)

    return summary


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Smoke test with empty frames
    result = merge_all_sources()
    print("Merged summary (empty inputs):")
    for k, v in result.items():
        print(f"  {k:30s}: {v}")
