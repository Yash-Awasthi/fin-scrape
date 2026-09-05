"""
ZAI Oracle — Sanity Validator
by Zawwar (github.com/Zawwarsami16)

Before any price hits the screen or goes into the AI prompt,
it passes through here. If something looks wrong — wrong range,
stale timestamp, suspicious spike — it gets flagged or corrected.

Gold showing $5,023 when real gold is $2,900 is a trust killer.
This module prevents that.

Also handles:
- yfinance futures vs spot price confusion (GC=F gives wrong gold price)
- Stale data detection (price not updated in X minutes)
- Percentage change sanity (>20% in one day = flag it)
- Unit normalization (some APIs return cents, not dollars)
"""

import os
import json
import time
import requests
from datetime import datetime


# ================================================================
# VALID PRICE RANGES PER ASSET
# These are wide enough to never false-positive in normal markets
# but tight enough to catch API bugs and contract mismatches
# ================================================================
VALID_RANGES = {
    "sp500":       (500,    10000),    # S&P 500
    "nasdaq":      (5000,   30000),    # NASDAQ Composite
    "dow":         (10000,  60000),    # Dow Jones
    "gold":        (1200,   4000),     # Gold spot $/oz
    "silver":      (10,     200),      # Silver spot $/oz
    "oil":         (20,     250),      # Crude oil $/barrel
    "natural_gas": (1,      20),       # Natural gas $/MMBtu
    "copper":      (2,      15),       # Copper $/lb
    "vix":         (5,      90),       # VIX fear index
    "dxy":         (70,     130),      # Dollar index
    "tnx":         (0.1,    15),       # 10Y Treasury yield %
    "nikkei":      (10000,  60000),    # Nikkei 225
    "ftse":        (5000,   10000),    # FTSE 100
    "eur_usd":     (0.8,    1.5),      # EUR/USD
    "usd_jpy":     (80,     200),      # USD/JPY
    "btc":         (1000,   250000),   # Bitcoin
    "eth":         (50,     20000),    # Ethereum
    "sol":         (5,      1000),     # Solana
    "bnb":         (10,     2000),     # BNB
    "xrp":         (0.1,    10),       # XRP
}

# Max realistic single-day % change per asset
# Beyond this = likely data error, not a real move
MAX_DAILY_CHANGE = {
    "sp500":       12,
    "nasdaq":      15,
    "dow":         12,
    "gold":        8,
    "silver":      15,
    "oil":         25,
    "natural_gas": 30,
    "vix":         80,    # VIX can spike hard
    "dxy":         5,
    "btc":         35,
    "eth":         40,
    "sol":         50,
    "bnb":         30,
    "xrp":         50,
}

# Known yfinance tickers that return FUTURES prices instead of spot
# These need a correction factor or alternative source
FUTURES_CORRECTION = {
    "gold":    {"ticker": "GC=F", "note": "Futures price ~$20-50 above spot"},
    "silver":  {"ticker": "SI=F", "note": "Futures price ~$0.10 above spot"},
    "oil":     {"ticker": "CL=F", "note": "WTI futures — close to spot"},
    "natural_gas": {"ticker": "NG=F", "note": "Henry Hub futures"},
    "copper":  {"ticker": "HG=F", "note": "Futures in cents/lb — multiply by 100"},
}


# ================================================================
# SPOT PRICE FETCHER
# For assets where yfinance gives wrong price, fetch from better source
# ================================================================
def fetch_spot_gold():
    """
    Fetches real gold spot price from multiple free sources.
    yfinance GC=F gives futures which can be $20-50 off.
    Falls back gracefully if all sources fail.
    """
    sources = [
        # Gold API (free tier)
        {
            "url":    "https://api.gold-api.com/price/XAU",
            "parser": lambda d: d.get("price"),
        },
        # Metals API (free)
        {
            "url":    "https://metals-api.com/api/latest?access_key=free&base=USD&symbols=XAU",
            "parser": lambda d: 1 / d.get("rates", {}).get("XAU", 0) if d.get("rates", {}).get("XAU") else None,
        },
    ]

    for source in sources:
        try:
            r = requests.get(source["url"], timeout=8)
            data = r.json()
            price = source["parser"](data)
            if price and 1500 < price < 4000:
                return round(float(price), 2)
        except Exception:
            continue

    return None  # will fall back to yfinance with warning


def fetch_spot_silver():
    """Fetches real silver spot price."""
    try:
        r = requests.get("https://api.gold-api.com/price/XAG", timeout=8)
        data = r.json()
        price = data.get("price")
        if price and 10 < float(price) < 200:
            return round(float(price), 2)
    except Exception:
        pass
    return None


