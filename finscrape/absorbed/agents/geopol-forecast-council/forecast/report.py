import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, pstdev


# ---------- Escape / formatting primitives ----------

def _esc(s) -> str:
    if s is None:
        return ""
    s = str(s).replace("\\", "\\\\")
    for ch in ("*", "_", "#", "<", ">", "@", "$", "`"):
        s = s.replace(ch, f"\\{ch}")
    return s


def _fmt(v, nd: int = 2) -> str:
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return "?"


# ---------- Model identity (code + Typst colour) ----------

# Typst literal expressions — used inline in the template, not quoted as strings.
_MODEL_STYLE = [
    (r"anthropic/",  ("CLD", "Claude",   'rgb("#cc785c")')),
    (r"deepseek/",   ("DSK", "DeepSeek", 'rgb("#1e88a8")')),
    (r"google/",     ("GEM", "Gemini",   'rgb("#4285f4")')),
    (r"moonshotai/", ("KMI", "Kimi",     'rgb("#8b5cf6")')),
    (r"z-ai/",       ("GLM", "GLM",      'rgb("#10b981")')),
    (r"x-ai/",       ("GRK", "Grok",     'rgb("#0ea5e9")')),
    (r"mistralai/",  ("MST", "Mistral",  'rgb("#f97316")')),
    (r"openai/",     ("OAI", "OpenAI",   'rgb("#000000")')),
]
_DEFAULT_STYLE = ("???", "Unknown", 'rgb("#6b7280")')


def _style_for(model_id: str) -> tuple[str, str, str]:
    for prefix, style in _MODEL_STYLE:
        if model_id.startswith(prefix):
            return style
    return _DEFAULT_STYLE


# ---------- Horizon → absolute UTC time ----------

_HORIZON_RE = re.compile(r"^\s*(\d+)\s*([hdwm])\s*$", re.IGNORECASE)


def _horizon_delta(h: str) -> timedelta | None:
    m = _HORIZON_RE.match(h)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    if unit == "h": return timedelta(hours=n)
    if unit == "d": return timedelta(days=n)
    if unit == "w": return timedelta(weeks=n)
    if unit == "m": return timedelta(days=30 * n)  # rough
    return None


def _absolute_utc(base: datetime, h: str) -> str:
    delta = _horizon_delta(h)
    if not delta:
        return "?"
    t = base + delta
    return t.strftime("%d %b %Y %H:%M UTC")


def _parse_as_of(as_of: str) -> datetime:
    try:
        s = as_of.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


# ---------- Tone heuristic (transparent, documented in methodology) ----------

_ESCALATORY = [
    r"\bstrike", r"\bwar\b", r"\bescalat", r"\battack", r"\bkill", r"\bassassinat",
    r"\bproxy\b", r"\bhostilit", r"\bcollapse", r"\benrichment", r"\bblockade",
    r"\binvasion", r"\brocket", r"\bmissile", r"\boffensive", r"\bretaliat",
    r"\bresum[ei]\w*", r"\bseize", r"\bclos(?:e|ure|ing)\s+of\s+hormuz",
    r"\bnuclear\s+(?:test|announcement|breakout)", r"\brupture", r"\bflare",
]
_CONCILIATORY = [
    r"\bcease[- ]?fire", r"\bagreement", r"\bdeal\b", r"\bde-?escalat",
    r"\btalks?\b", r"\bdiplomac", r"\bpause\b", r"\bwithdrawal", r"\brelease",
    r"\bnormali[zs]", r"\bframework", r"\bbreakthrough", r"\bresolution",
    r"\bexten(?:d|sion)", r"\bmediat", r"\bback[- ]channel", r"\binterim",
]


def _tone(text: str) -> str:
    t = (text or "").lower()
    e = sum(1 for p in _ESCALATORY if re.search(p, t))
    c = sum(1 for p in _CONCILIATORY if re.search(p, t))
    if e > c: return "escalatory"
    if c > e: return "conciliatory"
    return "mixed"


_TONE_COLOR = {
    "escalatory":   'rgb("#dc2626")',
    "conciliatory": 'rgb("#059669")',
    "mixed":        'rgb("#6b7280")',
}


# ---------- Stats ----------

def _overall_confidences(members: list[dict]) -> dict[str, float]:
    out = {}
    for m in members:
        if "_error" in m: continue
        c = m.get("overall_confidence")
        if isinstance(c, (int, float)):
            out[m["_member"]] = float(c)
    return out


