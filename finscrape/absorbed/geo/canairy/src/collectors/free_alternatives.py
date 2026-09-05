"""
Free alternatives to paid/restricted APIs.
Uses Yahoo Finance, Google Trends, public APIs, and web scraping.
"""

import requests
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base import BaseCollector


class YahooLuxuryIndexCollector(BaseCollector):
    """Free alternative to Bloomberg Luxury Index using Yahoo Finance ETFs."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "YahooLuxuryIndex"
        # Luxury-related ETFs/stocks as proxy
        self.symbols = ['LVMUY', 'MC.PA', 'RMS.PA']  # LVMH, Kering, Hermes ADRs
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

    def collect(self) -> Dict[str, Any]:
        """Collect luxury sector performance."""
        try:
            total_change = 0
            valid_symbols = 0

            for symbol in self.symbols:
                try:
                    response = requests.get(
                        f"{self.base_url}/{symbol}",
                        params={'interval': '1d', 'range': '5d'},
                        headers={'User-Agent': 'Canairy/1.0'},
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()
                        result = data.get('chart', {}).get('result', [{}])[0]
                        meta = result.get('meta', {})

                        prev_close = meta.get('chartPreviousClose', 0)
                        current = meta.get('regularMarketPrice', 0)

                        if prev_close and current:
                            change_pct = ((current - prev_close) / prev_close) * 100
                            total_change += change_pct
                            valid_symbols += 1
                except:
                    continue

            if valid_symbols > 0:
                avg_change = total_change / valid_symbols
                # Convert to index (100 = neutral, <100 = decline, >100 = growth)
                index_value = 100 + avg_change

                return {
                    'value': round(index_value, 1),
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'index',
                        'avg_change_pct': round(avg_change, 2),
                        'symbols_checked': valid_symbols,
                        'source': 'Yahoo Finance',
                        'data_source': 'LIVE'
                    }
                }

            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Luxury index collection failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 98.5,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class EIAOilInventoryCollector(BaseCollector):
    """EIA oil inventory as alternative to JODI."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "EIAOilInventory"
        import os
        self.api_key = os.getenv('EIA_API_KEY') or os.getenv('DATA_GOV_API_KEY', '')
        self.base_url = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"

    def collect(self) -> Dict[str, Any]:
        """Collect oil inventory data from EIA."""
        try:
            params = {
                'api_key': self.api_key or 'DEMO_KEY',
                'frequency': 'weekly',
                'data[0]': 'value',
                'facets[product][]': 'EPC0',  # Crude oil
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'length': 5
            }

            response = requests.get(self.base_url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                records = data.get('response', {}).get('data', [])

                if records:
                    latest = float(records[0].get('value', 0))

                    # Calculate days of supply (crude production ~12.5 million bbl/day)
                    days_supply = latest / 12.5

                    return {
                        'value': round(days_supply, 1),
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'collector': self.name,
                        'metadata': {
                            'unit': 'days_supply',
                            'inventory_mmbbl': latest,
                            'source': 'EIA',
                            'data_source': 'LIVE'
                        }
                    }

            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"EIA oil inventory failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 25.0,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class SemiconductorLeadTimeCollector(BaseCollector):
    """Semiconductor lead time from news/industry sources."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "SemiconductorLeadTime"

    def collect(self) -> Dict[str, Any]:
        """Collect semiconductor lead time estimates."""
        try:
            # Scrape from industry news
            response = requests.get(
                "https://news.google.com/rss/search?q=semiconductor+chip+lead+time+weeks",
                headers={'User-Agent': 'Canairy/1.0'},
                timeout=15
            )

            if response.status_code == 200:
                import feedparser
                feed = feedparser.parse(response.content)

                # Look for lead time mentions in weeks
                lead_times = []
                for entry in feed.entries[:20]:
                    text = entry.get('title', '') + ' ' + entry.get('summary', '')
                    # Find patterns like "XX weeks" or "XX-week"
                    matches = re.findall(r'(\d+)[\s-]*weeks?', text.lower())
                    for m in matches:
                        weeks = int(m)
                        if 5 <= weeks <= 52:  # Reasonable range
                            lead_times.append(weeks)

                if lead_times:
                    avg_lead_time = sum(lead_times) / len(lead_times)
                    return {
                        'value': round(avg_lead_time, 0),
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'collector': self.name,
                        'metadata': {
                            'unit': 'weeks',
                            'samples': len(lead_times),
                            'source': 'Industry News',
                            'data_source': 'LIVE'
                        }
                    }

            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Semiconductor lead time failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 15,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class ICEDetentionCollector(BaseCollector):
    """ICE detention data from public statistics."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "ICEDetention"
        self.url = "https://www.ice.gov/detain/detention-management"

    def collect(self) -> Dict[str, Any]:
        """Collect ICE detention statistics."""
        try:
            response = requests.get(
                self.url,
                headers={'User-Agent': 'Canairy/1.0'},
                timeout=15
            )

            if response.status_code == 200:
                text = response.text

                # Look for detention population numbers
                numbers = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*(?:detainees|detained|custody)', text.lower())

                if numbers:
                    # Get largest number (likely total)
                    populations = [int(n.replace(',', '')) for n in numbers]
                    max_pop = max(populations)

                    # Calculate fill rate (capacity ~40,000)
                    capacity = 40000
                    fill_pct = (max_pop / capacity) * 100

                    return {
                        'value': round(fill_pct, 1),
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'collector': self.name,
                        'metadata': {
                            'unit': 'percent_capacity',
                            'population': max_pop,
                            'capacity': capacity,
                            'source': 'ICE',
                            'data_source': 'LIVE'
                        }
                    }

            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"ICE detention failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 75.0,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class HormuzRiskCollector(BaseCollector):
    """Hormuz war risk from shipping/insurance news."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "HormuzRisk"

    def collect(self) -> Dict[str, Any]:
        """Collect Hormuz risk indicators from news."""
        try:
            response = requests.get(
                "https://news.google.com/rss/search?q=strait+hormuz+shipping+attack+iran",
                headers={'User-Agent': 'Canairy/1.0'},
                timeout=15
            )

            if response.status_code == 200:
                import feedparser
                feed = feedparser.parse(response.content)

                risk_score = 0
                keywords = {
                    'attack': 3, 'missile': 3, 'drone': 2, 'seized': 3,
                    'tension': 1, 'threat': 2, 'warning': 1, 'navy': 1,
                    'tanker': 1, 'blockade': 3, 'military': 1
                }

                for entry in feed.entries[:20]:
                    text = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()
                    for kw, weight in keywords.items():
                        if kw in text:
                            risk_score += weight

                # Convert to percentage (0-5% range typical for war risk premium)
                # Raw score ~30 = ~3% typical elevated risk
                risk_pct = min(risk_score / 10, 5.0)

                return {
                    'value': round(risk_pct, 2),
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'percent',
                        'raw_score': risk_score,
                        'source': 'News Analysis',
                        'data_source': 'LIVE'
                    }
                }

            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Hormuz risk failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 0.8,  # 0.8% is typical baseline war risk premium
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class MortgageDelinquencyCollector(BaseCollector):
    """Mortgage delinquency from FRED (free)."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "MortgageDelinquency"
        import os
        self.api_key = os.getenv('FRED_API_KEY', '')
        self.series_id = 'DRSFRMACBS'  # Delinquency Rate on Single-Family Residential Mortgages

    def collect(self) -> Dict[str, Any]:
        """Collect mortgage delinquency from FRED."""
        try:
            response = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    'series_id': self.series_id,
                    'api_key': self.api_key,
                    'file_type': 'json',
                    'sort_order': 'desc',
                    'limit': 1
                },
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                obs = data.get('observations', [])

                if obs:
                    value = float(obs[0].get('value', 0))
                    return {
                        'value': value,
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'collector': self.name,
                        'metadata': {
                            'unit': 'percent',
                            'series': self.series_id,
                            'source': 'FRED',
                            'data_source': 'LIVE'
                        }
                    }

            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Mortgage delinquency failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 2.5,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data


class GoogleTrendsCollector(BaseCollector):
    """Google Trends for AI religion/cult topics (free, no API key)."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "GoogleTrends"
        # We'll use news as proxy since Google Trends API requires authentication
        self.search_terms = ['AI god', 'AI religion', 'AI worship', 'basilisk', 'singularity']

    def collect(self) -> Dict[str, Any]:
        """Collect AI religion trend indicators."""
        try:
            total_mentions = 0

            for term in self.search_terms:
                response = requests.get(
                    f"https://news.google.com/rss/search?q={term.replace(' ', '+')}",
                    headers={'User-Agent': 'Canairy/1.0'},
                    timeout=10
                )

                if response.status_code == 200:
                    import feedparser
                    feed = feedparser.parse(response.content)
                    total_mentions += len(feed.entries)

            # Normalize to trend index (0-100)
            trend_index = min(total_mentions * 2, 100)

            return {
                'value': trend_index,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'trend_index',
                    'news_mentions': total_mentions,
                    'source': 'News/Google',
                    'data_source': 'LIVE'
                }
            }

        except Exception as e:
            self.logger.error(f"Google trends failed: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        return {
            'value': 15,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {'source': 'mock_data', 'data_source': 'MOCK'}
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data and 'value' in data
