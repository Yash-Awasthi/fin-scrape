from scraper.yahoo import *
from core.ai_engine import call_ai
from core.validator import calculate_heuristic_score, check_divergence, clean_tickers
import json
from datetime import datetime, timezone
from difflib import SequenceMatcher
import re
import os

FETCH_COUNT = 3
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
ENTITY_PATH = os.path.join(BASE_DIR, "core", "entity_index.json")

os.makedirs(STORAGE_DIR, exist_ok=True)

visited_path = os.path.join(STORAGE_DIR, "visited_urls.json")
events_path = os.path.join(STORAGE_DIR, "events.json")

def save_state():
    with open(visited_path, "w") as f:
        json.dump(visited, f, indent=2)

    with open(events_path, "w") as f:
        json.dump(events, f, indent=2)

os.makedirs("storage", exist_ok=True)
if not os.path.exists(visited_path):
    with open(visited_path, "w") as f:
        f.write("{}")

if not os.path.exists(events_path):
    with open(events_path, "w") as f:
        f.write("[]")

sources = {
    "yahoo": collect_yahoo_news_urls
}

with open(ENTITY_PATH) as f:
    ENTITY_INDEX = json.load(f)

def resolve_entity_tickers(text):

    text_lower = text.lower()
    words = set(text_lower.split())

    tickers = []

    for w in words:

        if w in ENTITY_INDEX:

            for company, ticker in ENTITY_INDEX[w]:

                if company in text_lower:
                    tickers.append(ticker)

    return tickers

try:
    with open(visited_path, "r") as f:
        visited = json.load(f)
except:
    visited = {}

for s in sources:
    if s not in visited:
        visited[s] = []

try:
    with open(events_path, "r") as f:
        events = json.load(f)
except:
    events = []


prompt = """

Analyze the financial news article below and return a single JSON object.

A financial event affects markets, sectors, commodities, or valuations (e.g. earnings, M&A, guidance, macro releases, regulatory decisions, supply disruptions, price moves).

RULES:
- Headline defines the event; article provides context.
- If the initiating actor is an analyst/bank/regulator, reflect that in subject — not the company.
- Only include tickers directly affected; skip passing mentions. Infer tickers from names if needed.
- Ignore fund letters, portfolio reviews, or retrospective commentary unless a new transaction is described.

EVENT TYPE — use exactly one of these strings:
earnings | guidance | price_target_change | analyst_upgrade | analyst_downgrade | merger_acquisition | regulatory_decision | product_launch | management_change | market_movement | investment_activity | geopolitical_event

SUBJECT — max 12 words, canonical phrasing:
- Name the main entity + use precise verbs: raises, cuts, acquires, reports, warns, beats, misses, secures, launches, faces, expands, delays
- No tickers, no dates, no editorial language.

SIGNAL SCORE — integer only:
+5 extremely strong positive | +3 strong positive | +1 weak positive | 0 neutral
-1 weak negative | -3 strong negative | -5 extremely strong negative

If no meaningful financial event exists, set "relevant": false and leave all other fields as empty strings, empty arrays, or 0.

Output valid JSON only — no markdown, no explanation, no extra keys.

SCHEMA (follow exactly):
{{
  "relevant": bol,
  "event": "one sentence",
  "event_type": "one from list",
  "subject": "max 12 words",
  "impact_direction": "positive/negative/neutral",
  "tickers": ["array of affected ticker symbols"],
  "signal_score": integer from -5 to 5,
  "confidence": float from 0 to 1
}}

HEADLINE: {{title}}
ARTICLE: {{article_text}}

"""

system_prompt = """
You are a financial event extraction engine.

Your task is to analyze financial news text and output structured data describing the primary market-relevant event and convert financial news descriptions into short canonical subjects.
You are NOT a chatbot.

You do NOT explain, justify, or add commentary.

You only return valid JSON following the provided schema.

"""

def normalize_subject(s):
    s = s.lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


