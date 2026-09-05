"""
ZAI Oracle — Scenario Engine v2.0
by Zawwar (github.com/Zawwarsami16)

Probability-based scenario forecasting — not generic prose.
Bull / Base / Bear with explicit triggers and invalidation conditions.
Geopolitical Risk Index — numerical 0-100 score with sub-indexes.
Explainability layer — why Oracle thinks what it thinks.
Cross-market causal chain — oil → inflation → yields → stocks.
"""

from datetime import datetime


# ================================================================
# GEOPOLITICAL RISK INDEX
# Numerical score 0-100 with sub-components
# ================================================================
def calculate_geo_risk_index(signals, prices):
    """
    Builds a numerical Geopolitical Risk Index (0-100).
    Sub-indexes: war, energy, sanctions, politics, financial.
    """
    components = {}

    # War escalation risk (0-25)
    war_count = signals.get("war_conflict", {}).get("count", 0)
    war_score = min(war_count * 1.2, 25)
    components["war_escalation"] = {
        "score":   round(war_score, 1),
        "max":     25,
        "trend":   "rising" if war_count > 15 else "stable",
        "note":    f"{war_count} conflict articles detected",
    }

    # Energy/oil chokepoint risk (0-20)
    oil_count = signals.get("oil_energy", {}).get("count", 0)
    oil_price = prices.get("oil", {}).get("price", 70)
    oil_score = min(oil_count * 0.8 + max(0, (oil_price - 70) * 0.3), 20)
    components["energy_chokepoint"] = {
        "score":   round(oil_score, 1),
        "max":     20,
        "trend":   "critical" if oil_price > 95 else "elevated" if oil_price > 80 else "normal",
        "note":    f"Oil at ${oil_price:.0f}, {oil_count} energy articles",
    }

    # Sanctions/trade conflict risk (0-15)
    geo_count = signals.get("geopolitics", {}).get("count", 0)
    san_score = min(geo_count * 1.5, 15)
    components["sanctions_trade"] = {
        "score":   round(san_score, 1),
        "max":     15,
        "trend":   "elevated" if geo_count > 5 else "normal",
        "note":    f"{geo_count} geopolitical articles",
    }

    # Political instability (0-15)
    pol_count = signals.get("elections_politics", {}).get("count", 0)
    pol_score = min(pol_count * 1.2, 15)
    components["political_instability"] = {
        "score":   round(pol_score, 1),
        "max":     15,
        "trend":   "uncertain" if pol_count > 8 else "stable",
        "note":    f"{pol_count} political articles",
    }

    # Financial systemic risk (0-15)
    vix      = prices.get("vix",  {}).get("price",      20)
    rec_count= signals.get("recession_economy", {}).get("count", 0)
    fin_score= min((max(0, vix - 15) * 0.8) + rec_count * 0.8, 15)
    components["financial_stress"] = {
        "score":   round(fin_score, 1),
        "max":     15,
        "trend":   "stressed" if vix > 28 else "elevated" if vix > 22 else "normal",
        "note":    f"VIX at {vix:.1f}, {rec_count} recession articles",
    }

    # Cyber/tech disruption (0-10)
    tech_count = signals.get("tech_ai", {}).get("count", 0)
    tech_score = min(tech_count * 0.5, 10)
    components["tech_disruption"] = {
        "score":   round(tech_score, 1),
        "max":     10,
        "note":    f"{tech_count} tech/AI articles",
    }

    total_score = sum(c["score"] for c in components.values())
    total_score = round(min(total_score, 100), 1)

    risk_label = (
        "EXTREME"   if total_score >= 80 else
        "CRITICAL"  if total_score >= 65 else
        "HIGH"      if total_score >= 45 else
        "ELEVATED"  if total_score >= 30 else
        "MODERATE"  if total_score >= 15 else
        "LOW"
    )

    fastest_rising = max(components.items(),
                         key=lambda x: x[1]["score"] / x[1]["max"])[0]

    return {
        "total":          total_score,
        "label":          risk_label,
        "components":     components,
        "fastest_rising": fastest_rising.replace("_", " ").title(),
        "calculated_at":  datetime.now().isoformat(),
    }


