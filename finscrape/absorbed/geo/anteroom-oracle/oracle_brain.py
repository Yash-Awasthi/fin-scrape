"""
ZAI Oracle — AI Brain
by Zawwar (github.com/Zawwarsami16)

Takes everything the Oracle has gathered:
- Live world situation (markets, news, geopolitics)
- Historical matches (which past events this resembles)
- Whale intelligence (where smart money is moving)

Feeds it all to the best available AI and gets a structured prediction.

Auto-selects AI: Groq → Gemini → Claude → Ollama → Rule-based
All you need to do is have at least one key in .env
"""

import os
import json
import re
import subprocess
import requests as req
from datetime import datetime
from config import DATA_PATH, GROQ_KEY, GEMINI_KEY, ANTHROPIC_KEY


# ================================================================
# PROMPT BUILDER
# The prompt is carefully structured to get the best prediction.
# Short enough to not timeout on CPU models, rich enough for accuracy.
# ================================================================
def build_oracle_prompt(world_situation, historical_matches, whale_data, prices):
    """
    Constructs the AI prompt with all available intelligence.
    Ordered from most important to least — in case of token limits.
    """

    # Top 3 historical matches (compact)
    top_hist = []
    for m in historical_matches.get("top_matches", [])[:3]:
        top_hist.append({
            "event":      m["name"],
            "period":     m["period"],
            "similarity": f"{m['similarity']}%",
            "what_happened_to_markets": m["impact"],
            "key_lesson": m["lesson"],
        })

    # Active crises (compact)
    crises = world_situation.get("active_crises", [])[:4]

    # Whale summary
    whale_summary = whale_data.get("summary", {}) if whale_data else {}

    # Market stress
    stress = world_situation.get("market_stress", [])[:4]

    # Key numbers
    key_nums = {}
    for asset in ["oil", "gold", "btc", "sp500", "vix", "dxy"]:
        p = prices.get(asset, {})
        if p:
            key_nums[asset] = f"${p['price']:,.2f} ({p['change_pct']:+.1f}%)"

    prompt = f"""You are ZAI Oracle — the most advanced geopolitical and market prediction AI.
You analyze current world events, compare them to history, and predict what comes next.
You cover EVERYTHING: markets, wars, politics, energy, crypto, geopolitics.

═══════════════════════════════════════════════
CURRENT WORLD SITUATION
═══════════════════════════════════════════════
Risk Level: {world_situation.get('risk_level', 'UNKNOWN')}
Active Crises: {json.dumps(crises, indent=None)}
Market Stress: {stress}

LIVE MARKET SNAPSHOT:
{json.dumps(key_nums)}

═══════════════════════════════════════════════
HISTORICAL COMPARISON — WHAT DOES THIS LOOK LIKE?
═══════════════════════════════════════════════
{json.dumps(top_hist, indent=1)}

═══════════════════════════════════════════════
WHALE INTELLIGENCE — WHERE IS SMART MONEY?
═══════════════════════════════════════════════
{json.dumps(whale_summary)}

═══════════════════════════════════════════════

Based on ALL of the above, provide your Oracle prediction.

Think through:
1. Which historical period does today MOST resemble and why?
2. If history rhymes, what typically happens in the next 4 weeks / 3 months / 6 months?
3. What is the single most dangerous risk right now?
4. What could make things BETTER than history suggests?
5. What should someone watch most closely?

Be specific. Use the historical data. Reference actual events and outcomes.

Respond ONLY in this exact JSON — no text before or after:
{{
  "current_situation_summary": "2-3 sentence description of what is happening in the world right now",
  "most_similar_historical_event": "event name and why",
  "overall_outlook": "BULLISH/BEARISH/NEUTRAL/VOLATILE/CRITICAL",
  "confidence": 0-100,
  "domain_outlooks": {{
    "markets":     "Complete sentence under 80 chars. Must include one specific trigger or level.",
    "geopolitics": "Complete sentence under 80 chars. Name the specific risk or actor.",
    "crypto":      "Complete sentence under 80 chars. Include BTC/ETH direction.",
    "energy":      "Complete sentence under 80 chars. Include oil price threshold.",
    "politics":    "Complete sentence under 80 chars. Name the specific political risk."
  }},
  "tactical_read": {{
    "stance":      "DEFENSIVE/NEUTRAL/OPPORTUNISTIC",
    "key_levels":  ["most important level 1 to watch", "level 2"],
    "avoid":       "what to avoid right now in one sentence",
    "watch_for":   "what signal would change the thesis in one sentence"
  }},
  "predictions": {{
    "4_weeks":  {{"direction": "UP/DOWN/SIDEWAYS/VOLATILE", "magnitude": "X%", "key_driver": "what drives this"}},
    "3_months": {{"direction": "UP/DOWN/SIDEWAYS/VOLATILE", "magnitude": "X%", "key_driver": "what drives this"}},
    "6_months": {{"direction": "UP/DOWN/SIDEWAYS/VOLATILE", "magnitude": "X%", "key_driver": "what drives this"}}
  }},
  "biggest_risk": "the single most dangerous thing that could happen",
  "biggest_opportunity": "the single best opportunity if things play out like history",
  "what_to_watch": ["most important indicator 1", "indicator 2", "indicator 3"],
  "scenario_if_escalates": "what happens if the worst risk materializes",
  "scenario_if_resolves": "what happens if tensions ease",
  "whale_signal_interpretation": "what does the smart money movement mean",
  "summary": "3 sentence plain English summary of everything — situation, prediction, action"
}}"""

    return prompt