for source, collector in sources.items():
    urls = collector(FETCH_COUNT)
    processed_count = 0
    skipped_count = 0
    ai_called_count = 0
    event_created_count = 0

    for URL in urls:
        processed_count += 1
        print(f"\n[{processed_count}/{len(urls)}] URL: {URL}")

        if URL in visited[source]:
            print("  [SKIP] Already visited")
            skipped_count += 1
            continue

        try:
            title, article_text, soup, exact_age = scrape_article(URL)
        except Exception as e:
            print(f"  [ERROR] scrape_article failed: {e}")
            skipped_count += 1
            if URL not in visited[source]:
                visited[source].append(URL)
                save_state()
            continue

        if not title or not article_text:
            print("  [SKIP] No title or text extracted")
            skipped_count += 1
            if URL not in visited[source]:
                visited[source].append(URL)
                save_state()
            continue

        if exact_age is not None and exact_age > 6:
            print(f"  [SKIP] Too old (exact {exact_age:.1f}h)")
            skipped_count += 1
            if URL not in visited[source]:
                visited[source].append(URL)
                save_state()
            continue

        print(f"  [OK] Processing '{title[:50]}...' (age: {exact_age if exact_age else 'unknown'}h)")

        try:
            filledprompt = prompt.replace("{{title}}", title).replace("{{article_text}}", article_text)
            result = call_ai(filledprompt, system_prompt)
            ai_called_count += 1
            if not result or len(result.strip()) < 20:
                print("  [SKIP] AI returned empty/invalid")
                skipped_count += 1
                if URL not in visited[source]:
                    visited[source].append(URL)
                    save_state()
                continue
        except Exception as e:
            print(f"  [ERROR] call_ai failed: {e}")
            skipped_count += 1
            if URL not in visited[source]:
                visited[source].append(URL)
                save_state()
            continue

        print("AI RAW RESPONSE:", result)

        clean = result.strip()
        clean = clean.replace("```json", "").replace("```", "").strip()
        clean = clean.replace("\ufeff", "").replace("\u200b", "")

        match = re.search(r"\{[\s\S]*\}", clean)
        if not match:
            print("  [SKIP] AI returned no JSON block")
            continue

        clean = match.group(0)

        try:
            result_json = json.loads(clean)
        except json.JSONDecodeError as e:
            print("JSON parse error:", e)
            print("Bad JSON:", clean)
            # Still mark as visited to avoid retry loop
            if URL not in visited[source]:
                visited[source].append(URL)
                save_state()
            continue

        if not isinstance(result_json, dict):
            print("  [SKIP] AI result not a dict")
            continue

        if not result_json.get("relevant", False):
            print("IRRELEVANT ARTICLE — SKIPPED")
            skipped_count +=1  #debug
            if URL not in visited[source]:
                visited[source].append(URL)
                save_state()
            continue

        event_created_count += 1
        print(f"  [EVENT CREATED] #{event_created_count} - {result_json.get('subject', 'No subject')}")
        
        # Ticker collection
        ai_tickers = result_json.get("tickers", [])
        entity_tickers = resolve_entity_tickers(title + " " + article_text)
        regex_tickers = extract_tickers(article_text, soup)  # renamed for clarity
        all_symbols = set(ai_tickers+entity_tickers + regex_tickers)

        tickers_list = clean_tickers([t for t in all_symbols if isinstance(t, str) and 1 < len(t) <= 5 and t.isupper()])

        ticker_data = get_market_data(tickers_list)

        market_boost = 0
        for t in ticker_data:
            change = abs(t["change_percent"])
            if change >= 10:
                market_boost = max(market_boost, 2)
            elif change >= 5:
                market_boost = max(market_boost, 1)

        print("\nTICKERS + MARKET DATA:\n")
        for t in ticker_data:
            print(f"{t['ticker']:6} | ${t['price']:.2f} | {t['change_percent']:+.2f}%")

        required = ["event_type", "impact_direction", "signal_score"]
        if not all(r in result_json for r in required):
            print("  [SKIP] Missing required AI fields")
            continue

        base_score = result_json.get("signal_score", 0)
        signal_score = max(-5, min(5, base_score + market_boost))

        # --- HEURISTIC VALIDATION ---
        h_sentiment, h_impact = calculate_heuristic_score(title + " " + article_text, result_json.get("event_type", ""))
        divergence = check_divergence(result_json.get("impact_direction", "neutral"), h_sentiment)

        event = {
            "subject": subject.strip(),
            "event_type": result_json.get("event_type"),
            "tickers": tickers_list,  # use filtered list
            "impact_direction": result_json.get("impact_direction"),
            "signal_score": signal_score,
            "heuristic_impact": h_impact,
            "divergence_flag": divergence,
            "confidence": result_json.get("confidence", 0.5),
            "sources": [source],
            "articles": [URL],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Skip if no tickers (optional — comment out if you want events without tickers)
        if not event["tickers"]:
            print("  [SKIP] No tickers assigned")
            continue

        # Deduplication logic (unchanged)
        def ticker_overlap_ratio(a, b):
            if not a or not b:
                return 0
            return len(set(a) & set(b)) / min(len(set(a)), len(set(b)))

        matched = None
        for e in events[-100:]:
            existing_tickers = set(e.get("tickers", []))
            if ticker_overlap_ratio(event["tickers"], existing_tickers) >= 0.5:
                if e.get("event_type") == event["event_type"]:
                    similarity = SequenceMatcher(
                        None,
                        normalize_subject(e.get("subject", "")),
                        normalize_subject(event["subject"])
                    ).ratio()
                    if similarity >= 0.9:
                        matched = e
                        break

        if matched:
            if "articles" not in matched:
                matched["articles"] = []
            if URL not in matched["articles"]:
                matched["articles"].append(URL)
            if "sources" not in matched:
                matched["sources"] = []
            if source not in matched["sources"]:
                matched["sources"].append(source)
        else:
            events.append(event)

        if len(events) > 5000:
            events[:] = events[-4000:]

        print(json.dumps(result_json, indent=2))

        # Always mark as visited
        if URL not in visited[source]:
            visited[source].append(URL)

        save_state()  # save after each successful event
        print(f"\nSUMMARY:")
        print(f"  Processed URLs: {processed_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  AI calls made: {ai_called_count}")
        print(f"  Events created: {event_created_count}")

    # Final save and summary
    print("Visited before final save:", visited)
    print("VISITED FILE:", os.path.abspath(visited_path))
    print("EVENTS FILE:", os.path.abspath(events_path))
    save_state()
