"""
Live Market Feed — Real-time price, news, and sentiment streaming.

Provides WebSocket-based market data streaming with price feeds,
news ingestion, social sentiment, and alert management.
All pure functions for processing — WebSocket transport is pluggable.
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums and data structures
# ---------------------------------------------------------------------------

class FeedType(str, Enum):
    PRICE = "price"
    NEWS = "news"
    SOCIAL = "social"
    TRADES = "trades"


class AlertType(str, Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    VOLUME_SPIKE = "volume_spike"
    NEWS_KEYWORD = "news_keyword"
    SENTIMENT_SHIFT = "sentiment_shift"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PriceTick:
    """Real-time price tick."""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: int
    timestamp: float
    source: str = ""


@dataclass
class NewsItem:
    """Live news item with sentiment."""
    headline: str
    source: str
    timestamp: float
    sentiment_score: float  # -1 to 1
    sentiment_label: str  # bearish, neutral, bullish
    tickers: List[str] = field(default_factory=list)
    url: str = ""


@dataclass
class SocialSignal:
    """Social media sentiment signal."""
    platform: str
    ticker: str
    sentiment: float  # -1 to 1
    volume: int  # mentions
    timestamp: float
    trend: str = "stable"  # rising, falling, stable


@dataclass
class MarketAlert:
    """Market alert."""
    alert_type: AlertType
    severity: AlertSeverity
    symbol: str
    message: str
    value: float
    threshold: float
    timestamp: float
    acknowledged: bool = False


@dataclass
class PriceBar:
    """Aggregated OHLCV bar from ticks."""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float
    start_time: float
    end_time: float


@dataclass
class FeedStatus:
    """Status of a market feed."""
    feed_type: FeedType
    is_connected: bool
    symbols_count: int
    ticks_per_second: float
    last_update: float
    buffer_size: int
    errors: int


# ---------------------------------------------------------------------------
# Price aggregation
# ---------------------------------------------------------------------------

class PriceAggregator:
    """Aggregates price ticks into OHLCV bars."""

    def __init__(self, bar_interval_seconds: int = 60):
        self.bar_interval = bar_interval_seconds
        self._current_bars: Dict[str, List[PriceTick]] = {}
        self._completed_bars: Dict[str, deque] = {}

    def add_tick(self, tick: PriceTick) -> Optional[PriceBar]:
        """Add a price tick. Returns a completed bar if interval elapsed."""
        symbol = tick.symbol
        
        if symbol not in self._current_bars:
            self._current_bars[symbol] = []
            self._completed_bars[symbol] = deque(maxlen=1000)
        
        ticks = self._current_bars[symbol]
        ticks.append(tick)
        
        # Check if bar is complete
        if len(ticks) >= 2:
            elapsed = ticks[-1].timestamp - ticks[0].timestamp
            if elapsed >= self.bar_interval:
                bar = self._create_bar(symbol, ticks)
                self._completed_bars[symbol].append(bar)
                self._current_bars[symbol] = []
                return bar
        
        return None

    def _create_bar(self, symbol: str, ticks: List[PriceTick]) -> PriceBar:
        """Create an OHLCV bar from ticks."""
        prices = [t.last for t in ticks]
        volumes = [t.volume for t in ticks]
        
        # VWAP
        total_pv = sum(t.last * t.volume for t in ticks)
        total_vol = sum(t.volume for t in ticks)
        vwap = total_pv / total_vol if total_vol > 0 else prices[-1]
        
        return PriceBar(
            symbol=symbol,
            open=prices[0],
            high=max(prices),
            low=min(prices),
            close=prices[-1],
            volume=sum(volumes),
            vwap=round(vwap, 4),
            start_time=ticks[0].timestamp,
            end_time=ticks[-1].timestamp,
        )

    def get_bars(self, symbol: str, count: int = 50) -> List[PriceBar]:
        """Get recent completed bars for a symbol."""
        bars = self._completed_bars.get(symbol, deque())
        return list(bars)[-count:]

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get the most recent price for a symbol."""
        ticks = self._current_bars.get(symbol, [])
        return ticks[-1].last if ticks else None


# ---------------------------------------------------------------------------
# News processor
# ---------------------------------------------------------------------------