# ================================================================
# CROSS-MARKET CAUSAL CHAIN
# Shows how signals propagate through markets
# ================================================================
def build_causal_chain(signals, prices):
    """
    Detects active causal chains — how one signal drives another.
    Example: Oil spike → inflation fear → yields rise → stocks pressure
    """
    chains = []

    oil_price  = prices.get("oil",  {}).get("price",      0)
    oil_change = prices.get("oil",  {}).get("change_pct", 0)
    vix        = prices.get("vix",  {}).get("price",      0)
    gold_change= prices.get("gold", {}).get("change_pct", 0)
    tnx        = prices.get("tnx",  {}).get("price",      0)
    dxy_change = prices.get("dxy",  {}).get("change_pct", 0)
    sp_change  = prices.get("sp500",{}).get("change_pct", 0)
    btc_change = prices.get("btc",  {}).get("change_pct", 0)

    # Chain 1: Energy shock inflation
    if oil_change > 2 and oil_price > 85:
        chains.append({
            "name":   "Energy Shock",
            "chain":  f"Oil +{oil_change:.1f}% → inflation pressure → yields rise → stock compression",
            "active": True,
            "severity": "HIGH" if oil_price > 95 else "MODERATE",
        })

    # Chain 2: War risk premium
    war_count = signals.get("war_conflict", {}).get("count", 0)
    if war_count > 10:
        chains.append({
            "name":   "War Risk Premium",
            "chain":  f"War headlines ({war_count}) → oil bid → gold safe haven → equity risk-off",
            "active": True,
            "severity": "HIGH",
        })

    # Chain 3: Dollar wrecking ball
    if dxy_change > 0.5:
        chains.append({
            "name":   "Dollar Wrecking Ball",
            "chain":  f"DXY +{dxy_change:.1f}% → EM pressure → crypto/gold headwind → commodities USD squeeze",
            "active": True,
            "severity": "MODERATE",
        })

    # Chain 4: Rates killing growth
    if tnx > 4.5:
        chains.append({
            "name":   "Rate Pressure",
            "chain":  f"10Y yield at {tnx:.2f}% → equity multiple compression → growth stocks lead down",
            "active": True,
            "severity": "HIGH" if tnx > 5.0 else "MODERATE",
        })

    # Chain 5: Fear spiral
    if vix > 25 and sp_change < -1:
        chains.append({
            "name":   "Fear Spiral",
            "chain":  f"VIX at {vix:.1f} + S&P {sp_change:.1f}% → margin calls possible → gold bid",
            "active": True,
            "severity": "HIGH" if vix > 30 else "MODERATE",
        })

    # Chain 6: Crypto risk-off
    if btc_change < -4 and vix > 22:
        chains.append({
            "name":   "Crypto Risk-Off",
            "chain":  f"BTC {btc_change:.1f}% + elevated VIX → risk appetite shrinking → alts under pressure",
            "active": True,
            "severity": "MODERATE",
        })

    return chains


# ================================================================
# SCENARIO ENGINE
# ================================================================
def build_scenarios(world_situation, hist_matches, signals, prices, regime):
    """
    Builds probability-weighted Bull/Base/Bear scenarios.
    Not generic prose — specific triggers and invalidation conditions.
    """
    risk_level  = world_situation.get("risk_level", "MODERATE")
    top_match   = (hist_matches.get("top_matches") or [{}])[0]
    hist_name   = top_match.get("name", "historical precedent")
    hist_lesson = top_match.get("lesson", "")
    oil_price   = prices.get("oil",  {}).get("price",      0)
    vix         = prices.get("vix",  {}).get("price",      0)
    war_count   = signals.get("war_conflict", {}).get("count", 0)

    # Determine base probabilities from risk level
    risk_probs = {
        "CRITICAL":  {"bull": 15, "base": 35, "bear": 50},
        "HIGH":      {"bull": 20, "base": 45, "bear": 35},
        "ELEVATED":  {"bull": 25, "base": 50, "bear": 25},
        "MODERATE":  {"bull": 35, "base": 45, "bear": 20},
        "LOW":       {"bull": 50, "base": 35, "bear": 15},
    }
    probs = risk_probs.get(risk_level, {"bull": 25, "base": 50, "bear": 25})

    # Build scenario content
    scenarios = {
        "base": {
            "label":       "Base Case",
            "probability": probs["base"],
            "outlook":     "VOLATILE",
            "market_path": f"Choppy markets, oil stays elevated, equities range-bound",
            "4_weeks":     f"S&P ±5-8%, Oil holds ${oil_price:.0f}-{oil_price+10:.0f}",
            "3_months":    "Gradual resolution or normalization of top crisis",
            "triggers":    ["No major escalation", "Central bank stays cautious", "Oil stabilizes"],
            "invalidated_if": [
                f"Oil breaks above ${oil_price*1.2:.0f}",
                f"VIX surges above {vix+10:.0f}",
                "Major new conflict zone opens",
            ],
        },

        "bear": {
            "label":       "Bear Case",
            "probability": probs["bear"],
            "outlook":     "BEARISH",
            "market_path": "Conflict escalates, oil spikes, risk assets dump",
            "4_weeks":     "S&P -10 to -20%, Oil +30-50%, Gold +10-15%",
            "3_months":    "Recession fears build, earnings guidance cut",
            "triggers":    [
                f"Oil closes above ${oil_price*1.15:.0f} for 3+ sessions",
                f"VIX breaks above {vix*1.3:.0f}",
                f"War spreads to {war_count + 2}+ active fronts",
                "Fed forced to hike despite weak economy",
            ],
            "invalidated_if": [
                "Ceasefire or diplomatic breakthrough",
                "Oil demand destruction pulls price back",
                "Fed pivots to emergency support",
            ],
        },

        "bull": {
            "label":       "Bull Case",
            "probability": probs["bull"],
            "outlook":     "BULLISH",
            "market_path": "Tensions ease, oil retreats, risk-on returns",
            "4_weeks":     "S&P +5-10%, Oil -10-20%, Crypto leads recovery",
            "3_months":    "V-shaped recovery, similar to Gulf War post-conflict",
            "triggers":    [
                f"Oil drops back below ${oil_price*0.85:.0f}",
                f"VIX returns to sub-20",
                "Diplomatic progress confirmed",
                "Fed signals pause or cut",
            ],
            "invalidated_if": [
                "New escalation event",
                "Inflation re-accelerates",
                "Bank or credit event emerges",
            ],
        },
    }

    # Add historical context
    scenarios["historical_note"] = (
        f"Most similar historical event: {hist_name}. "
        f"{hist_lesson}"
    ) if hist_name else ""

    return scenarios


