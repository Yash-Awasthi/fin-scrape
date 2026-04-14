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

    # --- Monitor command ---
    monitor_parser = subparsers.add_parser("monitor", help="Run continuous monitoring")
    monitor_parser.add_argument(
        "--sources", nargs="+", default=["yahoo"],
        choices=["yahoo", "bloomberg", "reuters", "cnbc", "rss",
                 "marketwatch", "seekingalpha", "benzinga", "investingcom", "ft", "edgar"],
    )
    monitor_parser.add_argument("--max-articles", type=int, default=10)
    monitor_parser.add_argument("--interval", type=int, default=None)

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

    if args.command == "scrape":
        pipeline = FinScrapePipeline(
            sources=args.sources,
            max_articles_per_source=args.max_articles,
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
        )
        monitor.start()

    elif args.command == "portfolio":
        if not args.portfolio_cmd:
            portfolio_parser.print_help()
            return
        handle_portfolio(args)


if __name__ == "__main__":
    main()
