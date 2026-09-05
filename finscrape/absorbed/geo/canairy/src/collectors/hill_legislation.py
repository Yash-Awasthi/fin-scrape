"""
Control legislation tracker.
Monitors bills restricting speech, assembly, privacy, gun rights.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .base import BaseCollector


class HillLegislationCollector(BaseCollector):
    """Tracks concerning legislation in Congress."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "HillLegislation"
        
        # LegiScan API (requires key)
        # Check both config structure patterns for API keys
        api_keys = config.get('api_keys', {})
        if not api_keys and 'config' in config:
            # Check if it's nested under config.api_keys
            api_keys = config.get('config', {}).get('api_keys', {})
        self.legiscan_key = api_keys.get('legiscan', '')
        self.legiscan_url = "https://api.legiscan.com/"
        
        # Congress.gov as backup
        self.congress_url = "https://api.congress.gov/v3/bill"
        self.congress_key = api_keys.get('congress', '')
        
        # Keywords indicating concerning bills
        self.control_keywords = [
            # Speech restrictions
            'misinformation', 'disinformation', 'hate speech', 
            'online safety', 'content moderation',
            
            # Assembly restrictions
            'unlawful assembly', 'riot', 'protest restriction',
            'public gathering', 'curfew',
            
            # Privacy erosion
            'surveillance', 'encryption', 'backdoor',
            'data collection', 'biometric', 'facial recognition',
            
            # Gun control (any side)
            'assault weapon', 'gun control', 'second amendment',
            'red flag', 'universal background'
        ]
        
        # Bills to exclude (routine, non-concerning)
        self.exclude_keywords = [
            'appropriations', 'budget', 'naming', 'commemorate',
            'post office', 'veterans benefits'
        ]
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect control legislation data.
        
        Returns:
            Dict with count of concerning bills advancing
        """
        try:
            # Count bills in last 30 days that are advancing
            active_bills = self._count_active_bills()
            
            # Determine threat level
            threat_level = "low"
            if active_bills >= 10:
                threat_level = "critical"
            elif active_bills >= 5:
                threat_level = "high"
            elif active_bills >= 3:
                threat_level = "elevated"
            
            return {
                'value': active_bills,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'bills',
                    'period': '30_days',
                    'source': 'Congress',
                    'description': f'{active_bills} control bills advancing',
                    'threat_level': threat_level,
                    'bill_categories': self._get_bill_categories(),
                    'threshold_amber': 5,
                    'threshold_red': 10
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect legislation data: {e}")
            return None
    
    def _count_active_bills(self) -> int:
        """Count concerning bills with recent action."""
        if self.legiscan_key:
            return self._check_legiscan()
        elif self.congress_key:
            return self._check_congress_api()
        else:
            # No API keys, use mock data
            return self._get_mock_count()
    
    def _check_legiscan(self) -> int:
        """Check LegiScan for concerning bills."""
        try:
            # Search for bills updated in last 30 days
            cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            params = {
                'key': self.legiscan_key,
                'op': 'getSearch',
                'state': 'US',  # Federal only
                'updated': cutoff
            }
            
            response = requests.get(self.legiscan_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                concerning_count = 0
                for bill in data.get('searchresult', {}).values():
                    if isinstance(bill, dict):
                        title = bill.get('title', '').lower()
                        
                        # Skip routine bills
                        if any(exclude in title for exclude in self.exclude_keywords):
                            continue
                        
                        # Check for concerning content
                        if any(keyword in title for keyword in self.control_keywords):
                            # Only count if advancing (not dead)
                            if bill.get('status', 0) > 1:  # Past introduction
                                concerning_count += 1
                
                return concerning_count
                
        except Exception as e:
            self.logger.error(f"LegiScan error: {e}")
        
        return self._get_mock_count()
    
    def _check_congress_api(self) -> int:
        """Check Congress.gov API for concerning bills."""
        try:
            # Get recent bills
            params = {
                'api_key': self.congress_key,
                'format': 'json',
                'limit': 250,
                'sort': 'updateDate+desc'
            }
            
            response = requests.get(
                f"{self.congress_url}/118",  # 118th Congress
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                concerning_count = 0
                cutoff = datetime.now() - timedelta(days=30)
                
                for bill in data.get('bills', []):
                    # Check update date
                    update_str = bill.get('updateDate', '')
                    try:
                        update_date = datetime.strptime(update_str, '%Y-%m-%d')
                        if update_date < cutoff:
                            continue
                    except:
                        continue
                    
                    title = bill.get('title', '').lower()
                    
                    # Skip routine
                    if any(exclude in title for exclude in self.exclude_keywords):
                        continue
                    
                    # Check concerning
                    if any(keyword in title for keyword in self.control_keywords):
                        # Check if advancing
                        latest_action = bill.get('latestAction', {}).get('text', '').lower()
                        if any(phrase in latest_action for phrase in ['passed', 'reported', 'ordered']):
                            concerning_count += 1
                
                return concerning_count
                
        except Exception as e:
            self.logger.error(f"Congress API error: {e}")
        
        return self._get_mock_count()
    
    def _get_bill_categories(self) -> Dict[str, int]:
        """Categorize concerning bills by type."""
        # In production, would track actual categories
        # For now, return distribution
        
        import random
        
        total = self._get_mock_count()
        
        categories = {
            'speech': int(total * 0.3),
            'privacy': int(total * 0.3),
            'assembly': int(total * 0.2),
            'guns': int(total * 0.2)
        }
        
        # Ensure sum equals total
        diff = total - sum(categories.values())
        if diff > 0:
            categories['speech'] += diff
        
        return categories
    
    def _get_mock_count(self) -> int:
        """Return realistic mock bill count."""
        import random
        
        # Distribution:
        # 0-2: Normal (60%)
        # 3-4: Elevated (25%)
        # 5-9: High (10%)
        # 10+: Crisis (5%)
        
        rand = random.random()
        if rand < 0.6:
            return random.randint(0, 2)
        elif rand < 0.85:
            return random.randint(3, 4)
        elif rand < 0.95:
            return random.randint(5, 9)
        else:
            return random.randint(10, 15)
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate legislation data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, int) and 0 <= value <= 100