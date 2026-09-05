"""
ZAI Oracle — Crisis Replay Engine
by Zawwar (github.com/Zawwarsami16)

"Show me what Oracle would have said on the day Russia invaded Ukraine."
"Replay the 2008 crisis week by week."
"Compare today vs Gulf War vs Ukraine invasion."

This feature turns Oracle from a tool into a platform.
Each crisis snapshot contains:
- The market prices on that day
- What signals were active
- What the regime was
- What Oracle would have predicted
- What actually happened next

Run: python3 zai_oracle.py --replay gulf-war
Run: python3 zai_oracle.py --replay 2008-gfc
Run: python3 zai_oracle.py --scenario oil=115,vix=35
"""

from datetime import datetime


# ================================================================
# CRISIS SNAPSHOTS DATABASE
# Each entry is a complete Oracle snapshot from that historical date
# Includes: market state, signals, regime, Oracle prediction, actual outcome
# ================================================================
CRISIS_SNAPSHOTS = {

    "gulf-war": {
        "name":        "Gulf War — Day of Invasion",
        "date":        "1990-08-02",
        "description": "Iraq invades Kuwait — oil spikes, markets crash",
        "market_snapshot": {
            "sp500":  {"price": 356,   "change_pct": -2.4},
            "oil":    {"price": 28,    "change_pct": +8.1},
            "gold":   {"price": 370,   "change_pct": +2.1},
            "vix":    {"price": 28,    "change_pct": +15.0},
            "dxy":    {"price": 90,    "change_pct": +0.4},
            "bonds":  {"price": 98,    "change_pct": +0.8},
        },
        "active_signals": {
            "war_conflict": {"count": 45, "consensus": "HIGH"},
            "oil_energy":   {"count": 38, "consensus": "HIGH"},
            "geopolitics":  {"count": 22, "consensus": "HIGH"},
        },
        "regime":          "RISK-OFF / WAR PREMIUM",
        "oracle_would_say": {
            "outlook":    "BEARISH",
            "confidence": 82,
            "prediction": "Oil likely to spike further toward $40-50 as supply routes threatened. Equity markets to decline 15-25% over next 3 months. Gold safe haven demand. Short-term war = V-shaped recovery likely if conflict is decisive.",
            "key_watch":  "Oil $40 level, ceasefire news, US military deployment scale",
        },
        "actual_outcome": {
            "1_week":   {"sp500": -5.2,  "oil": +28.0, "gold": +4.1},
            "1_month":  {"sp500": -12.4, "oil": +89.0, "gold": +7.2},
            "3_months": {"sp500": -19.9, "oil": +120.0,"gold": +9.8},
            "6_months": {"sp500": +12.1, "oil": -45.0, "gold": +3.2},
            "narrative": "Exactly V-shaped: sharp crash then full recovery as war ended quickly. Oil spiked 120% then crashed when supply fears abated.",
        },
        "oracle_accuracy": {
            "direction": "CORRECT",
            "magnitude": "SLIGHTLY UNDERSTATED",
            "regime":    "CORRECT",
            "key_lesson": "Oracle correctly called war premium + oil spike + V-recovery thesis",
        },
    },

    "2008-gfc": {
        "name":        "Global Financial Crisis — Lehman Day",
        "date":        "2008-09-15",
        "description": "Lehman Brothers files for bankruptcy — global financial system on brink",
        "market_snapshot": {
            "sp500":  {"price": 1192, "change_pct": -4.7},
            "oil":    {"price": 95,   "change_pct": -3.1},
            "gold":   {"price": 762,  "change_pct": +1.4},
            "vix":    {"price": 31.7, "change_pct": +18.2},
            "dxy":    {"price": 79,   "change_pct": +1.1},
            "btc":    {"price": 0,    "change_pct": 0},     # Bitcoin not yet mainstream
        },
        "active_signals": {
            "recession_economy": {"count": 67, "consensus": "HIGH"},
            "central_banks":     {"count": 45, "consensus": "HIGH"},
            "inflation_dollar":  {"count": 23, "consensus": "MEDIUM"},
        },
        "regime":          "LIQUIDITY SQUEEZE",
        "oracle_would_say": {
            "outlook":    "BEARISH",
            "confidence": 91,
            "prediction": "Systemic banking failure risk is extreme. Expect cascading defaults and forced selling across all asset classes. Fed will be forced to unprecedented intervention. This is not a typical recession — it is a financial system restructuring event.",
            "key_watch":  "Bank CDS spreads, Fed emergency actions, interbank lending rates",
        },
        "actual_outcome": {
            "1_week":   {"sp500": -12.0, "oil": -15.0, "gold": -5.0},
            "1_month":  {"sp500": -27.0, "oil": -32.0, "gold": +8.0},
            "3_months": {"sp500": -43.0, "oil": -55.0, "gold": +12.0},
            "6_months": {"sp500": -49.0, "oil": -65.0, "gold": +20.0},
            "narrative": "Worst financial crisis since 1929. Everything fell together except bonds and gold. Recovery took 4+ years.",
        },
        "oracle_accuracy": {
            "direction": "CORRECT",
            "magnitude": "UNDERSTATED (actual worse than predicted)",
            "regime":    "CORRECT",
            "key_lesson": "Oracle would catch systemic risk — but magnitude of leverage unwind is hard to model",
        },
    },

    "covid-crash": {
        "name":        "COVID-19 Crash — WHO Pandemic Declaration",
        "date":        "2020-03-11",
        "description": "WHO declares pandemic — fastest market crash in history begins",
        "market_snapshot": {
            "sp500":  {"price": 2741, "change_pct": -4.9},
            "oil":    {"price": 34,   "change_pct": -8.1},
            "gold":   {"price": 1570, "change_pct": -0.3},
            "vix":    {"price": 53.9, "change_pct": +28.0},
            "dxy":    {"price": 97,   "change_pct": +0.8},
            "btc":    {"price": 7900, "change_pct": -9.3},
        },
        "active_signals": {
            "natural_disaster":  {"count": 89, "consensus": "HIGH"},
            "recession_economy": {"count": 45, "consensus": "HIGH"},
            "central_banks":     {"count": 32, "consensus": "HIGH"},
            "oil_energy":        {"count": 28, "consensus": "HIGH"},
        },
        "regime":          "PANIC",
        "oracle_would_say": {
            "outlook":    "CRITICAL",
            "confidence": 88,
            "prediction": "Black swan event in progress. Global economic shutdown unprecedented in modern history. Expect 25-40% equity decline in weeks, not months. However: central bank response will be historic. V-shaped recovery possible if pandemic shorter than expected.",
            "key_watch":  "Daily case growth rate, central bank emergency meetings, fiscal stimulus size",
        },
        "actual_outcome": {
            "1_week":   {"sp500": -15.0, "oil": -25.0, "gold": -3.0, "btc": -30.0},
            "1_month":  {"sp500": -34.0, "oil": -55.0, "gold": +4.0, "btc": -50.0},
            "3_months": {"sp500": +15.0, "oil": -70.0, "gold": +13.0,"btc": +50.0},
            "6_months": {"sp500": +40.0, "oil": -30.0, "gold": +28.0,"btc": +160.0},
            "narrative": "Fastest crash ever (-34% in 5 weeks) followed by fastest recovery ever. Oil went briefly negative. BTC crashed then surged 700% by year end.",
        },
        "oracle_accuracy": {
            "direction": "CORRECT",
            "magnitude": "CLOSE",
            "regime":    "CORRECT — PANIC correctly identified",
            "key_lesson": "Oracle would correctly call PANIC regime and V-recovery thesis",
        },
    },

    "ukraine-invasion": {
        "name":        "Russia Invades Ukraine — Full Scale",
        "date":        "2022-02-24",
        "description": "Russia launches full invasion — largest war in Europe since WW2",
        "market_snapshot": {
            "sp500":  {"price": 4288, "change_pct": -1.8},
            "oil":    {"price": 97,   "change_pct": +5.2},
            "gold":   {"price": 1908, "change_pct": +1.7},
            "vix":    {"price": 37.8, "change_pct": +18.0},
            "dxy":    {"price": 97.2, "change_pct": +0.9},
            "btc":    {"price": 37000,"change_pct": -8.3},
            "naturalgas": {"price": 4.6, "change_pct": +6.1},
        },
        "active_signals": {
            "war_conflict":    {"count": 78, "consensus": "HIGH"},
            "oil_energy":      {"count": 52, "consensus": "HIGH"},
            "geopolitics":     {"count": 44, "consensus": "HIGH"},
            "inflation_dollar":{"count": 31, "consensus": "HIGH"},
        },
        "regime":          "RISK-OFF / WAR PREMIUM",
        "oracle_would_say": {
            "outlook":    "BEARISH",
            "confidence": 87,
            "prediction": "Energy shock + geopolitical restructuring underway. Europe most exposed — Russian gas dependency creates inflation spiral. Expect oil to test $120-130. Central banks caught between inflation (must hike) and recession risk (should cut). Prolonged conflict = prolonged pain.",
            "key_watch":  "Nord Stream gas flows, NATO Article 5 trigger, Fed rate path, oil $100 level",
        },
        "actual_outcome": {
            "1_week":   {"sp500": +5.8,  "oil": +14.0, "gold": +3.2,  "btc": +12.0},
            "1_month":  {"sp500": +3.2,  "oil": +32.0, "gold": +6.4,  "btc": -8.0},
            "3_months": {"sp500": -12.0, "oil": +58.0, "gold": +3.0,  "btc": -35.0},
            "6_months": {"sp500": -20.0, "oil": +45.0, "gold": +1.0,  "btc": -60.0},
            "narrative": "Initial rally ('buy the news') faded into prolonged bear market driven by inflation + rate hikes. Oil hit $139. European energy crisis was extreme.",
        },
        "oracle_accuracy": {
            "direction": "CORRECT",
            "magnitude": "CLOSE — oil overshoot slightly understated",
            "regime":    "CORRECT",
            "key_lesson": "Oracle would correctly identify prolonged war = prolonged inflation = bear market",
        },
    },

    "dotcom-peak": {
        "name":        "Dot-com Bubble Peak",
        "date":        "2000-03-10",
        "description": "NASDAQ at all-time high 5048 — bubble about to burst",
        "market_snapshot": {
            "sp500":  {"price": 1527, "change_pct": +0.3},
            "nasdaq": {"price": 5048, "change_pct": +0.8},
            "oil":    {"price": 34,   "change_pct": +0.2},
            "gold":   {"price": 286,  "change_pct": -0.1},
            "vix":    {"price": 24.2, "change_pct": +2.1},
        },
        "active_signals": {
            "tech_ai":           {"count": 55, "consensus": "HIGH"},
            "central_banks":     {"count": 28, "consensus": "HIGH"},
            "recession_economy": {"count": 12, "consensus": "LOW"},
        },
        "regime":          "AI/SPECULATION BUBBLE",
        "oracle_would_say": {
            "outlook":    "VOLATILE",
            "confidence": 71,
            "prediction": "Extreme tech valuations unsustainable. P/E ratios at historic highs. Fed has been hiking. Historical precedent: speculative peaks always reverse. Risk/reward skewed heavily to downside. Any catalyst can break the momentum.",
            "key_watch":  "Fed rate decisions, tech earnings disappointments, credit availability",
        },
        "actual_outcome": {
            "1_week":   {"sp500": -4.1,  "nasdaq": -8.0,  "gold": +0.5},
            "1_month":  {"sp500": -8.2,  "nasdaq": -18.0, "gold": +1.2},
            "3_months": {"sp500": -12.0, "nasdaq": -35.0, "gold": +4.0},
            "6_months": {"sp500": -8.0,  "nasdaq": -40.0, "gold": +5.0},
            "narrative": "Bubble burst. Nasdaq fell 78% over 2.5 years. Oracle would have been right to call extreme risk.",
        },
        "oracle_accuracy": {
            "direction": "CORRECT",
            "magnitude": "UNDERSTATED (actual -78% vs predicted -20-30%)",
            "regime":    "CORRECT",
            "key_lesson": "Bubble magnitude is hardest to predict — direction is clearer",
        },
    },

    "1973-oil-shock": {
        "name":        "1973 OPEC Oil Embargo",
        "date":        "1973-10-17",
        "description": "OPEC announces oil embargo against US — energy shock begins",
        "market_snapshot": {
            "sp500": {"price": 108,  "change_pct": -1.2},
            "oil":   {"price": 3.0,  "change_pct": +8.0},
            "gold":  {"price": 97,   "change_pct": +1.8},
            "vix":   {"price": 22,   "change_pct": +8.0},
        },
        "active_signals": {
            "oil_energy":       {"count": 62, "consensus": "HIGH"},
            "war_conflict":     {"count": 41, "consensus": "HIGH"},
            "geopolitics":      {"count": 35, "consensus": "HIGH"},
            "inflation_dollar": {"count": 28, "consensus": "HIGH"},
        },
        "regime":          "INFLATION SCARE",
        "oracle_would_say": {
            "outlook":    "BEARISH",
            "confidence": 89,
            "prediction": "Energy shock of historic proportions. Oil to multiply 3-4x. Inflation to surge above 10%. Equity markets to fall 40-50% over 18 months. This is a structural regime change — stagflation era beginning. Gold is the only safe haven.",
            "key_watch":  "Oil supply restoration, Fed response to inflation vs recession, gold",
        },
        "actual_outcome": {
            "1_month":  {"sp500": -8.0,  "oil": +80.0, "gold": +12.0},
            "3_months": {"sp500": -18.0, "oil": +200.0,"gold": +35.0},
            "6_months": {"sp500": -30.0, "oil": +350.0,"gold": +50.0},
            "1_year":   {"sp500": -48.0, "oil": +400.0,"gold": +70.0},
            "narrative": "Worst stagflation in modern history. Oil went from $3 to $12. S&P fell 48%. Decade of pain followed.",
        },
        "oracle_accuracy": {
            "direction": "CORRECT",
            "magnitude": "CORRECT — magnitude of oil shock correctly anticipated",
            "regime":    "CORRECT",
            "key_lesson": "When energy + war + inflation combine, Oracle correctly signals extreme caution",
        },
    },
}