# ================================================================
# AI PROVIDERS
# ================================================================

def _parse_json_response(text):
    """
    Extracts and parses JSON from AI response text.
    Handles common LLM formatting issues:
    - ```json code blocks
    - Comments inside JSON (// style)
    - Trailing commas
    - Extra text before/after JSON
    """
    # Remove code blocks
    text = text.replace("```json", "").replace("```", "").strip()

    # Remove JS-style comments (LLMs sometimes add these)
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    # Find the JSON object
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start < 0 or end <= start:
        return None

    json_str = text[start:end]

    # Try direct parse first
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Fix trailing commas (most common LLM mistake)
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def groq_predict(prompt):
    """
    Groq API — free, fastest, uses llama3-70b (best free model).
    Auto-fetches available models so it never breaks on deprecations.
    """
    if not GROQ_KEY:
        return None

    # Get best available model dynamically
    model = "llama-3.3-70b-versatile"  # best current model
    try:
        r = req.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            timeout=8
        )
        if r.status_code == 200:
            available = [m["id"] for m in r.json().get("data", [])]
            preferred = [
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile",
                "llama3-70b-8192",
                "llama-3.1-8b-instant",
            ]
            for p in preferred:
                if p in available:
                    model = p
                    break
    except Exception:
        pass  # use default model

    try:
        r = req.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "model":       model,
                "messages":    [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens":  2000,
            },
            timeout=45
        )
        data = r.json()

        if "error" in data:
            print(f"  Groq error: {data['error'].get('message','')[:80]}")
            return None

        text   = data["choices"][0]["message"]["content"]
        result = _parse_json_response(text)
        if result:
            result["ai_source"] = f"groq:{model}"
            return result

    except Exception as e:
        print(f"  Groq exception: {str(e)[:60]}")

    return None


def gemini_predict(prompt):
    """
    Google Gemini API — free tier, fast.
    Tries multiple models so it never breaks on deprecations.
    """
    if not GEMINI_KEY:
        return None

    models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

    for model in models:
        try:
            r = req.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature":     0.2,
                        "maxOutputTokens": 2000,
                    },
                },
                timeout=30
            )
            data = r.json()

            if "error" in data:
                print(f"  Gemini {model}: {data['error'].get('message','')[:60]}")
                continue

            text   = data["candidates"][0]["content"]["parts"][0]["text"]
            result = _parse_json_response(text)
            if result:
                result["ai_source"] = f"gemini:{model}"
                return result

        except Exception as e:
            print(f"  Gemini {model}: {str(e)[:50]}")
            continue

    return None


