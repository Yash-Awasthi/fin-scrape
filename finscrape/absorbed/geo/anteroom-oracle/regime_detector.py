"""
ZAI Oracle — Regime Detector
by Zawwar (github.com/Zawwarsami16)

"Volatile" is not a regime. It's a cop-out.

This module classifies the ACTUAL market regime from a defined set
of states that have real historical precedent and distinct behaviors.
Each regime has known characteristics, typical durations, and
what usually happens next.

Regimes are mutually exclusive — the system picks the dominant one
based on weighted signals, then shows the drivers.

This is what Bloomberg-level systems do:
they don't say "markets are uncertain"
they say "RISK-OFF / WAR PREMIUM — Oil breakout, VIX elevated"
"""

# ================================================================
# REGIME DEFINITIONS
# Each regime has:
# - detection conditions (which signals trigger it)
# - typical characteristics
# - what usually happens to each asset class
# - historical examples
# - average duration
# ================================================================
REGIMES = {

    "RISK_OFF_WAR_PREMIUM": {
        "label":       "RISK-OFF / WAR PREMIUM",
        "color":       "RED",
        "conditions": {
            "requires": ["war_conflict"],
            "supports": ["oil_energy", "geopolitics"],
            "prices":   {"oil": ">85", "vix": ">22"},
        },
        "drivers_template": [
            "Active conflict headlines ({war_count} articles)",
            "Oil elevated at ${oil_price:.0f}",
            "VIX at {vix:.1f} — risk aversion rising",
        ],
        "asset_behavior": {
            "gold":    "BULLISH — safe haven demand",
            "oil":     "BULLISH — supply risk premium",
            "stocks":  "BEARISH — risk-off selling",
            "bonds":   "BULLISH — flight to safety",
            "crypto":  "BEARISH — liquidation risk",
            "usd":     "BULLISH — dollar as safe haven",
        },
        "typical_duration": "Days to weeks depending on escalation",
        "historical_examples": ["Gulf War 1990", "Ukraine invasion 2022", "9/11 2001"],
        "what_ends_it":   "Ceasefire news, de-escalation, or market exhaustion",
    },

    "INFLATION_SCARE": {
        "label":       "INFLATION SCARE",
        "color":       "ORANGE",
        "conditions": {
            "requires": ["inflation_dollar", "oil_energy"],
            "supports": ["central_banks"],
            "prices":   {"oil": ">80", "vix": ">18"},
        },
        "drivers_template": [
            "Inflation/dollar signals: {inflation_count} articles",
            "Oil at ${oil_price:.0f} adding to price pressure",
            "Fed language shifting hawkish",
        ],
        "asset_behavior": {
            "gold":    "BULLISH — inflation hedge",
            "oil":     "BULLISH — commodity inflation",
            "stocks":  "VOLATILE — multiple compression risk",
            "bonds":   "BEARISH — rate hike expectations",
            "crypto":  "MIXED — BTC as inflation hedge narrative",
            "usd":     "MIXED — depends on rate differentials",
        },
        "typical_duration": "Weeks to months",
        "historical_examples": ["1973 Oil Crisis", "2021-2022 Post-COVID inflation"],
        "what_ends_it":   "Fed rate hikes bring inflation under control, or oil collapses",
    },

    "POLICY_FREEZE": {
        "label":       "POLICY FREEZE",
        "color":       "YELLOW",
        "conditions": {
            "requires": ["central_banks"],
            "supports": ["recession_economy"],
            "prices":   {"vix": ">20"},
        },
        "drivers_template": [
            "Fed/central bank signals elevated: {fed_count} articles",
            "Markets waiting for policy clarity",
            "VIX at {vix:.1f} — uncertainty premium",
        ],
        "asset_behavior": {
            "gold":    "NEUTRAL to BULLISH",
            "stocks":  "RANGE-BOUND — no directional conviction",
            "bonds":   "VOLATILE — rate expectations shifting",
            "crypto":  "BEARISH — risk-off with no catalyst",
            "usd":     "BULLISH — carry trade unwinding",
        },
        "typical_duration": "Until next major Fed meeting or data print",
        "historical_examples": ["2019 Fed pause", "Late 2023 policy uncertainty"],
        "what_ends_it":   "Clear Fed signal — either cut or hike decision",
    },

    "PANIC": {
        "label":       "PANIC",
        "color":       "RED_BOLD",
        "conditions": {
            "requires": [],
            "supports": ["recession_economy", "war_conflict"],
            "prices":   {"vix": ">35"},
        },
        "drivers_template": [
            "VIX at {vix:.1f} — extreme fear territory",
            "Forced selling and margin calls likely",
            "Risk assets under severe pressure",
        ],
        "asset_behavior": {
            "gold":    "INITIALLY DOWN (margin calls), then STRONG",
            "oil":     "DOWN — demand destruction fears",
            "stocks":  "SEVERE SELLING",
            "bonds":   "BULLISH — flight to safety",
            "crypto":  "SEVERE SELLING — highest beta risk",
            "usd":     "VERY BULLISH — dollar wrecking ball",
        },
        "typical_duration": "Days to weeks",
        "historical_examples": ["COVID crash March 2020", "Lehman Sep 2008", "Black Monday 1987"],
        "what_ends_it":   "Central bank intervention, circuit breakers, or capitulation exhaustion",
    },

    "RISK_ON": {
        "label":       "RISK-ON",
        "color":       "GREEN",
        "conditions": {
            "requires": [],
            "supports": ["tech_ai", "elections_politics"],
            "prices":   {"vix": "<18", "sp500_chg": ">0"},
        },
        "drivers_template": [
            "VIX at {vix:.1f} — low fear, complacency building",
            "Equity markets in positive momentum",
            "Limited crisis signals in news",
        ],
        "asset_behavior": {
            "gold":    "NEUTRAL to WEAK",
            "stocks":  "BULLISH — momentum favors equities",
            "bonds":   "BEARISH — yield curve steepening",
            "crypto":  "BULLISH — speculative appetite high",
            "usd":     "NEUTRAL to WEAK",
        },
        "typical_duration": "Weeks to months",
        "historical_examples": ["2017 crypto bull", "2019 Fed pivot rally", "2023 AI boom"],
        "what_ends_it":   "Shock event, Fed tightening, or valuation exhaustion",
    },

    "LIQUIDITY_SQUEEZE": {
        "label":       "LIQUIDITY SQUEEZE",
        "color":       "RED",
        "conditions": {
            "requires": ["recession_economy"],
            "supports": ["central_banks", "inflation_dollar"],
            "prices":   {"vix": ">25"},
        },
        "drivers_template": [
            "Recession signals active: {recession_count} articles",
            "Credit conditions tightening",
            "Dollar strength squeezing dollar-denominated debt",
        ],
        "asset_behavior": {
            "gold":    "INITIALLY WEAK — forced selling, then STRONG",
            "stocks":  "BEARISH — earnings risk + multiple compression",
            "bonds":   "MIXED — quality bonds up, junk bonds crushed",
            "crypto":  "SEVERELY BEARISH",
            "usd":     "VERY BULLISH — dollar wrecking ball",
            "em":      "SEVERELY BEARISH — EM debt crisis risk",
        },
        "typical_duration": "Months",
        "historical_examples": ["2008 GFC", "2018 Q4", "EM crisis 1997"],
        "what_ends_it":   "Fed pivot to easing, QE injection, or debt restructuring",
    },

    "POST_SHOCK_RECOVERY": {
        "label":       "POST-SHOCK RECOVERY",
        "color":       "CYAN",
        "conditions": {
            "requires": [],
            "supports": [],
            "prices":   {"vix": "<25", "sp500_chg": ">1"},
        },
        "drivers_template": [
            "Selling exhaustion — oversold bounce",
            "Policy response in place",
            "VIX retreating from highs",
        ],
        "asset_behavior": {
            "gold":    "STABLE to DECLINING as fear recedes",
            "stocks":  "BULLISH — mean reversion, short covering",
            "crypto":  "STRONGLY BULLISH — high beta recovery",
            "bonds":   "STABLE — rates settling",
        },
        "typical_duration": "Weeks to months",
        "historical_examples": ["Post-COVID recovery Q2 2020", "Post-Lehman recovery 2009"],
        "what_ends_it":   "Recovery confirmed, new normal established",
    },

    "GEOPOLITICAL_TENSION": {
        "label":       "GEOPOLITICAL TENSION",
        "color":       "ORANGE",
        "conditions": {
            "requires": ["geopolitics"],
            "supports": ["war_conflict", "china_asia"],
            "prices":   {"vix": ">20"},
        },
        "drivers_template": [
            "Geopolitical signals: {geo_count} articles",
            "Trade/sanctions risk elevated",
            "Regional instability detected",
        ],
        "asset_behavior": {
            "gold":    "BULLISH — uncertainty premium",
            "oil":     "BULLISH if Middle East, mixed otherwise",
            "stocks":  "CAUTIOUS — headline risk elevated",
            "crypto":  "MIXED",
        },
        "typical_duration": "Weeks to months",
        "historical_examples": ["2018-19 US-China trade war", "Taiwan strait tensions"],
        "what_ends_it":   "Diplomatic resolution or escalation to full conflict",
    },
}


