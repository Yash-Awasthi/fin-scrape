"""
Anteroom Oracle - Intelligence Terminal

Professional terminal renderer for macro, geopolitical, market-regime, historical,
and scenario research output.
"""

import os
from datetime import datetime
from config import DATA_PATH


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    ORANGE = "\033[38;5;208m"
    BRED = "\033[91m\033[1m"


def g(text, color):
    return f"{color}{text}{C.RESET}"


def clr():
    os.system("cls" if os.name == "nt" else "clear")


def sec(title, col=C.CYAN):
    print(g(f"  {title}", col + C.BOLD))
    print(g("  " + "─" * 58, C.GRAY))


def wrap(text, width=60, indent="    "):
    words = str(text).split()
    line, lines = indent, []
    for word in words:
        if len(line) + len(word) > width:
            lines.append(line)
            line = indent + word + " "
        else:
            line += word + " "
    if line.strip():
        lines.append(line)
    return lines


def print_header(source):
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    print(g("╔══════════════════════════════════════════════════════════════╗", C.GREEN))
    print(g("║", C.GREEN) + g("        ANTEROOM ORACLE — INTELLIGENCE TERMINAL              ", C.BOLD + C.WHITE) + g("║", C.GREEN))
    print(g("║", C.GREEN) + g("        Macro · Geopolitics · Markets · Scenarios            ", C.GRAY) + g("║", C.GREEN))
    print(g("║", C.GREEN) + g(f"        {now}                                ", C.GRAY) + g("║", C.GREEN))
    print(g("╚══════════════════════════════════════════════════════════════╝", C.GREEN))
    if source:
        print(g(f"  Summary source: {source}", C.GREEN))
    print()