# ================================================================
# EXPLAINABILITY LAYER
# ================================================================
def build_explanation(signals, prices, hist_matches, whale_data, regime, conf_breakdown):
    """
    Produces a transparent explanation of why Oracle thinks what it thinks.
    Shows top supporting signals, contradicting signals, and weakest component.
    """
    supporting    = []
    contradicting = []

    oil_price  = prices.get("oil",  {}).get("price",      0)
    vix        = prices.get("vix",  {}).get("price",      0)
    gold_chg   = prices.get("gold", {}).get("change_pct", 0)
    sp_chg     = prices.get("sp500",{}).get("change_pct", 0)
    war_count  = signals.get("war_conflict", {}).get("count", 0)
    oil_count  = signals.get("oil_energy",   {}).get("count", 0)
    top_match  = (hist_matches.get("top_matches") or [{}])[0]
    sim        = top_match.get("similarity", 0)

    # Supporting evidence
    if war_count > 10:
        supporting.append(f"War/conflict signal elevated ({war_count} articles)")
    if oil_price > 90:
        supporting.append(f"Oil at ${oil_price:.0f} — supply risk premium")
    if vix > 25:
        supporting.append(f"VIX at {vix:.1f} — market pricing in fear")
    if gold_chg > 1:
        supporting.append(f"Gold rising +{gold_chg:.1f}% — safe haven demand")
    if sim > 70:
        supporting.append(f"Historical parallel: {top_match.get('name','')} at {sim}% similarity")
    if oil_count > 10:
        supporting.append(f"Energy disruption narrative strong ({oil_count} articles)")

    # Contradicting evidence
    if sp_chg > 0:
        contradicting.append(f"S&P 500 still positive +{sp_chg:.1f}% — no panic yet")
    whale_sig = (whale_data or {}).get("summary", {}).get("overall_signal", "")
    if "ACCUM" in whale_sig:
        contradicting.append("Whale wallets accumulating — smart money buying dips")
    if vix < 20:
        contradicting.append(f"VIX at {vix:.1f} — market not yet pricing crisis")
    if war_count < 5:
        contradicting.append("War signal count low — may be media noise, not escalation")

    # Find weakest confidence component
    weakest = "whale alignment"
    lowest_pct = 100
    if conf_breakdown:
        for name, comp in conf_breakdown.get("components", {}).items():
            s  = comp.get("score", 0)
            mx = comp.get("max",   1)
            pct = s / mx * 100 if mx else 0
            if pct < lowest_pct:
                lowest_pct = pct
                weakest    = name

    # Missing data
    missing = []
    if (whale_data or {}).get("btc", {}).get("wallets_checked", 0) == 0:
        missing.append("BTC whale wallet data unavailable — reduces confidence")
    if len(supporting) < 3:
        missing.append("Limited supporting signals — prediction less certain")

    return {
        "supporting":    supporting[:5],
        "contradicting": contradicting[:3],
        "weakest_link":  weakest.replace("_", " "),
        "weakest_pct":   round(lowest_pct, 1),
        "missing_data":  missing,
    }
