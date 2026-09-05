"""
ZAI World Model — Correlation & Pattern Engine
by Zawwar (github.com/Zawwarsami16)

This is the brain of the whole system.
It takes all the downloaded data and finds hidden relationships:
- Which market moves BEFORE another
- How today's conditions compare to historical crashes
- What typically happens next based on past patterns

The idea came from thinking about markets like a physics simulation —
everything is connected, you just have to find the connections.
"""

import os
import json
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import DATA_PATH, ANTHROPIC_KEY

# ================================================================
# LOAD DATA
# ================================================================
def load_all_data():
    """Load all downloaded CSV files into memory"""
    data = {}
    historical_path = f"{DATA_PATH}/historical"

    if not os.path.exists(historical_path):
        print("❌ No data found. Run data_collector.py first.")
        return {}

    for file in os.listdir(historical_path):
        if file.endswith(".csv"):
            name = file.replace(".csv", "")
            try:
                df = pd.read_csv(f"{historical_path}/{file}", parse_dates=["date"])
                df = df.sort_values("date").set_index("date")
                if len(df) > 0:
                    data[name] = df["value"]
                    print(f"  ✅ {name}: {len(df)} records")
            except Exception as e:
                print(f"  ❌ {name}: {e}")

    return data


def merge_data(data_dict):
    """Combine all series into one DataFrame, resampled weekly"""
    if not data_dict:
        return pd.DataFrame()

    # Drop empty series
    data_dict = {k: v for k, v in data_dict.items() if len(v) > 0}

    df = pd.DataFrame(data_dict)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    # Weekly resample — daily data is too heavy for cross-series analysis
    df = df.resample("W").last()
    df = df.ffill()

    return df


# ================================================================
# CORRELATIONS
# How much does each market move with every other market?
# ================================================================
def find_correlations(df):
    """Calculate correlation between every pair of markets"""
    if df.empty:
        return {}

    # Use % change instead of raw price — more meaningful
    pct = df.pct_change(4)  # 4-week change

    corr_matrix = pct.corr()
    correlations = {}
    cols = corr_matrix.columns.tolist()

    for i, col1 in enumerate(cols):
        for col2 in cols[i+1:]:
            corr = corr_matrix.loc[col1, col2]
            if not np.isnan(corr):
                correlations[f"{col1}_vs_{col2}"] = round(corr, 3)

    # Sort strongest first
    correlations = dict(sorted(correlations.items(),
                               key=lambda x: abs(x[1]), reverse=True))
    return correlations


# ================================================================
# LEAD-LAG RELATIONSHIPS
# The most important thing — which market moves FIRST?
# Example: Oil moves up → 8 weeks later inflation follows
# ================================================================
def find_lead_lag_relationships(df, max_lag_weeks=12):
    relationships = []
    cols = df.columns.tolist()
    pct = df.pct_change(4)

    for leader in cols:
        for follower in cols:
            if leader == follower:
                continue

            best_corr = 0
            best_lag = 0

            for lag in range(1, max_lag_weeks + 1):
                try:
                    corr = pct[leader].corr(pct[follower].shift(-lag))
                    if abs(corr) > abs(best_corr):
                        best_corr = corr
                        best_lag = lag
                except:
                    continue

            # Only keep strong relationships (40%+ correlation)
            if abs(best_corr) > 0.4:
                relationships.append({
                    "leader": leader,
                    "follower": follower,
                    "lag_weeks": best_lag,
                    "correlation": round(best_corr, 3),
                    "direction": "same" if best_corr > 0 else "opposite"
                })

    relationships.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return relationships[:50]


# ================================================================
# HISTORICAL CRASH PATTERNS
# What were conditions like 6 months BEFORE each major crash?
# ================================================================
KNOWN_CRASHES = {
    "Great Depression 1929":  ("1928-01-01", "1933-01-01"),
    "Oil Crisis 1973":        ("1972-01-01", "1975-01-01"),
    "Black Monday 1987":      ("1987-06-01", "1988-06-01"),
    "Dot-com Crash 2000":     ("1999-01-01", "2002-12-01"),
    "Financial Crisis 2008":  ("2007-01-01", "2009-12-01"),
    "COVID Crash 2020":       ("2020-01-01", "2020-12-01"),
    "Crypto Crash 2022":      ("2021-11-01", "2022-12-01"),
}