def print_data_health(val_report):
    if not val_report:
        return
    total = val_report.get("total_assets", 0)
    errors = val_report.get("errors_count", 0)
    fixed = val_report.get("fixed_count", 0)
    trust = max(0, 100 - errors * 12 + fixed * 5)
    color = C.GREEN if trust >= 80 else C.YELLOW if trust >= 60 else C.RED
    bar = g("█" * (trust // 10), color) + g("░" * (10 - trust // 10), C.GRAY)
    sec("DATA HEALTH", C.CYAN)
    print(f"  Market feeds:    {g(str(total - errors) + '/' + str(total) + ' verified', C.GREEN if not errors else C.YELLOW)}")
    print(f"  Data trust:      [{bar}] {g(str(trust) + '%', color)}")
    for item in val_report.get("fixed", []):
        print(f"  {g('Adjusted:', C.YELLOW)} {item}")
    for item in val_report.get("warnings", [])[:2]:
        print(f"  {g('Warning:', C.YELLOW)} {item}")
    for item in val_report.get("errors", [])[:2]:
        print(f"  {g('Conflict:', C.RED)} {item}")
    print()


def print_markets(prices):
    sec("LIVE MARKETS", C.CYAN)
    assets = [
        ("S&P 500", "sp500", "$"),
        ("NASDAQ", "nasdaq", "$"),
        ("Gold", "gold", "$"),
        ("Oil WTI", "oil", "$"),
        ("Nat. Gas", "naturalgas", "$"),
        ("Silver", "silver", "$"),
        ("VIX", "vix", ""),
        ("DXY", "dxy", ""),
        ("10Y Yield", "tnx", "%"),
        ("Bitcoin", "btc", "$"),
        ("Ethereum", "eth", "$"),
        ("Solana", "sol", "$"),
    ]
    for label, key, prefix in assets:
        data = prices.get(key)
        if not data:
            continue
        price = data.get("price", 0)
        change = data.get("change_pct", 0)
        source = data.get("source", "")
        arrow = g("↑", C.GREEN) if change >= 0 else g("↓", C.RED)
        change_color = C.GREEN if change >= 0 else C.RED
        if prefix == "$":
            price_text = f"${price:>10,.0f}" if price > 999 else f"${price:>10,.2f}"
        elif prefix == "%":
            price_text = f" {price:>10,.2f}%"
        else:
            price_text = f" {price:>10,.2f}"
        source_text = g(f" [{source}]", C.GRAY) if source else ""
        print(f"  {g(label, C.WHITE):<16}  {g(price_text, C.YELLOW)}   {arrow} {g(f'{change:+.2f}%', change_color)}{source_text}")
    print()


def print_geo_risk_index(geo_index):
    if not geo_index:
        return
    total = geo_index.get("total", 0)
    label = geo_index.get("label", "?")
    comps = geo_index.get("components", {})
    color_map = {"EXTREME": C.BRED, "CRITICAL": C.RED, "HIGH": C.RED, "ELEVATED": C.ORANGE, "MODERATE": C.YELLOW, "LOW": C.GREEN}
    color = color_map.get(label, C.YELLOW)
    sec("GEOPOLITICAL RISK INDEX", C.MAGENTA)
    bar = g("█" * int(total / 10), color) + g("░" * (10 - int(total / 10)), C.GRAY)
    print(f"  Global risk:     [{bar}] {g(str(total) + '/100', C.WHITE)}  {g(label, color + C.BOLD)}")
    fastest = geo_index.get("fastest_rising", "")
    if fastest:
        print(f"  Fastest rising:  {g(fastest, C.ORANGE)}")
    print()
    for name, comp in comps.items():
        score = comp.get("score", 0)
        maximum = comp.get("max", 1)
        trend = comp.get("trend", "")
        pct = score / maximum if maximum else 0
        bar_color = C.RED if pct > 0.7 else C.ORANGE if pct > 0.4 else C.CYAN
        mini_bar = g("█" * int(pct * 5), bar_color) + g("░" * (5 - int(pct * 5)), C.GRAY)
        label_text = name.replace("_", " ").title()
        trend_color = C.RED if trend in ["critical", "rising", "stressed"] else C.YELLOW if trend in ["elevated", "uncertain"] else C.GREEN
        print(f"  {g(label_text, C.GRAY):<26} [{mini_bar}] {score:.0f}/{maximum}  {g(trend, trend_color)}")
    print()


def print_regime(regime_data):
    if not regime_data:
        return
    regime = regime_data.get("regime", "UNKNOWN")
    confidence = regime_data.get("confidence", "LOW")
    drivers = regime_data.get("drivers", [])
    behavior = regime_data.get("asset_behavior", {})
    ends = regime_data.get("what_ends_it", "")
    color_name = regime_data.get("color", "YELLOW")
    color_map = {"RED": C.RED, "RED_BOLD": C.BRED, "ORANGE": C.ORANGE, "YELLOW": C.YELLOW, "GREEN": C.GREEN, "CYAN": C.CYAN}
    sec("MARKET REGIME", C.MAGENTA)
    print(f"  {g(regime, color_map.get(color_name, C.YELLOW) + C.BOLD)}  {g('(' + confidence + ' confidence)', C.GRAY)}")
    if drivers:
        print("\n" + g("  Drivers:", C.WHITE))
        for item in drivers[:4]:
            print(f"    {g('-', C.GRAY)} {item}")
    if behavior:
        print("\n" + g("  Asset behavior:", C.WHITE))
        for asset, text in list(behavior.items())[:5]:
            color = C.GREEN if "BULL" in text else C.RED if any(term in text for term in ["BEAR", "SEVERE"]) else C.YELLOW
            print(f"    {g(asset.capitalize() + ':', C.GRAY):<14} {g(text, color)}")
    if ends:
        print("\n" + g(f"  Ends when: {ends}", C.GRAY))
    print()


def print_world_signals(news_data, world_situation):
    risk = news_data.get("risk_level", "UNKNOWN")
    unique = news_data.get("unique_articles", news_data.get("total_articles", 0))
    sources = news_data.get("total_sources", 0)
    signals = news_data.get("signals", {})
    colors = {"CRITICAL": C.BRED, "HIGH": C.RED, "ELEVATED": C.ORANGE, "MODERATE": C.YELLOW, "LOW": C.GREEN}
    sec("WORLD SIGNALS", C.MAGENTA)
    print(f"  Risk level:  {g(risk, colors.get(risk, C.YELLOW) + C.BOLD)}  {g('(' + str(unique) + ' unique articles · ' + str(sources) + ' sources)', C.GRAY)}")
    stresses = world_situation.get("market_stress", [])
    for item in stresses[:3]:
        print(f"  {g('►', C.RED)} {item}")
    print()
    for category, data in list(signals.items())[:7]:
        count = data.get("count", 0)
        consensus = data.get("consensus", "LOW")
        source_count = data.get("unique_sources", 0)
        bar_color = C.RED if count > 12 else C.ORANGE if count > 6 else C.CYAN
        bar = g("█" * min(count, 15), bar_color) + g("░" * (15 - min(count, 15)), C.GRAY)
        print(f"  {g(category, C.WHITE):<26} {bar} {g(str(count), bar_color)}")
        print(f"  {'':<26}  {g(str(source_count) + ' sources', C.GRAY)} · Consensus: {g(consensus, C.GREEN if consensus == 'HIGH' else C.YELLOW if consensus == 'MEDIUM' else C.GRAY)}")
        headline = (data.get("headlines") or [{}])[0].get("title", "")
        if headline:
            print(f"  {'':<26}  {g('→ ' + headline[:52], C.GRAY)}")
        print()


def print_causal_chains(chains):
    if not chains:
        return
    sec("CAUSAL CHAINS", C.CYAN)
    for chain in chains[:4]:
        severity = chain.get("severity", "MODERATE")
        color = C.RED if severity == "HIGH" else C.ORANGE
        print(f"  {g(chain.get('name', ''), color + C.BOLD)}")
        print(f"    {g(chain.get('chain', ''), C.GRAY)}")
        print()


def print_oracle_memory(delta):
    sec("RUN MEMORY", C.CYAN)
    if not delta or not delta.get("has_previous"):
        print(g("  First run — baseline established. Next run will show delta.", C.GRAY))
        print()
        return
    trend = delta.get("risk_trend", "STABLE")
    trend_color = C.RED if trend == "DETERIORATING" else C.GREEN if trend == "IMPROVING" else C.YELLOW
    print(f"  Previous scan:   {g(delta.get('previous_scan', 'unknown'), C.GRAY)}")
    print(f"  Risk change:     {g(delta.get('risk_change', ''), C.WHITE)}  {g(trend, trend_color + C.BOLD)}")
    confidence_delta = delta.get("confidence_delta", 0)
    if confidence_delta:
        print(f"  Confidence:      {g(f'{confidence_delta:+.1f}%', C.RED if confidence_delta < -5 else C.GREEN if confidence_delta > 5 else C.YELLOW)}")
    print()


def print_whale_intel(whale_data):
    if not whale_data:
        return
    summary = whale_data.get("summary", {})
    btc = whale_data.get("btc", {})
    eth = whale_data.get("eth", {})
    congress = whale_data.get("congress", {})
    overall = summary.get("overall_signal", "UNKNOWN")
    color = C.RED if any(term in overall for term in ["EXIT", "SELL"]) else C.GREEN if "ACCUM" in overall else C.YELLOW
    sec("PUBLIC FLOW CONTEXT", C.CYAN)
    print(f"  Overall:   {g(overall, color + C.BOLD)}  {g('Confidence: ' + summary.get('confidence', 'LOW'), C.GRAY)}")
    if btc.get("wallets_checked", 0) > 0:
        print(f"  BTC flows: {g(btc.get('movement_signal', 'UNKNOWN'), C.YELLOW)} · {btc.get('wallets_checked', 0)} wallets")
    else:
        print(f"  BTC flows: {g('Source not connected', C.GRAY)}")
    if eth.get("status") == "no_key":
        print(f"  ETH flows: {g('Add ETHERSCAN_KEY to .env to enable', C.GRAY)}")
    else:
        print(f"  ETH flows: {g(eth.get('signal', 'UNKNOWN'), C.YELLOW)}")
    print(f"  Congress:  {g(congress.get('signal', 'NEUTRAL')[:45], C.YELLOW)}")
    print()


def print_historical_parallels(hist_data):
    matches = hist_data.get("top_matches", [])
    if not matches:
        return
    sec("HISTORICAL PARALLELS", C.YELLOW)
    print(g(f"  {hist_data.get('total_events_in_db', 0)} events in database · similarity analysis", C.GRAY))
    print()
    for index, match in enumerate(matches[:3], start=1):
        similarity = match.get("similarity", 0)
        color = C.RED if similarity >= 80 else C.ORANGE if similarity >= 60 else C.YELLOW
        bar = g("█" * int(similarity / 10), color) + g("░" * (10 - int(similarity / 10)), C.GRAY)
        print(f"  {g(str(index) + '.', C.GRAY)} {g(match.get('name', ''), C.WHITE)}  {g('(' + match.get('period', '') + ')', C.GRAY)}")
        if match.get("trigger"):
            print(f"     {g('Trigger: ' + match.get('trigger', '')[:60], C.GRAY)}")
        print(f"     Similarity  [{bar}] {g(str(similarity) + '%', color)}")
        if match.get("lesson"):
            print(f"     {g('Lesson:', C.GRAY)} {g(match.get('lesson', '')[:70], C.DIM)}")
        print()


def print_scenarios(scenarios):
    if not scenarios:
        return
    sec("SCENARIO ENGINE", C.GREEN)
    if scenarios.get("historical_note"):
        print(g(f"  Context: {scenarios.get('historical_note', '')[:70]}", C.GRAY))
        print()
    for key in ["bear", "base", "bull"]:
        item = scenarios.get(key, {})
        if not item:
            continue
        probability = item.get("probability", 0)
        color = C.RED if key == "bear" else C.GREEN if key == "bull" else C.YELLOW
        bar = g("█" * (probability // 5), color) + g("░" * (20 - probability // 5), C.GRAY)
        print(f"  {g(item.get('label', key.title()), color + C.BOLD):<32} [{bar}] {g(str(probability) + '%', color)}")
        print(f"    {g(item.get('market_path', ''), C.GRAY)}")
        print(f"    {g('4 weeks: ' + item.get('4_weeks', ''), C.WHITE)}")
        for trigger in item.get("triggers", [])[:2]:
            print(f"      {g('→ ' + trigger, C.GRAY)}")
        print()


def print_explainability(explain):
    if not explain:
        return
    sec("WHY THE SYSTEM READS THIS WAY", C.CYAN)
    for item in explain.get("supporting", [])[:4]:
        print(f"    {g('✓', C.GREEN)} {item}")
    for item in explain.get("contradicting", [])[:3]:
        print(f"    {g('⚠', C.YELLOW)} {item}")
    if explain.get("weakest_link"):
        print(f"  {g('Weakest component:', C.GRAY)} {explain.get('weakest_link')} ({explain.get('weakest_pct', 0):.0f}%)")
    print()


def print_tactical_read(prediction):
    if not prediction:
        return
    tactical = prediction.get("tactical_read", {})
    if not tactical:
        return
    sec("TACTICAL READ", C.YELLOW)
    stance = tactical.get("stance", "NEUTRAL")
    color = C.RED if stance == "DEFENSIVE" else C.GREEN if stance == "OPPORTUNISTIC" else C.YELLOW
    print(f"  Stance:    {g(stance, color + C.BOLD)}")
    for level in tactical.get("key_levels", [])[:3]:
        print(f"    {g('►', C.CYAN)} {level}")
    if tactical.get("avoid"):
        print(f"  {g('Avoid:', C.RED):<12} {tactical.get('avoid', '')[:65]}")
    if tactical.get("watch_for"):
        print(f"  {g('Watch for:', C.GREEN):<12} {tactical.get('watch_for', '')[:65]}")
    print()


def print_prediction(prediction, conf_breakdown):
    if not prediction:
        return
    outlook = prediction.get("overall_outlook", "NEUTRAL")
    confidence = int(prediction.get("confidence", 0) or 0)
    source = prediction.get("ai_source", "unknown")
    summary = prediction.get("summary", "")
    generated = prediction.get("generated_at", "")[:19]
    color_map = {"BULLISH": C.GREEN, "MILDLY BULLISH": C.GREEN, "BEARISH": C.RED, "VOLATILE": C.ORANGE, "CRITICAL": C.BRED, "NEUTRAL": C.YELLOW}
    sec("SCENARIO SUMMARY", C.GREEN)
    situation = prediction.get("current_situation_summary", "")
    if situation:
        print(g("  Situation:", C.WHITE))
        for line in wrap(situation, 62):
            print(g(line, C.GRAY))
        print()
    bar = g("█" * (confidence // 10), C.GREEN) + g("░" * (10 - confidence // 10), C.GRAY)
    interpretation = conf_breakdown.get("interpretation", "") if conf_breakdown else ""
    print(f"  Outlook:         {g(outlook, color_map.get(outlook, C.YELLOW) + C.BOLD)}")
    print(f"  Confidence:      [{bar}] {g(str(confidence) + '%', C.CYAN)}  {g('(' + interpretation + ')', C.GRAY) if interpretation else ''}")
    domains = prediction.get("domain_outlooks", {})
    if domains:
        print("\n" + g("  Domain outlook:", C.WHITE))
        for domain, text in domains.items():
            domain_color = C.RED if any(term in text.upper() for term in ["BEAR", "DANGER"]) else C.GREEN if any(term in text.upper() for term in ["BULL", "POSITIVE"]) else C.GRAY
            print(f"    {g(domain.capitalize() + ':', C.CYAN):<16} {g(text[:55], domain_color)}")
    watch = prediction.get("what_to_watch", [])
    if watch:
        print("\n" + g("  Watch:", C.CYAN))
        for item in watch[:3]:
            print(f"    {g('►', C.GREEN)} {item}")
    if prediction.get("biggest_risk"):
        print(f"  {g('⚠ Risk:', C.RED):<12} {prediction.get('biggest_risk', '')[:60]}")
    if prediction.get("biggest_opportunity"):
        print(f"  {g('★ Opp:', C.GREEN):<12} {prediction.get('biggest_opportunity', '')[:60]}")
    if summary:
        print("\n" + g("  Summary:", C.WHITE))
        for line in wrap(summary, 62):
            print(g(line, C.GRAY))
    print(g(f"  Source: {source}  ·  Generated: {generated}", C.GRAY))
    print()


def print_accuracy(acc):
    if not acc:
        return
    sec("RESEARCH SCOREBOARD", C.CYAN)
    hit_rate = acc.get("hit_rate", 0)
    last_10 = acc.get("last_10_rate", 0)
    color = C.GREEN if hit_rate >= 60 else C.YELLOW if hit_rate >= 45 else C.RED
    print(f"  Total summaries:      {acc.get('total_predictions', 0)}")
    print(f"  Overall hit rate:     {g(str(hit_rate) + '%', color)}")
    print(f"  Last 10 hit rate:     {g(str(last_10) + '%', color)}")
    print()


def print_footer():
    print()
    print(g("  " + "─" * 58, C.GRAY))
    print(g("  Anteroom Oracle  ·  Research system  ·  Data saved locally", C.GRAY))
    print(g(f"  Storage: {DATA_PATH}/  ·  Run again for a fresh scan", C.GRAY))
    print()


def render(hw, prices, news_data, world_situation, whale_data, hist_data,
           prediction, val_report, conf_breakdown, delta, regime_data,
           accuracy_stats, geo_index, scenarios, explain, causal_chains):
    clr()
    source = prediction.get("ai_source", "") if prediction else ""
    print_header(source)
    print_data_health(val_report)
    print_markets(prices)
    print_geo_risk_index(geo_index)
    print_regime(regime_data)
    print_world_signals(news_data, world_situation)
    print_causal_chains(causal_chains)
    print_oracle_memory(delta)
    print_whale_intel(whale_data)
    print_historical_parallels(hist_data)
    print_scenarios(scenarios)
    print_explainability(explain)
    print_tactical_read(prediction)
    print_prediction(prediction, conf_breakdown)
    print_accuracy(accuracy_stats)
    print_footer()
