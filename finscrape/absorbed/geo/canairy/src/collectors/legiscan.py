"""
LegiScan collector for monitoring AI surveillance legislation.
Tracks state bills mentioning AI and surveillance/public safety.
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base import BaseCollector


class LegiScanCollector(BaseCollector):
    """Collects AI surveillance bill data from LegiScan API."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "LegiScan"
        # Try to get API key from config/secrets first, then environment
        self.api_key = config.get('api_keys', {}).get('legiscan', '') or os.getenv('LEGISCAN_API_KEY', '')
        self.base_url = "https://api.legiscan.com"
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect AI surveillance bills from LegiScan.
        
        Returns:
            Dict with bill count or None if collection fails
        """
        try:
            if not self.api_key:
                self.logger.warning("No LegiScan API key found, using mock data")
                return self._get_mock_data()
            
            bill_count = self._fetch_ai_bills()
            
            if bill_count is None:
                return None
            
            return {
                'value': bill_count,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'bills',
                    'period': '30_days',
                    'source': 'LegiScan_API',
                    'description': f'{bill_count} AI surveillance bills in last 30 days',
                    'search_terms': 'artificial intelligence AND (public safety OR surveillance)'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect LegiScan data: {e}")
            return None
    
    def _fetch_ai_bills(self) -> Optional[int]:
        """Fetch AI surveillance bills from LegiScan API."""
        try:
            # Search for bills with AI and surveillance keywords
            params = {
                'key': self.api_key,
                'op': 'getSearch',
                'state': 'ALL',
                'query': 'artificial intelligence surveillance "public safety"'
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK':
                    bills = data.get('searchresult', {})
                    
                    # Filter bills from last 30 days
                    cutoff_date = datetime.now() - timedelta(days=30)
                    recent_bills = 0
                    
                    for bill_id, bill_info in bills.items():
                        if bill_id == 'summary':
                            continue
                            
                        # Check if bill was introduced recently
                        last_action = bill_info.get('last_action_date', '')
                        if last_action:
                            action_date = datetime.strptime(last_action, '%Y-%m-%d')
                            if action_date >= cutoff_date:
                                recent_bills += 1
                    
                    self.logger.info(f"Found {recent_bills} AI surveillance bills in last 30 days")
                    return recent_bills
                else:
                    self.logger.error(f"API error: {data.get('status')}")
                    return None
            else:
                self.logger.error(f"API returned status {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to fetch LegiScan data: {e}")
            return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data when API key is not available."""
        import random
        
        # Simulate realistic bill counts
        bill_count = random.randint(2, 8)
        
        return {
            'value': bill_count,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'bills',
                'period': '30_days',
                'source': 'mock_data',
                'description': f'{bill_count} AI surveillance bills (mock)',
                'note': 'Using mock data - set LEGISCAN_API_KEY for real data'
            }
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate LegiScan data."""
        if not data:
            return False
        return 'value' in data and isinstance(data['value'], (int, float))