# ================================================================
# REGIME DETECTION ENGINE
# ================================================================
def detect_regime(signals, prices):
    """
    Analyzes current signals and prices to identify the dominant regime.

    Returns the best matching regime with drivers and confidence.
    """
    oil    = prices.get("oil",   {}).get("price",      0)
    vix    = prices.get("vix",   {}).get("price",      0)
    sp_chg = prices.get("sp500", {}).get("change_pct", 0)

    signal_counts = {k: v.get("count", 0) for k, v in signals.items()}

    scores = {}

    for regime_id, regime in REGIMES.items():
        score = 0

        # Required signals check
        cond = regime["conditions"]
        for req in cond.get("requires", []):
            if req in signal_counts and signal_counts[req] >= 3:
                score += 20

        # Supporting signals
        for sup in cond.get("supports", []):
            if sup in signal_counts and signal_counts[sup] >= 3:
                score += 8

        # Price conditions
        # oil/vix default to 0 when the live feed is missing a value, and a
        # real price is never 0, so skip those checks unless we actually have
        # data. Otherwise a "<threshold" condition (e.g. RISK_ON vix<18) would
        # pass on every outage and bias the classifier toward risk-on regimes.
        price_conds = cond.get("prices", {})
        if "oil" in price_conds and oil > 0:
            threshold = float(price_conds["oil"].replace(">", "").replace("<", ""))
            if ">" in price_conds["oil"] and oil > threshold:  score += 10
            if "<" in price_conds["oil"] and oil < threshold:  score += 10
        if "vix" in price_conds and vix > 0:
            threshold = float(price_conds["vix"].replace(">", "").replace("<", ""))
            if ">" in price_conds["vix"] and vix > threshold:  score += 10
            if "<" in price_conds["vix"] and vix < threshold:  score += 10
        if "sp500_chg" in price_conds:
            threshold = float(price_conds["sp500_chg"].replace(">", "").replace("<", ""))
            if ">" in price_conds["sp500_chg"] and sp_chg > threshold: score += 5
            if "<" in price_conds["sp500_chg"] and sp_chg < threshold: score += 5

        # PANIC override — VIX > 35 always means panic
        if regime_id == "PANIC" and vix > 35:
            score += 40

        scores[regime_id] = score

    # Pick the dominant regime
    best_id    = max(scores, key=scores.get)
    best_score = scores[best_id]
    best       = REGIMES[best_id]

    # If no regime scored meaningfully, return neutral
    if best_score < 15:
        return {
            "regime":     "NEUTRAL / WAIT-AND-SEE",
            "color":      "YELLOW",
            "drivers":    ["No dominant regime signal detected", "Mixed cross-asset signals"],
            "asset_behavior": {
                "gold":   "NEUTRAL",
                "stocks": "RANGE-BOUND",
                "crypto": "NEUTRAL",
            },
            "confidence": "LOW",
            "score":      best_score,
        }

    # Build driver strings with actual values
    drivers = []
    for template in best.get("drivers_template", []):
        try:
            driver = template.format(
                war_count       = signal_counts.get("war_conflict",    0),
                inflation_count = signal_counts.get("inflation_dollar", 0),
                recession_count = signal_counts.get("recession_economy",0),
                fed_count       = signal_counts.get("central_banks",   0),
                geo_count       = signal_counts.get("geopolitics",     0),
                oil_price       = oil,
                vix             = vix,
            )
            drivers.append(driver)
        except Exception:
            drivers.append(template)

    # Secondary regimes (runner-ups with significant scores)
    secondary = [
        {"regime": REGIMES[r]["label"], "score": s}
        for r, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)[1:3]
        if s >= 10 and r != best_id
    ]

    confidence = "HIGH" if best_score >= 35 else "MODERATE" if best_score >= 20 else "LOW"

    return {
        "regime":           best["label"],
        "color":            best["color"],
        "drivers":          drivers,
        "asset_behavior":   best["asset_behavior"],
        "typical_duration": best.get("typical_duration", "unknown"),
        "what_ends_it":     best.get("what_ends_it", ""),
        "historical_examples": best.get("historical_examples", []),
        "secondary_regimes": secondary,
        "confidence":       confidence,
        "score":            best_score,
    }


if __name__ == "__main__":
    test_signals = {
        "war_conflict": {"count": 18},
        "oil_energy":   {"count": 19},
        "geopolitics":  {"count": 8},
    }
    test_prices = {
        "oil":   {"price": 99,   "change_pct": 3.7},
        "vix":   {"price": 27.2, "change_pct": -0.4},
        "sp500": {"price": 6632, "change_pct": -0.6},
    }
    regime = detect_regime(test_signals, test_prices)
    print(f"\nREGIME: {regime['regime']}")
    print(f"Confidence: {regime['confidence']}")
    print("Drivers:")
    for d in regime["drivers"]:
        print(f"  - {d}")
    print("Asset behavior:")
    for asset, beh in regime["asset_behavior"].items():
        print(f"  {asset}: {beh}")