def _per_horizon_conf(members: list[dict], horizons: list[str]) -> dict[str, dict[str, list[float]]]:
    """Return {horizon: {member: [confidences of its 3 predictions]}}."""
    out: dict[str, dict[str, list[float]]] = {h: {} for h in horizons}
    for m in members:
        if "_error" in m: continue
        fx = m.get("forecasts", {}) or {}
        for h in horizons:
            preds = fx.get(h, []) or []
            cs = [float(p["confidence"]) for p in preds if isinstance(p.get("confidence"), (int, float))]
            if cs:
                out[h][m["_member"]] = cs
    return out


def _tone_tally(members: list[dict], horizons: list[str]) -> dict[str, dict[str, int]]:
    out = {h: {"escalatory": 0, "conciliatory": 0, "mixed": 0} for h in horizons}
    for m in members:
        if "_error" in m: continue
        fx = m.get("forecasts", {}) or {}
        for h in horizons:
            for p in fx.get(h, []) or []:
                out[h][_tone(p.get("prediction", ""))] += 1
    return out


# ---------- Typst fragments ----------

def _preamble(title: str, run_ts_readable: str) -> list[str]:
    return [
        f'#set document(title: "{_esc(title)}")',
        '#set page(',
        '  paper: "a4",',
        '  margin: (top: 2.6cm, bottom: 2.4cm, left: 2cm, right: 2cm),',
        '  numbering: "1 / 1",',
        '  number-align: center,',
        '  header: context {',
        '    if counter(page).get().first() > 1 {',
        '      set text(size: 8pt, fill: rgb("#6b7280"))',
        '      grid(columns: (1fr, auto),',
        '        [Geopol Forecast Council],',
        f'        [{_esc(run_ts_readable)}],',
        '      )',
        '      v(-6pt)',
        '      line(length: 100%, stroke: 0.4pt + rgb("#d1d5db"))',
        '    }',
        '  },',
        ')',
        '#set text(font: "IBM Plex Sans", size: 10pt, lang: "en")',
        '#set par(justify: true, leading: 0.6em)',
        '#set heading(numbering: "1.")',
        '#show heading.where(level: 1): h => { v(10pt); block(text(size: 16pt, weight: "bold", h.body)) }',
        '#show heading.where(level: 2): h => { v(6pt); block(text(size: 12pt, weight: "bold", fill: rgb("#374151"), h.body)) }',
        '#show heading.where(level: 3): h => { v(4pt); block(text(size: 10.5pt, weight: "bold", h.body)) }',
        '',
        '#let confbar(v, color) = box[',
        '  #box(width: 4cm, height: 8pt, fill: rgb("#e5e7eb"), radius: 1.5pt)[',
        '    #place(left + horizon, box(width: v * 4cm, height: 8pt, fill: color, radius: 1.5pt))',
        '  ]',
        ']',
        '',
        '#let mdot(color, code) = box(baseline: 2pt)[',
        '  #box(width: 10pt, height: 10pt, fill: color, radius: 5pt)',
        '  #h(3pt) #text(size: 8.5pt, weight: "bold", code)',
        ']',
        '',
        '#let tonedot(color) = box(width: 8pt, height: 8pt, fill: color, radius: 4pt)',
        '',
    ]


