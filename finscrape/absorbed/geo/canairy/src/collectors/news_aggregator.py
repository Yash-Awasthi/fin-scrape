"""
News aggregator for security/conflict indicators.
Searches news sources for NATO activations, nuclear tests, etc.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import re
from .base import BaseCollector


class NewsAggregatorCollector(BaseCollector):
    """Aggregates news for various security indicators."""
    
    def __init__(self, config, search_terms: List[str], indicator_name: str):
        super().__init__(config)
        self._name = f"NewsAggregator_{indicator_name}"
        self.search_terms = search_terms
        self.indicator_name = indicator_name
        
        # Get News API key from config
        self.news_api_key = config.get('news_api_key', '')
        self.news_api_url = "https://newsapi.org/v2/everything"
        
        # Alternative: Use Google News RSS (no API key needed)
        self.google_news_rss = "https://news.google.com/rss/search"
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Search news for specific terms and count occurrences.
        
        Returns:
            Dict with count of relevant news items
        """
        try:
            # Try News API first if we have a key
            if self.news_api_key and self.news_api_key != '88dd145bb61d4aa0b9655edec04309f8':
                count = self._search_news_api()
                if count is not None:
                    return self._format_result(count, 'news_api')
            
            # Fall back to RSS feeds
            count = self._search_rss_feeds()
            if count is not None:
                return self._format_result(count, 'rss_feeds')
            
            # If all else fails, return mock
            return self._get_mock_data()
            
        except Exception as e:
            self.logger.error(f"Failed to aggregate news: {e}")
            return self._get_mock_data()
    
    def _search_news_api(self) -> Optional[int]:
        """Search using News API."""
        try:
            # Build query from search terms
            query = ' OR '.join(f'"{term}"' for term in self.search_terms)
            
            # Search last 7 days
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            params = {
                'q': query,
                'from': from_date,
                'sortBy': 'relevancy',
                'language': 'en',
                'apiKey': self.news_api_key
            }
            
            response = requests.get(self.news_api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                total_results = data.get('totalResults', 0)
                
                # For some indicators, we want to analyze the articles more closely
                if self.indicator_name == 'NATOReadiness':
                    # Count only articles mentioning actual activations
                    activation_count = 0
                    for article in data.get('articles', []):
                        text = f"{article.get('title', '')} {article.get('description', '')}"
                        if any(word in text.lower() for word in ['activated', 'mobilized', 'deployed']):
                            activation_count += 1
                    return activation_count
                else:
                    return total_results
            
            return None
            
        except Exception as e:
            self.logger.error(f"News API search failed: {e}")
            return None
    
    def _search_rss_feeds(self) -> Optional[int]:
        """Search using RSS feeds as fallback."""
        try:
            count = 0
            
            # Search Google News RSS for each term
            for term in self.search_terms[:3]:  # Limit to avoid rate limiting
                params = {'q': term, 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'}
                
                response = requests.get(
                    self.google_news_rss,
                    params=params,
                    timeout=30,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                if response.status_code == 200:
                    # Count items in RSS feed
                    items = response.text.count('<item>')
                    count += items
            
            return count if count > 0 else None
            
        except Exception as e:
            self.logger.error(f"RSS search failed: {e}")
            return None
    
    def _format_result(self, count: int, source: str) -> Dict[str, Any]:
        """Format the result based on indicator type."""
        metadata = {
            'unit': 'articles',
            'period': '7_days',
            'source': source,
            'search_terms': self.search_terms
        }
        
        # Customize based on indicator
        if self.indicator_name == 'NATOReadiness':
            # For NATO, count of activations is the value
            value = 1 if count >= 2 else 0  # Binary indicator
            metadata['description'] = f'{count} NATO activation articles found'
            metadata['unit'] = 'activations'
        elif self.indicator_name == 'NuclearTests':
            # For nuclear tests, high article count suggests activity
            value = count // 5  # Rough estimate of actual tests
            metadata['description'] = f'Est. {value} nuclear/missile tests based on {count} articles'
            metadata['unit'] = 'tests'
        else:
            value = count
            metadata['description'] = f'{count} relevant news articles'
        
        return {
            'value': value,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': metadata
        }
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data based on indicator type."""
        import random
        
        if self.indicator_name == 'NATOReadiness':
            # Binary: 0 or 1 activation
            value = 1 if random.random() < 0.05 else 0  # 5% chance
            desc = 'NATO forces activated' if value else 'No NATO activations'
        elif self.indicator_name == 'NuclearTests':
            # Number of tests in quarter
            rand = random.random()
            if rand < 0.7:
                value = random.randint(0, 2)
            elif rand < 0.9:
                value = random.randint(3, 5)
            else:
                value = random.randint(6, 10)
            desc = f'{value} nuclear/missile tests (mock)'
        else:
            value = random.randint(0, 50)
            desc = f'{value} news articles (mock)'
        
        return {
            'value': value,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'activations' if self.indicator_name == 'NATOReadiness' else 'tests',
                'period': '7_days',
                'source': 'mock_data',
                'description': desc,
                'search_terms': self.search_terms
            }
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate news aggregator data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, int) and value >= 0