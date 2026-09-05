"""OSINT-signals variant of the forecast council.

Pipeline:
  1. grounding (reuse)
  2. head SITREP (reuse prompt / schema)
  3. members return 5 OSINT signals per horizon (new prompt / schema)
  4. Claude-authored synthesis + Typst report with matplotlib viz (no LLM author stage)
"""
import json as _json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv()

from .config import (
    DEFAULT_COUNCIL_HEAD,
    DEFAULT_COUNCIL_MEMBERS,
    DEFAULT_RSS_FEEDS,
    Role,
)
from .grounding import format_grounding_block, run_grounding
from .openrouter import call_json
from .osint_report import write_osint_report
from .osint_schemas import osint_member_schema
from .run import (
    _head_user_msg,
    _rehydrate_grounding,
    _safe_grounding_for_json,
    resolve_run_dir,
)
from .schemas import head_schema

ROOT = Path(__file__).resolve().parent.parent
HEAD_PROMPT = (ROOT / "prompts/council_head.md").read_text()
MEMBER_PROMPT = (ROOT / "prompts/council_member_osint.md").read_text()

DEFAULT_OSINT_HORIZONS: list[str] = ["24h", "1w"]
DEFAULT_GROUNDING_TOOLS = ["rss", "sonar", "tavily"]


def _member_user_msg(scenario: str, horizons: list[str], head_out: dict) -> str:
    return (
        f"# Scenario\n\n{scenario}\n\n"
        f"# Horizons\n\n{', '.join(horizons)}\n\n"
        f"# SITREP (as of {head_out.get('as_of','?')})\n\n{head_out.get('sitrep','')}\n\n"
        f"# Key actors\n\n{_json.dumps(head_out.get('key_actors', []), indent=2)}\n\n"
        f"# Load-bearing uncertainties\n\n"
        + "\n".join(f"- {u}" for u in head_out.get("load_bearing_uncertainties", []))
    )


def _normalise_member(out: dict, horizons: list[str]) -> dict:
    """Accept minor shape drift. Target: {signals: {<h>: [...]}}"""
    if isinstance(out.get("signals"), dict) and any(
        isinstance(v, list) and v for v in out["signals"].values()
    ):
        return out
    for alt in ("osint_signals", "by_horizon", "horizons"):
        if isinstance(out.get(alt), dict):
            out["signals"] = out.pop(alt)
            return out
    # list of {horizon, signals}
    for alt in ("signals", "osint_signals", "horizons"):
        v = out.get(alt)
        if isinstance(v, list):
            remapped = {}
            for entry in v:
                if not isinstance(entry, dict):
                    continue
                h = entry.get("horizon") or entry.get("label")
                items = entry.get("signals") or entry.get("items") or []
                if h:
                    remapped[h] = items
            if remapped:
                out["signals"] = remapped
                return out
    return out


def _member_call(member: Role, scenario: str, horizons: list[str], head_out: dict,
                 schema: dict, ckpt: Path) -> dict:
    if ckpt.exists():
        try:
            cached = _json.loads(ckpt.read_text())
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
            temperature=0.6, response_schema=schema,
        )
        out = _normalise_member(out, horizons)
        out["_member"] = member.name
        out["_model"] = member.model
        out["_lineage"] = member.lineage
    except Exception as e:
        out = {"_member": member.name, "_model": member.model, "_lineage": member.lineage,
               "_error": str(e)}

    ckpt.write_text(_json.dumps(out, indent=2))
    return out


