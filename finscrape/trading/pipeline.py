"""
Pipeline orchestrator — runs the full multi-agent trading analysis.

Flow:
  1. Analysts run in parallel (market, sentiment, news, fundamentals)
  2. Bull/Bear debate (configurable rounds)
  3. Research Manager synthesizes
  4. Trader creates proposal
  5. Risk team debates (configurable rounds)
  6. Risk Manager synthesizes
  7. Portfolio Manager decides

Usage:
    from finscrape.trading.pipeline import run_analysis
    result = run_analysis("NVDA", "2025-01-15")
    print(result["signal"], result["decision"])
"""
from __future__ import annotations

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any

from finscrape.trading.agents import (
    market_analyst,
    sentiment_analyst,
    news_analyst,
    fundamentals_analyst,
    bull_researcher,
    bear_researcher,
    research_manager,
    trader,
    aggressive_analyst,
    conservative_analyst,
    neutral_analyst,
    risk_manager,
    portfolio_manager,
)
from finscrape.trading.memory import DecisionMemory
from finscrape.trading.state import TradeState

logger = logging.getLogger(__name__)
_memory = DecisionMemory()

DEFAULT_DEBATE_ROUNDS = 1
DEFAULT_RISK_ROUNDS = 1
DEFAULT_MAX_WORKERS = 4


def run_analysis(
    ticker: str,
    trade_date: str | None = None,
    *,
    debate_rounds: int = DEFAULT_DEBATE_ROUNDS,
    risk_rounds: int = DEFAULT_RISK_ROUNDS,
    selected_analysts: tuple[str, ...] = ("market", "sentiment", "news", "fundamentals"),
    save_reports: bool = True,
    results_dir: str | None = None,
) -> dict[str, Any]:
    """
    Run the full multi-agent trading analysis pipeline.

    Returns dict with keys: ticker, trade_date, signal, decision,
    reports, debate, risk_debate, errors, duration_seconds.
    """
    start = time.time()
    if trade_date is None:
        from datetime import datetime
        trade_date = datetime.now().strftime("%Y-%m-%d")

    state = TradeState(ticker=ticker, trade_date=trade_date)
    logger.info("Starting analysis for %s on %s", ticker, trade_date)

    # Resolve any past decisions for this ticker
    _memory.resolve_entries(ticker)

    # --- Phase 1: Analysts (parallel) ---
    analyst_fns = {
        "market": market_analyst,
        "sentiment": sentiment_analyst,
        "news": news_analyst,
        "fundamentals": fundamentals_analyst,
    }
    active_analysts = [analyst_fns[name] for name in selected_analysts if name in analyst_fns]

    with ThreadPoolExecutor(max_workers=min(len(active_analysts), DEFAULT_MAX_WORKERS)) as pool:
        futures = {pool.submit(fn, state): fn.__name__ for fn in active_analysts}
        for future in as_completed(futures):
            name = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error("Analyst %s failed: %s", name, e)
                state.add_error(name, str(e))

    # --- Phase 2: Bull/Bear debate ---
    for round_num in range(1, debate_rounds + 1):
        logger.info("Debate round %d/%d", round_num, debate_rounds)
        bull_researcher(state)
        bear_researcher(state)

    # --- Phase 3: Research Manager ---
    research_manager(state)

    # --- Phase 4: Trader ---
    trader(state)

    # --- Phase 5: Risk debate ---
    for round_num in range(1, risk_rounds + 1):
        logger.info("Risk round %d/%d", round_num, risk_rounds)
        aggressive_analyst(state)
        conservative_analyst(state)
        neutral_analyst(state)

    # --- Phase 6: Risk Manager ---
    risk_manager(state)

    # --- Phase 7: Portfolio Manager ---
    portfolio_manager(state)

    duration = time.time() - start
    logger.info("Analysis complete for %s — signal: %s (%.1fs)", ticker, state.signal, duration)

    # Store decision for future reflection
    _memory.store_decision(
        ticker=ticker,
        trade_date=trade_date,
        signal=state.signal,
        decision=state.final_decision,
    )

    # --- Save reports ---
    if save_reports:
        _save_reports(state, results_dir)

    return {
        "ticker": state.ticker,
        "trade_date": state.trade_date,
        "signal": state.signal,
        "decision": state.final_decision,
        "reports": {
            "market": state.market_report,
            "sentiment": state.sentiment_report,
            "news": state.news_report,
            "fundamentals": state.fundamentals_report,
        },
        "investment_plan": state.investment_plan,
        "trader_proposal": state.trader_proposal,
        "debate": state.investment_debate_history,
        "risk_assessment": state.risk_assessment,
        "risk_debate": state.risk_debate_history,
        "errors": state.errors,
        "duration_seconds": round(duration, 1),
    }


def _save_reports(state: TradeState, results_dir: str | None = None) -> None:
    """Save pipeline output to disk."""
    base = Path(results_dir or os.getenv("FINSCRAPE_RESULTS_DIR", "results"))
    ticker_dir = base / state.ticker / "trading_agents"
    ticker_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "ticker": state.ticker,
        "trade_date": state.trade_date,
        "signal": state.signal,
        "final_decision": state.final_decision,
        "market_report": state.market_report,
        "sentiment_report": state.sentiment_report,
        "news_report": state.news_report,
        "fundamentals_report": state.fundamentals_report,
        "investment_plan": state.investment_plan,
        "trader_proposal": state.trader_proposal,
        "investment_debate": state.investment_debate_history,
        "risk_assessment": state.risk_assessment,
        "risk_debate": state.risk_debate_history,
        "errors": state.errors,
    }

    path = ticker_dir / f"analysis_{state.trade_date}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info("Reports saved to %s", path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point: python -m finscrape.trading.pipeline NVDA"""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m finscrape.trading.pipeline <TICKER> [DATE]")
        sys.exit(1)
    ticker = sys.argv[1]
    date = sys.argv[2] if len(sys.argv) > 2 else None
    result = run_analysis(ticker, date)
    print(f"\n{'='*60}")
    print(f"  {result['ticker']} — {result['trade_date']}")
    print(f"  Signal: {result['signal']}")
    print(f"  Duration: {result['duration_seconds']}s")
    if result["errors"]:
        print(f"  Errors: {len(result['errors'])}")
    print(f"{'='*60}")
    print(f"\nDecision:\n{result['decision'][:500]}")


if __name__ == "__main__":
    main()
