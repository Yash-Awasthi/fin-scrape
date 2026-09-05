import json as _json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .config import Role
from .grounding import format_grounding_block, run_grounding
from .openrouter import call_json
from .report import write_report
from .schemas import author_schema, head_schema, member_schema

ROOT = Path(__file__).resolve().parent.parent
HEAD_PROMPT = (ROOT / "prompts/council_head.md").read_text()
MEMBER_PROMPT = (ROOT / "prompts/council_member.md").read_text()
AUTHOR_PROMPT = (ROOT / "prompts/report_author.md").read_text()


def _head_user_msg(scenario: str, horizons: list[str], grounding_block: str, now_iso: str) -> str:
    return (
        f"# Scenario\n\n{scenario}\n\n"
        f"# Horizons\n\n{', '.join(horizons)}\n\n"
        f"# Current time (treat as 'now' unless grounding shows otherwise)\n\n{now_iso}\n\n"
        f"# Grounding pack\n\n{grounding_block}"
    )


def _member_user_msg(scenario: str, horizons: list[str], head_out: dict) -> str:
    return (
        f"# Scenario\n\n{scenario}\n\n"
        f"# Horizons\n\n{', '.join(horizons)}\n\n"
        f"# SITREP (as of {head_out.get('as_of','?')})\n\n{head_out.get('sitrep','')}\n\n"
        f"# Key actors\n\n{_json.dumps(head_out.get('key_actors', []), indent=2)}\n\n"
        f"# Load-bearing uncertainties\n\n"
        + "\n".join(f"- {u}" for u in head_out.get("load_bearing_uncertainties", []))
        + "\n\n# Reporting contradictions\n\n"
        + "\n".join(f"- {c}" for c in head_out.get("reporting_contradictions", []))
    )


def _author_user_msg(scenario: str, horizons: list[str], head_out: dict, members: list[dict],
                     prior: dict | None = None) -> str:
    base = (
        f"# Scenario\n\n{scenario}\n\n"
        f"# Horizons\n\n{', '.join(horizons)}\n\n"
        f"# Council Head output\n\n{_json.dumps(head_out, indent=2)}\n\n"
        f"# Member outputs\n\n{_json.dumps(members, indent=2)}"
    )
    if prior:
        base += (
            f"\n\n# Prior run (for delta analysis)\n\n"
            f"## prior_run_id\n\n{prior['run_id']}\n\n"
            f"## Prior Council Head output\n\n{_json.dumps(prior['head'], indent=2)}\n\n"
            f"## Prior synthesis\n\n{_json.dumps(prior['synthesis'], indent=2)}\n\n"
            "Populate `delta_vs_prior` in your output. If no meaningful change applies "
            "to a sub-array, return an empty list rather than fabricating items."
        )
    return base


def _find_prior_run(current_dir: Path) -> dict | None:
    """Most-recent completed run before current_dir. Returns {run_id, head, synthesis} or None."""
    reports = current_dir.parent
    candidates = sorted(
        [d for d in reports.iterdir() if d.is_dir() and d.name != current_dir.name],
        key=lambda d: d.name, reverse=True,
    )
    for d in candidates:
        head_p = d / "head.json"
        syn_p = d / "synthesis.json"
        if head_p.exists() and syn_p.exists():
            try:
                return {
                    "run_id": d.name,
                    "head": _json.loads(head_p.read_text()),
                    "synthesis": _json.loads(syn_p.read_text()),
                }
            except Exception:
                continue
    return None


def _remap_horizon_list(lst: list) -> dict:
    """[{horizon:'24h', predictions:[...]}, ...] -> {'24h': [...]}"""
    out = {}
    for entry in lst:
        if not isinstance(entry, dict):
            continue
        h = entry.get("horizon") or entry.get("label") or entry.get("name")
        preds = entry.get("predictions") or entry.get("items") or entry.get("forecasts") or []
        if h:
            out[h] = preds
    return out