# ================================================================
# MAIN VALIDATION FUNCTION
# ================================================================
def validate_and_fix_prices(raw_prices):
    """
    Takes the raw price dict from world_scanner.py and:
    1. Checks each price against valid ranges
    2. Flags suspicious daily changes
    3. Attempts to fix known issues (gold futures vs spot)
    4. Adds validation metadata to each price entry
    5. Returns cleaned prices + validation report

    Returns: (cleaned_prices, validation_report)
    """
    cleaned  = {}
    warnings = []
    fixed    = []
    errors   = []

    for asset, data in raw_prices.items():
        if not isinstance(data, dict):
            continue

        price = data.get("price", 0)
        chg   = data.get("change_pct", 0)

        entry = data.copy()
        entry["validated"] = True
        entry["warnings"]  = []

        # --- Range check ---
        if asset in VALID_RANGES:
            lo, hi = VALID_RANGES[asset]

            # Special case: copper from yfinance comes in cents/lb
            if asset == "copper" and price < 2:
                price = price * 100
                entry["price"] = round(price, 2)
                fixed.append(f"{asset}: corrected cents→dollars (${entry['price']:.2f})")

            if not (lo <= price <= hi):
                # Try to fix gold specifically (known futures issue)
                if asset == "gold":
                    spot = fetch_spot_gold()
                    if spot:
                        entry["price"]        = spot
                        entry["price_source"] = "spot (corrected from futures)"
                        fixed.append(f"gold: corrected futures ${price:.0f} → spot ${spot:.0f}")
                        price = spot
                    else:
                        entry["warnings"].append(f"price ${price:.0f} outside valid range ${lo}-${hi}")
                        warnings.append(f"{asset}: suspicious price ${price:.2f} (valid: ${lo}-${hi})")

                elif asset == "silver":
                    spot = fetch_spot_silver()
                    if spot:
                        entry["price"]        = spot
                        entry["price_source"] = "spot (corrected)"
                        fixed.append(f"silver: corrected to spot ${spot:.2f}")
                        price = spot
                    else:
                        entry["warnings"].append(f"price ${price:.2f} outside valid range")
                        warnings.append(f"{asset}: price ${price:.2f} outside valid range")

                else:
                    entry["validated"] = False
                    entry["warnings"].append(f"price ${price:.2f} outside valid range ${lo}-${hi}")
                    errors.append(f"{asset}: price ${price:.2f} outside expected ${lo}-${hi}")

        # --- Daily change sanity ---
        max_chg = MAX_DAILY_CHANGE.get(asset, 25)
        if abs(chg) > max_chg:
            entry["warnings"].append(f"unusual daily change {chg:+.1f}% (max expected ±{max_chg}%)")
            warnings.append(f"{asset}: {chg:+.1f}% daily change seems extreme")

        # --- Stale data detection ---
        updated = entry.get("updated", "")
        if updated:
            try:
                update_time = datetime.fromisoformat(updated)
                age_minutes = (datetime.now() - update_time).total_seconds() / 60
                entry["data_age_minutes"] = round(age_minutes, 1)
                if age_minutes > 30:
                    entry["warnings"].append(f"data is {age_minutes:.0f} min old")
                    warnings.append(f"{asset}: data stale ({age_minutes:.0f} min)")
            except Exception:
                pass

        cleaned[asset] = entry

    report = {
        "total_assets":   len(cleaned),
        "warnings_count": len(warnings),
        "fixed_count":    len(fixed),
        "errors_count":   len(errors),
        "warnings":       warnings,
        "fixed":          fixed,
        "errors":         errors,
        "validated_at":   datetime.now().isoformat(),
    }

    return cleaned, report


