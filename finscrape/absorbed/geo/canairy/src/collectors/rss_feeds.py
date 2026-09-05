"""
RSS Feed collectors for various indicators.
Free alternatives to paid APIs using public RSS feeds and news sources.
"""

import requests
import feedparser
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .base import BaseCollector


class RSSBaseCollector(BaseCollector):
    """Base class for RSS-based collectors."""

    def __init__(self, config):
        super().__init__(config)
        self.headers = {'User-Agent': 'Canairy/1.0 (household-resilience-monitor)'}

    def _fetch_rss(self, url: str) -> Optional[List[Dict]]:
        """Fetch and parse RSS feed."""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                return feed.entries
            return None
        except Exception as e:
            self.logger.error(f"RSS fetch error for {url}: {e}")
            return None

    def _count_keywords(self, entries: List[Dict], keywords: List[str], days: int = 7) -> int:
        """Count entries containing keywords within date range."""
        count = 0
        cutoff = datetime.utcnow() - timedelta(days=days)

        for entry in entries:
            # Check date if available
            pub_date = entry.get('published_parsed') or entry.get('updated_parsed')
            if pub_date:
                entry_date = datetime(*pub_date[:6])
                if entry_date < cutoff:
                    continue

            # Check for keywords
            text = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()
            if any(kw.lower() in text for kw in keywords):
                count += 1

        return count


