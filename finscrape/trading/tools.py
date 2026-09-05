"""
Data tools — wrap fin-scrape's existing scrapers as pipeline data providers.

Each tool fetches data for a ticker and returns a formatted string the LLM
analysts can reason over. No langchain tool decorators — these are plain
functions called by agent nodes.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_stock_data(ticker: str, period: str = "3mo") -> str:
    """Fetch OHLCV price history via yfinance."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return f"No price data available for {ticker}"
        lines = [f"=== {ticker} Price History ({period}) ==="]
        lines.append(f"Latest close: ${hist['Close'].iloc[-1]:.2f}")
        lines.append(f"52-week high: ${hist['High'].max():.2f}")
        lines.append(f"52-week low: ${hist['Low'].min():.2f}")
        lines.append(f"Avg volume (20d): {hist['Volume'].tail(20).mean():,.0f}")
        # Recent daily summary
        recent = hist.tail(10)
        lines.append("\nLast 10 trading days:")
        lines.append("Date | Open | High | Low | Close | Volume")
        for date, row in recent.iterrows():
            d = date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date)[:10]
            lines.append(f"{d} | {row['Open']:.2f} | {row['High']:.2f} | {row['Low']:.2f} | {row['Close']:.2f} | {row['Volume']:,.0f}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching stock data for {ticker}: {e}"


def get_indicators(ticker: str) -> str:
    """Fetch technical indicators via fin-scrape's market_data module."""
    try:
        from finscrape.market_data import get_indicators as _get_indicators
        indicators = _get_indicators([ticker])
        if ticker not in indicators:
            return f"No indicator data available for {ticker}"
        data = indicators[ticker]
        lines = [f"=== {ticker} Technical Indicators ==="]
        for key, value in data.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching indicators for {ticker}: {e}"


def get_fundamentals(ticker: str) -> str:
    """Fetch fundamental data via yfinance."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info:
            return f"No fundamental data available for {ticker}"
        lines = [f"=== {ticker} Fundamentals ==="]
        fields = [
            ("Company", "shortName"),
            ("Sector", "sector"),
            ("Industry", "industry"),
            ("Market Cap", "marketCap"),
            ("P/E Ratio", "trailingPE"),
            ("Forward P/E", "forwardPE"),
            ("EPS (TTM)", "trailingEps"),
            ("Dividend Yield", "dividendYield"),
            ("Revenue", "totalRevenue"),
            ("Net Income", "netIncomeToCommon"),
            ("Profit Margin", "profitMargins"),
            ("Operating Margin", "operatingMargins"),
            ("ROE", "returnOnEquity"),
            ("Debt/Equity", "debtToEquity"),
            ("Free Cash Flow", "freeCashflow"),
            ("Target Price", "targetMeanPrice"),
            ("Recommendation", "recommendationKey"),
        ]
        for label, key in fields:
            val = info.get(key)
            if val is not None:
                if isinstance(val, float) and abs(val) > 1_000_000:
                    lines.append(f"  {label}: ${val:,.0f}")
                elif isinstance(val, float) and abs(val) < 1:
                    lines.append(f"  {label}: {val:.2%}")
                else:
                    lines.append(f"  {label}: {val}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching fundamentals for {ticker}: {e}"


def get_news(ticker: str, days: int = 7) -> str:
    """Fetch recent news via yfinance."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        news = stock.news
        if not news:
            return f"No recent news available for {ticker}"
        lines = [f"=== {ticker} Recent News ==="]
        for i, item in enumerate(news[:15], 1):
            title = item.get("title", "No title")
            publisher = item.get("publisher", "Unknown")
            pub_time = item.get("providerPublishTime", "")
            if pub_time and isinstance(pub_time, (int, float)):
                from datetime import datetime
                pub_time = datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M")
            lines.append(f"{i}. [{publisher}] {title}")
            if pub_time:
                lines.append(f"   Published: {pub_time}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching news for {ticker}: {e}"


def get_sentiment(ticker: str) -> str:
    """Fetch social sentiment from Reddit + StockTwits via fin-scrape."""
    parts = []
    # StockTwits
    try:
        from finscrape.sentiment.stocktwits import fetch_stocktwits_messages
        msgs = fetch_stocktwits_messages(ticker, limit=20)
        if msgs:
            parts.append(f"=== StockTwits ({ticker}) ===")
            for m in msgs[:10]:
                sentiment = m.get("sentiment", "neutral")
                body = m.get("body", "")[:120]
                parts.append(f"  [{sentiment}] {body}")
    except Exception as e:
        parts.append(f"StockTwits unavailable: {e}")

    # Reddit
    try:
        from finscrape.sentiment.reddit import fetch_reddit_posts
        posts = fetch_reddit_posts(ticker, limit=10)
        if posts:
            parts.append(f"\n=== Reddit ({ticker}) ===")
            for p in posts[:5]:
                title = p.get("title", "")[:100]
                score = p.get("score", 0)
                parts.append(f"  [score={score}] {title}")
    except Exception as e:
        parts.append(f"Reddit unavailable: {e}")

    return "\n".join(parts) if parts else f"No sentiment data available for {ticker}"


def get_balance_sheet(ticker: str) -> str:
    """Fetch balance sheet via yfinance."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        bs = stock.balance_sheet
        if bs is None or bs.empty:
            return f"No balance sheet data for {ticker}"
        lines = [f"=== {ticker} Balance Sheet ==="]
        latest = bs.iloc[:, 0] if len(bs.columns) > 0 else None
        if latest is not None:
            for idx in latest.index[:15]:
                val = latest[idx]
                if val is not None and not (isinstance(val, float) and val != val):
                    if abs(val) > 1_000_000:
                        lines.append(f"  {idx}: ${val:,.0f}")
                    else:
                        lines.append(f"  {idx}: {val}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching balance sheet for {ticker}: {e}"


def get_cashflow(ticker: str) -> str:
    """Fetch cash flow statement via yfinance."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        cf = stock.cashflow
        if cf is None or cf.empty:
            return f"No cash flow data for {ticker}"
        lines = [f"=== {ticker} Cash Flow ==="]
        latest = cf.iloc[:, 0] if len(cf.columns) > 0 else None
        if latest is not None:
            for idx in latest.index[:10]:
                val = latest[idx]
                if val is not None and not (isinstance(val, float) and val != val):
                    if abs(val) > 1_000_000:
                        lines.append(f"  {idx}: ${val:,.0f}")
                    else:
                        lines.append(f"  {idx}: {val}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching cash flow for {ticker}: {e}"
