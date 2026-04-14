"""
FinScrape — AI-powered financial news intelligence engine.

Usage:
    python main.py                    # Run with default sources (Yahoo Finance)
    python main.py --sources yahoo bloomberg reuters cnbc rss
    python main.py --sources yahoo rss --max-articles 20
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


def main():
    parser = argparse.ArgumentParser(description="FinScrape — Financial News Intelligence Engine")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["yahoo"],
        choices=["yahoo", "bloomberg", "reuters", "cnbc", "rss",
                 "marketwatch", "seekingalpha", "benzinga", "investingcom", "ft", "edgar"],
        help="News sources to scrape (default: yahoo)",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=10,
        help="Maximum articles per source (default: 10)",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Run in continuous monitoring mode instead of a single pass",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Override default scrape interval for all sources (seconds)",
    )
    args = parser.parse_args()

    if args.monitor:
        monitor = Monitor(
            sources=args.sources,
            default_interval=args.interval,
            max_articles_per_source=args.max_articles,
        )
        monitor.start()
    else:
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


if __name__ == "__main__":
    main()
