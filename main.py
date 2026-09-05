"""
FinScrape — AI-powered financial news intelligence engine.

Usage:
    python main.py                    # Run with default sources (Yahoo Finance)
    python main.py --sources yahoo bloomberg reuters cnbc rss
    python main.py --sources yahoo rss --max-articles 20
    python main.py portfolio add AAPL 100 150.0
    python main.py portfolio watchlist tech AAPL MSFT GOOGL
"""

import argparse
import logging
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import UTC

from finscrape.monitor import Monitor
from finscrape.pipeline import FinScrapePipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "app.log")),
    ],
)


def handle_quotes(args):
    """Realtime quotes across every tracked exchange."""
    from finscrape.exchanges import get_global_quotes

    wanted = [(args.exchange.upper(), s) for s in args.symbols]
    quotes = get_global_quotes(wanted)
    if not quotes:
        print("No quotes returned (check exchange code / symbol / network).")
        return
    print(f"\n{'='*60}\n  Global Quotes ({', '.join(q.get('source', '?') for q in quotes.values())})\n{'='*60}")
    for symbol, q in quotes.items():
        price = q.get("price")
        change = q.get("change_pct")
        if price is None:
            print(f"  {symbol:<16} unavailable")
            continue
        arrow = "▲" if (change or 0) > 0 else "▼" if (change or 0) < 0 else "·"
        change_str = f"{change:+.2f}%" if change is not None else "  —"
        print(f"  {symbol:<16} {price:>12} {arrow} {change_str}  [{q.get('source', '?')}]")


