"""
News monitoring base class for geopolitical indicators.

Monitors news sources for Taiwan Strait and Strait of Hormuz activity.
"""

from typing import Dict, Any, Optional, List
import logging
import requests
from datetime import datetime, timedelta
from .base import BaseCollector


class NewsMonitorCollector(BaseCollector):
    """Base class for news-based monitoring collectors."""
    
    def __init__(self, config, search_terms: List[str], indicator_name: str):
        """Initialize the news monitor."""
        super().__init__(config)
        self.search_terms = search_terms
        self.indicator_name = indicator_name
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def search_news(self, query: str, lookback_days: int = 7) -> Optional[Dict[str, Any]]:
        """
        Search news for specific terms using News API.
        
        Args:
            query: Search query
            lookback_days: How many days back to search
            
        Returns:
            News data or None if search fails
        """
        try:
            api_key = self.config.get_secrets().get('news_api_key')
            
            if not api_key or api_key == 'your-news-api-key-here':
                self.logger.warning(f"No News API key for {self.indicator_name}")
                return None
                
            # News API endpoint
            url = "https://newsapi.org/v2/everything"
            
            # Calculate date range
            to_date = datetime.utcnow()
            from_date = to_date - timedelta(days=lookback_days)
            
            params = {
                'q': query,
                'apiKey': api_key,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'sortBy': 'relevancy',
                'language': 'en',
                'pageSize': 100
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'total_results': data.get('totalResults', 0),
                    'articles': data.get('articles', []),
                    'query': query,
                    'period_days': lookback_days
                }
            elif response.status_code == 426:
                self.logger.error("News API requires paid plan for this timeframe")
                return None
            else:
                self.logger.error(f"News API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to search news: {e}")
            return None
            
    def analyze_sentiment_intensity(self, articles: List[Dict]) -> float:
        """
        Simple intensity analysis based on article count and keywords.
        
        Returns:
            Intensity score 0-100
        """
        if not articles:
            return 0
            
        # Keywords indicating escalation
        escalation_keywords = [
            'military', 'warship', 'fighter', 'missile', 'blockade',
            'invasion', 'conflict', 'tension', 'threat', 'deploy',
            'intercept', 'scramble', 'violation', 'incursion'
        ]
        
        intensity_score = 0
        
        for article in articles[:20]:  # Analyze top 20 most relevant
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = title + ' ' + description
            
            # Count escalation keywords
            keyword_count = sum(1 for keyword in escalation_keywords if keyword in content)
            
            # Add to intensity (max 5 points per article)
            intensity_score += min(keyword_count, 5)
            
        # Normalize to 0-100 scale
        return min(intensity_score, 100)
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate news-based data."""
        if not data:
            return False
        
        required_fields = ['value', 'timestamp', 'collector']
        for field in required_fields:
            if field not in data:
                return False
        
        # Value should be non-negative
        if not isinstance(data['value'], (int, float)) or data['value'] < 0:
            return False
            
        return True


class TaiwanNewsCollector(NewsMonitorCollector):
    """Monitor Taiwan Strait tensions via news."""
    
    def __init__(self, config):
        search_terms = [
            "Taiwan Strait military",
            "PLA Taiwan incursion",
            "Taiwan airspace violation",
            "China Taiwan military exercise"
        ]
        super().__init__(config, search_terms, "Taiwan Strait")
        self._name = "TaiwanZone"
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """Collect Taiwan Strait activity from news."""
        try:
            # Search for recent Taiwan military activity
            all_articles = []
            
            for term in self.search_terms:
                result = self.search_news(term, lookback_days=7)
                if result and result['articles']:
                    all_articles.extend(result['articles'])
                    
            if all_articles:
                # Remove duplicates by URL
                unique_articles = {a['url']: a for a in all_articles}.values()
                intensity = self.analyze_sentiment_intensity(list(unique_articles))
                
                # Convert intensity to incursions estimate (0-30 scale)
                incursions_estimate = int(intensity * 0.3)
                
                self.logger.info(f"Taiwan news intensity: {intensity}, est. incursions: {incursions_estimate}")
                
                return {
                    'value': incursions_estimate,
                    'timestamp': datetime.utcnow().isoformat(),
                    'collector': self.name,
                    'metadata': {
                        'unit': 'incursions_per_week',
                        'source': 'news_analysis',
                        'article_count': len(unique_articles),
                        'intensity_score': intensity,
                        'threshold_amber': 10,
                        'threshold_red': 20,
                        'note': f'Based on {len(unique_articles)} news articles'
                    }
                }
            
            # Fallback to mock data
            return self._get_mock_data()
            
        except Exception as e:
            self.logger.error(f"Failed to collect Taiwan news: {e}")
            return self._get_mock_data()
            
    def _get_mock_data(self):
        """Return mock data when news unavailable."""
        return {
            'value': 8,
            'timestamp': datetime.utcnow().isoformat(),
            'collector': self.name,
            'metadata': {
                'unit': 'incursions_per_week',
                'source': 'mock_data',
                'threshold_amber': 10,
                'threshold_red': 20,
                'note': 'Mock data - add news_api_key for real monitoring'
            }
        }


class HormuzNewsCollector(NewsMonitorCollector):
    """Monitor Strait of Hormuz tensions via news."""
    
    def __init__(self, config):
        search_terms = [
            "Strait of Hormuz tanker",
            "Hormuz shipping threat",
            "Iran navy Hormuz",
            "Persian Gulf oil tanker"
        ]
        super().__init__(config, search_terms, "Strait of Hormuz")
        self._name = "HormuzRisk"
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """Collect Hormuz risk from news."""
        try:
            # Search for Hormuz shipping threats
            all_articles = []
            
            for term in self.search_terms:
                result = self.search_news(term, lookback_days=14)
                if result and result['articles']:
                    all_articles.extend(result['articles'])
                    
            if all_articles:
                unique_articles = {a['url']: a for a in all_articles}.values()
                intensity = self.analyze_sentiment_intensity(list(unique_articles))
                
                # Convert intensity to risk premium estimate (0-5% scale)
                risk_premium = intensity * 0.05
                
                self.logger.info(f"Hormuz news intensity: {intensity}, risk premium: {risk_premium:.2f}%")
                
                return {
                    'value': risk_premium,
                    'timestamp': datetime.utcnow().isoformat(),
                    'collector': self.name,
                    'metadata': {
                        'unit': 'percent',
                        'source': 'news_analysis',
                        'article_count': len(unique_articles),
                        'intensity_score': intensity,
                        'threshold_amber': 1.5,
                        'threshold_red': 3.0,
                        'note': f'Based on {len(unique_articles)} news articles'
                    }
                }
            
            return self._get_mock_data()
            
        except Exception as e:
            self.logger.error(f"Failed to collect Hormuz news: {e}")
            return self._get_mock_data()
            
    def _get_mock_data(self):
        """Return mock data when news unavailable."""
        return {
            'value': 0.8,
            'timestamp': datetime.utcnow().isoformat(),
            'collector': self.name,
            'metadata': {
                'unit': 'percent',
                'source': 'mock_data',
                'threshold_amber': 1.5,
                'threshold_red': 3.0,
                'note': 'Mock data - add news_api_key for real monitoring'
            }
        }