# ================================================================
# CONFIDENCE FORMULA
# This is the actual math behind every confidence score
# Shown in --explain mode so users can audit it
# ================================================================
def calculate_confidence(news_signals=None, hist_matches=None, whale_data=None, prices=None):
    """
    Transparent confidence calculation.
    Every component is documented so the user can verify it.

    Returns: (score 0-100, breakdown dict)
    """
    components = {}
    total = 0

    # Component 1: Signal volume (max 25 points)
    # More articles from diverse sources = more confidence
    total_articles = sum(s.get("count", 0) for s in news_signals.values())
    signal_score   = min(total_articles / 4, 25)  # 100 articles = max score
    components["signal_volume"] = {
        "score":   round(signal_score, 1),
        "max":     25,
        "formula": f"min({total_articles} articles / 4, 25)",
        "meaning": "More articles from more sources = higher confidence"
    }
    total += signal_score

    # Component 2: Historical match quality (max 30 points)
    # How well does today match a historical event?
    top_match    = (hist_matches.get("top_matches") or [{}])[0]
    similarity   = top_match.get("similarity", 0)
    hist_score   = similarity * 0.30  # 100% similarity = 30 points
    components["historical_match"] = {
        "score":   round(hist_score, 1),
        "max":     30,
        "formula": f"{similarity}% similarity × 0.30",
        "meaning": "Stronger historical parallel = higher confidence",
        "best_match": top_match.get("name", "none"),
    }
    total += hist_score

    # Component 3: Cross-domain signal agreement (max 20 points)
    # When war news + oil news + market stress all point same way
    active_domains = len([s for s in news_signals.values() if s.get("count", 0) >= 3])
    cross_score    = min(active_domains * 4, 20)
    components["cross_domain_agreement"] = {
        "score":   round(cross_score, 1),
        "max":     20,
        "formula": f"min({active_domains} active domains × 4, 20)",
        "meaning": "More domains confirming same risk = higher confidence"
    }
    total += cross_score

    # Component 4: Whale signal alignment (max 15 points)
    # When whales move same direction as macro signals
    whale_sig = (whale_data or {}).get("summary", {}).get("overall_signal", "")
    whale_conf= (whale_data or {}).get("summary", {}).get("confidence", "LOW")
    if whale_conf == "HIGH":
        whale_score = 15
    elif "MOVEMENT" in whale_sig or "ACCUMUL" in whale_sig or "EXIT" in whale_sig:
        whale_score = 8
    else:
        whale_score = 3
    components["whale_alignment"] = {
        "score":   whale_score,
        "max":     15,
        "formula": f"HIGH confidence=15, signal detected=8, quiet=3",
        "meaning": "Smart money moving = adds confidence to prediction",
        "whale_signal": whale_sig[:50] if whale_sig else "none",
    }
    total += whale_score

    # Component 5: Market stress confirmation (max 10 points)
    # VIX elevation, oil spike, gold flight all confirm risk
    stress_signals = 0
    oil   = prices.get("oil",  {}).get("price", 0)
    vix   = prices.get("vix",  {}).get("price", 0)
    gold  = prices.get("gold", {}).get("change_pct", 0)
    if vix   > 25: stress_signals += 1
    if oil   > 90: stress_signals += 1
    if gold  > 1:  stress_signals += 1
    if vix   > 35: stress_signals += 1  # extra weight for extreme fear
    market_score = min(stress_signals * 3, 10)
    components["market_stress_confirmation"] = {
        "score":   market_score,
        "max":     10,
        "formula": f"{stress_signals} stress indicators × 3",
        "meaning": "VIX>25, Oil>$90, Gold rising = confirms prediction",
    }
    total += market_score

    # Penalties for data quality issues
    penalties = {}

    # Missing whale data penalty
    whale_btc = (whale_data or {}).get("btc", {}).get("wallets_checked", 0)
    if whale_btc == 0:
        penalty = 5
        total  -= penalty
        penalties["missing_whale_data"] = f"-{penalty} pts (BTC wallets not connected)"

    # Source conflict penalty (price outside range)
    conflicts = (news_signals or {})  # reuse news_signals count for diversity check
    if prices:
        bad_prices = sum(1 for p in prices.values()
                        if isinstance(p, dict) and p.get("trust") == "LOW")
        if bad_prices > 0:
            penalty = bad_prices * 3
            total  -= penalty
            penalties["data_conflict_penalty"] = f"-{penalty} pts ({bad_prices} price conflicts)"

    # Stale data penalty
    stale_count = sum(1 for p in (prices or {}).values()
                     if isinstance(p, dict) and p.get("data_age_minutes", 0) > 30)
    if stale_count > 0:
        penalty = stale_count * 2
        total  -= penalty
        penalties["stale_data_penalty"] = f"-{penalty} pts ({stale_count} stale feeds)"

    final_score = round(max(0, min(total, 100)), 1)

    return final_score, {
        "final_score":  final_score,
        "components":   components,
        "penalties":    penalties,
        "interpretation": (
            "HIGH"     if final_score >= 70 else
            "MODERATE" if final_score >= 45 else
            "LOW"
        ),
        "calculated_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    # Quick test
    test_prices = {
        "gold":  {"price": 5023, "change_pct": -1.8, "updated": datetime.now().isoformat()},
        "oil":   {"price": 99.3, "change_pct": 3.7,  "updated": datetime.now().isoformat()},
        "btc":   {"price": 70800,"change_pct": -1.3,  "updated": datetime.now().isoformat()},
        "sp500": {"price": 6632, "change_pct": -0.6,  "updated": datetime.now().isoformat()},
    }
    cleaned, report = validate_and_fix_prices(test_prices)
    print(f"Fixed: {report['fixed']}")
    print(f"Warnings: {report['warnings']}")
    for asset, data in cleaned.items():
        print(f"{asset}: ${data['price']} {data.get('warnings', [])}")