def _cover(scenario: str, run_ts_readable: str, horizons: list[str],
           abs_times: dict[str, str], members: list[dict],
           head_model: str, author_model: str, grounding: list[dict]) -> list[str]:
    L = [
        '#v(2cm)',
        '#align(center)[',
        '  #text(size: 26pt, weight: "bold")[Geopol Forecast Council]',
        '  #v(4pt)',
        '  #text(size: 11pt, fill: rgb("#6b7280"))[Multi-model geopolitical forecast and methodology report]',
        ']',
        '#v(1.2cm)',
        '#block(inset: 14pt, stroke: 0.6pt + rgb("#d1d5db"), radius: 4pt, width: 100%)[',
        '  #text(size: 9pt, fill: rgb("#6b7280"), weight: "bold")[SCENARIO]',
        '  #v(4pt)',
        f'  #text(size: 12pt)[{_esc(scenario)}]',
        ']',
        '#v(10pt)',
        '#grid(columns: (auto, 1fr), column-gutter: 14pt, row-gutter: 6pt,',
        f'  text(fill: rgb("#6b7280"))[Run time], [{_esc(run_ts_readable)}],',
    ]
    for h in horizons:
        L.append(f'  text(fill: rgb("#6b7280"))[Horizon {_esc(h)}], [{_esc(abs_times.get(h, "?"))}],')
    L += [
        f'  text(fill: rgb("#6b7280"))[Council Head], [`{_esc(head_model)}`],',
        f'  text(fill: rgb("#6b7280"))[Report Author], [`{_esc(author_model)}`],',
    ]
    tools_summary = ", ".join(
        f"{g['tool']}({'ok' if g['ok'] else 'fail'})" for g in grounding
    )
    L.append(f'  text(fill: rgb("#6b7280"))[Grounding], [{_esc(tools_summary)}],')
    L += [')']

    L += ['', '#v(14pt)', '== Panel roster']
    L += ['', '#grid(columns: (auto, auto, 1fr), column-gutter: 10pt, row-gutter: 4pt,']
    for m in members:
        code, label, color = _style_for(m.get("_model", ""))
        conf = m.get("overall_confidence")
        conf_s = _fmt(conf) if conf is not None else "—"
        err = " (error)" if "_error" in m else ""
        L.append(
            f'  mdot({color}, "{code}"), text(weight: "bold")[{_esc(label)}{err}], '
            f'text(fill: rgb("#6b7280"))[`{_esc(m.get("_model",""))}` · overall {conf_s}],'
        )
    L += [')']

    L += ['', '#v(12pt)',
          'This report presents forecasts from a deliberately diverse council of large language models. '
          'Each model was briefed on an identical SITREP, asked to produce three concrete predictions '
          'per horizon, and scored on its own confidence. The remainder of this document presents their '
          'predictions, a comparative analysis of divergence and convergence, and the methodology used.',
          '#pagebreak()']
    return L


def _confidence_chart(members: list[dict], horizons: list[str],
                      per_h_conf: dict[str, dict[str, list[float]]]) -> list[str]:
    L = ['== Member confidence by horizon', '',
         'Each bar shows the member\'s *mean confidence across its three predictions* at that horizon. '
         'Longer bar = more confident the prediction will hold.', '']
    for h in horizons:
        L += ['', f'=== {_esc(h)}', '']
        rows = []
        for m in members:
            if "_error" in m: continue
            code, label, color = _style_for(m.get("_model", ""))
            cs = per_h_conf.get(h, {}).get(m["_member"], [])
            avg = mean(cs) if cs else 0.0
            rows.append((label, code, color, avg, cs))
        rows.sort(key=lambda r: r[3], reverse=True)
        L += ['', '#grid(columns: (auto, auto, auto, auto), column-gutter: 10pt, row-gutter: 5pt,']
        for label, code, color, avg, cs in rows:
            per_pred = " · ".join(f"{_fmt(c)}" for c in cs) or "—"
            L.append(
                f'  mdot({color}, "{code}"), text(weight: "bold")[{_esc(label)}], '
                f'confbar({_fmt(avg,3)}, {color}), '
                f'text(fill: rgb("#6b7280"))[mean {_fmt(avg)} · per-pred {_esc(per_pred)}],'
            )
        L += [')']
        if len(rows) >= 2:
            vals = [r[3] for r in rows]
            spread = max(vals) - min(vals)
            sd = pstdev(vals) if len(vals) > 1 else 0.0
            L += ['',
                  f'_Spread at {_esc(h)}: range {_fmt(spread)}, σ {_fmt(sd)}, '
                  f'high {_fmt(max(vals))} ({_esc(rows[0][0])}), low {_fmt(min(vals))} ({_esc(rows[-1][0])})._']
    return L