def extract_crash_patterns(df):
    """Extract what conditions looked like 6 months before each crash"""
    patterns = {}

    for crash_name, (start, end) in KNOWN_CRASHES.items():
        try:
            pre_start = pd.to_datetime(start) - timedelta(weeks=26)
            pre_end = pd.to_datetime(start)
            pre_crash = df.loc[pre_start:pre_end]

            if pre_crash.empty:
                continue

            pattern = {"crash": crash_name, "period": start}

            for col in df.columns:
                if col in pre_crash.columns:
                    series = pre_crash[col].dropna()
                    if len(series) > 4 and series.iloc[0] != 0:
                        total_change = ((series.iloc[-1] - series.iloc[0]) /
                                        abs(series.iloc[0])) * 100
                        pattern[f"{col}_change_pct"] = round(total_change, 2)

            patterns[crash_name] = pattern

        except Exception:
            continue

    return patterns


# ================================================================
# COMPARE TODAY TO HISTORY
# How similar is today to each historical crash?
# ================================================================
def compare_current_to_history(df, crash_patterns):
    if df.empty or not crash_patterns:
        return []

    six_months_ago = datetime.now() - timedelta(weeks=26)
    current = df.loc[six_months_ago:]

    if current.empty:
        return []

    current_changes = {}
    for col in df.columns:
        if col in current.columns:
            series = current[col].dropna()
            if len(series) > 2 and series.iloc[0] != 0:
                change = ((series.iloc[-1] - series.iloc[0]) /
                          abs(series.iloc[0])) * 100
                current_changes[col] = round(change, 2)

    similarities = []

    for crash_name, pattern in crash_patterns.items():
        score = 0
        compared = 0
        details = []

        for col in current_changes:
            hist_key = f"{col}_change_pct"
            if hist_key in pattern:
                curr_val = current_changes[col]
                hist_val = pattern[hist_key]

                # Count every indicator the two periods share, THEN check
                # direction. score (numerator) and compared (denominator) have
                # to move independently — incrementing them together pinned the
                # ratio at 100% the moment a single indicator lined up.
                compared += 1
                if (curr_val > 0 and hist_val > 0) or (curr_val < 0 and hist_val < 0):
                    score += 1
                    details.append(
                        f"{col}: now {curr_val:+.1f}% vs history {hist_val:+.1f}%"
                    )

        if compared > 0:
            similarity_pct = (score / compared) * 100
            similarities.append({
                "crash": crash_name,
                "similarity_pct": round(similarity_pct, 1),
                "matching_indicators": score,
                "indicators_compared": compared,
                "details": details[:5]
            })

    similarities.sort(key=lambda x: x["similarity_pct"], reverse=True)
    return similarities


