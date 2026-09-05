"""Claude-authored OSINT report synthesis + Typst render.

Synthesis is deterministic (no LLM author stage). Visualisations are
produced as PNGs via matplotlib and embedded by Typst.
"""
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .report import _absolute_utc, _esc, _parse_as_of, _style_for


# ---------- signal canonicalisation ----------

_STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with",
    "by", "at", "near", "from", "over", "vs", "via",
}


def _tokens(s: str) -> set[str]:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return {t for t in s.split() if t and t not in _STOPWORDS and len(t) > 2}


def _similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _cluster_signals(members: list[dict], horizon: str,
                     threshold: float = 0.35) -> list[dict]:
    """Greedy Jaccard clustering of signals across members for one horizon.

    Returns list of clusters: {canonical, members, class, count, items:[{member,model,...}]}.
    """
    flat = []
    for m in members:
        if "_error" in m:
            continue
        for sig in (m.get("signals") or {}).get(horizon, []) or []:
            if not isinstance(sig, dict):
                continue
            flat.append({
                "member": m["_member"],
                "model": m["_model"],
                "signal": sig.get("signal", ""),
                "signal_class": sig.get("signal_class", "other"),
                "interpretation": sig.get("interpretation", ""),
                "monitoring_strategy": sig.get("monitoring_strategy", ""),
                "sources": sig.get("sources", []) or [],
                "rationale": sig.get("rationale", ""),
                "novelty": float(sig.get("novelty_self_score") or 0.0),
            })

    clusters: list[dict] = []
    for item in flat:
        best_idx, best_sim = -1, 0.0
        for i, c in enumerate(clusters):
            sim = _similarity(item["signal"], c["canonical"])
            if sim > best_sim:
                best_sim, best_idx = sim, i
        if best_idx >= 0 and best_sim >= threshold:
            c = clusters[best_idx]
            c["items"].append(item)
            c["members"].add(item["member"])
        else:
            clusters.append({
                "canonical": item["signal"],
                "class": item["signal_class"],
                "members": {item["member"]},
                "items": [item],
            })

    for c in clusters:
        c["count"] = len(c["members"])
        c["mean_novelty"] = sum(i["novelty"] for i in c["items"]) / len(c["items"])
        # class vote
        classes = Counter(i["signal_class"] for i in c["items"])
        c["class"] = classes.most_common(1)[0][0]
        # pick canonical = most novel phrasing
        c["canonical"] = max(c["items"], key=lambda i: i["novelty"])["signal"]
    clusters.sort(key=lambda c: (-c["count"], -c["mean_novelty"]))
    return clusters


# ---------- visualisations ----------

_MODEL_COLORS = {
    "anthropic/": "#cc785c",
    "deepseek/":  "#1e88a8",
    "google/":    "#4285f4",
    "moonshotai/": "#8b5cf6",
    "z-ai/":      "#10b981",
}


def _model_color(model_id: str) -> str:
    for p, c in _MODEL_COLORS.items():
        if model_id.startswith(p):
            return c
    return "#6b7280"


