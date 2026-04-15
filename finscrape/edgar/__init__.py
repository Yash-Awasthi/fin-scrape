"""
SEC EDGAR deep integration package.

Provides filing fetching, content parsing, and insider trading analysis
for 10-K, 10-Q, 8-K, Form 4, DEF 14A, and 13-F filings.
"""

from finscrape.edgar.filings import Filing, FilingFetcher, FilingType
from finscrape.edgar.parser import FilingParser
from finscrape.edgar.insider_tracker import InsiderTracker, InsiderTransaction

__all__ = [
    "Filing",
    "FilingFetcher",
    "FilingType",
    "FilingParser",
    "InsiderTracker",
    "InsiderTransaction",
]
