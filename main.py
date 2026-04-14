"""
FinScrape — AI-powered financial news intelligence engine.

Usage:
    python main.py                    # Run with default sources (Yahoo Finance)
    python main.py --sources yahoo bloomberg reuters cnbc rss
    python main.py --sources yahoo rss --max-articles 20
    python main.py portfolio add AAPL 100 150.0
    python main.py portfolio watchlist tech AAPL MSFT GOOGL
"""

import sys
import os
import logging
import argparse

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finscrape.pipeline import FinScrapePipeline
from finscrape.monitor import Monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "app.log")),
    ],
)


def handle_portfolio(args):
    """Handle portfolio subcommands."""
    from finscrape.portfolio import PortfolioManager
    pm = PortfolioManager()

    if args.portfolio_cmd == "add":
        pm.add_position(args.ticker, shares=args.shares, avg_cost=args.cost,
                        current_price=args.cost)
        print(f"Added position: {args.ticker.upper()} — {args.shares} shares @ ${args.cost:.2f}")

    elif args.portfolio_cmd == "remove":
        if pm.remove_position(args.ticker):
            print(f"Removed position: {args.ticker.upper()}")
        else:
            print(f"Position {args.ticker.upper()} not found.")

    elif args.portfolio_cmd == "list":
        positions = pm.get_all_positions()
        if not positions:
            print("No positions in portfolio.")
            return
        print(f"\n{'Ticker':<8} {'Shares':>10} {'Avg Cost':>10} {'Price':>10} {'Value':>12} {'P&L':>10} {'P&L%':>8}")
        print("-" * 70)
        for p in positions:
            print(f"{p.ticker:<8} {p.shares:>10.1f} {p.avg_cost:>10.2f} "
                  f"{p.current_price:>10.2f} {p.market_value:>12.2f} "
                  f"{p.unrealized_pnl:>+10.2f} {p.unrealized_pnl_pct:>+7.1f}%")
        print(f"\nTotal value: ${pm.total_value():,.2f}  |  Total P&L: ${pm.total_pnl():+,.2f}")

    elif args.portfolio_cmd == "watchlist":
        if args.watchlist_action == "create":
            pm.create_watchlist(args.name, args.tickers or [], args.description or "")
            print(f"Watchlist '{args.name}' created with {len(args.tickers or [])} tickers.")
        elif args.watchlist_action == "add":
            pm.add_to_watchlist(args.name, args.tickers)
            print(f"Added {', '.join(args.tickers)} to '{args.name}'.")
        elif args.watchlist_action == "remove":
            pm.remove_from_watchlist(args.name, args.tickers)
            print(f"Removed {', '.join(args.tickers)} from '{args.name}'.")
        elif args.watchlist_action == "delete":
            pm.delete_watchlist(args.name)
            print(f"Deleted watchlist '{args.name}'.")
        elif args.watchlist_action == "list":
            watchlists = pm.get_all_watchlists()
            if not watchlists:
                print("No watchlists.")
                return
            for wl in watchlists:
                print(f"  {wl.name}: {', '.join(wl.tickers)} — {wl.description}")

    elif args.portfolio_cmd == "summary":
        s = pm.summary()
        print(f"\nPortfolio: {s['positions']} positions | ${s['total_value']:,.2f} value | ${s['total_pnl']:+,.2f} P&L")
        print(f"Tickers: {', '.join(s['tickers'])}")
        print(f"Watched: {', '.join(s['watched_tickers'])}")
        print(f"Watchlists: {len(s['watchlists'])}")

    elif args.portfolio_cmd == "alerts":
        alerts = pm.get_recent_alerts(limit=args.limit)
        if not alerts:
            print("No recent alerts.")
            return
        for a in alerts:
            print(f"  [{a['triggered_at']}] {a['alert_type']} — {a['message']}")

    pm.close()