def _tone_analysis(members: list[dict], horizons: list[str],
                   tone_tally: dict[str, dict[str, int]]) -> list[str]:
    n_members = len([m for m in members if "_error" not in m])
    n_total = sum(tone_tally[horizons[0]].values()) if horizons else 0
    L = ['== Predicted tone by horizon', '',
         f'Each of the {n_total} predictions per horizon ({n_members} members × 3) is classified by keyword heuristic '
         'as *escalatory* (strikes, attacks, enrichment, blockade…), *conciliatory* (ceasefire, '
         'talks, framework, de-escalation…), or *mixed* (both or neither). The heuristic is coarse '
         'but transparent — see methodology appendix.',
         '']
    L += ['#grid(columns: (auto, auto, auto, auto, auto), column-gutter: 10pt, row-gutter: 4pt,',
          '  text(weight: "bold")[Horizon],',
          '  text(weight: "bold")[#tonedot(rgb("#dc2626")) Escalatory],',
          '  text(weight: "bold")[#tonedot(rgb("#059669")) Conciliatory],',
          '  text(weight: "bold")[#tonedot(rgb("#6b7280")) Mixed],',
          '  text(weight: "bold")[Leaning],']
    for h in horizons:
        t = tone_tally[h]
        e, c, mx = t["escalatory"], t["conciliatory"], t["mixed"]
        lean = "escalatory" if e > c else ("conciliatory" if c > e else "balanced")
        lean_color = _TONE_COLOR.get(lean, 'rgb("#6b7280")') if lean != "balanced" else 'rgb("#6b7280")'
        L.append(
            f'  [{_esc(h)}], [{e}/{n_total}], [{c}/{n_total}], [{mx}/{n_total}], '
            f'text(fill: {lean_color}, weight: "bold")[{_esc(lean)}],'
        )
    L += [')']

    # Per-member tone breakdown
    L += ['', '=== Tone distribution per member', '']
    for m in members:
        if "_error" in m: continue
        code, label, color = _style_for(m.get("_model", ""))
        fx = m.get("forecasts", {}) or {}
        counts = {"escalatory": 0, "conciliatory": 0, "mixed": 0}
        total = 0
        for h in horizons:
            for p in fx.get(h, []) or []:
                counts[_tone(p.get("prediction", ""))] += 1
                total += 1
        L.append(
            f'- #mdot({color}, "{code}") *{_esc(label)}* — '
            f'{counts["escalatory"]} escalatory, {counts["conciliatory"]} conciliatory, '
            f'{counts["mixed"]} mixed (of {total})'
        )
    return L


def _divergence_analysis(synthesis: dict, members: list[dict], horizons: list[str],
                         per_h_conf: dict[str, dict[str, list[float]]]) -> list[str]:
    L = ['== Divergence and convergence', '']
    # Deterministic numerical summary
    L += ['=== Confidence spread by horizon', '']
    L += ['#grid(columns: (auto, auto, auto, auto, auto), column-gutter: 10pt, row-gutter: 4pt,',
          '  text(weight: "bold")[Horizon],',
          '  text(weight: "bold")[Low],',
          '  text(weight: "bold")[High],',
          '  text(weight: "bold")[Range],',
          '  text(weight: "bold")[σ],']
    for h in horizons:
        per_mem = per_h_conf.get(h, {})
        avgs = [mean(v) for v in per_mem.values() if v]
        if not avgs:
            L.append(f'  [{_esc(h)}], [—], [—], [—], [—],')
            continue
        lo, hi = min(avgs), max(avgs)
        sd = pstdev(avgs) if len(avgs) > 1 else 0.0
        L.append(f'  [{_esc(h)}], [{_fmt(lo)}], [{_fmt(hi)}], [{_fmt(hi-lo)}], [{_fmt(sd)}],')
    L += [')']

    conv = synthesis.get("convergent_signals", []) or []
    if conv:
        L += ['', '=== Where the council converged', '']
        for s in conv:
            L.append(f'- {_esc(s)}')
    cont = synthesis.get("contested_signals", []) or []
    if cont:
        L += ['', '=== Where the council split', '']
        for s in cont:
            L.append(f'- {_esc(s)}')

    # Sharp disagreements from synthesis by_horizon
    by_h = synthesis.get("by_horizon", {}) or {}
    any_sd = False
    for h in horizons:
        sds = (by_h.get(h) or {}).get("sharp_disagreements", []) or []
        if sds:
            if not any_sd:
                L += ['', '=== Sharp disagreements', '']
                any_sd = True
            L += ['', f'*{_esc(h)}:*']
            for s in sds:
                L.append(f'- {_esc(s)}')

    themes = synthesis.get("cross_horizon_themes", []) or []
    if themes:
        L += ['', '=== Cross-horizon themes', '']
        for t in themes:
            L.append(f'- {_esc(t)}')

    return L