def _normalise_member(out: dict, horizons: list[str]) -> dict:
    """Accept common alternate shapes and remap to {forecasts: {<h>: [...]}}."""
    # Already correct.
    if (isinstance(out.get("forecasts"), dict)
            and any(isinstance(v, list) and v for v in out["forecasts"].values())):
        return out

    # Flat-dict aliases.
    for alt in ("horizons", "predictions", "by_horizon"):
        if isinstance(out.get(alt), dict):
            out["forecasts"] = out[alt]
            return out

    # Single-horizon flat-list (predictions: [...] with only one horizon requested).
    if len(horizons) == 1:
        for alt in ("predictions", "forecasts", "items"):
            v = out.get(alt)
            if isinstance(v, list) and v and isinstance(v[0], dict) and "prediction" in v[0]:
                out["forecasts"] = {horizons[0]: v}
                return out

    # List of {horizon, predictions} at top level.
    for key in ("forecasts", "horizons", "predictions"):
        if isinstance(out.get(key), list):
            remapped = _remap_horizon_list(out[key])
            if remapped:
                out["forecasts"] = remapped
                return out

    # Nested under a singular wrapper like {"forecast": {"horizons": [...]}} or
    # {"forecast": {"24h": [...]}}.
    for wrapper in ("forecast", "output", "result", "data"):
        inner = out.get(wrapper)
        if not isinstance(inner, dict):
            continue
        for inner_key in ("horizons", "predictions", "forecasts", "by_horizon"):
            v = inner.get(inner_key)
            if isinstance(v, list):
                remapped = _remap_horizon_list(v)
                if remapped:
                    out["forecasts"] = remapped
                    # Lift overall fields if present.
                    for k in ("overall_confidence", "overall_notes"):
                        if k in inner and k not in out:
                            out[k] = inner[k]
                    return out
            if isinstance(v, dict) and any(h in v for h in horizons):
                out["forecasts"] = v
                return out
        # Inner dict keyed directly by horizon.
        if any(h in inner for h in horizons):
            out["forecasts"] = {h: inner[h] for h in horizons if h in inner}
            return out

    return out


def _member_call(member: Role, scenario: str, horizons: list[str], head_out: dict,
                 schema: dict, checkpoint_path: Path) -> dict:
    if checkpoint_path.exists():
        try:
            cached = _json.loads(checkpoint_path.read_text())
            # Re-normalise on load — normalisation rules may have improved since it was saved.
            if "_error" not in cached:
                cached = _normalise_member(cached, horizons)
                cached.setdefault("_member", member.name)
                cached.setdefault("_model", member.model)
                cached.setdefault("_lineage", member.lineage)
            print(f"  - {member.name}: loaded from checkpoint")
            return cached
        except Exception:
            print(f"  - {member.name}: checkpoint unreadable, re-running")

    try:
        out = call_json(
            member.model, MEMBER_PROMPT,
            _member_user_msg(scenario, horizons, head_out),
            temperature=0.5, response_schema=schema,
        )
        out = _normalise_member(out, horizons)
        out["_member"] = member.name
        out["_model"] = member.model
        out["_lineage"] = member.lineage
    except Exception as e:
        out = {"_member": member.name, "_model": member.model, "_lineage": member.lineage,
               "_error": str(e)}

    checkpoint_path.write_text(_json.dumps(out, indent=2))
    return out


def _safe_grounding_for_json(grounding: list[dict]) -> list[dict]:
    out = []
    for g in grounding:
        items = []
        for it in g.get("items", []) or []:
            item = {k: v for k, v in it.items() if k != "published"}
            if it.get("published"):
                item["published_iso"] = (
                    it["published"].isoformat() if hasattr(it["published"], "isoformat") else str(it["published"])
                )
            items.append(item)
        out.append({**{k: v for k, v in g.items() if k != "items"}, "items": items})
    return out


def _rehydrate_grounding(serialised: list[dict]) -> list[dict]:
    from datetime import datetime as _dt
    out = []
    for g in serialised:
        items = []
        for it in g.get("items", []) or []:
            item = dict(it)
            if item.get("published_iso"):
                try:
                    item["published"] = _dt.fromisoformat(item.pop("published_iso"))
                except Exception:
                    item.pop("published_iso", None)
            items.append(item)
        out.append({**{k: v for k, v in g.items() if k != "items"}, "items": items})
    return out


def resolve_run_dir(resume: str | None, resume_latest: bool) -> tuple[Path, bool]:
    """Return (run_dir, is_resume). Creates a fresh dir if not resuming."""
    if resume:
        p = Path(resume)
        if not p.is_absolute():
            p = ROOT / "reports" / resume
        if not p.exists():
            raise FileNotFoundError(f"resume dir not found: {p}")
        return p, True
    if resume_latest:
        reports = ROOT / "reports"
        candidates = sorted(
            [d for d in reports.iterdir() if d.is_dir() and d.name != ".gitkeep"],
            key=lambda d: d.name, reverse=True,
        )
        if not candidates:
            raise FileNotFoundError("no existing runs to resume")
        return candidates[0], True
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = ROOT / "reports" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir, False