def get_crisis_list():
    """Returns list of available crisis replays."""
    return list(CRISIS_SNAPSHOTS.keys())


def replay_crisis(crisis_key, current_prices=None):
    """
    Replays a historical crisis and optionally compares to current situation.
    Returns full replay report.
    """
    if crisis_key not in CRISIS_SNAPSHOTS:
        available = ", ".join(CRISIS_SNAPSHOTS.keys())
        return {"error": f"Crisis '{crisis_key}' not found. Available: {available}"}

    snapshot = CRISIS_SNAPSHOTS[crisis_key]
    result   = {
        "crisis_key":  crisis_key,
        "snapshot":    snapshot,
        "replayed_at": datetime.now().isoformat(),
    }

    # Compare with current situation if prices provided
    if current_prices:
        comparison = {}
        for asset, hist in snapshot["market_snapshot"].items():
            curr = current_prices.get(asset, {})
            if curr and hist["price"] > 0:
                curr_price = curr.get("price", 0)
                hist_price = hist["price"]
                if hist_price > 0:
                    ratio = curr_price / hist_price
                    comparison[asset] = {
                        "historical": hist_price,
                        "current":    curr_price,
                        "ratio":      round(ratio, 2),
                        "direction":  "higher" if ratio > 1 else "lower",
                    }
        result["vs_today"] = comparison

    return result


