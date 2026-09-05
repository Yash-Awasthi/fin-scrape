"""
ZAI Oracle — Memory Engine
by Zawwar (github.com/Zawwarsami16)

Every run is saved. Every change is tracked.
This is what turns a snapshot tool into a living intelligence system.

Tracks:
- Risk level changes (LOW → CRITICAL)
- Signal additions and removals
- Confidence trajectory
- Whale signal shifts
- Historical analog changes
- Prediction accuracy over time

"DETERIORATING" vs "IMPROVING" — this single output
tells you more than 500 articles combined.
"""

import os
import json
from datetime import datetime
from config import DATA_PATH

MEMORY_PATH = f"{DATA_PATH}/memory"
MEMORY_FILE = f"{MEMORY_PATH}/history.json"


# ================================================================
# SAVE SNAPSHOT
# Called at the end of every run
# ================================================================
def save_snapshot(risk_level, signals, confidence, whale_signal,
                  hist_match, prediction_outlook, prices):
    """
    Saves a compact snapshot of this run.
    Only stores what's needed for delta detection — keeps file small.
    """
    os.makedirs(MEMORY_PATH, exist_ok=True)

    snapshot = {
        "timestamp":       datetime.now().isoformat(),
        "risk_level":      risk_level,
        "confidence":      confidence,
        "whale_signal":    whale_signal,
        "hist_match":      hist_match,
        "prediction":      prediction_outlook,
        "active_signals":  {k: v.get("count", 0) for k, v in signals.items()},
        "key_prices": {
            "oil":   prices.get("oil",   {}).get("price", 0),
            "gold":  prices.get("gold",  {}).get("price", 0),
            "btc":   prices.get("btc",   {}).get("price", 0),
            "sp500": prices.get("sp500", {}).get("price", 0),
            "vix":   prices.get("vix",   {}).get("price", 0),
        },
    }

    # Load existing history
    history = load_history()
    history.append(snapshot)

    # Keep last 50 runs max
    if len(history) > 50:
        history = history[-50:]

    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    return snapshot


def load_history():
    """Loads all saved snapshots."""
    try:
        with open(MEMORY_FILE) as f:
            return json.load(f)
    except Exception:
        return []


# ================================================================
# DELTA DETECTION
# Compares current run to previous run
# ================================================================
def get_delta(current_signals, current_risk, current_confidence,
              current_whale, current_hist):
    """
    Compares current state to last saved snapshot.
    Returns a structured delta report.

    This is the feature that makes the Oracle feel alive.
    """
    history = load_history()

    if not history:
        return {
            "has_previous": False,
            "message":      "First run — no previous data to compare",
        }

    prev = history[-1]

    # Risk level change
    risk_levels = ["LOW", "MODERATE", "ELEVATED", "HIGH", "CRITICAL"]
    prev_risk   = prev.get("risk_level", "UNKNOWN")
    prev_idx    = risk_levels.index(prev_risk)  if prev_risk in risk_levels else 2
    curr_idx    = risk_levels.index(current_risk) if current_risk in risk_levels else 2

    if   curr_idx > prev_idx: risk_trend = "DETERIORATING"
    elif curr_idx < prev_idx: risk_trend = "IMPROVING"
    else:                     risk_trend = "STABLE"

    # Signal changes
    prev_signals = prev.get("active_signals", {})
    new_signals  = [k for k in current_signals if k not in prev_signals]
    dropped      = [k for k in prev_signals    if k not in current_signals]
    intensified  = [
        k for k in current_signals
        if k in prev_signals and
        current_signals[k].get("count", 0) > prev_signals[k] * 1.3
    ]
    eased = [
        k for k in current_signals
        if k in prev_signals and
        current_signals[k].get("count", 0) < prev_signals[k] * 0.7
    ]

    # Confidence change
    prev_conf = prev.get("confidence", 50)
    curr_conf = current_confidence
    conf_delta = round(curr_conf - prev_conf, 1)

    # Price changes since last run
    prev_prices = prev.get("key_prices", {})
    price_moves = {}
    for asset in ["oil", "gold", "btc", "sp500", "vix"]:
        prev_p = prev_prices.get(asset, 0)
        if prev_p and prev_p > 0:
            curr_p = 0
            # current prices passed in as current_signals context
            price_moves[asset] = prev_p  # stored for reference

    # Time since last scan
    prev_time = prev.get("timestamp", "")
    time_ago  = ""
    if prev_time:
        try:
            prev_dt  = datetime.fromisoformat(prev_time)
            diff_min = (datetime.now() - prev_dt).total_seconds() / 60
            if   diff_min < 60:   time_ago = f"{diff_min:.0f} min ago"
            elif diff_min < 1440: time_ago = f"{diff_min/60:.1f} hours ago"
            else:                 time_ago = f"{diff_min/1440:.1f} days ago"
        except Exception:
            pass

    return {
        "has_previous":    True,
        "previous_scan":   time_ago,
        "risk_change":     f"{prev_risk} → {current_risk}",
        "risk_trend":      risk_trend,
        "confidence_delta": conf_delta,
        "prev_confidence": prev_conf,
        "new_signals":     new_signals,
        "dropped_signals": dropped,
        "intensified":     intensified,
        "eased":           eased,
        "prev_hist_match": prev.get("hist_match", "unknown"),
        "prev_whale":      prev.get("whale_signal", "unknown"),
    }


# ================================================================
# PREDICTION ACCURACY TRACKER
# Over time, track how often Oracle was right
# ================================================================
def record_prediction_outcome(run_timestamp, prediction_outlook,
                              actual_outcome, notes=""):
    """
    Called manually or by a verification script.
    Stores actual vs predicted for scorekeeping.
    """
    accuracy_file = f"{MEMORY_PATH}/accuracy.json"

    try:
        with open(accuracy_file) as f:
            records = json.load(f)
    except Exception:
        records = []

    records.append({
        "run_timestamp":     run_timestamp,
        "predicted_outlook": prediction_outlook,
        "actual_outcome":    actual_outcome,
        "correct":           prediction_outlook.lower() in actual_outcome.lower(),
        "notes":             notes,
        "recorded_at":       datetime.now().isoformat(),
    })

    with open(accuracy_file, "w") as f:
        json.dump(records, f, indent=2)


def get_accuracy_stats():
    """Returns Oracle hit rate statistics."""
    accuracy_file = f"{MEMORY_PATH}/accuracy.json"

    try:
        with open(accuracy_file) as f:
            records = json.load(f)
    except Exception:
        return None

    if not records:
        return None

    total   = len(records)
    correct = sum(1 for r in records if r.get("correct"))

    return {
        "total_predictions": total,
        "correct":           correct,
        "hit_rate":          round(correct / total * 100, 1),
        "last_10_rate":      round(
            sum(1 for r in records[-10:] if r.get("correct")) / min(10, len(records)) * 100, 1
        ),
    }