def handle_accuracy(args):
    """Handle accuracy subcommands."""
    from finscrape.accuracy import AccuracyTracker
    tracker = AccuracyTracker()

    if args.accuracy_cmd == "check":
        hours = args.hours if hasattr(args, "hours") and args.hours else 24
        results = tracker.check_outcomes(hours_after=hours)
        if not results:
            print(f"No pending signals older than {hours}h to check.")
        else:
            correct = sum(1 for r in results if r["outcome"] == "correct")
            incorrect = sum(1 for r in results if r["outcome"] == "incorrect")
            neutral = sum(1 for r in results if r["outcome"] == "neutral")
            print(f"\nChecked {len(results)} signals ({hours}h lookback):")
            print(f"  Correct:   {correct}")
            print(f"  Incorrect: {incorrect}")
            print(f"  Neutral:   {neutral}")
            for r in results:
                symbol = {"correct": "+", "incorrect": "-", "neutral": "~"}.get(r["outcome"], "?")
                print(f"  [{symbol}] {r['ticker']} {r['verdict']} "
                      f"-> {r['price_change_pct']:+.2f}% ({r['outcome']})")
        tracker.update_accuracy_stats()

    elif args.accuracy_cmd == "report":
        tracker.update_accuracy_stats()
        report = tracker.get_accuracy_report()
        print(f"\n=== Signal Accuracy Report ===")
        print(f"Overall accuracy: {report['overall_accuracy']:.1f}% "
              f"({report['correct']}/{report['total_scored']} scored signals)")
        if report["per_verdict"]:
            print("\nPer-verdict:")
            for v, stats in report["per_verdict"].items():
                print(f"  {v}: {stats['accuracy_pct']:.1f}% ({stats['correct']}/{stats['total']})")
        if report["best_sources"]:
            print("\nBest sources:")
            for s in report["best_sources"][:3]:
                print(f"  {s['source']}: {s['accuracy_pct']:.1f}% ({s['total']} signals)")
        if report["avg_confidence_when_correct"] is not None:
            print(f"\nAvg confidence when correct:   {report['avg_confidence_when_correct']:.3f}")
        if report["avg_confidence_when_incorrect"] is not None:
            print(f"Avg confidence when incorrect: {report['avg_confidence_when_incorrect']:.3f}")

    elif args.accuracy_cmd == "ticker":
        if not hasattr(args, "ticker_symbol") or not args.ticker_symbol:
            print("Please provide a ticker symbol.")
            tracker.close()
            return
        result = tracker.get_ticker_accuracy(args.ticker_symbol)
        print(f"\n=== Accuracy for {result['ticker']} ===")
        print(f"Total signals: {result['total_signals']} (scored: {result['scored']})")
        print(f"Accuracy: {result['accuracy_pct']:.1f}% "
              f"({result['correct']} correct, {result['incorrect']} incorrect, {result['neutral']} neutral)")
        if result["avg_price_move"] is not None:
            print(f"Avg price move: {result['avg_price_move']:+.2f}%")
        if result["per_verdict"]:
            print("Per-verdict:")
            for v, stats in result["per_verdict"].items():
                print(f"  {v}: {stats['accuracy_pct']:.1f}% ({stats['correct']}/{stats['total']})")

    elif args.accuracy_cmd == "source":
        if not hasattr(args, "source_name") or not args.source_name:
            print("Please provide a source name.")
            tracker.close()
            return
        result = tracker.get_source_accuracy(args.source_name)
        print(f"\n=== Accuracy for source '{result['source']}' ===")
        print(f"Total signals: {result['total_signals']} (scored: {result['scored']})")
        print(f"Accuracy: {result['accuracy_pct']:.1f}%")

    else:
        print("Unknown accuracy subcommand. Use: check, report, ticker, source")

    tracker.close()


