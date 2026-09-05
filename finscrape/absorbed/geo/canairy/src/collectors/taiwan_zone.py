"""
Taiwan Strait activity collector.

Monitors military and civilian activity in the Taiwan Strait region
as an indicator of geopolitical tensions.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from .base import BaseCollector

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class TaiwanZoneCollector(BaseCollector):
    """Collects Taiwan Strait activity data."""
    
    def __init__(self, config):
        """Initialize the Taiwan zone collector."""
        super().__init__(config)
        self.threshold_amber = 10  # 10 incursions/week
        self.threshold_red = 20    # 20 incursions/week
        
    def collect(self) -> Dict[str, Any]:
        """
        Collect Taiwan Strait activity data.
        
        Returns:
            Dictionary with weekly incursion count
        """
        try:
            # Try to use News API if available
            news_api_key = self.config.get_secrets().get('news_api_key')
            
            if news_api_key and news_api_key != 'your-news-api-key-here':
                # Import news collector
                try:
                    from .news_monitor import TaiwanNewsCollector
                    news_collector = TaiwanNewsCollector(self.config)
                    news_data = news_collector.collect()
                    
                    if news_data and news_data.get('metadata', {}).get('source') == 'news_analysis':
                        return news_data
                except Exception as e:
                    self.logger.warning(f"News API failed, using mock: {e}")
            
            # Fallback to mock data
            weekly_incursions = 8
            
            self.logger.info(f"Taiwan Strait incursions: {weekly_incursions}/week (mock)")
            
            return self._create_reading(
                value=weekly_incursions,
                metadata={
                    'unit': 'incursions_per_week',
                    'period': 'last_7_days',
                    'types': ['aircraft', 'naval'],
                    'threshold_amber': self.threshold_amber,
                    'threshold_red': self.threshold_red,
                    'source': 'mock_data',
                    'note': 'Mock data - news monitoring available'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect Taiwan zone data: {e}")
            raise
            
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate the collected Taiwan zone data."""
        if not data or 'value' not in data:
            return False
            
        value = data['value']
        
        # Incursions should be non-negative integer
        if not isinstance(value, int) or value < 0:
            self.logger.warning(f"Invalid incursion count: {value}")
            return False
            
        return True
        
    def format_reading(self, data: Dict[str, Any]) -> str:
        """Format the incursion reading for display."""
        value = data.get('value', 0)
        return f"{value} incursions/week"