"""CLI: ingest runs, evaluate due predictions, generate reports.

Usage:
    python -m forecast.accuracy ingest
    python -m forecast.accuracy evaluate [--limit N] [--model MODEL]
    python -m forecast.accuracy report [--run RUN_ID]
    python -m forecast.accuracy status
    python -m forecast.accuracy run            # ingest + evaluate + report
"""
from __future__ import annotations

import click
from dotenv import load_dotenv

load_dotenv()

from .db import connect, ingest_all, due_predictions
from .evaluate import DEFAULT_EVALUATOR, evaluate_due
from .report import generate_leaderboard, generate_per_run_report


@click.group()
def cli():
    """Forecast accuracy evaluation."""


@cli.command()
def ingest():
    """Walk reports/ and register any new runs + predictions in the DB."""
    conn = connect()
    r, p = ingest_all(conn)
    click.echo(f"[ingest] new runs: {r}, new predictions: {p}")


@cli.command()
@click.option("--limit", type=int, default=None, help="Max predictions to evaluate this pass.")
@click.option("--model", default=DEFAULT_EVALUATOR, help="Evaluator model (OpenRouter slug).")
@click.option("--tools", default="sonar,tavily",
              help="Comma-separated grounding tools (rss,sonar,tavily).")
def evaluate(limit, model, tools):
    """Evaluate predictions whose horizon has elapsed and which lack a verdict."""
    conn = connect()
    # Ingest first so newly-dropped runs are picked up.
    ingest_all(conn)
    rows = due_predictions(conn)
    if limit:
        rows = rows[:limit]
    if not rows:
        click.echo("[evaluate] nothing due")
        return
    click.echo(f"[evaluate] {len(rows)} predictions due; evaluator={model}")
    stats = evaluate_due(conn, rows, evaluator_model=model,
                        grounding_tools=[t.strip() for t in tools.split(",") if t.strip()])
    click.echo(f"[evaluate] done: {stats}")


@cli.command()
@click.option("--run", "run_id", default=None,
              help="If set, also generate a per-run report for this run_id.")
def report(run_id):
    """(Re)generate the cross-run leaderboard and optionally a per-run report."""
    conn = connect()
    path = generate_leaderboard(conn)
    click.echo(f"[report] leaderboard → {path}")
    if run_id:
        p = generate_per_run_report(conn, run_id)
        click.echo(f"[report] per-run → {p}" if p else f"[report] no evals for {run_id}")


@cli.command()
def status():
    """Show DB counts and due-predictions preview."""
    conn = connect()
    n_runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    n_preds = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    n_evals = conn.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]
    due = due_predictions(conn)
    click.echo(f"runs={n_runs}  predictions={n_preds}  evaluations={n_evals}  due={len(due)}")
    for r in due[:10]:
        click.echo(f"  due: {r['run_id']} · {r['member']} · {r['horizon']} "
                   f"(target {r['horizon_target_utc']})")


@cli.command(name="run")
@click.option("--model", default=DEFAULT_EVALUATOR)
@click.option("--limit", type=int, default=None)
@click.pass_context
def run_all(ctx, model, limit):
    """Full pass: ingest → evaluate due → regenerate leaderboard."""
    ctx.invoke(ingest)
    ctx.invoke(evaluate, model=model, limit=limit, tools="sonar,tavily")
    ctx.invoke(report, run_id=None)


if __name__ == "__main__":
    cli()