def main():
    parser = argparse.ArgumentParser(description="FinScrape — Financial News Intelligence Engine")
    subparsers = parser.add_subparsers(dest="command")

    # --- Scrape command (default) ---
    scrape_parser = subparsers.add_parser("scrape", help="Run a single scrape pass")
    scrape_parser.add_argument(
        "--sources", nargs="+", default=["yahoo"],
        choices=["yahoo", "bloomberg", "reuters", "cnbc", "rss",
                 "marketwatch", "seekingalpha", "benzinga", "investingcom", "ft", "edgar"],
    )
    scrape_parser.add_argument("--max-articles", type=int, default=10)
    scrape_parser.add_argument("--council", action="store_true",
                               help="Use multi-agent AI council for analysis")

    # --- Monitor command ---
    monitor_parser = subparsers.add_parser("monitor", help="Run continuous monitoring")
    monitor_parser.add_argument(
        "--sources", nargs="+", default=["yahoo"],
        choices=["yahoo", "bloomberg", "reuters", "cnbc", "rss",
                 "marketwatch", "seekingalpha", "benzinga", "investingcom", "ft", "edgar"],
    )
    monitor_parser.add_argument("--max-articles", type=int, default=10)
    monitor_parser.add_argument("--interval", type=int, default=None)
    monitor_parser.add_argument("--council", action="store_true",
                                help="Use multi-agent AI council for analysis")

    # --- Portfolio command ---
    portfolio_parser = subparsers.add_parser("portfolio", help="Manage portfolio")
    portfolio_sub = portfolio_parser.add_subparsers(dest="portfolio_cmd")

    # portfolio add
    add_p = portfolio_sub.add_parser("add", help="Add a position")
    add_p.add_argument("ticker")
    add_p.add_argument("shares", type=float)
    add_p.add_argument("cost", type=float, help="Average cost per share")

    # portfolio remove
    rm_p = portfolio_sub.add_parser("remove", help="Remove a position")
    rm_p.add_argument("ticker")

    # portfolio list
    portfolio_sub.add_parser("list", help="List all positions")

    # portfolio summary
    portfolio_sub.add_parser("summary", help="Portfolio summary")

    # portfolio alerts
    alerts_p = portfolio_sub.add_parser("alerts", help="View recent alerts")
    alerts_p.add_argument("--limit", type=int, default=20)

    # portfolio watchlist
    wl_parser = portfolio_sub.add_parser("watchlist", help="Manage watchlists")
    wl_sub = wl_parser.add_subparsers(dest="watchlist_action")

    wl_create = wl_sub.add_parser("create")
    wl_create.add_argument("name")
    wl_create.add_argument("tickers", nargs="*")
    wl_create.add_argument("--description", default="")

    wl_add = wl_sub.add_parser("add")
    wl_add.add_argument("name")
    wl_add.add_argument("tickers", nargs="+")

    wl_rm = wl_sub.add_parser("remove")
    wl_rm.add_argument("name")
    wl_rm.add_argument("tickers", nargs="+")

    wl_del = wl_sub.add_parser("delete")
    wl_del.add_argument("name")

    wl_sub.add_parser("list")

    # --- Alerts command ---
    alerts_parser = subparsers.add_parser("alerts", help="Manage alert rules")
    alerts_sub = alerts_parser.add_subparsers(dest="alerts_cmd")

    alerts_sub.add_parser("list", help="List all alert rules")

    alerts_add = alerts_sub.add_parser("add", help="Add an alert rule")
    alerts_add.add_argument("--name", required=True, help="Rule name")
    alerts_add.add_argument(
        "--preset",
        choices=["faang_pullout", "high_confidence_invest", "high_impact", "breaking_news"],
        required=True,
        help="Preset rule template",
    )

    alerts_rm = alerts_sub.add_parser("remove", help="Remove an alert rule")
    alerts_rm.add_argument("rule_id", help="Rule ID to remove")

    alerts_enable = alerts_sub.add_parser("enable", help="Enable an alert rule")
    alerts_enable.add_argument("rule_id", help="Rule ID to enable")

    alerts_disable = alerts_sub.add_parser("disable", help="Disable an alert rule")
    alerts_disable.add_argument("rule_id", help="Rule ID to disable")

    # --- Accuracy command ---
    accuracy_parser = subparsers.add_parser("accuracy", help="Signal accuracy tracking")
    accuracy_sub = accuracy_parser.add_subparsers(dest="accuracy_cmd")

    acc_check = accuracy_sub.add_parser("check", help="Check outcomes for past signals")
    acc_check.add_argument("--hours", type=float, default=24, help="Hours lookback (default: 24)")

    accuracy_sub.add_parser("report", help="Print accuracy report")

    acc_ticker = accuracy_sub.add_parser("ticker", help="Accuracy for a specific ticker")
    acc_ticker.add_argument("ticker_symbol", help="Ticker symbol (e.g. AAPL)")

    acc_source = accuracy_sub.add_parser("source", help="Accuracy for a specific source")
    acc_source.add_argument("source_name", help="Source name (e.g. yahoo)")

    args = parser.parse_args()

    # Handle backward compat (no subcommand = scrape with old flags)
    if args.command is None:
        # Check for old-style --monitor flag
        if "--monitor" in sys.argv:
            # Re-parse with old style
            old_parser = argparse.ArgumentParser()
            old_parser.add_argument("--sources", nargs="+", default=["yahoo"])
            old_parser.add_argument("--max-articles", type=int, default=10)
            old_parser.add_argument("--monitor", action="store_true")
            old_parser.add_argument("--interval", type=int, default=None)
            old_args = old_parser.parse_args()
            if old_args.monitor:
                monitor = Monitor(
                    sources=old_args.sources,
                    default_interval=old_args.interval,
                    max_articles_per_source=old_args.max_articles,
                )
                monitor.start()
                return
        # Default: single scrape
        args.command = "scrape"
        args.sources = ["yahoo"]
        args.max_articles = 10
        args.council = False

    if args.command == "scrape":
        pipeline = FinScrapePipeline(
            sources=args.sources,
            max_articles_per_source=args.max_articles,
            use_council=getattr(args, "council", False),
        )
        try:
            events = pipeline.run()
            if events:
                print(f"\nExtracted {len(events)} actionable signals.")
            else:
                print("\nNo new signals found in this run.")
        except KeyboardInterrupt:
            print("\nPipeline stopped by user.")
        except Exception as e:
            print(f"\nFATAL ERROR: {e}")
            raise

    elif args.command == "monitor":
        monitor = Monitor(
            sources=args.sources,
            default_interval=args.interval,
            max_articles_per_source=args.max_articles,
            use_council=getattr(args, "council", False),
        )
        monitor.start()

    elif args.command == "portfolio":
        if not args.portfolio_cmd:
            portfolio_parser.print_help()
            return
        handle_portfolio(args)

    elif args.command == "alerts":
        if not args.alerts_cmd:
            alerts_parser.print_help()
            return
        handle_alerts(args)

    elif args.command == "accuracy":
        if not args.accuracy_cmd:
            accuracy_parser.print_help()
            return
        handle_accuracy(args)


