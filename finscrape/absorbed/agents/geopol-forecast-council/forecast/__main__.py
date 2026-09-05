import os
import sys

import click
from dotenv import load_dotenv

load_dotenv()

from .config import (
    DEFAULT_COUNCIL_HEAD,
    DEFAULT_COUNCIL_MEMBERS,
    DEFAULT_HORIZONS,
    DEFAULT_REPORT_AUTHOR,
    DEFAULT_RSS_FEEDS,
    Role,
)
from .run import resolve_run_dir, run_forecast

DEFAULT_GROUNDING_TOOLS = ["rss", "sonar", "tavily"]


@click.command()
@click.argument("scenario", nargs=-1, required=False)
@click.option("--horizons", default=",".join(DEFAULT_HORIZONS),
              help="Comma-separated forecast horizons, e.g. '24h,1w,1m'.")
@click.option("--rss", "rss_feeds", default=",".join(DEFAULT_RSS_FEEDS),
              help="Comma-separated RSS feed URLs.")
@click.option("--grounding-tools", default=",".join(DEFAULT_GROUNDING_TOOLS),
              help="Comma-separated grounding tool names: rss,sonar,tavily.")
@click.option("--council-head", default=DEFAULT_COUNCIL_HEAD.model,
              help="Model ID for Council_Head (SITREP synthesis).")
@click.option("--council-members",
              default=",".join(m.model for m in DEFAULT_COUNCIL_MEMBERS),
              help="Comma-separated model IDs for Council_Member panel.")
@click.option("--report-author", default=DEFAULT_REPORT_AUTHOR.model,
              help="Model ID for Report_Author (final synthesis).")
@click.option("--resume", default=None,
              help="Resume a specific run by timestamp dir name or absolute path.")
@click.option("--resume-latest", is_flag=True, default=False,
              help="Resume the most recent run in reports/.")
def main(scenario, horizons, rss_feeds, grounding_tools, council_head, council_members,
         report_author, resume, resume_latest):
    """Run a geopolitical forecast council over SCENARIO. Use --resume[-latest] to pick up
    an interrupted run from its stage checkpoints."""
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
        click.echo("[warn] tavily requested but TAVILY_API_KEY not set — skipping tavily.", err=True)
        tools = [t for t in tools if t != "tavily"]

    # Build member Roles. Try to match lineages from defaults where we can.
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
    author = Role("Report_Author", report_author, "")

    run_forecast(
        scenario=s,
        horizons=h_list,
        rss_feeds=feeds,
        grounding_tools=tools,
        council_head=head,
        council_members=members,
        report_author=author,
        run_dir=run_dir,
        is_resume=is_resume,
    )


if __name__ == "__main__":
    main()