class NewsProcessor:
    """Processes live news items with sentiment analysis."""

    def __init__(self, max_items: int = 500):
        self._items: deque = deque(maxlen=max_items)
        self._by_ticker: Dict[str, deque] = {}

    def ingest(self, item: NewsItem) -> None:
        """Ingest a news item."""
        self._items.append(item)
        
        for ticker in item.tickers:
            if ticker not in self._by_ticker:
                self._by_ticker[ticker] = deque(maxlen=100)
            self._by_ticker[ticker].append(item)

    def get_latest(self, count: int = 10) -> List[NewsItem]:
        """Get latest news items."""
        return list(self._items)[-count:]

    def get_for_ticker(self, ticker: str, count: int = 10) -> List[NewsItem]:
        """Get news for a specific ticker."""
        items = self._by_ticker.get(ticker, deque())
        return list(items)[-count:]

    def get_sentiment_average(
        self, ticker: str, window_minutes: int = 60
    ) -> Optional[float]:
        """Get average sentiment for a ticker over a time window."""
        cutoff = time.time() - window_minutes * 60
        items = [i for i in self._by_ticker.get(ticker, []) if i.timestamp >= cutoff]
        
        if not items:
            return None
        
        return sum(i.sentiment_score for i in items) / len(items)


# ---------------------------------------------------------------------------
# Social sentiment processor
# ---------------------------------------------------------------------------

class SocialProcessor:
    """Processes social media sentiment signals."""

    def __init__(self, max_signals: int = 1000):
        self._signals: deque = deque(maxlen=max_signals)
        self._by_ticker: Dict[str, deque] = {}

    def ingest(self, signal: SocialSignal) -> None:
        """Ingest a social sentiment signal."""
        self._signals.append(signal)
        
        if signal.ticker not in self._by_ticker:
            self._by_ticker[signal.ticker] = deque(maxlen=200)
        self._by_ticker[signal.ticker].append(signal)

    def get_sentiment_score(
        self, ticker: str, window_minutes: int = 30
    ) -> Optional[float]:
        """Get weighted sentiment score for a ticker."""
        cutoff = time.time() - window_minutes * 60
        signals = [s for s in self._by_ticker.get(ticker, []) if s.timestamp >= cutoff]
        
        if not signals:
            return None
        
        # Weight by volume
        total_weight = sum(s.volume for s in signals)
        if total_weight == 0:
            return 0
        
        weighted = sum(s.sentiment * s.volume for s in signals) / total_weight
        return round(weighted, 3)

    def get_mention_volume(
        self, ticker: str, window_minutes: int = 60
    ) -> int:
        """Get total mention volume for a ticker."""
        cutoff = time.time() - window_minutes * 60
        signals = [s for s in self._by_ticker.get(ticker, []) if s.timestamp >= cutoff]
        return sum(s.volume for s in signals)

    def detect_trending(
        self, window_minutes: int = 15, min_volume: int = 100
    ) -> List[Tuple[str, float, int]]:
        """Detect trending tickers by mention volume surge."""
        now = time.time()
        recent_cutoff = now - window_minutes * 60
        older_cutoff = now - window_minutes * 120  # Double window
        
        trending = []
        for ticker, signals in self._by_ticker.items():
            recent = [s for s in signals if s.timestamp >= recent_cutoff]
            older = [s for s in signals if older_cutoff <= s.timestamp < recent_cutoff]
            
            recent_vol = sum(s.volume for s in recent)
            older_vol = sum(s.volume for s in older)
            
            if recent_vol >= min_volume and older_vol > 0:
                surge = recent_vol / older_vol
                if surge > 2.0:  # 2x volume increase
                    avg_sentiment = sum(s.sentiment for s in recent) / len(recent) if recent else 0
                    trending.append((ticker, round(avg_sentiment, 3), recent_vol))
        
        return sorted(trending, key=lambda x: x[2], reverse=True)[:10]


# ---------------------------------------------------------------------------
# Alert manager
# ---------------------------------------------------------------------------