def handle_alerts(args):
    """Handle alerts subcommands."""
    from finscrape.alerts import AlertEngine

    engine = AlertEngine()

    if args.alerts_cmd == "list":
        rules = engine.get_rules()
        if not rules:
            print("No alert rules configured.")
            engine.close()
            return
        print(f"\n{'ID':<14} {'Enabled':<9} {'Name':<30} {'Conditions':<6} {'Created'}")
        print("-" * 80)
        for r in rules:
            status = "YES" if r.enabled else "NO"
            print(f"{r.id:<14} {status:<9} {r.name:<30} {len(r.conditions):<6} {r.created_at[:19]}")
        print()

    elif args.alerts_cmd == "add":
        presets = {
            "faang_pullout": AlertEngine.preset_faang_pullout,
            "high_confidence_invest": AlertEngine.preset_high_confidence_invest,
            "high_impact": AlertEngine.preset_high_impact,
            "breaking_news": AlertEngine.preset_breaking_news,
        }
        preset_fn = presets[args.preset]
        conditions, actions = preset_fn()
        rule_id = engine.add_rule(args.name, conditions, actions)
        print(f"Added alert rule: {args.name} (id={rule_id})")

    elif args.alerts_cmd == "remove":
        if engine.remove_rule(args.rule_id):
            print(f"Removed rule {args.rule_id}")
        else:
            print(f"Rule {args.rule_id} not found.")

    elif args.alerts_cmd == "enable":
        engine.enable_rule(args.rule_id)
        print(f"Enabled rule {args.rule_id}")

    elif args.alerts_cmd == "disable":
        engine.disable_rule(args.rule_id)
        print(f"Disabled rule {args.rule_id}")

    engine.close()


if __name__ == "__main__":
    main()