def _clustered_predictions(synthesis: dict, horizons: list[str], abs_times: dict[str, str]) -> list[str]:
    L = ['== Clustered predictions by horizon',
         '',
         'The Report_Author has clustered concrete predictions across members where they were '
         'structurally similar. Consensus strength reflects how many members raised a member of each cluster.',
         '']
    by_h = synthesis.get("by_horizon", {}) or {}
    for h in horizons:
        entry = by_h.get(h, {}) or {}
        L += ['', f'=== {_esc(h)} — by {_esc(abs_times.get(h, "?"))}', '']
        headline = entry.get("headline", "")
        if headline:
            L += [f'*Headline.* {_esc(headline)}', '']
        tops = entry.get("top_predictions", []) or []
        if not tops:
            L.append('(no clustered predictions)')
            continue
        for i, p in enumerate(tops, 1):
            mem = ", ".join(p.get("members_raising", []))
            strength = p.get("consensus_strength", "")
            strength_color = {
                "strong": 'rgb("#059669")',
                "moderate": 'rgb("#0891b2")',
                "weak": 'rgb("#d97706")',
                "single-source": 'rgb("#6b7280")',
            }.get(strength, 'rgb("#6b7280")')
            L += [
                f'==== {i}. {_esc(p.get("prediction",""))}',
                '',
                f'#box(inset: (x: 6pt, y: 2pt), fill: {strength_color}, radius: 2pt)['
                f'#text(fill: white, size: 8.5pt, weight: "bold")[{_esc(strength.upper())}]] '
                f'#h(6pt) mean confidence *{_fmt(p.get("mean_confidence"))}* '
                f'#h(6pt) raised by: {_esc(mem)}',
                '',
            ]
            if p.get("supporting_rationale"):
                L += [f'_Supporting._ {_esc(p["supporting_rationale"])}', '']
            if p.get("counterveiling_rationale"):
                L += [f'_Counterveiling._ {_esc(p["counterveiling_rationale"])}', '']
            if p.get("watch_trigger"):
                L += [f'_Watch trigger._ {_esc(p["watch_trigger"])}', '']
    return L


def _sitrep_section(head_out: dict) -> list[str]:
    L = ['== SITREP', '', _esc(head_out.get("sitrep", "")), '']
    if head_out.get("key_actors"):
        L += ['=== Key actors', '']
        for a in head_out["key_actors"]:
            L.append(f'- *{_esc(a.get("name",""))}* — {_esc(a.get("stated_position",""))}')
    if head_out.get("load_bearing_uncertainties"):
        L += ['', '=== Load-bearing uncertainties', '']
        for u in head_out["load_bearing_uncertainties"]:
            L.append(f'- {_esc(u)}')
    if head_out.get("reporting_contradictions"):
        L += ['', '=== Reporting contradictions flagged in grounding', '']
        for c in head_out["reporting_contradictions"]:
            L.append(f'- {_esc(c)}')
    return L


def _delta_section(synthesis: dict) -> list[str]:
    delta = synthesis.get("delta_vs_prior")
    if not isinstance(delta, dict) or not delta:
        return []
    L = ['#pagebreak()', '= Delta vs prior run', '',
         f'_Compared against run `{_esc(delta.get("prior_run_id",""))}` '
         f'(as of {_esc(delta.get("prior_run_as_of","?"))})._', '']
    sections = [
        ("circumstance_changes", "Circumstance changes",
         "What materially changed in the world between the two runs."),
        ("lens_shifts", "Analytical lens shifts",
         "How the council's framing, predictions, and confidences moved."),
        ("vindicated_signals", "Vindicated prior signals",
         "Prior predictions or watch-triggers corroborated by intervening events."),
        ("falsified_signals", "Falsified prior signals",
         "Prior predictions or watch-triggers contradicted by intervening events."),
    ]
    for key, title, blurb in sections:
        items = delta.get(key) or []
        if not items:
            continue
        L += ['', f'== {title}', '', _esc(blurb), '']
        for it in items:
            L.append(f'- {_esc(it)}')
    return L


def _watchlist_and_calibration(synthesis: dict) -> list[str]:
    L = []
    tr = synthesis.get("watchlist_triggers", []) or []
    if tr:
        L += ['== Watchlist triggers', '',
              'Concrete observable events that, if they occur, would meaningfully shift the council\'s forecasts.', '']
        for t in tr:
            L.append(f'- {_esc(t)}')
    cal = synthesis.get("calibration_note", "")
    if cal:
        L += ['', '== Calibration note', '', _esc(cal)]
    return L


