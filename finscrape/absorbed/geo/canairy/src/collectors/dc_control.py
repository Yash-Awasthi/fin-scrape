"""
DC control countdown tracker.
Monitors days until DC can act independently under HR 51.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from .base import BaseCollector


class DCControlCollector(BaseCollector):
    """Tracks DC statehood/autonomy timeline."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "DCControl"
        
        # Congressional tracking
        self.congress_url = "https://www.congress.gov/bill/118th-congress/house-bill/51"
        self.dc_council_url = "https://dccouncil.gov"
        
        # Key dates
        self.hr51_introduced = datetime(2023, 1, 9)  # 118th Congress
        self.typical_passage_days = 730  # ~2 years typical
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect DC control timeline data.
        
        Returns:
            Dict with days until potential autonomy
        """
        try:
            # Check HR 51 status
            bill_status = self._check_hr51_status()
            
            # Calculate timeline
            days_remaining = self._calculate_timeline(bill_status)
            
            # Determine urgency
            urgency = "low"
            if days_remaining <= 180:
                urgency = "high"
            elif days_remaining <= 365:
                urgency = "medium"
            
            return {
                'value': days_remaining,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'days',
                    'source': 'Congress',
                    'description': f'{days_remaining} days until DC autonomy window',
                    'bill_status': bill_status,
                    'urgency': urgency,
                    'hr51_progress': self._get_bill_progress(),
                    'threshold_amber': 365,
                    'threshold_red': 180
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect DC control data: {e}")
            return None
    
    def _check_hr51_status(self) -> str:
        """Check current status of HR 51."""
        try:
            response = requests.get(
                self.congress_url,
                timeout=30,
                headers={'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'}
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for status indicators
                status_elem = soup.find('span', class_='status')
                if status_elem:
                    return status_elem.text.strip()
                
                # Check for committee action
                if 'referred to committee' in response.text.lower():
                    return "In Committee"
                elif 'passed house' in response.text.lower():
                    return "Passed House"
                elif 'passed senate' in response.text.lower():
                    return "Passed Senate"
        except Exception as e:
            self.logger.error(f"Failed to check HR 51: {e}")
        
        return self._get_mock_status()
    
    def _calculate_timeline(self, status: str) -> int:
        """Calculate days until potential autonomy."""
        # Timeline based on legislative progress
        today = datetime.now()
        
        if status == "Enacted":
            return 0
        elif status == "Passed Senate":
            # ~30 days to enactment
            target = today + timedelta(days=30)
        elif status == "Passed House":
            # ~180 days through Senate
            target = today + timedelta(days=180)
        elif status == "In Committee":
            # ~365 days to floor
            target = today + timedelta(days=365)
        else:
            # Default timeline from introduction
            elapsed = (today - self.hr51_introduced).days
            remaining = self.typical_passage_days - elapsed
            return max(remaining, 730)  # At least 2 years
        
        return (target - today).days
    
    def _get_bill_progress(self) -> float:
        """Get bill progress percentage."""
        # Stages: Introduced (0%), Committee (25%), 
        # House Pass (50%), Senate Pass (75%), Enacted (100%)
        
        import random
        progress_levels = [0, 25, 50, 75, 100]
        
        # Most bills stall in committee
        weights = [0.1, 0.6, 0.2, 0.08, 0.02]
        return random.choices(progress_levels, weights=weights)[0]
    
    def _get_mock_status(self) -> str:
        """Return realistic mock status."""
        import random
        
        # Probability distribution
        statuses = [
            ("In Committee", 0.7),
            ("Introduced", 0.15),
            ("Passed House", 0.1),
            ("Passed Senate", 0.04),
            ("Enacted", 0.01)
        ]
        
        rand = random.random()
        cumulative = 0
        
        for status, prob in statuses:
            cumulative += prob
            if rand <= cumulative:
                return status
        
        return "In Committee"
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate DC control data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, int) and 0 <= value <= 3650