def handle_devtools(args):
    """Developer mode: manage API keys for external tools by class."""
    from finscrape import devmode

    cmd = getattr(args, "devtools_cmd", "list") or "list"

    if cmd == "list":
        status = devmode.status()
        print(f"Developer mode: {status['mode'].upper()}   (config: {status['path']})")
        for cls, info in status["classes"].items():
            active = f" → ACTIVE: {info['active']}" if info["active"] else ""
            print(f"\n  {cls}  ({info['label']}){active}")
            print(f"    fields:    {', '.join(info['fields'])}")
            print(f"    providers: {', '.join(info['providers']) or '—'}")
        if status["mode"] != "dev":
            print("\n  Mode is OFF — run `main.py devtools on` to activate dev providers.")
    elif cmd == "on":
        devmode.set_mode("dev")
        print("Developer mode ON — active providers now override env config.")
    elif cmd == "off":
        devmode.set_mode("off")
        print("Developer mode OFF — all dev providers inert.")
    elif cmd == "path":
        print(devmode.config_path())
    elif cmd == "set":
        fields = {}
        for item in args.field:
            if "=" not in item:
                print(f"  [SKIP] malformed --field (need key=value): {item}")
                continue
            key, _, value = item.partition("=")
            fields[key.strip()] = value.strip()
        if not fields:
            print("No --field values given. Example: --field api_key=fc-123")
            return
        result = devmode.set_provider(args.tool_class, args.provider, fields,
                                      activate=not args.no_activate)
        print(f"Saved {result['tool_class']}/{result['provider']} "
              f"(active: {result['active'] or '—'}) with fields: {', '.join(result['fields'])}")
    elif cmd == "test":
        active = devmode.get_active(args.tool_class)
        if not active:
            print(f"No active provider for '{args.tool_class}' "
                  f"(dev mode off, or none set — see `main.py devtools list`)")
            return
        print(f"{args.tool_class} → {active['provider']}: {active['fields']}")


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
        print("\n=== Signal Accuracy Report ===")
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
                 "marketwatch", "seekingalpha", "benzinga", "investingcom", "ft", "google_news", "edgar",
                 "firecrawl", "serp"],
    )
    scrape_parser.add_argument("--max-articles", type=int, default=30)
    scrape_parser.add_argument("--age-hours", type=float, default=2.0,
                               help="Only include articles within last N hours (default: 2)")
    scrape_parser.add_argument("--council", action="store_true",
                               help="Use multi-agent AI council for analysis")
    scrape_parser.add_argument("--ollama", action="store_true",
                               help="Use local Ollama instead of cloud API (auto-sets OPENAI_BASE_URL)")
    scrape_parser.add_argument("--ollama-model", default="qwen2.5:7b",
                               help="Ollama model to use (default: qwen2.5:7b)")
    scrape_parser.add_argument("--smoke-test", action="store_true",
                               help="Run one article end-to-end, print JSON result, then exit")

    # --- Monitor command ---
    monitor_parser = subparsers.add_parser("monitor", help="Run continuous monitoring")
    monitor_parser.add_argument(
        "--sources", nargs="+", default=["yahoo"],
        choices=["yahoo", "bloomberg", "reuters", "cnbc", "rss",
                 "marketwatch", "seekingalpha", "benzinga", "investingcom", "ft", "google_news", "edgar",
                 "firecrawl", "serp"],
    )
    monitor_parser.add_argument("--max-articles", type=int, default=30)
    monitor_parser.add_argument("--age-hours", type=float, default=2.0,
                                help="Only include articles within last N hours (default: 2)")
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
        choices=[
            "faang_pullout", "high_confidence_invest", "high_impact", "breaking_news",
            "discord_high_confidence", "slack_pullout", "multi_channel_high_impact",
        ],
        required=True,
        help="Preset rule template",
    )

    alerts_rm = alerts_sub.add_parser("remove", help="Remove an alert rule")
    alerts_rm.add_argument("rule_id", help="Rule ID to remove")

    alerts_enable = alerts_sub.add_parser("enable", help="Enable an alert rule")
    alerts_enable.add_argument("rule_id", help="Rule ID to enable")

    alerts_disable = alerts_sub.add_parser("disable", help="Disable an alert rule")
    alerts_disable.add_argument("rule_id", help="Rule ID to disable")

    # --- Trading command ---
    trading_parser = subparsers.add_parser("trading", help="Multi-agent trading analysis")
    trading_parser.add_argument("ticker", help="Ticker symbol (e.g. NVDA, AAPL)")
    trading_parser.add_argument("--date", help="Analysis date (YYYY-MM-DD, default: today)")
    trading_parser.add_argument("--debate-rounds", type=int, default=1,
                                help="Bull/bear debate rounds (default: 1)")
    trading_parser.add_argument("--risk-rounds", type=int, default=1,
                                help="Risk team debate rounds (default: 1)")
    trading_parser.add_argument("--no-save", action="store_true",
                                help="Skip saving reports to disk")
    trading_parser.add_argument("--analysts", nargs="+",
                                default=["market", "sentiment", "news", "fundamentals"],
                                choices=["market", "sentiment", "news", "fundamentals"],
                                help="Which analysts to run (default: all)")

    # --- Quotes command (global, all exchanges) ---
    quotes_parser = subparsers.add_parser(
        "quotes", help="Realtime quotes across every tracked exchange (US, IN, CN, EU, ...)"
    )
    quotes_parser.add_argument("--exchange", default="",
                               help="Exchange code: NSE, BSE, SSE, SZSE, HKEX, TSE, LSE, XETRA, ... "
                                    "(empty = US/bare tickers; CN exchanges use keyless native APIs)")
    quotes_parser.add_argument("--symbols", nargs="+", required=True,
                               help="Bare tickers, e.g. --symbols RELIANCE TCS or --symbols 600519 000001")

    # --- Serve command (whole product on localhost) ---
    serve_parser = subparsers.add_parser(
        "serve", help="Run the WorldFin web app on localhost (SQLite + live quotes, no Postgres)"
    )
    serve_parser.add_argument("--port", type=int, default=8080)
    serve_parser.add_argument("--host", default="127.0.0.1")

    # --- Accuracy command ---
    accuracy_parser = subparsers.add_parser("accuracy", help="Signal accuracy tracking")

    # --- Digest command ---
    digest_parser = subparsers.add_parser("digest", help="Send email digests")
    digest_sub = digest_parser.add_subparsers(dest="digest_cmd")
    digest_sub.add_parser("daily", help="Send daily digest email")
    digest_sub.add_parser("weekly", help="Send weekly digest email")
    digest_preview = digest_sub.add_parser("preview", help="Preview digest HTML (write to file)")
    digest_preview.add_argument("--type", choices=["daily", "weekly"], default="daily")
    digest_preview.add_argument("--output", default="/mnt/user-outputs/digest_preview.html")

    # --- Accuracy command ---
    accuracy_sub = accuracy_parser.add_subparsers(dest="accuracy_cmd")

    acc_check = accuracy_sub.add_parser("check", help="Check outcomes for past signals")
    acc_check.add_argument("--hours", type=float, default=24, help="Hours lookback (default: 24)")

    # --- Devtools command (developer mode: bring-your-own API keys) ---
    devtools_parser = subparsers.add_parser(
        "devtools",
        help="Developer mode: configure API keys for external tools (search, AI, scraping, ...)",
    )
    devtools_sub = devtools_parser.add_subparsers(dest="devtools_cmd")
    devtools_sub.add_parser("list", help="Show tool classes, their fields and providers")
    devtools_sub.add_parser("path", help="Print the dev-tools config file location")
    devtools_sub.add_parser("on", help="Turn developer mode ON")
    devtools_sub.add_parser("off", help="Turn developer mode OFF")
    devtools_set = devtools_sub.add_parser(
        "set", help="Set a provider under a tool class, e.g. "
        "devtools set news_fetch firecrawl --field api_key=fc-... ; "
        "unknown classes go to `custom`, unknown providers are created on the fly"
    )
    devtools_set.add_argument("tool_class", help="Tool class: ai, web_search, news_fetch, market_data, geo_intel, alerts, custom")
    devtools_set.add_argument("provider", help="Provider name (any name you like)")
    devtools_set.add_argument("--field", action="append", default=[],
                              help="field=value, repeatable (e.g. --field api_key=... --field model=qwen2.5:7b)")
    devtools_set.add_argument("--no-activate", action="store_true", help="Save without making this provider active")
    devtools_test = devtools_sub.add_parser("test", help="Show the active provider for a tool class")
    devtools_test.add_argument("tool_class", help="Tool class to inspect")

    accuracy_sub.add_parser("report", help="Print accuracy report")

    acc_ticker = accuracy_sub.add_parser("ticker", help="Accuracy for a specific ticker")
    acc_ticker.add_argument("ticker_symbol", help="Ticker symbol (e.g. AAPL)")

    acc_source = accuracy_sub.add_parser("source", help="Accuracy for a specific source")
    acc_source.add_argument("source_name", help="Source name (e.g. yahoo)")

    args = parser.parse_args()

    # Developer mode: project active providers onto env before anything reads them.
    # Explicit --ollama below still wins because it runs later.
    from finscrape.devmode import apply_to_env
    apply_to_env()

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
        args.max_articles = 30
        args.age_hours = 2.0
        args.council = False
        args.ollama = False
        args.ollama_model = "qwen2.5:7b"
        args.smoke_test = False

    if args.command == "scrape":
        # Wire Ollama if requested — must happen before any ai_client import
        if getattr(args, "ollama", False):
            os.environ["OPENAI_BASE_URL"]  = "http://localhost:11434/v1"
            os.environ["OPENAI_API_KEY"]   = "ollama"
            os.environ["FINSCRAPE_MODEL"]  = getattr(args, "ollama_model", "qwen2.5:7b")
            os.environ.setdefault("FINSCRAPE_AI_TIMEOUT", "180")
            os.environ.pop("OPENROUTER_API_KEY", None)  # force proxy branch
            print(f"[Ollama] Using {os.environ['FINSCRAPE_MODEL']} at {os.environ['OPENAI_BASE_URL']}")

        # Smoke-test: run one article and exit
        if getattr(args, "smoke_test", False):
            import json as _json

            from finscrape.analysis.ai_client import call_ai
            from finscrape.analysis.prompts import ANALYSIS_PROMPT, SYSTEM_PROMPT
            test_text = "Apple Inc. reported record Q1 earnings, beating estimates by 12%. EPS $2.40 vs $2.14 expected."
            prompt = ANALYSIS_PROMPT.replace("{{title}}", "Apple Q1 earnings beat").replace("{{article_text}}", test_text)
            print("\n[Smoke test] Sending one article to AI...")
            result = call_ai(prompt, SYSTEM_PROMPT)
            print("[Smoke test] Result:")
            print(_json.dumps(result, indent=2))
            return

        # Set age window before pipeline construction (scrapers read from env)
        age_hours = getattr(args, "age_hours", 2.0)
        os.environ["FINSCRAPE_MAX_AGE_HOURS"] = str(age_hours)
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

    elif args.command == "trading":
        handle_trading(args)

    elif args.command == "quotes":
        handle_quotes(args)

    elif args.command == "serve":
        import uvicorn

        from finscrape.serve import app

        print(f"\n  WorldFin → http://{args.host}:{args.port}\n")
        uvicorn.run(app, host=args.host, port=args.port, log_level="warning")

    elif args.command == "accuracy":
        if not args.accuracy_cmd:
            accuracy_parser.print_help()
            return
        handle_accuracy(args)

    elif args.command == "devtools":
        handle_devtools(args)

    elif args.command == "digest":
        if not args.digest_cmd:
            digest_parser.print_help()
            return
        handle_digest(args)


