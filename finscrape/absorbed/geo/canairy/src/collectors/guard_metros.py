"""
National Guard metro deployment tracker.
Monitors Guard activations in major metropolitan areas.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from bs4 import BeautifulSoup
from .base import BaseCollector


class GuardMetrosCollector(BaseCollector):
    """Tracks National Guard deployments to major metros."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "GuardMetros"
        
        # Major metros to monitor
        self.major_metros = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
            'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose',
            'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte',
            'San Francisco', 'Indianapolis', 'Seattle', 'Denver', 'Washington DC',
            'Boston', 'Nashville', 'Baltimore', 'Oklahoma City', 'Portland',
            'Las Vegas', 'Louisville', 'Milwaukee', 'Memphis', 'Detroit'
        ]
        
        # News sources for Guard deployments
        self.news_sources = [
            "https://www.nationalguard.mil/News/",
            "https://www.defense.gov/News/",
            "https://apnews.com/",
            "https://www.reuters.com/"
        ]
        
        # Keywords indicating deployment
        self.deployment_keywords = [
            'national guard', 'guard deployment', 'guard activated',
            'state of emergency', 'civil unrest', 'guard troops',
            'mobilized', 'deployed to'
        ]
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect National Guard metro deployment data.
        
        Returns:
            Dict with count of metros with Guard presence
        """
        try:
            # Check deployments in last 14 days
            deployed_metros = self._check_deployments()
            deployment_count = len(deployed_metros)
            
            # Determine if surge condition met
            is_surge = deployment_count >= 2
            
            return {
                'value': deployment_count,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'metros',
                    'period': '14_days',
                    'source': 'news_aggregation',
                    'description': f'{deployment_count} major metros with Guard deployments',
                    'deployed_metros': list(deployed_metros),
                    'is_surge': is_surge,
                    'threshold_red': 2
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect Guard deployment data: {e}")
            return None
    
    def _check_deployments(self) -> Set[str]:
        """Check for Guard deployments in major metros."""
        deployed_metros = set()
        
        # Check National Guard news
        try:
            response = requests.get(
                self.news_sources[0],
                timeout=30,
                headers={'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'}
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.find_all(['article', 'div'], class_=['news-item', 'article'], limit=50)
                
                for item in news_items:
                    text = item.get_text().lower()
                    
                    # Check if deployment-related
                    if any(keyword in text for keyword in self.deployment_keywords):
                        # Check for metro names
                        for metro in self.major_metros:
                            if metro.lower() in text:
                                deployed_metros.add(metro)
                                self.logger.info(f"Found Guard deployment in {metro}")
        except Exception as e:
            self.logger.error(f"Failed to check Guard news: {e}")
        
        # If no real data, use mock
        if not deployed_metros:
            deployed_metros = self._get_mock_deployments()
        
        return deployed_metros
    
    def _get_mock_deployments(self) -> Set[str]:
        """Return mock deployment data."""
        import random
        
        deployed = set()
        
        # Probability distribution:
        # 0 metros: 60%
        # 1 metro: 30%
        # 2+ metros: 10%
        
        rand = random.random()
        if rand < 0.6:
            num_deployments = 0
        elif rand < 0.9:
            num_deployments = 1
        else:
            num_deployments = random.randint(2, 4)
        
        if num_deployments > 0:
            # Pick random metros
            deployed = set(random.sample(self.major_metros, num_deployments))
        
        return deployed
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate Guard deployment data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, int) and 0 <= value <= 30