def run_forecast(
    scenario: str,
    horizons: list[str],
    rss_feeds: list[str],
    grounding_tools: list[str],
    council_head: Role,
    council_members: list[Role],
    report_author: Role,
    run_dir: Path,
    is_resume: bool = False,
) -> Path:
    members_dir = run_dir / "members"
    members_dir.mkdir(exist_ok=True)
    meta_path = run_dir / "meta.json"
    grounding_path = run_dir / "grounding.json"
    head_path = run_dir / "head.json"
    synthesis_path = run_dir / "synthesis.json"

    if not meta_path.exists():
        meta_path.write_text(_json.dumps({
            "scenario": scenario,
            "horizons": horizons,
            "rss_feeds": rss_feeds,
            "grounding_tools": grounding_tools,
            "council_head": {"name": council_head.name, "model": council_head.model},
            "council_members": [{"name": m.name, "model": m.model, "lineage": m.lineage}
                                for m in council_members],
            "report_author": {"name": report_author.name, "model": report_author.model},
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }, indent=2))
    elif is_resume:
        meta = _json.loads(meta_path.read_text())
        print(f"[resume] {run_dir.name} — scenario: {meta.get('scenario','')[:80]}")
        scenario = meta.get("scenario", scenario)
        horizons = meta.get("horizons", horizons)

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # ---- Stage: grounding
    if grounding_path.exists():
        print(f"[grounding] cached at {grounding_path.name}")
        grounding = _rehydrate_grounding(_json.loads(grounding_path.read_text()))
    else:
        print(f"[grounding] running tools: {grounding_tools}")
        grounding = run_grounding(scenario, grounding_tools, rss_feeds=rss_feeds)
        for g in grounding:
            status = "ok" if g["ok"] else f"FAILED: {g.get('error','')}"
            n_items = len(g.get("items", [])) if g.get("items") else 0
            print(f"  - {g['tool']}: {status} ({n_items} items)")
        grounding_path.write_text(_json.dumps(_safe_grounding_for_json(grounding), indent=2, default=str))
    grounding_block = format_grounding_block(grounding)

    # ---- Stage: head
    if head_path.exists():
        print(f"[head] cached at {head_path.name}")
        head_out = _json.loads(head_path.read_text())
    else:
        h_schema = head_schema(horizons)
        print(f"[head] {council_head.model} producing SITREP…")
        head_out = call_json(
            council_head.model, HEAD_PROMPT,
            _head_user_msg(scenario, horizons, grounding_block, now_iso),
            temperature=0.2, response_schema=h_schema,
        )
        head_out.setdefault("as_of", now_iso)
        head_path.write_text(_json.dumps(head_out, indent=2))

    # ---- Stage: members (checkpointed per-member)
    m_schema = member_schema(horizons)
    print(f"[members] polling {len(council_members)} members "
          f"(resume-aware, checkpoints in {members_dir.name}/)…")
    def _call(m: Role) -> dict:
        ckpt = members_dir / f"{m.name}.json"
        return _member_call(m, scenario, horizons, head_out, m_schema, ckpt)

    with ThreadPoolExecutor(max_workers=len(council_members)) as ex:
        members_out = list(ex.map(_call, council_members))

    for m in members_out:
        if "_error" in m:
            print(f"  ! {m['_member']} ({m['_model']}): {m['_error'][:200]}")
        else:
            oc = m.get("overall_confidence", "?")
            counts = {h: len((m.get("forecasts") or {}).get(h, [])) for h in horizons}
            print(f"  - {m['_member']}: confidence={oc} predictions={counts}")

    successful = [m for m in members_out if "_error" not in m and m.get("forecasts")]
    if not successful:
        raise RuntimeError("no usable member forecasts; aborting synthesis")

    # ---- Stage: synthesis
    if synthesis_path.exists():
        print(f"[author] cached at {synthesis_path.name}")
        synthesis = _json.loads(synthesis_path.read_text())
    else:
        a_schema = author_schema(horizons)
        prior = _find_prior_run(run_dir)
        if prior:
            print(f"[author] prior run for delta: {prior['run_id']}")
        else:
            print("[author] no prior run; delta analysis skipped")
        print(f"[author] {report_author.model} writing synthesis…")
        synthesis = call_json(
            report_author.model, AUTHOR_PROMPT,
            _author_user_msg(scenario, horizons, head_out, members_out, prior=prior),
            temperature=0.2, response_schema=a_schema,
        )
        synthesis_path.write_text(_json.dumps(synthesis, indent=2))

    # ---- Stage: report render (always re-render from checkpoints)
    path = write_report(run_dir, scenario, horizons, head_out, members_out, synthesis, grounding)
    print(f"[done] {path}")
    return path