class ProtestNewsCollector(RSSBaseCollector):
    """Collects protest/civil unrest data from news RSS feeds."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "ProtestNews"
        # Multiple news sources for better coverage
        self.rss_feeds = [
            "https://news.google.com/rss/search?q=protest+united+states&hl=en-US&gl=US&ceid=US:en",
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
        ]

    def collect(self) -> Dict[str, Any]:
        """Collect protest news from RSS feeds."""
        try:
            total_protests = 0
            sources_checked = 0

            for feed_url in self.rss_feeds:
                entries = self._fetch_rss(feed_url)
                if entries:
                    sources_checked += 1
                    count = self._count_keywords(
                        entries,
                        ['protest', 'demonstration', 'rally', 'march', 'riot', 'unrest'],
                        days=7
                    )
                    total_protests += count

            if sources_checked > 0:
                # Normalize to approximate daily average
                avg_per_day = total_protests / 7.0

                return {
                    'value': round(avg_per_day, 1),
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'news_mentions_per_day',
                        'sources_checked': sources_checked,
                        'total_mentions': total_protests,
                        'source': 'News RSS Feeds',
                        'data_source': 'LIVE'
                    }
                }

            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Protest news collection failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 5.0,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class GlobalConflictNewsCollector(RSSBaseCollector):
    """Collects global conflict data from news RSS feeds."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "GlobalConflictNews"
        self.rss_feeds = [
            "https://news.google.com/rss/search?q=military+conflict+war&hl=en-US&gl=US&ceid=US:en",
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        ]

    def collect(self) -> Dict[str, Any]:
        """Collect global conflict news."""
        try:
            total_conflicts = 0
            sources_checked = 0

            for feed_url in self.rss_feeds:
                entries = self._fetch_rss(feed_url)
                if entries:
                    sources_checked += 1
                    count = self._count_keywords(
                        entries,
                        ['war', 'conflict', 'military', 'strike', 'attack', 'battle', 'troops', 'bombing'],
                        days=7
                    )
                    total_conflicts += count

            if sources_checked > 0:
                # Convert news mentions to estimated weekly events
                # News typically covers a fraction of actual events
                # Be more conservative: ~3 mentions per actual event on avg
                # Threshold expects events/wk: green <150, amber 150-300, red >300
                estimated_events_weekly = total_conflicts * 3
                estimated_events_weekly = min(estimated_events_weekly, 500)  # Cap reasonably

                return {
                    'value': round(estimated_events_weekly, 0),
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'events_per_week',
                        'news_mentions': total_conflicts,
                        'sources_checked': sources_checked,
                        'source': 'News RSS Feeds',
                        'data_source': 'LIVE'
                    }
                }

            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Global conflict collection failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 450,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class NATONewsCollector(RSSBaseCollector):
    """Collects NATO readiness news from RSS feeds."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "NATONews"
        self.rss_feeds = [
            "https://www.nato.int/cps/en/natohq/news.htm?rss=1",
            "https://news.google.com/rss/search?q=NATO+military+readiness&hl=en-US&gl=US&ceid=US:en",
        ]

    def collect(self) -> Dict[str, Any]:
        """Collect NATO readiness indicators."""
        try:
            alert_level = 0
            keywords_found = []

            for feed_url in self.rss_feeds:
                entries = self._fetch_rss(feed_url)
                if entries:
                    text = ' '.join([
                        (e.get('title', '') + ' ' + e.get('summary', '')).lower()
                        for e in entries[:20]
                    ])

                    # Check for escalation keywords
                    escalation_keywords = {
                        'high readiness': 2,
                        'alert': 1,
                        'deployment': 1,
                        'mobilization': 2,
                        'exercise': 0.5,
                        'troops': 0.5,
                        'defense': 0.5
                    }

                    for kw, weight in escalation_keywords.items():
                        if kw in text:
                            alert_level += weight
                            keywords_found.append(kw)

            # Normalize to 0-5 scale
            normalized_level = min(alert_level, 5)

            return {
                'value': round(normalized_level, 1),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'readiness_level',
                    'keywords_found': keywords_found[:5],
                    'source': 'NATO/News RSS',
                    'data_source': 'LIVE'
                }
            }

        except Exception as e:
            self.logger.error(f"NATO news collection failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 2.0,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class DefenseSpendingCollector(RSSBaseCollector):
    """Collects defense spending news from SIPRI and news sources."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "DefenseSpending"
        self.rss_feeds = [
            "https://www.sipri.org/rss.xml",
            "https://news.google.com/rss/search?q=defense+spending+military+budget&hl=en-US&gl=US&ceid=US:en",
        ]

    def collect(self) -> Dict[str, Any]:
        """Collect defense spending indicators."""
        try:
            growth_indicators = 0

            for feed_url in self.rss_feeds:
                entries = self._fetch_rss(feed_url)
                if entries:
                    for entry in entries[:15]:
                        text = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()

                        if any(kw in text for kw in ['increase', 'growth', 'boost', 'surge', 'rise']):
                            growth_indicators += 1
                        if any(kw in text for kw in ['cut', 'decrease', 'reduction']):
                            growth_indicators -= 1

            # Convert to percentage growth estimate (baseline 3%)
            estimated_growth = 3.0 + (growth_indicators * 0.5)
            estimated_growth = max(0, min(estimated_growth, 15))  # Cap at 0-15%

            return {
                'value': round(estimated_growth, 1),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'percent_growth',
                    'growth_signals': growth_indicators,
                    'source': 'SIPRI/News RSS',
                    'data_source': 'LIVE'
                }
            }

        except Exception as e:
            self.logger.error(f"Defense spending collection failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 4.5,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class AILayoffsCollector(RSSBaseCollector):
    """Collects AI-related layoff news."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "AILayoffs"
        self.rss_feeds = [
            "https://news.google.com/rss/search?q=AI+layoffs+tech+jobs&hl=en-US&gl=US&ceid=US:en",
            "https://news.ycombinator.com/rss",
        ]

    def collect(self) -> Dict[str, Any]:
        """Collect AI layoff news."""
        try:
            layoff_count = 0
            total_entries = 0

            for feed_url in self.rss_feeds:
                entries = self._fetch_rss(feed_url)
                if entries:
                    for entry in entries[:30]:
                        text = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()
                        total_entries += 1

                        if 'layoff' in text or 'job cut' in text or 'workforce reduction' in text:
                            if 'ai' in text or 'tech' in text or 'automation' in text:
                                # Try to extract numbers
                                numbers = re.findall(r'(\d+(?:,\d+)?)\s*(?:employees|workers|jobs|people)', text)
                                if numbers:
                                    layoff_count += int(numbers[0].replace(',', ''))
                                else:
                                    layoff_count += 100  # Estimate if no number

            # Cap at reasonable values and convert to K (thousands)
            # Threshold expects K/month: green <10K, amber 10-50K, red >50K
            layoff_count = min(layoff_count, 100000)
            layoff_k = layoff_count / 1000.0

            return {
                'value': round(layoff_k, 1),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'K_per_month',
                    'raw_count': layoff_count,
                    'articles_checked': total_entries,
                    'source': 'News RSS',
                    'data_source': 'LIVE'
                }
            }

        except Exception as e:
            self.logger.error(f"AI layoffs collection failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 5.0,  # 5K layoffs per month (in thousands)
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class NuclearTestsCollector(RSSBaseCollector):
    """Collects nuclear/missile test news from CTBTO and news."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "NuclearTests"
        self.rss_feeds = [
            "https://news.google.com/rss/search?q=nuclear+test+missile+test+north+korea+iran&hl=en-US&gl=US&ceid=US:en",
            "https://www.armscontrol.org/rss.xml",
        ]

    def collect(self) -> Dict[str, Any]:
        """Collect nuclear/missile test news."""
        try:
            news_mentions = 0

            for feed_url in self.rss_feeds:
                entries = self._fetch_rss(feed_url)
                if entries:
                    # Only count very specific test-related keywords
                    news_mentions += self._count_keywords(
                        entries,
                        ['conducted test', 'launched missile', 'test-fired', 'detonation detected'],
                        days=90
                    )

            # Multiple articles typically cover the same event
            # Be conservative: ~10 articles per actual test event
            # Threshold: green <0.5, amber 0.5-1, red >1
            estimated_tests = news_mentions / 10.0
            estimated_tests = min(estimated_tests, 5)  # Cap at 5 events

            return {
                'value': round(estimated_tests, 1),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'estimated_tests_90d',
                    'news_mentions': news_mentions,
                    'source': 'Arms Control/News RSS',
                    'data_source': 'LIVE'
                }
            }

        except Exception as e:
            self.logger.error(f"Nuclear tests collection failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 2,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data