# ================================================================
# AI PREDICTION
# Tries local Ollama model first, falls back to Claude API
# ================================================================
def get_ai_prediction(correlations, relationships, similarities, current_data):

    import requests as req

    top_corr = dict(list(correlations.items())[:15])
    top_rel = relationships[:10]
    top_similar = similarities[:3] if similarities else []

    # Load latest live prices if available
    live_path = f"{DATA_PATH}/live/latest.json"
    live_data = {}
    if os.path.exists(live_path):
        with open(live_path) as f:
            live_data = json.load(f)

    prompt = f"""You are ZAI — a macro market research AI built on 125+ years of financial data.

HISTORICAL CORRELATIONS (strongest relationships found):
{json.dumps(top_corr, indent=2)}

LEAD-LAG RELATIONSHIPS (which market moves before another):
{json.dumps(top_rel, indent=2)}

CURRENT CONDITIONS vs HISTORICAL CRASHES:
{json.dumps(top_similar, indent=2)}

LIVE MARKET DATA (today):
{json.dumps(live_data, indent=2)}

Based on all this data, give me your market prediction and research analysis.

Think about:
1. Which historical period does today most resemble and why?
2. What typically happened to markets after similar conditions?
3. What are the biggest warning signs right now?
4. What is your outlook for 4 weeks, 3 months, and 6 months?

Respond ONLY in this exact JSON format — no extra text:
{{
  "current_era_similarity": "which historical period this most resembles",
  "overall_market_outlook": "BULLISH/BEARISH/NEUTRAL/VOLATILE",
  "confidence": 0-100,
  "key_signals": ["signal1", "signal2", "signal3"],
  "warning_signs": ["warning1", "warning2"],
  "positive_signs": ["positive1", "positive2"],
  "predictions": {{
    "4_weeks":  {{"direction": "UP/DOWN/SIDEWAYS", "magnitude": "X%", "reasoning": "..."}},
    "3_months": {{"direction": "UP/DOWN/SIDEWAYS", "magnitude": "X%", "reasoning": "..."}},
    "6_months": {{"direction": "UP/DOWN/SIDEWAYS", "magnitude": "X%", "reasoning": "..."}}
  }},
  "crypto_specific": {{"outlook": "...", "key_driver": "..."}},
  "most_important_indicator_to_watch": "...",
  "summary": "2-3 sentence plain English summary"
}}"""

    # Try local Ollama first (free, no API costs)
    try:
        from config import LOCAL_LLM_MODEL, USE_LOCAL_LLM
        ollama_check = subprocess.run(["ollama", "list"],
                                       capture_output=True, timeout=5)
        if USE_LOCAL_LLM and ollama_check.returncode == 0:
            print(f"   Using local model: {LOCAL_LLM_MODEL}")
            result = subprocess.run(
                ["ollama", "run", LOCAL_LLM_MODEL, prompt],
                capture_output=True, text=True, timeout=180
            )
            if result.returncode == 0 and result.stdout.strip():
                text = result.stdout.strip()
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    prediction = json.loads(text[start:end])
                    print("   ✅ Local prediction complete!")
                    return prediction
    except Exception as e:
        print(f"   ⚠️  Ollama error: {e} — trying Claude API...")

    # Fallback: Claude API
    if not ANTHROPIC_KEY or ANTHROPIC_KEY == "YOUR_ANTHROPIC_API_KEY_HERE":
        print("   ⚠️  No API key — skipping AI prediction")
        return None

    try:
        response = req.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60
        )
        result = response.json()
        text = result["content"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return None


# ================================================================
# SAVE
# ================================================================
def save_analysis(correlations, relationships, crash_patterns, similarities, prediction):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    analysis = {
        "generated_at": datetime.now().isoformat(),
        "top_correlations": dict(list(correlations.items())[:20]),
        "lead_lag_relationships": relationships[:20],
        "crash_patterns_found": len(crash_patterns),
        "current_similarity": similarities[:5] if similarities else [],
        "ai_prediction": prediction
    }

    path = f"{DATA_PATH}/predictions/analysis_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(analysis, f, indent=2)

    latest_path = f"{DATA_PATH}/predictions/latest.json"
    with open(latest_path, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"✅ Saved: {path}")
    return analysis


# ================================================================
# RUN
# ================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 ZAI CORRELATION ENGINE")
    print("=" * 60)

    print("\n📂 Loading data...")
    data = load_all_data()

    if not data:
        print("❌ No data found. Run: python3 data_collector.py")
        exit()

    print(f"\n✅ {len(data)} datasets loaded")

    print("\n🔗 Merging datasets...")
    df = merge_data(data)
    print(f"   Shape: {df.shape}")

    print("\n📊 Calculating correlations...")
    correlations = find_correlations(df)
    print(f"   {len(correlations)} pairs found")

    print("\n⏱️  Finding lead-lag relationships...")
    relationships = find_lead_lag_relationships(df)
    print(f"   {len(relationships)} relationships found")

    print("\n💥 Analyzing historical crash patterns...")
    crash_patterns = extract_crash_patterns(df)
    print(f"   {len(crash_patterns)} crashes analyzed")

    print("\n🔍 Comparing current conditions to history...")
    similarities = compare_current_to_history(df, crash_patterns)
    if similarities:
        print(f"   Most similar to: {similarities[0]['crash']} ({similarities[0]['similarity_pct']}%)")

    print("\n🤖 Getting AI prediction...")
    prediction = get_ai_prediction(correlations, relationships, similarities, df)

    if prediction:
        print(f"\n{'=' * 60}")
        print("📋 PREDICTION:")
        print(f"   Outlook:    {prediction.get('overall_market_outlook')}")
        print(f"   Confidence: {prediction.get('confidence')}%")
        print(f"   Similar to: {prediction.get('current_era_similarity')}")
        print(f"   Summary:    {prediction.get('summary')}")
        print(f"{'=' * 60}")

    save_analysis(correlations, relationships, crash_patterns, similarities, prediction)
    print("\n✅ Done. Run dashboard: python3 dashboard.py")