def claude_predict(prompt):
    """Anthropic Claude API — most accurate, paid."""
    if not ANTHROPIC_KEY:
        return None

    try:
        r = req.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 2000,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=45
        )
        data = r.json()
        if "content" in data:
            text   = data["content"][0]["text"]
            result = _parse_json_response(text)
            if result:
                result["ai_source"] = "claude"
                return result
    except Exception as e:
        print(f"  Claude error: {str(e)[:60]}")

    return None


def ollama_predict(prompt, model):
    """Local Ollama — free, private, no internet needed once installed."""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True, text=True, timeout=600
        )
        if result.returncode == 0:
            parsed = _parse_json_response(result.stdout)
            if parsed:
                parsed["ai_source"] = f"ollama:{model}"
                return parsed
    except subprocess.TimeoutExpired:
        print(f"  Ollama timed out (10 min)")
    except Exception as e:
        print(f"  Ollama error: {str(e)[:60]}")

    return None


def rule_based_predict(world_situation, historical_matches, whale_data, prices):
    """
    Pure logic prediction — no AI needed, always works.
    Based on signal count + historical patterns + price momentum.
    Less nuanced than an LLM but completely reliable.
    """
    risk_level = world_situation.get("risk_level", "MODERATE")
    crises     = world_situation.get("active_crises", [])
    stress     = world_situation.get("market_stress", [])
    top_match  = (historical_matches.get("top_matches") or [{}])[0]
    whale_sig  = (whale_data or {}).get("summary", {}).get("overall_signal", "UNKNOWN")

    # Determine outlook from risk level
    outlook_map = {
        "CRITICAL":  "BEARISH",
        "HIGH":      "BEARISH",
        "ELEVATED":  "VOLATILE",
        "MODERATE":  "NEUTRAL",
        "LOW":       "BULLISH",
    }
    outlook = outlook_map.get(risk_level, "NEUTRAL")

    # Adjust for whale signal
    if "EXITING" in whale_sig or "SELLING" in whale_sig:
        outlook = "BEARISH"
    elif "ACCUMULATING" in whale_sig:
        if outlook == "NEUTRAL":
            outlook = "MILDLY BULLISH"

    # Build predictions based on historical match
    hist_impact = top_match.get("impact", {})
    hist_name   = top_match.get("name", "historical patterns")

    # 4-week prediction
    if risk_level in ("CRITICAL", "HIGH") and len(stress) > 2:
        p4w = {"direction": "DOWN", "magnitude": "5-15%",
               "key_driver": f"Active crises + elevated stress signals"}
    else:
        p4w = {"direction": "SIDEWAYS", "magnitude": "0-3%",
               "key_driver": "Mixed signals, consolidation likely"}

    p3m = {"direction": "DOWN" if outlook == "BEARISH" else "UP",
           "magnitude": "10-20%" if outlook == "BEARISH" else "5-10%",
           "key_driver": f"Historical parallel to {hist_name}"}

    p6m = {"direction": "UP", "magnitude": "5-15%",
           "key_driver": "Long-term recovery typical after crises"}

    crisis_names = [c["type"] for c in crises[:3]]

    return {
        "ai_source":                 "rule_based",
        "current_situation_summary": (
            f"World risk level: {risk_level}. "
            f"Active crises: {', '.join(crisis_names) if crisis_names else 'none major'}. "
            f"Most similar historical event: {hist_name}."
        ),
        "most_similar_historical_event": f"{hist_name} — {top_match.get('similarity', 0)}% match",
        "overall_outlook":               outlook,
        "confidence":                    40 + len(stress) * 5,
        "domain_outlooks": {
            "markets":     f"Stress signals elevated — caution advised",
            "geopolitics": f"{len(crises)} active crisis categories detected",
            "crypto":      "Following risk-off sentiment with broader markets",
            "energy":      f"Oil at ${prices.get('oil',{}).get('price',0):.0f} — watch $100 level",
            "politics":    "Congress trade data suggests defensive positioning",
        },
        "predictions": {
            "4_weeks":  p4w,
            "3_months": p3m,
            "6_months": p6m,
        },
        "biggest_risk":             f"Escalation of {crisis_names[0] if crisis_names else 'current tensions'}",
        "biggest_opportunity":      "Dips if tensions resolve = buying opportunity",
        "what_to_watch":            ["Oil price at $100 level", "VIX above 30", "Fed statements"],
        "scenario_if_escalates":    "Markets -15-30%, gold +15%, oil +30%",
        "scenario_if_resolves":     "Relief rally +5-10%, crypto leads",
        "whale_signal_interpretation": whale_sig,
        "summary": (
            f"Current world risk is {risk_level} with {len(crises)} active crisis domains. "
            f"Situation resembles {hist_name}. "
            f"Short-term outlook: {p4w['direction']}, longer-term recovery expected. "
            f"Add Groq key to .env for AI-enhanced analysis."
        ),
        "generated_at": datetime.now().isoformat(),
    }