class MarketAlertManager:
    """Manages market alerts with cooldown."""

    def __init__(self, cooldown_seconds: int = 30):
        self.cooldown_seconds = cooldown_seconds
        self._rules: List[Dict] = []
        self._alerts: deque = deque(maxlen=100)
        self._last_fired: Dict[str, float] = {}

    def add_rule(
        self,
        alert_type: AlertType,
        symbol: str,
        threshold: float,
        severity: AlertSeverity = AlertSeverity.WARNING,
        message_template: str = "",
    ) -> None:
        """Add an alert rule."""
        self._rules.append({
            "type": alert_type,
            "symbol": symbol,
            "threshold": threshold,
            "severity": severity,
            "message": message_template,
        })

    def check_price(
        self, symbol: str, price: float, timestamp: float
    ) -> Optional[MarketAlert]:
        """Check price against alert rules."""
        for rule in self._rules:
            if rule["type"] != AlertType.PRICE_ABOVE and rule["type"] != AlertType.PRICE_BELOW:
                continue
            if rule["symbol"] != "*" and rule["symbol"] != symbol:
                continue
            
            key = f"{rule['type']}_{symbol}_{rule['threshold']}"
            if timestamp - self._last_fired.get(key, 0) < self.cooldown_seconds:
                continue
            
            triggered = False
            if rule["type"] == AlertType.PRICE_ABOVE and price >= rule["threshold"]:
                triggered = True
            elif rule["type"] == AlertType.PRICE_BELOW and price <= rule["threshold"]:
                triggered = True
            
            if triggered:
                self._last_fired[key] = timestamp
                alert = MarketAlert(
                    alert_type=rule["type"],
                    severity=rule["severity"],
                    symbol=symbol,
                    message=rule["message"] or f"{symbol} price {rule['type'].value}: {price}",
                    value=price,
                    threshold=rule["threshold"],
                    timestamp=timestamp,
                )
                self._alerts.append(alert)
                return alert
        
        return None

    def get_active_alerts(self) -> List[MarketAlert]:
        return [a for a in self._alerts if not a.acknowledged]


# ---------------------------------------------------------------------------
# Live feed
# ---------------------------------------------------------------------------

class LiveMarketFeed:
    """
    Main live market feed combining price, news, and social streams.
    
    Usage:
        feed = LiveMarketFeed()
        feed.on_price(PriceTick("AAPL", 150, 150.5, 150.25, 1000, time.time()))
        bars = feed.aggregator.get_bars("AAPL")
    """

    def __init__(self):
        self.aggregator = PriceAggregator(bar_interval_seconds=60)
        self.news = NewsProcessor()
        self.social = SocialProcessor()
        self.alerts = MarketAlertManager()
        self._subscribers: Dict[str, List[Callable]] = {}

    def on_price(self, tick: PriceTick) -> Optional[PriceBar]:
        """Process a price tick."""
        bar = self.aggregator.add_tick(tick)
        
        # Check alerts
        self.alerts.check_price(tick.symbol, tick.last, tick.timestamp)
        
        # Notify subscribers
        self._notify("price", tick)
        
        return bar

    def on_news(self, item: NewsItem) -> None:
        """Process a news item."""
        self.news.ingest(item)
        self._notify("news", item)

    def on_social(self, signal: SocialSignal) -> None:
        """Process a social sentiment signal."""
        self.social.ingest(signal)
        self._notify("social", signal)

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to feed events."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def _notify(self, event_type: str, data: Any) -> None:
        for cb in self._subscribers.get(event_type, []):
            try:
                cb(data)
            except Exception:
                pass  # Don't let subscriber errors break the feed

    def get_status(self) -> List[FeedStatus]:
        """Get status of all feed components."""
        return [
            FeedStatus(
                feed_type=FeedType.PRICE,
                is_connected=True,
                symbols_count=len(self.aggregator._current_bars),
                ticks_per_second=0,
                last_update=time.time(),
                buffer_size=sum(len(b) for b in self.aggregator._current_bars.values()),
                errors=0,
            ),
            FeedStatus(
                feed_type=FeedType.NEWS,
                is_connected=True,
                symbols_count=len(self.news._by_ticker),
                ticks_per_second=0,
                last_update=time.time(),
                buffer_size=len(self.news._items),
                errors=0,
            ),
            FeedStatus(
                feed_type=FeedType.SOCIAL,
                is_connected=True,
                symbols_count=len(self.social._by_ticker),
                ticks_per_second=0,
                last_update=time.time(),
                buffer_size=len(self.social._signals),
                errors=0,
            ),
        ]
