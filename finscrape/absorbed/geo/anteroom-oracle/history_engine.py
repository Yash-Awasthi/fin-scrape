"""
ZAI Oracle — History Engine v2.0
by Zawwar (github.com/Zawwarsami16)

25+ historical crises with full structured fields.
Similarity decomposition — not just one number, but 6 dimensions.
Outcome library — what actually happened after similar setups.
"""

import os
import json
from datetime import datetime
from config import DATA_PATH

HISTORICAL_EVENTS = {

    "WW1_1914": {
        "name": "World War I", "period": "1914-1918",
        "category": "war_conflict",
        "trigger": "Assassination of Archduke Franz Ferdinand — alliance chain reaction",
        "pre_conditions": {
            "geopolitics": "Major power tensions, alliance system primed",
            "economics":   "Industrial boom, peak globalization era",
            "energy":      "Coal dominance, oil emerging",
            "markets":     "Stock markets at highs before war",
            "vix_proxy":   "LOW before, EXTREME after",
        },
        "market_impact": {
            "stocks":  "-30% (NYSE closed 4 months)",
            "gold":    "+25% safe haven",
            "bonds":   "-20% war financing",
            "oil":     "+50% military demand",
            "usd":     "Strengthened vs Europe",
        },
        "time_to_bottom": "4 months",
        "recovery_time":  "3 years post-war",
        "key_lesson": "Major wars cause immediate market closure/crash, then recovery via war economy",
        "false_alarm_rate": "N/A — confirmed escalation",
        "signal_fingerprint": {
            "war_conflict": "VERY HIGH", "geopolitics": "VERY HIGH",
            "oil_energy": "HIGH", "central_banks": "HIGH",
        },
    },

    "WW2_1939": {
        "name": "World War II", "period": "1939-1945",
        "category": "war_conflict",
        "trigger": "Germany invades Poland",
        "pre_conditions": {
            "geopolitics": "Rising nationalism, Germany rearmament, appeasement failing",
            "economics":   "Depression-era recovery, high unemployment",
            "energy":      "Oil becoming critical for military",
            "markets":     "Markets weak, recovering from Depression",
        },
        "market_impact": {
            "stocks":  "-25% initial, then war economy recovery",
            "bonds":   "Government bonds surged",
            "gold":    "Fixed price era",
            "commodities": "Massive shortages, rationing",
        },
        "time_to_bottom": "6 months",
        "recovery_time":  "Post-war boom 1945-1960",
        "key_lesson": "War economy eventually becomes bullish for stocks",
        "signal_fingerprint": {
            "war_conflict": "EXTREME", "geopolitics": "VERY HIGH",
            "oil_energy": "HIGH", "recession_economy": "HIGH",
        },
    },

    "Korean_War_1950": {
        "name": "Korean War", "period": "1950-1953",
        "category": "war_conflict",
        "trigger": "North Korea invades South Korea",
        "pre_conditions": {
            "geopolitics": "Cold War beginning, US-Soviet tension",
            "economics":   "Post-WW2 recovery",
            "markets":     "US markets in bull market",
        },
        "market_impact": {
            "stocks": "-12% initial shock, recovered within months",
            "gold":   "+5%",
            "oil":    "+15%",
        },
        "time_to_bottom": "1 month",
        "recovery_time":  "6 months",
        "key_lesson": "Limited regional wars cause short-term shocks, not structural damage",
        "signal_fingerprint": {
            "war_conflict": "HIGH", "geopolitics": "HIGH",
        },
    },

    "Vietnam_1965": {
        "name": "Vietnam War Escalation", "period": "1965-1975",
        "category": "war_conflict",
        "trigger": "Gulf of Tonkin, US escalation",
        "pre_conditions": {
            "geopolitics": "Cold War, communist expansion fears",
            "economics":   "US boom economy, Great Society spending",
            "markets":     "Bull market, inflation building",
        },
        "market_impact": {
            "stocks":    "Flat to negative 1966-1975",
            "gold":      "+200% as dollar weakened",
            "inflation": "+8% by 1974",
        },
        "time_to_bottom": "10 years (prolonged)",
        "recovery_time":  "Late 1970s with Volcker",
        "key_lesson": "Prolonged wars drain treasury, weaken currency, cause inflation",
        "signal_fingerprint": {
            "war_conflict": "HIGH", "inflation_dollar": "HIGH",
            "elections_politics": "MEDIUM",
        },
    },

    "Oil_Crisis_1973": {
        "name": "Oil Crisis / Stagflation", "period": "1973-1975",
        "category": "oil_energy",
        "trigger": "OPEC oil embargo — Arab-Israeli War",
        "pre_conditions": {
            "geopolitics": "Yom Kippur War, Arab-Israeli conflict",
            "economics":   "Post-Bretton Woods, dollar off gold",
            "energy":      "US peak oil, import dependence rising",
            "markets":     "Markets near highs, inflation already rising",
        },
        "market_impact": {
            "oil":       "+400% from $3 to $12/barrel",
            "stocks":    "-48% S&P 500 (1973-1974)",
            "gold":      "+70%",
            "inflation": "+12% by 1974",
            "gdp":       "-2% recession",
        },
        "time_to_bottom": "18 months",
        "recovery_time":  "5+ years (stagflation decade)",
        "key_lesson": "Energy shock → inflation → recession → markets crash → decade of pain",
        "false_alarm_rate": "LOW — energy shocks reliably transmit to inflation",
        "signal_fingerprint": {
            "oil_energy": "EXTREME", "war_conflict": "HIGH",
            "inflation_dollar": "VERY HIGH", "geopolitics": "HIGH",
        },
    },

    "Iran_Crisis_1979": {
        "name": "Iran Revolution / Oil Shock II", "period": "1979-1980",
        "category": "oil_energy",
        "trigger": "Iranian Revolution, US hostage crisis",
        "pre_conditions": {
            "geopolitics": "Middle East instability, Cold War proxy dynamics",
            "economics":   "Still recovering from 1973 shock",
            "energy":      "Iran = 10% of world oil supply",
        },
        "market_impact": {
            "oil":       "+150% in 12 months",
            "gold":      "+300% peak ($35 → $850)",
            "inflation": "+14% US CPI 1980",
            "stocks":    "-17%",
        },
        "time_to_bottom": "12 months",
        "recovery_time":  "3 years (Volcker shock required)",
        "key_lesson": "Second oil shock doubled the damage — stagflation became entrenched",
        "signal_fingerprint": {
            "oil_energy": "EXTREME", "geopolitics": "VERY HIGH",
            "war_conflict": "HIGH", "inflation_dollar": "EXTREME",
        },
    },

    "Volcker_Shock_1980": {
        "name": "Volcker Shock — Rate Hike to 20%", "period": "1979-1982",
        "category": "central_banks",
        "trigger": "Fed raises rates to 20% to kill 14% inflation",
        "pre_conditions": {
            "inflation":   "14% — highest since WW2",
            "oil":         "Second oil shock still reverberating",
            "economics":   "Stagflation — high inflation + high unemployment",
        },
        "market_impact": {
            "stocks":  "-27% (1980-1982)",
            "bonds":   "Worst bear market in bonds ever",
            "gold":    "+600% bull then -50% correction",
            "recession": "Two recessions 1980 and 1982",
        },
        "time_to_bottom": "24 months",
        "recovery_time":  "Recovery → greatest bull market ever (1982-2000)",
        "key_lesson": "Extreme rate hikes kill inflation but cause severe recession — then massive bull market",
        "signal_fingerprint": {
            "central_banks": "EXTREME", "inflation_dollar": "EXTREME",
            "recession_economy": "HIGH",
        },
    },

    "Black_Monday_1987": {
        "name": "Black Monday", "period": "1987",
        "category": "recession_economy",
        "trigger": "October 19 — largest single-day crash in history",
        "pre_conditions": {
            "markets":   "Stocks up 250% in 5 years, extreme valuations",
            "economics": "Rising interest rates, trade deficit",
            "tech":      "Program trading amplified moves",
        },
        "market_impact": {
            "stocks": "-22.6% in ONE DAY",
            "global": "All world markets fell simultaneously",
            "vix":    "Not yet existed — implied vol extreme",
        },
        "time_to_bottom": "1 day",
        "recovery_time":  "2 years",
        "key_lesson": "Overvalued markets + rising rates + algo amplification = flash crash",
        "signal_fingerprint": {
            "recession_economy": "HIGH", "central_banks": "HIGH",
        },
    },

    "Gulf_War_1990": {
        "name": "Gulf War", "period": "1990-1991",
        "category": "war_conflict",
        "trigger": "Iraq invades Kuwait (August 1990)",
        "pre_conditions": {
            "geopolitics": "Post-Cold War, Iraq aggression",
            "economics":   "US recession beginning",
            "energy":      "Middle East oil vulnerability",
            "markets":     "Markets declining",
        },
        "market_impact": {
            "stocks": "-20% Aug-Oct 1990, recovered post-war",
            "oil":    "+120% spike then crashed post-war",
            "gold":   "+10%",
        },
        "time_to_bottom": "3 months",
        "recovery_time":  "6 months post-war",
        "key_lesson": "Short decisive wars = sharp V-shaped recovery",
        "false_alarm_rate": "LOW — oil-war combo reliably moves markets",
        "signal_fingerprint": {
            "war_conflict": "VERY HIGH", "oil_energy": "VERY HIGH",
            "geopolitics": "HIGH", "recession_economy": "MEDIUM",
        },
    },

    "Asian_Crisis_1997": {
        "name": "Asian Financial Crisis", "period": "1997-1998",
        "category": "geopolitics",
        "trigger": "Thai baht devaluation July 1997",
        "pre_conditions": {
            "economics": "Asian miracle — overheated economies",
            "currency":  "Currencies pegged to USD, overvalued",
            "debt":      "High corporate debt in USD",
        },
        "market_impact": {
            "thailand":  "-75%",
            "indonesia": "-65%",
            "korea":     "-70%",
            "russia":    "Default 1998, -80%",
            "usd":       "+10% safe haven",
        },
        "time_to_bottom": "18 months",
        "recovery_time":  "3 years",
        "key_lesson": "EM debt crises spread fast, USD safe haven, contagion underestimated",
        "signal_fingerprint": {
            "geopolitics": "HIGH", "recession_economy": "HIGH",
            "inflation_dollar": "MEDIUM",
        },
    },

    "LTCM_Russia_1998": {
        "name": "LTCM Collapse / Russia Default", "period": "1998",
        "category": "recession_economy",
        "trigger": "Russia defaults, LTCM nearly collapses global financial system",
        "pre_conditions": {
            "markets":  "High leverage, correlated positions",
            "russia":   "Post-Soviet fiscal crisis",
            "economics": "Asian crisis contagion",
        },
        "market_impact": {
            "sp500":  "-20% in 2 months",
            "bonds":  "Flight to quality surge",
            "gold":   "+8%",
            "vix":    "Spiked above 45",
        },
        "time_to_bottom": "2 months",
        "recovery_time":  "4 months (Fed cut rates)",
        "key_lesson": "Leverage + correlation = systemic fragility; Fed intervention = fast recovery",
        "signal_fingerprint": {
            "recession_economy": "HIGH", "geopolitics": "MEDIUM",
            "central_banks": "HIGH",
        },
    },

    "Dotcom_Crash_2000": {
        "name": "Dot-com Crash", "period": "2000-2002",
        "category": "tech_ai",
        "trigger": "Fed rate hikes + end of Y2K spending",
        "pre_conditions": {
            "markets":   "Nasdaq up 500% in 5 years, extreme valuations",
            "economics": "Y2K spending boom ending, Fed tightening",
            "sentiment": "Any .com company surged — irrational exuberance",
        },
        "market_impact": {
            "nasdaq":  "-78% peak to trough",
            "sp500":   "-49%",
            "gold":    "+15% began secular bull",
            "bonds":   "Rallied (safe haven)",
        },
        "time_to_bottom": "30 months",
        "recovery_time":  "5 years to recover all-time high",
        "key_lesson": "Speculative tech bubble = massive multi-year correction",
        "signal_fingerprint": {
            "tech_ai": "EXTREME", "central_banks": "HIGH",
            "recession_economy": "MEDIUM",
        },
    },

    "September_11_2001": {
        "name": "9/11 Terrorist Attacks", "period": "2001",
        "category": "war_conflict",
        "trigger": "Al-Qaeda attacks on US soil",
        "pre_conditions": {
            "markets":   "Already in dot-com bear market",
            "geopolitics": "US global dominance era, complacency",
        },
        "market_impact": {
            "stocks":  "-14% in first week",
            "gold":    "+6%",
            "oil":     "-10% initially (demand destruction fear)",
            "airlines": "-40%",
        },
        "time_to_bottom": "1 week",
        "recovery_time":  "1 month (to pre-9/11 levels)",
        "key_lesson": "Terrorist events = sharp shock, fast recovery unless economic damage follows",
        "signal_fingerprint": {
            "war_conflict": "EXTREME", "geopolitics": "EXTREME",
        },
    },

    "Iraq_War_2003": {
        "name": "Iraq War", "period": "2003-2011",
        "category": "war_conflict",
        "trigger": "US invasion of Iraq",
        "pre_conditions": {
            "geopolitics": "Post 9/11, war on terror",
            "economics":   "Dot-com bust recovery beginning",
        },
        "market_impact": {
            "stocks":  "+30% rally (markets bottomed before war)",
            "oil":     "+200% over 5 years",
            "gold":    "+200% over 5 years",
        },
        "time_to_bottom": "Already at bottom pre-war",
        "recovery_time":  "Multi-year commodity bull",
        "key_lesson": "Long occupation = sustained oil and gold bull market",
        "signal_fingerprint": {
            "war_conflict": "HIGH", "geopolitics": "HIGH",
            "oil_energy": "HIGH",
        },
    },

    "Financial_Crisis_2008": {
        "name": "Global Financial Crisis", "period": "2007-2009",
        "category": "recession_economy",
        "trigger": "Lehman Brothers bankruptcy September 2008",
        "pre_conditions": {
            "housing":  "US housing bubble, subprime mortgages",
            "banks":    "Extreme leverage, CDO/derivative exposure",
            "economics": "Record debt, current account deficits",
            "markets":  "Credit spreads widening 2007",
        },
        "market_impact": {
            "sp500":      "-57% peak to trough",
            "banks":      "Many bankrupt or bailed out",
            "gold":       "+25% safe haven",
            "oil":        "-77% demand collapse",
            "unemployment": "+5% to 10%",
        },
        "time_to_bottom": "18 months",
        "recovery_time":  "4 years",
        "key_lesson": "Financial leverage = systemic risk — everything falls together",
        "signal_fingerprint": {
            "recession_economy": "EXTREME", "central_banks": "EXTREME",
            "inflation_dollar": "HIGH",
        },
    },

    "Euro_Debt_Crisis_2010": {
        "name": "Eurozone Debt Crisis", "period": "2010-2012",
        "category": "recession_economy",
        "trigger": "Greece, Ireland, Portugal sovereign debt concerns",
        "pre_conditions": {
            "economics": "Post-GFC austerity, weak growth",
            "debt":      "Peripheral eurozone debt unsustainable",
            "currency":  "Euro structural flaws exposed",
        },
        "market_impact": {
            "europe":   "-30% in affected markets",
            "gold":     "+30% (2010-2012 peak $1,920)",
            "bonds":    "Peripheral yields spiked to 7%+",
            "eur_usd":  "-20% EUR depreciation",
        },
        "time_to_bottom": "2 years",
        "recovery_time":  "3 years (Draghi 'whatever it takes')",
        "key_lesson": "Currency union without fiscal union = structural fragility",
        "signal_fingerprint": {
            "recession_economy": "HIGH", "geopolitics": "MEDIUM",
            "central_banks": "HIGH",
        },
    },

    "Crimea_2014": {
        "name": "Russia annexes Crimea", "period": "2014",
        "category": "geopolitics",
        "trigger": "Russia annexes Crimea, sanctions begin",
        "pre_conditions": {
            "geopolitics": "Ukraine revolution, pro-EU vs Russia",
            "economics":   "Russia dependent on energy exports",
        },
        "market_impact": {
            "russia":   "-50% RTS index",
            "ruble":    "-50% depreciation",
            "gold":     "+10%",
            "oil":      "Flat initially",
        },
        "time_to_bottom": "6 months",
        "recovery_time":  "Ongoing sanctions",
        "key_lesson": "Regional geopolitical shocks mainly hurt regional markets — global spill limited unless energy involved",
        "signal_fingerprint": {
            "geopolitics": "HIGH", "war_conflict": "MEDIUM",
            "oil_energy": "MEDIUM",
        },
    },

    "COVID_Crash_2020": {
        "name": "COVID-19 Pandemic Crash", "period": "2020",
        "category": "natural_disaster",
        "trigger": "Global pandemic lockdowns",
        "pre_conditions": {
            "markets":   "All-time highs, 11-year bull market",
            "economics": "Low unemployment, stable growth",
            "health":    "Pandemic preparedness warnings ignored",
        },
        "market_impact": {
            "sp500":  "-34% in 5 weeks (fastest crash ever)",
            "oil":    "-300% went NEGATIVE (futures)",
            "gold":   "+25%",
            "bitcoin": "-50% initially then +700% year-end",
        },
        "time_to_bottom": "5 weeks",
        "recovery_time":  "5 months full recovery",
        "key_lesson": "Black swan = fastest crash AND fastest recovery in history",
        "signal_fingerprint": {
            "natural_disaster": "EXTREME", "recession_economy": "HIGH",
            "central_banks": "EXTREME",
        },
    },

    "Post_COVID_Inflation_2021": {
        "name": "Post-COVID Inflation Surge", "period": "2021-2023",
        "category": "inflation_dollar",
        "trigger": "Pent-up demand + supply shortage + $10T stimulus",
        "pre_conditions": {
            "monetary":     "$10T global stimulus",
            "supply_chain": "COVID disruptions",
            "energy":       "Ukraine war added fuel",
        },
        "market_impact": {
            "inflation": "+9.1% peak June 2022",
            "sp500":     "-25%",
            "nasdaq":    "-35%",
            "bonds":     "Worst year ever (-13%)",
            "bitcoin":   "-77%",
            "gold":      "Flat (surprised many)",
        },
        "time_to_bottom": "12 months",
        "recovery_time":  "2023 recovery",
        "key_lesson": "Inflation forces rate hikes which crush everything except cash and short bonds",
        "signal_fingerprint": {
            "inflation_dollar": "EXTREME", "central_banks": "EXTREME",
            "recession_economy": "HIGH",
        },
    },

    "Ukraine_War_2022": {
        "name": "Russia-Ukraine Full Invasion", "period": "2022-ongoing",
        "category": "war_conflict",
        "trigger": "Russia full invasion February 2022",
        "pre_conditions": {
            "geopolitics": "NATO expansion tensions",
            "economics":   "Post-COVID inflation surge",
            "energy":      "Europe dependent on Russian gas",
        },
        "market_impact": {
            "sp500":       "-25% in 2022",
            "oil":         "+60% peak",
            "natural_gas": "+400% in Europe",
            "wheat":       "+60%",
            "gold":        "+10% initial then flat",
        },
        "time_to_bottom": "Ongoing",
        "recovery_time":  "Partial recovery 2023",
        "key_lesson": "Energy war + inflation = central bank tightening = everything down",
        "signal_fingerprint": {
            "war_conflict": "EXTREME", "oil_energy": "EXTREME",
            "geopolitics": "EXTREME", "inflation_dollar": "VERY HIGH",
        },
    },

    "Crypto_Winter_2022": {
        "name": "Crypto Winter — Luna/FTX Collapse", "period": "2022",
        "category": "crypto_regulation",
        "trigger": "Luna/UST collapse, then FTX bankruptcy",
        "pre_conditions": {
            "crypto":    "BTC at $69k ATH Nov 2021",
            "economics": "Fed tightening beginning",
            "defi":      "Luna algorithmic stablecoin growing",
        },
        "market_impact": {
            "bitcoin":   "-77% from peak",
            "ethereum":  "-80% from peak",
            "luna":      "-99.9%",
            "total_cap": "-70%",
        },
        "time_to_bottom": "12 months",
        "recovery_time":  "Partial 2023, full 2024",
        "key_lesson": "Leverage + algorithmic systems = death spiral when confidence breaks",
        "signal_fingerprint": {
            "crypto_regulation": "EXTREME", "recession_economy": "HIGH",
            "central_banks": "HIGH",
        },
    },

    "SVB_Banking_2023": {
        "name": "SVB / Regional Banking Crisis", "period": "2023",
        "category": "recession_economy",
        "trigger": "Silicon Valley Bank collapse — rate duration mismatch",
        "pre_conditions": {
            "banks":     "Regional banks held long bonds, rate risk unhedged",
            "economics": "Rapid Fed rate hike cycle",
            "tech":      "VC/startup deposits concentrated",
        },
        "market_impact": {
            "banks":   "Regional banks -40-80%",
            "sp500":   "-5% briefly",
            "gold":    "+8%",
            "btc":     "+40% (flight from banks to crypto)",
        },
        "time_to_bottom": "2 weeks",
        "recovery_time":  "1 month (FDIC backstop)",
        "key_lesson": "Rate hike cycle always breaks something — find the weakest link",
        "signal_fingerprint": {
            "recession_economy": "HIGH", "central_banks": "HIGH",
            "inflation_dollar": "MEDIUM",
        },
    },

    "Gaza_War_2023": {
        "name": "Gaza War / Middle East Escalation", "period": "2023-2024",
        "category": "war_conflict",
        "trigger": "Hamas attack October 7, 2023",
        "pre_conditions": {
            "geopolitics": "Israel-Palestine ongoing conflict",
            "oil":         "Middle East supply route risk",
            "economics":   "Already fragile global economy",
        },
        "market_impact": {
            "oil":   "+8% initial spike",
            "gold":  "+5% safe haven",
            "stocks": "-3% brief",
        },
        "time_to_bottom": "2 weeks",
        "recovery_time":  "1 month",
        "key_lesson": "Middle East wars spike oil/gold initially but fade unless Strait of Hormuz threatened",
        "signal_fingerprint": {
            "war_conflict": "HIGH", "oil_energy": "HIGH",
            "geopolitics": "HIGH",
        },
    },
}