# ================================================================
# MAIN PREDICTION FUNCTION
# Auto-selects best available AI, falls back gracefully
# ================================================================
def get_oracle_prediction(hw, world_situation, historical_matches, whale_data, prices):
    """
    Tries AI providers in priority order.
    Falls back to rule-based if nothing is available.
    Never crashes — always returns a prediction.
    """
    prompt   = build_oracle_prompt(world_situation, historical_matches, whale_data, prices)
    ai_mode  = hw.get("ai_mode", "none")

    print(f"\n  Generating Oracle prediction...")

    # 1. Groq — free, fastest (llama3-70b)
    if GROQ_KEY:
        print("  Trying Groq (llama3-70b)...")
        result = groq_predict(prompt)
        if result:
            print(f"  Groq prediction complete ({result.get('ai_source','')})")
            return result
        print("  Groq failed — trying next...")

    # 2. Gemini — free tier
    if GEMINI_KEY:
        print("  Trying Gemini...")
        result = gemini_predict(prompt)
        if result:
            print(f"  Gemini prediction complete ({result.get('ai_source','')})")
            return result
        print("  Gemini failed — trying next...")

    # 3. Claude — paid, most accurate
    if ANTHROPIC_KEY:
        print("  Trying Claude API...")
        result = claude_predict(prompt)
        if result:
            print(f"  Claude prediction complete")
            return result
        print("  Claude failed — trying next...")

    # 4. Ollama — local model
    if hw.get("ollama_ready") and hw.get("ollama_model"):
        model = hw["ollama_model"]
        print(f"  Trying Ollama ({model}) — may take 2-4 min on CPU...")
        result = ollama_predict(prompt, model)
        if result:
            print(f"  Ollama prediction complete")
            return result
        print("  Ollama failed — using rule-based...")

    # 5. Rule-based — always works
    print("  Using rule-based prediction (add GROQ_KEY to .env for AI)")
    return rule_based_predict(world_situation, historical_matches, whale_data, prices)


# ================================================================
# SAVE PREDICTION
# ================================================================
def save_prediction(prediction, metadata):
    """Saves prediction to disk with full context for documentation."""
    os.makedirs(f"{DATA_PATH}/predictions", exist_ok=True)

    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    doc = {
        "generated_at": datetime.now().isoformat(),
        "metadata":     metadata,
        "prediction":   prediction,
    }

    with open(f"{DATA_PATH}/predictions/oracle_{ts}.json", "w") as f:
        json.dump(doc, f, indent=2)

    with open(f"{DATA_PATH}/predictions/latest.json", "w") as f:
        json.dump(doc, f, indent=2)

    return doc