def handle_trading(args):
    """Handle multi-agent trading analysis."""
    from finscrape.trading.pipeline import run_analysis

    print(f"\n{'='*60}")
    print(f"  Multi-Agent Trading Analysis: {args.ticker.upper()}")
    print(f"  Analysts: {', '.join(args.analysts)}")
    print(f"  Debate rounds: {args.debate_rounds} | Risk rounds: {args.risk_rounds}")
    print(f"{'='*60}\n")

    result = run_analysis(
        ticker=args.ticker.upper(),
        trade_date=args.date,
        debate_rounds=args.debate_rounds,
        risk_rounds=args.risk_rounds,
        selected_analysts=tuple(args.analysts),
        save_reports=not args.no_save,
    )

    print(f"{'='*60}")
    print(f"  {result['ticker']} — {result['trade_date']}")
    print(f"  Signal: {result['signal']}")
    print(f"  Duration: {result['duration_seconds']}s")
    if result["errors"]:
        print(f"  Errors: {len(result['errors'])}")
    print(f"{'='*60}\n")

    print("--- Final Decision ---")
    print(result["decision"][:2000])
    print()

    if result["errors"]:
        print("--- Errors ---")
        for e in result["errors"]:
            print(f"  {e}")


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
            "discord_high_confidence": AlertEngine.preset_discord_high_confidence,
            "slack_pullout": AlertEngine.preset_slack_pullout,
            "multi_channel_high_impact": AlertEngine.preset_multi_channel_high_impact,
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