def _per_member_compact(members: list[dict], horizons: list[str]) -> list[str]:
    L = ['#pagebreak()', '== Per-member predictions', '']
    for m in members:
        code, label, color = _style_for(m.get("_model", ""))
        header = f'=== #mdot({color}, "{code}") {_esc(label)}'
        L += ['', header,
              f'_`{_esc(m.get("_model",""))}` · lineage {_esc(m.get("_lineage","?"))}_']
        if "_error" in m:
            L.append(f'Error: {_esc(m["_error"])}')
            continue
        if m.get("overall_confidence") is not None:
            L.append(f'*Overall confidence.* {_fmt(m.get("overall_confidence"))}')
        if m.get("overall_notes"):
            L.append(f'_Notes._ {_esc(m["overall_notes"])}')
        fx = m.get("forecasts", {}) or {}
        for h in horizons:
            preds = fx.get(h, []) or []
            L += ['', f'==== {_esc(h)}']
            if not preds:
                L.append('(no predictions returned)')
                continue
            for i, p in enumerate(preds, 1):
                tone = _tone(p.get("prediction", ""))
                tc = _TONE_COLOR[tone]
                L += [
                    '',
                    f'*{i}. {_esc(p.get("prediction",""))}* '
                    f'#h(4pt) #tonedot({tc}) #h(2pt) '
                    f'#text(size: 8.5pt, fill: rgb("#6b7280"))[{_esc(tone)}] '
                    f'#h(6pt) conf *{_fmt(p.get("confidence"))}*',
                    '',
                    f'_Reasoning._ {_esc(p.get("supporting_reasoning",""))}',
                    '',
                    f'_Supporting precedent._ {_esc(p.get("historical_precedent_supporting",""))}',
                    '',
                    f'_Counterveiling precedent._ {_esc(p.get("historical_precedent_counterveiling",""))}',
                    '',
                    f'_Change factor._ {_esc(p.get("change_factor",""))}',
                ]
    return L


def _methodology(run_ts_readable: str, horizons: list[str], abs_times: dict[str, str],
                 members: list[dict], head_model: str, author_model: str,
                 grounding: list[dict]) -> list[str]:
    L = ['#pagebreak()', '== Methodology and interpretation notes', '']
    L += [
        f'*Run time.* {_esc(run_ts_readable)}. All horizon end-times in this report are '
        f'computed deterministically as run-time + horizon (1m approximated as 30 days):',
        '',
    ]
    for h in horizons:
        L.append(f'- `{_esc(h)}` → {_esc(abs_times.get(h,"?"))}')

    L += ['', '*Grounding stack.* Each source is invoked independently and the results concatenated '
          'into the Council_Head\'s input. The Head then produces a single reconciled SITREP.', '']
    for g in grounding:
        status = "ok" if g.get("ok") else f"failed — {g.get('error','')}"
        n = len(g.get("items", []) or [])
        L.append(f'- `{_esc(g.get("tool",""))}` — {_esc(status)} ({n} items)')

    L += ['', f'*Panel.* {len(members)} models from different training lineages, polled in parallel with '
          'identical prompts. Members do not see each other\'s outputs.', '']
    for m in members:
        code, label, color = _style_for(m.get("_model", ""))
        L.append(f'- #mdot({color}, "{code}") {_esc(label)} — `{_esc(m.get("_model",""))}` '
                 f'(lineage: {_esc(m.get("_lineage","?"))})')
    L += ['', f'*Council Head.* `{_esc(head_model)}` (produces SITREP + uncertainties). '
          f'*Report Author.* `{_esc(author_model)}` (clusters predictions, writes synthesis). '
          'Both roles are single-shot calls with structured-output JSON schema.']

    L += ['', '*Tone heuristic.* Each prediction is classified as escalatory / conciliatory / mixed '
          'by keyword matching. This is a coarse post-hoc label — it reflects the *tone of the predicted '
          'event*, not whether a member believes escalation is desirable. Escalatory keywords include: '
          f'{_esc(", ".join(p.strip(chr(92)+"b ").strip() for p in _ESCALATORY[:10]))}… '
          f'Conciliatory keywords include: {_esc(", ".join(p.strip(chr(92)+"b ").strip() for p in _CONCILIATORY[:10]))}…']

    L += ['', '*What this report is.* A structured snapshot of five LLMs\' concrete predictions at a '
          'single moment in time, grounded in current reporting. It is useful for (a) mapping where '
          'models agree and disagree, (b) surfacing concrete watch-triggers, and (c) comparing against '
          'actual outcomes after the horizon lapses.', '',
          '*What this report is not.* It is not a calibrated probabilistic forecast in the superforecaster '
          'sense — no base-rate adjustment, no market aggregation, no explicit bias correction. LLM '
          'confidences are *model-reported* and not necessarily well-calibrated. Tail risks in particular '
          'tend to be under-weighted by default-temperature sampling.']
    return L