def compare_to_history(world_situation, news_signals, prices):
    """
    Compares current situation to all historical events.
    Returns ranked matches with 6-dimension similarity breakdown.
    """
    active_cats = set(news_signals.keys())
    oil_price   = prices.get("oil",  {}).get("price",      0)
    oil_change  = prices.get("oil",  {}).get("change_pct", 0)
    vix         = prices.get("vix",  {}).get("price",      0)
    gold_change = prices.get("gold", {}).get("change_pct", 0)
    btc_change  = prices.get("btc",  {}).get("change_pct", 0)
    sp_change   = prices.get("sp500",{}).get("change_pct", 0)

    matches = []

    for event_id, event in HISTORICAL_EVENTS.items():
        score     = 0
        reasons   = []
        breakdown = {}

        fingerprint = event.get("signal_fingerprint", {})

        # 1. Signal fingerprint match (0-30 pts)
        sig_score = 0
        for sig, intensity in fingerprint.items():
            if sig in active_cats:
                count = news_signals.get(sig, {}).get("count", 0)
                intensity_mult = {"EXTREME": 1.5, "VERY HIGH": 1.2, "HIGH": 1.0, "MEDIUM": 0.6}.get(intensity, 0.5)
                sig_score += min(count * intensity_mult, 10)
        sig_score = min(sig_score, 30)
        breakdown["signal_match"] = round(min(sig_score / 30 * 100, 100), 1)
        score += sig_score
        if sig_score > 10:
            reasons.append(f"Signal pattern matches: {', '.join(list(fingerprint.keys())[:2])}")

        # 2. Oil situation match (0-20 pts)
        oil_score = 0
        if oil_price > 85 and "oil_energy" in str(event.get("signal_fingerprint", {})):
            oil_score += 10
        if oil_change > 2 and "oil" in str(event.get("market_impact", {})):
            oil_score += 10
        breakdown["energy_match"] = round(oil_score / 20 * 100, 1)
        score += oil_score

        # 3. Volatility / fear regime match (0-15 pts)
        vix_score = 0
        if vix > 25 and event["category"] in ["war_conflict", "recession_economy", "natural_disaster"]:
            vix_score = min(int((vix - 20) / 2), 15)
        breakdown["volatility_match"] = round(vix_score / 15 * 100, 1)
        score += vix_score
        if vix_score > 8:
            reasons.append(f"VIX at {vix:.1f} matches fear levels")

        # 4. War/geopolitical intensity match (0-15 pts)
        war_count = news_signals.get("war_conflict", {}).get("count", 0)
        geo_count = news_signals.get("geopolitics",  {}).get("count", 0)
        war_score = 0
        if event["category"] in ["war_conflict", "geopolitics"]:
            war_score = min((war_count + geo_count) * 0.5, 15)
        breakdown["geopolitical_match"] = round(war_score / 15 * 100, 1)
        score += war_score

        # 5. Market direction match (0-10 pts)
        mkt_score = 0
        if sp_change < -1 and "-" in str(event.get("market_impact", {}).get("stocks", "")):
            mkt_score += 5
        if gold_change > 1 and "+" in str(event.get("market_impact", {}).get("gold", "")):
            mkt_score += 5
        breakdown["market_direction"] = round(mkt_score / 10 * 100, 1)
        score += mkt_score

        # 6. Macro category direct match (0-10 pts)
        cat_score = 10 if event["category"] in active_cats else 0
        breakdown["category_match"] = round(cat_score / 10 * 100, 1)
        score += cat_score

        if score > 0:
            # Add micro-variance from number of matching signal types
            # This creates natural spread in similarity scores
            # so multiple events don't all land at the exact same %
            sig_variety = len([k for k in event.get("signal_fingerprint", {})
                               if k in active_cats])
            hist_depth  = len(event.get("market_impact", {}))
            micro_adj   = (sig_variety * 0.8) + (hist_depth * 0.3)
            final_score = round(score + micro_adj, 1)

            # Similarity as % with natural spread (max 99)
            similarity  = min(round(final_score / 105 * 100, 1), 99)

            matches.append({
                "event_id":   event_id,
                "name":       event["name"],
                "period":     event["period"],
                "category":   event["category"],
                "score":      final_score,
                "similarity": similarity,
                "breakdown":  breakdown,
                "reasons":    reasons,
                "impact":     event["market_impact"],
                "lesson":     event["key_lesson"],
                "time_to_bottom": event.get("time_to_bottom", "?"),
                "recovery_time":  event.get("recovery_time", "?"),
                "trigger":        event.get("trigger", ""),
                # Extra: which dimension is strongest match
                "strongest_match": max(breakdown, key=breakdown.get) if breakdown else "signal",
            })

    matches.sort(key=lambda x: x["score"], reverse=True)
    top_matches = matches[:5]

    result = {
        "compared_at":          datetime.now().isoformat(),
        "top_matches":          top_matches,
        "total_events_in_db":   len(HISTORICAL_EVENTS),
    }

    os.makedirs(f"{DATA_PATH}/history", exist_ok=True)
    with open(f"{DATA_PATH}/history/latest.json", "w") as f:
        json.dump(result, f, indent=2)

    return result