def run_osint_council(scenario: str, horizons: list[str], rss_feeds: list[str],
                      grounding_tools: list[str], council_head: Role,
                      council_members: list[Role], run_dir: Path,
                      is_resume: bool = False) -> Path:
    members_dir = run_dir / "members"
    members_dir.mkdir(exist_ok=True)
    meta_path = run_dir / "meta.json"
    grounding_path = run_dir / "grounding.json"
    head_path = run_dir / "head.json"

    if not meta_path.exists():
        meta_path.write_text(_json.dumps({
            "variant": "osint-signals",
            "scenario": scenario,
            "horizons": horizons,
            "rss_feeds": rss_feeds,
            "grounding_tools": grounding_tools,
            "council_head": {"name": council_head.name, "model": council_head.model},
            "council_members": [{"name": m.name, "model": m.model, "lineage": m.lineage}
                                for m in council_members],
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }, indent=2))
    elif is_resume:
        meta = _json.loads(meta_path.read_text())
        print(f"[resume] {run_dir.name} — scenario: {meta.get('scenario','')[:80]}")
        scenario = meta.get("scenario", scenario)
        horizons = meta.get("horizons", horizons)

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # grounding
    if grounding_path.exists():
        print(f"[grounding] cached at {grounding_path.name}")
        grounding = _rehydrate_grounding(_json.loads(grounding_path.read_text()))
    else:
        print(f"[grounding] running tools: {grounding_tools}")
        grounding = run_grounding(scenario, grounding_tools, rss_feeds=rss_feeds)
        for g in grounding:
            status = "ok" if g["ok"] else f"FAILED: {g.get('error','')}"
            n = len(g.get("items", [])) if g.get("items") else 0
            print(f"  - {g['tool']}: {status} ({n} items)")
        grounding_path.write_text(_json.dumps(_safe_grounding_for_json(grounding), indent=2, default=str))
    grounding_block = format_grounding_block(grounding)

    # head
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

    # members
    m_schema = osint_member_schema(horizons)
    print(f"[members] polling {len(council_members)} members for OSINT signals…")

    def _call(m: Role) -> dict:
        return _member_call(m, scenario, horizons, head_out, m_schema,
                            members_dir / f"{m.name}.json")

    with ThreadPoolExecutor(max_workers=len(council_members)) as ex:
        members_out = list(ex.map(_call, council_members))

    for m in members_out:
        if "_error" in m:
            print(f"  ! {m['_member']}: {m['_error'][:200]}")
        else:
            counts = {h: len((m.get("signals") or {}).get(h, [])) for h in horizons}
            print(f"  - {m['_member']}: signals={counts}")

    usable = [m for m in members_out if "_error" not in m and m.get("signals")]
    if not usable:
        raise RuntimeError("no usable member signal sets; aborting")

    print("[report] claude-authored synthesis + viz…")
    path = write_osint_report(run_dir, scenario, horizons, head_out, members_out, grounding)
    print(f"[done] {path}")
    return path


@click.command()
@click.argument("scenario", nargs=-1, required=False)
@click.option("--horizons", default=",".join(DEFAULT_OSINT_HORIZONS),
              help="Comma-separated horizons, e.g. '24h,1w'.")
@click.option("--rss", "rss_feeds", default=",".join(DEFAULT_RSS_FEEDS))
@click.option("--grounding-tools", default=",".join(DEFAULT_GROUNDING_TOOLS))
@click.option("--council-head", default=DEFAULT_COUNCIL_HEAD.model)
@click.option("--council-members",
              default=",".join(m.model for m in DEFAULT_COUNCIL_MEMBERS))
@click.option("--resume", default=None)
@click.option("--resume-latest", is_flag=True, default=False)
def main(scenario, horizons, rss_feeds, grounding_tools, council_head, council_members,
         resume, resume_latest):
    """OSINT-signals variant: each council member names 5 signals per horizon."""
    run_dir, is_resume = resolve_run_dir(resume, resume_latest)
    s = " ".join(scenario).strip() if scenario else ""
    if not is_resume and not s:
        click.echo("empty scenario (required unless --resume/--resume-latest)", err=True)
        sys.exit(1)
    if is_resume:
        click.echo(f"[resume] using {run_dir}")

    h_list = [h.strip() for h in horizons.split(",") if h.strip()]
    feeds = [f.strip() for f in rss_feeds.split(",") if f.strip()]
    tools = [t.strip() for t in grounding_tools.split(",") if t.strip()]
    if "tavily" in tools and not os.environ.get("TAVILY_API_KEY"):
        click.echo("[warn] tavily requested but TAVILY_API_KEY not set — skipping.", err=True)
        tools = [t for t in tools if t != "tavily"]

    default_by_model = {m.model: m for m in DEFAULT_COUNCIL_MEMBERS}
    members: list[Role] = []
    for i, model in enumerate(council_members.split(",")):
        model = model.strip()
        if not model:
            continue
        if model in default_by_model:
            d = default_by_model[model]
            members.append(Role(d.name, d.model, d.lineage))
        else:
            members.append(Role(f"Council_Member_{i+1}", model, ""))

    head = Role("Council_Head", council_head, "")

    run_osint_council(
        scenario=s, horizons=h_list, rss_feeds=feeds, grounding_tools=tools,
        council_head=head, council_members=members,
        run_dir=run_dir, is_resume=is_resume,
    )


if __name__ == "__main__":
    main()