def _grounding_appendix(grounding: list[dict]) -> list[str]:
    L = ['#pagebreak()', '== Grounding appendix', '']
    for g in grounding:
        L += ['', f'=== Source: `{_esc(g.get("tool",""))}`']
        if not g.get("ok"):
            L.append(f'_Failed: {_esc(g.get("error",""))}_')
            continue
        items = g.get("items", []) or []
        if g["tool"] == "sonar":
            L += ['', _esc((g.get("output") or "")[:3000])]
            if items:
                L += ['', '*Citations.*']
                for it in items[:20]:
                    url = it.get("url", "")
                    if url:
                        L.append(f'- #link("{url}")')
        elif g["tool"] == "tavily":
            for it in items[:20]:
                url = it.get("url", "")
                L += ['', f'*{_esc(it.get("title",""))}*  _(published {_esc(it.get("published",""))})_']
                if url:
                    L.append(f'#link("{url}")')
                if it.get("snippet"):
                    L.append(_esc(it["snippet"]))
        elif g["tool"] == "rss":
            for it in items[:30]:
                if it.get("_error"):
                    continue
                url = it.get("link", "")
                ts = it["published_iso"] if it.get("published_iso") else it.get("published_raw", "?")
                L += ['', f'*{_esc(it.get("title",""))}*  _({_esc(it.get("feed",""))} — {_esc(ts)})_']
                if url:
                    L.append(f'#link("{url}")')
    return L


def _full_member_dump(members: list[dict], horizons: list[str]) -> list[str]:
    """Appendix rendering full per-member responses as formatted text (no JSON)."""
    L = ['#pagebreak()',
         '== Appendix: full model responses',
         '',
         'Every prediction from every member, rendered verbatim as formatted text. '
         'Use this section when you want to inspect each model\'s raw output in full.', '']
    for m in members:
        code, label, color = _style_for(m.get("_model", ""))
        L += ['#pagebreak()',
              f'=== #mdot({color}, "{code}") {_esc(label)}',
              f'_`{_esc(m.get("_model",""))}` · lineage {_esc(m.get("_lineage","?"))}_',
              '']
        if "_error" in m:
            L.append(f'*Error.* {_esc(m["_error"])}')
            continue
        if m.get("overall_confidence") is not None:
            L.append(f'*Overall confidence.* {_fmt(m.get("overall_confidence"))}')
        if m.get("overall_notes"):
            L.append(f'*Overall notes.* {_esc(m["overall_notes"])}')
        fx = m.get("forecasts", {}) or {}
        for h in horizons:
            preds = fx.get(h, []) or []
            L += ['', f'==== Horizon {_esc(h)}']
            if not preds:
                L.append('_No predictions returned at this horizon._')
                continue
            for i, p in enumerate(preds, 1):
                tone = _tone(p.get("prediction", ""))
                tc = _TONE_COLOR[tone]
                L += [
                    '',
                    f'===== Prediction {i}',
                    '',
                    f'#box(inset: (x: 6pt, y: 3pt), fill: rgb("#f3f4f6"), radius: 2pt, width: 100%)['
                    f'{_esc(p.get("prediction",""))}'
                    f']',
                    '',
                    f'#tonedot({tc}) #h(2pt) tone: *{_esc(tone)}* '
                    f'#h(8pt) confidence: *{_fmt(p.get("confidence"))}*',
                    '',
                    '*Supporting reasoning.*',
                    '',
                    _esc(p.get("supporting_reasoning", "")),
                    '',
                    '*Historical precedent — supporting.*',
                    '',
                    _esc(p.get("historical_precedent_supporting", "")),
                    '',
                    '*Historical precedent — counterveiling.*',
                    '',
                    _esc(p.get("historical_precedent_counterveiling", "")),
                    '',
                    '*Change factor.*',
                    '',
                    _esc(p.get("change_factor", "")),
                ]
    return L


# ---------- Top-level template ----------