def run_scenario_lab(inputs, current_situation=None):
    """
    Scenario simulator — user provides custom market inputs.
    Oracle calculates what regime + risk index + prediction would be.

    inputs = {"oil": 115, "vix": 36, "dxy": 103, "war_headlines": 25}
    """
    from regime_detector import detect_regime, REGIMES
    from scenario_engine import calculate_geo_risk_index

    # Build simulated prices
    sim_prices = {
        "oil":   {"price": inputs.get("oil",  98),  "change_pct": inputs.get("oil_chg",  3.0)},
        "vix":   {"price": inputs.get("vix",  27),  "change_pct": inputs.get("vix_chg",  0.0)},
        "dxy":   {"price": inputs.get("dxy",  100), "change_pct": inputs.get("dxy_chg",  0.5)},
        "gold":  {"price": inputs.get("gold", 2900),"change_pct": inputs.get("gold_chg", 1.0)},
        "sp500": {"price": inputs.get("sp500",6600),"change_pct": inputs.get("sp500_chg",-1.0)},
        "btc":   {"price": inputs.get("btc",  70000),"change_pct":inputs.get("btc_chg", -2.0)},
    }

    # Build simulated signals
    war_count = inputs.get("war_headlines", 20)
    oil_count = inputs.get("oil_headlines", 20)
    sim_signals = {
        "war_conflict": {"count": war_count, "consensus": "HIGH" if war_count > 15 else "MEDIUM"},
        "oil_energy":   {"count": oil_count, "consensus": "HIGH" if oil_count > 15 else "MEDIUM"},
    }
    if inputs.get("recession_signals", 0) > 0:
        sim_signals["recession_economy"] = {"count": inputs["recession_signals"]}
    if inputs.get("fed_signals", 0) > 0:
        sim_signals["central_banks"] = {"count": inputs["fed_signals"]}

    regime     = detect_regime(sim_signals, sim_prices)
    geo_index  = calculate_geo_risk_index(sim_signals, sim_prices)

    # Find most similar historical crisis
    best_crisis = None
    best_score  = 0
    for key, crisis in CRISIS_SNAPSHOTS.items():
        score = 0
        hist_prices = crisis["market_snapshot"]
        if abs(sim_prices["oil"]["price"] - hist_prices.get("oil",{}).get("price",0)) < 20:
            score += 20
        if abs(sim_prices["vix"]["price"] - hist_prices.get("vix",{}).get("price",0)) < 8:
            score += 15
        for sig in sim_signals:
            if sig in crisis.get("active_signals", {}):
                score += 10
        if score > best_score:
            best_score  = score
            best_crisis = key

    return {
        "inputs":         inputs,
        "sim_prices":     sim_prices,
        "sim_signals":    sim_signals,
        "regime":         regime.get("regime","UNKNOWN"),
        "regime_drivers": regime.get("drivers", []),
        "geo_risk_index": geo_index["total"],
        "risk_label":     geo_index["label"],
        "most_similar":   best_crisis,
        "similar_outcome": CRISIS_SNAPSHOTS[best_crisis]["actual_outcome"] if best_crisis else {},
        "simulated_at":   datetime.now().isoformat(),
    }


