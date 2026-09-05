"""
Strait of Hormuz risk collector.

Monitors shipping insurance rates and naval activity in the Strait of Hormuz
as an indicator of Middle East tensions and oil supply risks.
"""

from typing import Dict, Any
from .base import BaseCollector

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class HormuzRiskCollector(BaseCollector):
    """Collects Strait of Hormuz risk indicators."""
    
    def __init__(self, config):
        """Initialize the Hormuz risk collector."""
        super().__init__(config)
        self.threshold_amber = 1.5  # 1.5% war risk premium
        self.threshold_red = 3.0    # 3.0% war risk premium
        
    def collect(self) -> Dict[str, Any]:
        """
        Collect Hormuz Strait risk data.
        
        Returns:
            Dictionary with war risk premium percentage
        """
        try:
            # Try to use News API if available
            news_api_key = self.config.get_secrets().get('news_api_key')
            
            if news_api_key and news_api_key != 'your-news-api-key-here':
                # Import news collector
                try:
                    from .news_monitor import HormuzNewsCollector
                    news_collector = HormuzNewsCollector(self.config)
                    news_data = news_collector.collect()
                    
                    if news_data and news_data.get('metadata', {}).get('source') == 'news_analysis':
                        return news_data
                except Exception as e:
                    self.logger.warning(f"News API failed, using mock: {e}")
            
            # Fallback to mock data
            war_risk_premium = 0.8  # 0.8% premium
            
            self.logger.info(f"Hormuz war risk premium: {war_risk_premium}% (mock)")
            
            return self._create_reading(
                value=war_risk_premium,
                metadata={
                    'unit': 'percent',
                    'type': 'war_risk_premium',
                    'region': 'strait_of_hormuz',
                    'threshold_amber': self.threshold_amber,
                    'threshold_red': self.threshold_red,
                    'source': 'mock_data',
                    'note': 'Mock data - news monitoring available'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect Hormuz risk data: {e}")
            raise
            
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate the collected Hormuz risk data."""
        if not data or 'value' not in data:
            return False
            
        value = data['value']
        
        # Premium should be between 0 and 10 percent (reasonable bounds)
        if not isinstance(value, (int, float)) or value < 0 or value > 10:
            self.logger.warning(f"Invalid war risk premium: {value}")
            return False
            
        return True
        
    def format_reading(self, data: Dict[str, Any]) -> str:
        """Format the risk premium reading for display."""
        value = data.get('value', 0)
        return f"{value:.1f}% war risk premium"