def _save_signal_overlap_chart(clusters_by_h: dict[str, list[dict]], out_path: Path) -> None:
    """Horizontal bar: for each horizon, top-N clusters by member count."""
    fig, axes = plt.subplots(
        len(clusters_by_h), 1,
        figsize=(9, 1 + 2.6 * len(clusters_by_h)),
        squeeze=False,
    )
    for ax, (h, clusters) in zip(axes[:, 0], clusters_by_h.items()):
        top = [c for c in clusters if c["count"] >= 2][:8]
        if not top:
            top = clusters[:6]
        labels = [c["canonical"][:55] + ("…" if len(c["canonical"]) > 55 else "") for c in top]
        vals = [c["count"] for c in top]
        colors = ["#0f766e" if v >= 3 else ("#0284c7" if v == 2 else "#94a3b8") for v in vals]
        ax.barh(range(len(top)), vals, color=colors)
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("members raising signal", fontsize=8)
        ax.set_title(f"Signal convergence — {h}", fontsize=10, loc="left")
        ax.set_xlim(0, 5)
        ax.tick_params(axis="x", labelsize=8)
        ax.grid(axis="x", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_class_mix_chart(members: list[dict], horizons: list[str], out_path: Path) -> None:
    """Stacked bar: per member, class composition across all horizons."""
    class_order = ["diplomatic", "military", "economic", "cyber", "maritime",
                   "air", "energy", "humanitarian", "satellite", "social",
                   "domestic_political", "legal", "other"]
    palette = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#0891b2",
               "#0ea5e9", "#ea580c", "#db2777", "#4f46e5", "#f59e0b",
               "#7c2d12", "#475569", "#94a3b8"]
    class_color = dict(zip(class_order, palette))

    names, stacks = [], []
    for m in members:
        if "_error" in m:
            continue
        counts = Counter()
        for h in horizons:
            for s in (m.get("signals") or {}).get(h, []) or []:
                cls = s.get("signal_class", "other")
                if cls not in class_color:
                    cls = "other"
                counts[cls] += 1
        names.append(m["_member"].replace("Council_Member_", ""))
        stacks.append(counts)

    fig, ax = plt.subplots(figsize=(9, 3.2))
    bottom = [0] * len(names)
    for cls in class_order:
        vals = [s.get(cls, 0) for s in stacks]
        if sum(vals) == 0:
            continue
        ax.bar(names, vals, bottom=bottom, color=class_color[cls], label=cls, width=0.6)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_ylabel("signals across all horizons", fontsize=8)
    ax.set_title("Signal-class composition by member", fontsize=10, loc="left")
    ax.tick_params(axis="both", labelsize=8)
    ax.legend(fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12),
              frameon=False)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_source_tier_chart(members: list[dict], horizons: list[str], out_path: Path) -> None:
    """Grouped bar: free / freemium / registration / paid share per member."""
    tiers = ["free", "freemium", "registration", "paid"]
    colors = {"free": "#16a34a", "freemium": "#65a30d", "registration": "#f59e0b", "paid": "#dc2626"}
    names, data = [], {t: [] for t in tiers}
    for m in members:
        if "_error" in m:
            continue
        c = Counter()
        for h in horizons:
            for s in (m.get("signals") or {}).get(h, []) or []:
                for src in s.get("sources") or []:
                    t = src.get("access_tier", "free")
                    if t not in tiers:
                        t = "free"
                    c[t] += 1
        total = sum(c.values()) or 1
        names.append(m["_member"].replace("Council_Member_", ""))
        for t in tiers:
            data[t].append(100 * c.get(t, 0) / total)

    fig, ax = plt.subplots(figsize=(9, 3))
    bottom = [0] * len(names)
    for t in tiers:
        ax.bar(names, data[t], bottom=bottom, color=colors[t], label=t, width=0.55)
        bottom = [b + v for b, v in zip(bottom, data[t])]
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of cited sources", fontsize=8)
    ax.set_title("Source access-tier mix by member (paid ≠ closed)", fontsize=10, loc="left")
    ax.tick_params(axis="both", labelsize=8)
    ax.legend(fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.14),
              frameon=False)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_novelty_scatter(members: list[dict], horizons: list[str], out_path: Path) -> None:
    """Scatter: novelty (y) vs member (x), one dot per signal, colour by horizon."""
    h_colors = {"24h": "#0ea5e9", "1w": "#7c3aed", "1m": "#f97316"}
    fig, ax = plt.subplots(figsize=(9, 3.2))
    member_names = [m["_member"].replace("Council_Member_", "")
                    for m in members if "_error" not in m]
    x_for = {n: i for i, n in enumerate(member_names)}

    for m in members:
        if "_error" in m:
            continue
        for h in horizons:
            for s in (m.get("signals") or {}).get(h, []) or []:
                ax.scatter(
                    x_for[m["_member"].replace("Council_Member_", "")],
                    float(s.get("novelty_self_score") or 0.0),
                    c=h_colors.get(h, "#94a3b8"),
                    s=40, alpha=0.75, edgecolors="white", linewidths=0.8,
                )
    ax.set_xticks(range(len(member_names)))
    ax.set_xticklabels(member_names, fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_ylabel("self-reported novelty", fontsize=8)
    ax.set_title("Signal novelty (self-scored) by member and horizon", fontsize=10, loc="left")
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    handles = [plt.Line2D([], [], marker="o", color="w", markerfacecolor=c, markersize=8, label=h)
               for h, c in h_colors.items() if h in horizons]
    ax.legend(handles=handles, fontsize=8, loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------- Typst writer ----------

def _horizon_cluster_block(h: str, clusters: list[dict], abs_time: str) -> list[str]:
    lines = [f"== Horizon {h} — through {abs_time}", ""]

    convergent = [c for c in clusters if c["count"] >= 3]
    paired = [c for c in clusters if c["count"] == 2]
    singletons = [c for c in clusters if c["count"] == 1]

    lines.append(
        f"*{len(convergent)}* convergent signal(s) (≥3 members), *{len(paired)}* paired, "
        f"*{len(singletons)}* singleton. Total distinct clusters: *{len(clusters)}*."
    )
    lines.append("")

    if convergent:
        lines.append("=== Convergent signals (≥3 members)")
        for c in convergent:
            members_str = ", ".join(sorted(c["members"]))
            lines.append("")
            lines.append(f"*{_esc(c['canonical'])}*  — class: `{_esc(c['class'])}` · raised by "
                         f"{c['count']}/5 ({_esc(members_str)})")
            # show one representative interpretation + strategy
            rep = max(c["items"], key=lambda i: len(i.get("interpretation", "")))
            lines.append("")
            lines.append(f"_Interpretation._  {_esc(rep['interpretation'])}")
            lines.append("")
            lines.append(f"_Monitoring._  {_esc(rep['monitoring_strategy'])}")
            if rep["sources"]:
                src_strs = []
                for s in rep["sources"][:4]:
                    tier = s.get("access_tier", "?")
                    src_strs.append(f"{_esc(s.get('name','?'))} ({_esc(tier)})")
                lines.append("")
                lines.append(f"_Sources._  {'; '.join(src_strs)}")
        lines.append("")

    # imaginative picks = top novelty across singletons + paired
    imaginative = sorted(
        [c for c in (singletons + paired) if c["mean_novelty"] >= 0.6],
        key=lambda c: -c["mean_novelty"],
    )[:4]
    if imaginative:
        lines.append("=== Most imaginative singletons / pairs")
        for c in imaginative:
            members_str = ", ".join(sorted(c["members"]))
            rep = c["items"][0]
            lines.append("")
            lines.append(f"*{_esc(c['canonical'])}*  — class: `{_esc(c['class'])}` · "
                         f"novelty {c['mean_novelty']:.2f} · by {_esc(members_str)}")
            lines.append("")
            lines.append(f"_Interpretation._  {_esc(rep['interpretation'])}")
            lines.append("")
            lines.append(f"_Monitoring._  {_esc(rep['monitoring_strategy'])}")
            if rep["sources"]:
                src_strs = [f"{_esc(s.get('name','?'))} ({_esc(s.get('access_tier','?'))})"
                            for s in rep["sources"][:3]]
                lines.append("")
                lines.append(f"_Sources._  {'; '.join(src_strs)}")
        lines.append("")
    return lines


def _full_signal_appendix(members: list[dict], horizons: list[str]) -> list[str]:
    lines = ["= Appendix: full signal inventory", ""]
    for m in members:
        if "_error" in m:
            lines.append(f"== {_esc(m['_member'])} — error")
            lines.append(f"`{_esc(m.get('_error','?'))}`")
            continue
        code, label, color = _style_for(m["_model"])
        lines.append(f"== {_esc(m['_member'])} ({_esc(m['_model'])})")
        if m.get("overall_notes"):
            lines.append(f"_Notes._  {_esc(m['overall_notes'])}")
            lines.append("")
        for h in horizons:
            lines.append(f"=== Horizon {h}")
            for i, s in enumerate((m.get("signals") or {}).get(h, []) or [], 1):
                lines.append("")
                lines.append(f"{i}. *{_esc(s.get('signal','?'))}* "
                             f"— `{_esc(s.get('signal_class','?'))}` · "
                             f"novelty {float(s.get('novelty_self_score') or 0):.2f}")
                lines.append("")
                lines.append(f"   _Interpretation._  {_esc(s.get('interpretation',''))}")
                lines.append("")
                lines.append(f"   _Monitoring._  {_esc(s.get('monitoring_strategy',''))}")
                lines.append("")
                lines.append(f"   _Rationale._  {_esc(s.get('rationale',''))}")
                if s.get("sources"):
                    lines.append("")
                    lines.append("   _Sources:_")
                    for src in s["sources"]:
                        lines.append(
                            f"   - {_esc(src.get('name','?'))} "
                            f"({_esc(src.get('access_tier','?'))}, "
                            f"{_esc(src.get('type','?'))}, "
                            f"`{_esc(src.get('language','?'))}`) "
                            f"— `{_esc(src.get('url','?'))}`"
                        )
            lines.append("")
    return lines


def write_osint_report(run_dir: Path, scenario: str, horizons: list[str],
                       head_out: dict, members: list[dict],
                       grounding: list[dict]) -> Path:
    base = _parse_as_of(head_out.get("as_of") or datetime.now(timezone.utc).isoformat())
    run_ts_readable = base.strftime("%d %b %Y %H:%M UTC")

    # cluster + viz
    clusters_by_h = {h: _cluster_signals(members, h) for h in horizons}

    viz_dir = run_dir / "viz"
    viz_dir.mkdir(exist_ok=True)
    p_overlap = viz_dir / "signal_overlap.png"
    p_class = viz_dir / "class_mix.png"
    p_tier = viz_dir / "source_tier.png"
    p_nov = viz_dir / "novelty_scatter.png"
    _save_signal_overlap_chart(clusters_by_h, p_overlap)
    _save_class_mix_chart(members, horizons, p_class)
    _save_source_tier_chart(members, horizons, p_tier)
    _save_novelty_scatter(members, horizons, p_nov)

    # ----- stats for executive summary -----
    n_total_signals = sum(
        len((m.get("signals") or {}).get(h, []) or [])
        for m in members if "_error" not in m for h in horizons
    )
    all_srcs = []
    for m in members:
        if "_error" in m:
            continue
        for h in horizons:
            for s in (m.get("signals") or {}).get(h, []) or []:
                all_srcs.extend(s.get("sources") or [])
    tier_counts = Counter(s.get("access_tier", "free") for s in all_srcs)
    type_counts = Counter(s.get("type", "other") for s in all_srcs)
    lang_counts = Counter(s.get("language", "en") for s in all_srcs)

    # most imaginative overall (top novelty)
    all_items_flat = []
    for m in members:
        if "_error" in m:
            continue
        for h in horizons:
            for s in (m.get("signals") or {}).get(h, []) or []:
                all_items_flat.append({
                    **s, "_member": m["_member"], "_horizon": h,
                })
    top_novel = sorted(all_items_flat, key=lambda s: -float(s.get("novelty_self_score") or 0))[:5]

    # ----- Typst document -----
    lines: list[str] = [
        f'#set document(title: "OSINT Signals Council — {_esc(scenario[:60])}")',
        '#set page(',
        '  paper: "a4",',
        '  margin: (top: 2.6cm, bottom: 2.4cm, left: 2cm, right: 2cm),',
        '  numbering: "1 / 1",',
        '  number-align: center,',
        '  header: context {',
        '    if counter(page).get().first() > 1 {',
        '      set text(size: 8pt, fill: rgb("#6b7280"))',
        '      grid(columns: (1fr, auto),',
        '        [Geopol Forecast Council — OSINT variant],',
        f'        [{run_ts_readable}],',
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
        '#v(2cm)',
        '#align(center)[',
        '  #text(size: 26pt, weight: "bold")[OSINT Signals Council]',
        '  #v(4pt)',
        '  #text(size: 11pt, fill: rgb("#6b7280"))[What five open-source signals each council member would watch]',
        ']',
        '#v(1.2cm)',
        '#block(inset: 14pt, stroke: 0.6pt + rgb("#d1d5db"), radius: 4pt, width: 100%)[',
        '  #text(size: 9pt, fill: rgb("#6b7280"), weight: "bold")[SCENARIO]',
        '  #v(4pt)',
        f'  #text(size: 12pt)[{_esc(scenario)}]',
        ']',
        '#v(10pt)',
        '#grid(columns: (auto, 1fr), column-gutter: 14pt, row-gutter: 6pt,',
        f'  text(fill: rgb("#6b7280"))[Run time], [{run_ts_readable}],',
    ]
    for h in horizons:
        lines.append(f'  text(fill: rgb("#6b7280"))[Horizon {h}], [{_absolute_utc(base, h)}],')
    lines.append('  text(fill: rgb("#6b7280"))[Variant], [OSINT-signals (Claude-authored synthesis)],')
    lines.append(')')
    lines.append('#pagebreak()')

    # ----- Executive summary -----
    lines += [
        '= Executive summary',
        '',
        f'The council produced *{n_total_signals}* distinct OSINT signal recommendations across '
        f'{len([m for m in members if "_error" not in m])} models and {len(horizons)} horizons. '
        'Below, signals are clustered by semantic similarity so that the same underlying '
        'observable raised by different models counts once.',
        '',
    ]
    # convergence headline per horizon
    for h, clusters in clusters_by_h.items():
        convg = [c for c in clusters if c["count"] >= 3]
        if convg:
            top = convg[0]
            lines.append(
                f'*{h}* — *{len(convg)}* convergent signal(s). Most raised: '
                f'"{_esc(top["canonical"])}" ({top["count"]}/5 members).'
            )
        else:
            lines.append(f'*{h}* — no signal was raised by 3+ members; panel is fragmented.')
        lines.append('')

    # source posture
    if all_srcs:
        total = sum(tier_counts.values())
        pct_free = 100 * (tier_counts.get("free", 0) + tier_counts.get("freemium", 0)) / total
        lines.append(
            f'Of *{total}* cited sources, *{pct_free:.0f}%* are free or freemium; '
            f'*{100*tier_counts.get("paid",0)/total:.0f}%* paid. '
            f'Dominant source types: '
            + ", ".join(f"`{t}` ({n})" for t, n in type_counts.most_common(5))
            + '.'
        )
        lines.append('')
        lines.append(
            'Languages represented: '
            + ", ".join(f"`{l}` ({n})" for l, n in lang_counts.most_common(6))
            + '.'
        )
        lines.append('')

    lines.append('#pagebreak()')

    # ----- Convergence & divergence per horizon -----
    lines += ['= Convergence, divergence, and imagination by horizon', '']
    for h in horizons:
        lines += _horizon_cluster_block(h, clusters_by_h[h], _absolute_utc(base, h))
    lines.append('#pagebreak()')

    # ----- Most imaginative overall -----
    lines += ['= Most imaginative signals overall', '',
              '_Ranked by self-reported novelty. Claude\'s judgment: these are the signals '
              'the panel flagged as cleverest or most non-obvious._', '']
    for s in top_novel:
        lines.append(
            f'- *{_esc(s.get("signal","?"))}* — `{_esc(s.get("signal_class","?"))}` · '
            f'{_esc(s["_member"])} · {_esc(s["_horizon"])} · '
            f'novelty {float(s.get("novelty_self_score") or 0):.2f}'
        )
        lines.append('')
        lines.append(f'  {_esc((s.get("interpretation","")[:260]))}')
        lines.append('')
    lines.append('#pagebreak()')

    # ----- Visualisations -----
    lines += ['= Visualisations', '']

    lines += [
        '== Signal convergence by horizon',
        '_Horizontal bars show how many of the five council members independently raised '
        'each clustered signal. Clusters are formed by Jaccard similarity of signal names (threshold 0.35)._',
        '',
        f'#image("viz/signal_overlap.png", width: 100%)',
        '#pagebreak()',
        '== Signal-class composition by member',
        '_Each member\'s five-per-horizon × N-horizon signal budget, coloured by class. '
        'Shows which models spread across classes vs double down on a single lens._',
        '',
        f'#image("viz/class_mix.png", width: 100%)',
        '',
        '== Source access-tier mix',
        '_Share of cited sources that are free, freemium, registration-gated, or paid. '
        '"Paid" does not mean "closed": every source here is, by instruction, open._',
        '',
        f'#image("viz/source_tier.png", width: 100%)',
        '#pagebreak()',
        '== Novelty by member and horizon',
        '_One dot per signal. Y-axis is the model\'s self-reported novelty score. '
        'Tight clusters near the bottom suggest a conservative signal diet; spread toward the top '
        'suggests imaginative picks._',
        '',
        f'#image("viz/novelty_scatter.png", width: 100%)',
        '#pagebreak()',
    ]

    # ----- Head SITREP (for world context) -----
    lines += [
        '= World-state context (Council Head SITREP)',
        '',
        f'_As-of: {_esc(head_out.get("as_of","?"))}_',
        '',
        _esc(head_out.get("sitrep", "") or ""),
        '',
        '== Key actors',
    ]
    for a in head_out.get("key_actors", []) or []:
        lines.append(f'- *{_esc(a.get("name","?"))}* — {_esc(a.get("stated_position",""))}')
    lines.append('')
    lines.append('== Load-bearing uncertainties')
    for u in head_out.get("load_bearing_uncertainties", []) or []:
        lines.append(f'- {_esc(u)}')
    if head_out.get("reporting_contradictions"):
        lines.append('')
        lines.append('== Reporting contradictions')
        for c in head_out["reporting_contradictions"]:
            lines.append(f'- {_esc(c)}')
    lines.append('#pagebreak()')

    # ----- Appendix -----
    lines += _full_signal_appendix(members, horizons)

    typ_path = run_dir / "osint-report.typ"
    typ_path.write_text("\n".join(lines))

    # compile
    pdf_path = run_dir / "osint-report.pdf"
    try:
        subprocess.run(
            ["typst", "compile", str(typ_path), str(pdf_path)],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        print("[typst] compile failed:")
        print(e.stderr)
        raise
    return pdf_path