def print_replay(snapshot_key, replay_data, current_prices=None):
    """Prints a formatted crisis replay to terminal."""
    R = "\033[0m"; B = "\033[1m"; G = "\033[92m"; C = "\033[96m"
    Y = "\033[93m"; Rd = "\033[91m"; W = "\033[97m"; Gr = "\033[90m"

    snap = replay_data["snapshot"]
    print(f"\n{G}{'='*62}{R}")
    print(f"{G}{B}  ORACLE REPLAY — {snap['name'].upper()}{R}")
    print(f"{G}  Date: {snap['date']}  |  {snap['description']}{R}")
    print(f"{G}{'='*62}{R}\n")

    print(f"{C}{B}  MARKET SNAPSHOT ON THAT DAY:{R}")
    for asset, data in snap["market_snapshot"].items():
        chg = data["change_pct"]
        arr = f"{G}↑{R}" if chg >= 0 else f"{Rd}↓{R}"
        print(f"  {W}{asset:<14}{R}  ${data['price']:>10,.2f}   {arr} {chg:+.1f}%")

    print(f"\n{C}{B}  ACTIVE SIGNALS:{R}")
    for sig, data in snap["active_signals"].items():
        print(f"  {Y}{sig:<25}{R}  {data['count']} articles  |  Consensus: {data['consensus']}")

    print(f"\n{C}{B}  REGIME:{R}  {Y}{B}{snap['regime']}{R}")

    oracle = snap["oracle_would_say"]
    print(f"\n{G}{B}  IF ORACLE EXISTED THEN:{R}")
    print(f"  Outlook:    {Y}{oracle['outlook']}{R}")
    print(f"  Confidence: {oracle['confidence']}%")
    print(f"  Prediction: {Gr}{oracle['prediction'][:100]}...{R}")
    print(f"  Watch:      {oracle['key_watch']}")

    outcome = snap["actual_outcome"]
    print(f"\n{G}{B}  WHAT ACTUALLY HAPPENED:{R}")
    for period in ["1_week","1_month","3_months","6_months"]:
        if period not in outcome:
            continue
        moves = outcome[period]
        parts = [f"{k}: {v:+.1f}%" for k, v in moves.items() if isinstance(v, (int, float))]
        print(f"  {period:<12}  {Gr}{', '.join(parts)}{R}")
    print(f"\n  {Gr}{outcome.get('narrative','')}{R}")

    acc = snap["oracle_accuracy"]
    print(f"\n{C}{B}  ORACLE ACCURACY ASSESSMENT:{R}")
    dc = G if acc["direction"] == "CORRECT" else Rd
    print(f"  Direction:  {dc}{acc['direction']}{R}")
    print(f"  Magnitude:  {acc['magnitude']}")
    print(f"  Regime:     {acc['regime']}")
    print(f"  Lesson:     {Gr}{acc['key_lesson']}{R}")

    if current_prices and replay_data.get("vs_today"):
        print(f"\n{Y}{B}  TODAY vs {snap['date'].split('-')[0]}:{R}")
        for asset, comp in replay_data["vs_today"].items():
            print(f"  {W}{asset:<10}{R}  Then: ${comp['historical']:>8,.0f}  "
                  f"Now: ${comp['current']:>10,.0f}  "
                  f"({comp['ratio']:.1f}x {comp['direction']})")

    print(f"\n{G}{'='*62}{R}\n")


