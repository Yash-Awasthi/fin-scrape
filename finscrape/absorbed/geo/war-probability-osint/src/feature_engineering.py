"""
feature_engineering.py — Computes anomaly scores from merged data summary.

Takes the flat dictionary produced by data_cleaner.merge_all_sources() and
transforms it into the 8-feature vector expected by the Random Forest model.

Feature vector
--------------
| #  | Feature                 | Description                                           |
|----|-------------------------|-------------------------------------------------------|
| 0  | military_flight_surge   | Z-score of military flight count vs 30-day baseline   |
| 1  | tanker_refueler_ratio   | Ratio of aerial refuelers to total military flights   |
| 2  | foot_traffic_anomaly    | Mean late-night foot-traffic ratio across geofences   |
| 3  | gdelt_negative_tone     | Rolling mean GDELT tone (more negative = worse)       |
| 4  | gdelt_article_spike     | Z-score of conflict article volume vs 7-day baseline  |
| 5  | oil_price_z             | Brent Crude z-score (30-day rolling)                  |
| 6  | defense_stock_z         | Average z-score of defense contractor stocks           |
| 7  | gold_price_z            | Gold futures z-score                                  |

Public API
----------
compute_features(summary_dict, baselines=None) -> np.ndarray   (shape (1, 8))
get_feature_names()                            -> list[str]
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Feature names (order matters — must match model training order)
# ---------------------------------------------------------------------------
FEATURE_NAMES: list[str] = [
    "military_flight_surge",
    "tanker_refueler_ratio",
    "foot_traffic_anomaly",
    "gdelt_negative_tone",
    "gdelt_article_spike",
    "oil_price_z",
    "defense_stock_z",
    "gold_price_z",
]


def get_feature_names() -> list[str]:
    """Return the ordered feature names expected by the model."""
    return list(FEATURE_NAMES)


# ---------------------------------------------------------------------------
# Default baselines (rough "normal day" values for bootstrapping)
# ---------------------------------------------------------------------------
DEFAULT_BASELINES = {
    "military_aircraft_mean":    12.0,   # average military flights in view
    "military_aircraft_std":      5.0,
    "gdelt_article_count_mean":  30.0,   # average conflict articles / 24 h
    "gdelt_article_count_std":   10.0,
}


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------
def compute_features(summary: dict,
                     baselines: dict | None = None) -> np.ndarray:
    """
    Transform a merged summary dictionary into a (1, 8) feature array.

    Parameters
    ----------
    summary   : dict produced by data_cleaner.merge_all_sources().
    baselines : optional override for baseline means/stds.  If None the
                built-in DEFAULT_BASELINES are used.

    Returns
    -------
    np.ndarray of shape (1, 8) — one row ready for model.predict_proba().
    """
    b = {**DEFAULT_BASELINES, **(baselines or {})}

    # 0 — military_flight_surge (z-score)
    mil_count = summary.get("military_aircraft", 0)
    mil_mean  = b["military_aircraft_mean"]
    mil_std   = b["military_aircraft_std"]
    military_flight_surge = (
        (mil_count - mil_mean) / mil_std if mil_std > 0 else 0.0
    )

    # 1 — tanker_refueler_ratio
    tanker_refueler_ratio = summary.get("tanker_ratio", 0.0)

    # 2 — foot_traffic_anomaly (mean across geofences, 1.0 = normal)
    foot_traffic_anomaly = summary.get("foot_traffic_mean_ratio", 0.0)
    # Shift so that 1.0 (normal) → 0.0; values >1 are anomalous
    foot_traffic_anomaly = max(foot_traffic_anomaly - 1.0, 0.0)

    # 3 — gdelt_negative_tone (lower = more negative = higher risk)
    # Invert sign so that a more negative tone gives a larger positive feature
    gdelt_negative_tone = -summary.get("gdelt_mean_tone", 0.0)

    # 4 — gdelt_article_spike (z-score of article count)
    art_count = summary.get("gdelt_article_count", 0)
    art_mean  = b["gdelt_article_count_mean"]
    art_std   = b["gdelt_article_count_std"]
    gdelt_article_spike = (
        (art_count - art_mean) / art_std if art_std > 0 else 0.0
    )

    # 5 — oil_price_z
    oil_price_z = summary.get("oil_z", 0.0)

    # 6 — defense_stock_z
    defense_stock_z = summary.get("defense_stock_avg_z", 0.0)

    # 7 — gold_price_z
    gold_price_z = summary.get("gold_z", 0.0)

    feature_vector = np.array([[
        military_flight_surge,
        tanker_refueler_ratio,
        foot_traffic_anomaly,
        gdelt_negative_tone,
        gdelt_article_spike,
        oil_price_z,
        defense_stock_z,
        gold_price_z,
    ]])

    return feature_vector


# ---------------------------------------------------------------------------
# Human-readable breakdown
# ---------------------------------------------------------------------------
def explain_features(feature_vector: np.ndarray) -> list[dict]:
    """
    Return a list of {name, value, interpretation} dicts for display.
    """
    names = get_feature_names()
    values = feature_vector.flatten()

    interpretations = {
        "military_flight_surge": lambda v: "ELEVATED" if v > 1.5 else ("ABOVE NORMAL" if v > 0.5 else "NORMAL"),
        "tanker_refueler_ratio": lambda v: "HIGH" if v > 0.3 else ("MODERATE" if v > 0.1 else "LOW"),
        "foot_traffic_anomaly":   lambda v: "SPIKE DETECTED" if v > 1.0 else ("ELEVATED" if v > 0.3 else "NORMAL"),
        "gdelt_negative_tone":    lambda v: "VERY NEGATIVE" if v > 5 else ("NEGATIVE" if v > 2 else "NEUTRAL"),
        "gdelt_article_spike":    lambda v: "SURGE" if v > 2 else ("ELEVATED" if v > 1 else "NORMAL"),
        "oil_price_z":           lambda v: "SPIKE" if v > 2 else ("ELEVATED" if v > 1 else "NORMAL"),
        "defense_stock_z":       lambda v: "SPIKE" if v > 2 else ("ELEVATED" if v > 1 else "NORMAL"),
        "gold_price_z":          lambda v: "SPIKE" if v > 2 else ("ELEVATED" if v > 1 else "NORMAL"),
    }

    result = []
    for name, val in zip(names, values):
        interp_fn = interpretations.get(name, lambda v: "UNKNOWN")
        result.append({
            "name":           name,
            "value":          round(float(val), 4),
            "interpretation": interp_fn(val),
        })
    return result


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Simulate an elevated-alert scenario
    test_summary = {
        "military_aircraft":       30,    # well above the 12 ± 5 baseline
        "tanker_ratio":            0.25,
        "foot_traffic_mean_ratio": 2.5,   # 250% of usual
        "gdelt_mean_tone":        -6.2,
        "gdelt_article_count":     75,    # well above 30 ± 10
        "oil_z":                   2.1,
        "defense_stock_avg_z":     1.8,
        "gold_z":                  1.5,
    }

    features = compute_features(test_summary)
    print("Feature vector:", features)
    print()
    for item in explain_features(features):
        print(f"  {item['name']:25s}  {item['value']:+8.4f}  [{item['interpretation']}]")