def handle_digest(args):
    """Handle digest subcommands."""
    from datetime import datetime, timedelta

    from finscrape.digest import DigestBuilder, EmailDigest
    from finscrape.storage import StateManager

    if args.digest_cmd == "daily":
        digest = EmailDigest()
        if not digest.is_configured:
            print("Email digest not configured. Set RESEND_PROXY_URL and FINSCRAPE_DIGEST_TO env vars.")
            return
        result = digest.send_daily()
        if result.get("ok"):
            print(f"Daily digest sent to {digest.to_email}")
        else:
            print(f"Failed: {result}")

    elif args.digest_cmd == "weekly":
        digest = EmailDigest()
        if not digest.is_configured:
            print("Email digest not configured. Set RESEND_PROXY_URL and FINSCRAPE_DIGEST_TO env vars.")
            return
        result = digest.send_weekly()
        if result.get("ok"):
            print(f"Weekly digest sent to {digest.to_email}")
        else:
            print(f"Failed: {result}")

    elif args.digest_cmd == "preview":
        state = StateManager()
        cutoff = datetime.now(UTC) - timedelta(days=7 if args.type == "weekly" else 1)
        cutoff_str = cutoff.isoformat()
        events = [e for e in state.events if e.get("timestamp", "") >= cutoff_str]

        builder = DigestBuilder()
        if args.type == "weekly":
            subject, html = builder.build_weekly(events)
        else:
            subject, html = builder.build_daily(events)

        output = args.output
        with open(output, "w") as f:
            f.write(html)
        print(f"Preview written to {output}")
        print(f"Subject: {subject}")
        print(f"Events included: {len(events)}")


if __name__ == "__main__":
    main()