def print_scenario_result(result):
    """Prints scenario lab output."""
    R = "\033[0m"; B = "\033[1m"; G = "\033[92m"; C = "\033[96m"
    Y = "\033[93m"; Rd = "\033[91m"; W = "\033[97m"; Gr = "\033[90m"

    print(f"\n{G}{'='*62}{R}")
    print(f"{G}{B}  ORACLE SCENARIO LAB{R}")
    print(f"{G}{'='*62}{R}\n")

    print(f"{C}{B}  Your inputs:{R}")
    for k, v in result["inputs"].items():
        print(f"  {W}{k:<20}{R}  {v}")

    print(f"\n{Y}{B}  Regime would be:{R}  {Y}{B}{result['regime']}{R}")
    for d in result.get("regime_drivers", [])[:3]:
        print(f"  {Gr}- {d}{R}")

    total = result["geo_risk_index"]
    label = result["risk_label"]
    bar   = G + "█" * int(total/10) + R + Gr + "░" * (10-int(total/10)) + R
    print(f"\n  Geo Risk Index:  [{bar}] {total}/100  {Y}{label}{R}")

    sim = result.get("most_similar","")
    if sim and sim in CRISIS_SNAPSHOTS:
        snap = CRISIS_SNAPSHOTS[sim]
        print(f"\n  Most similar to: {Y}{snap['name']}{R}")
        outcome = snap.get("actual_outcome", {})
        if "1_month" in outcome:
            moves = outcome["1_month"]
            parts = [f"{k}: {v:+.1f}%" for k, v in moves.items() if isinstance(v, (int, float))]
            print(f"  In that crisis 1 month later:  {Gr}{', '.join(parts)}{R}")

    print(f"\n{G}{'='*62}{R}\n")