def _build_typst(
    scenario: str,
    horizons: list[str],
    head_out: dict,
    members: list[dict],
    synthesis: dict,
    grounding: list[dict],
    head_model: str,
    author_model: str,
    include_full_dump: bool,
) -> str:
    run_dt = _parse_as_of(head_out.get("as_of") or datetime.now(timezone.utc).isoformat())
    run_ts_readable = run_dt.strftime("%d %b %Y %H:%M UTC")
    abs_times = {h: _absolute_utc(run_dt, h) for h in horizons}

    per_h_conf = _per_horizon_conf(members, horizons)
    tone_tally = _tone_tally(members, horizons)

    title = f"Geopol Forecast Council — {scenario[:60]}"
    L: list[str] = []
    L += _preamble(title, run_ts_readable)
    L += _cover(scenario, run_ts_readable, horizons, abs_times, members, head_model, author_model, grounding)

    L += ['= Executive summary', '']
    by_h = synthesis.get("by_horizon", {}) or {}
    for h in horizons:
        entry = by_h.get(h, {}) or {}
        L += [f'*{_esc(h)} — by {_esc(abs_times.get(h,"?"))}.* {_esc(entry.get("headline",""))}', '']

    L += _delta_section(synthesis)

    L += ['#pagebreak()', '= Comparative analysis', '']
    L += _confidence_chart(members, horizons, per_h_conf)
    L += ['', '#v(10pt)']
    L += _tone_analysis(members, horizons, tone_tally)
    L += ['', '#v(10pt)']
    L += _divergence_analysis(synthesis, members, horizons, per_h_conf)

    L += ['#pagebreak()', '= Predictions']
    L += _clustered_predictions(synthesis, horizons, abs_times)
    L += ['', '#v(10pt)']
    L += _watchlist_and_calibration(synthesis)

    L += _per_member_compact(members, horizons)

    L += ['#pagebreak()', '= SITREP & grounding']
    L += _sitrep_section(head_out)
    L += _grounding_appendix(grounding)

    L += _methodology(run_ts_readable, horizons, abs_times, members, head_model, author_model, grounding)

    if include_full_dump:
        L += _full_member_dump(members, horizons)

    return "\n".join(L)


def _compile(typ_path: Path) -> Path | None:
    pdf = typ_path.with_suffix(".pdf")
    try:
        subprocess.run(["typst", "compile", str(typ_path), str(pdf)], check=True)
        return pdf
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"[warn] typst compile failed for {typ_path.name}: {e}")
        return None


def write_report(
    out_dir: Path,
    scenario: str,
    horizons: list[str],
    head_out: dict,
    member_outs: list[dict],
    synthesis: dict,
    grounding: list[dict],
    head_model: str = "",
    author_model: str = "",
) -> Path:
    # Backwards-compatible raw dump (per-stage checkpoints are the authoritative store).
    safe_grounding = []
    for g in grounding:
        items = []
        for it in g.get("items", []) or []:
            item = {k: v for k, v in it.items() if k != "published"}
            if it.get("published"):
                item["published_iso"] = (
                    it["published"].isoformat() if hasattr(it["published"], "isoformat") else str(it["published"])
                )
            items.append(item)
        safe_grounding.append({**{k: v for k, v in g.items() if k != "items"}, "items": items})
    (out_dir / "raw.json").write_text(
        json.dumps(
            {
                "scenario": scenario, "horizons": horizons, "head": head_out,
                "members": member_outs, "synthesis": synthesis, "grounding": safe_grounding,
            },
            indent=2, default=str,
        )
    )

    # Try to pull head/author model ids from meta.json if not passed.
    meta_path = out_dir / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            head_model = head_model or (meta.get("council_head") or {}).get("model", "")
            author_model = author_model or (meta.get("report_author") or {}).get("model", "")
        except Exception:
            pass

    main_typ = out_dir / "report.typ"
    main_typ.write_text(_build_typst(
        scenario, horizons, head_out, member_outs, synthesis, grounding,
        head_model, author_model, include_full_dump=False,
    ))
    full_typ = out_dir / "report-full.typ"
    full_typ.write_text(_build_typst(
        scenario, horizons, head_out, member_outs, synthesis, grounding,
        head_model, author_model, include_full_dump=True,
    ))

    main_pdf = _compile(main_typ)
    _compile(full_typ)
    return main_pdf or main_typ
