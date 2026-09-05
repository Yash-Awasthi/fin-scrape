"""
Congress.gov Bills collector - LegiScan workaround.
Tracks bills related to AI, surveillance, and control measures.

Uses the free Congress.gov API (no key required).
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .base import BaseCollector


class CongressBillsCollector(BaseCollector):
    """Collects bill tracking data from Congress.gov API."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "CongressBills"
        self.base_url = "https://api.congress.gov/v3"
        # Congress.gov API key from environment
        import os
        self.api_key = os.environ.get('CONGRESS_API_KEY', '')

        # Keywords to track for control-related legislation
        self.keywords = [
            'artificial intelligence',
            'surveillance',
            'facial recognition',
            'cbdc',
            'digital currency',
            'emergency powers',
            'martial law',
            'detention'
        ]

    def collect(self) -> Dict[str, Any]:
        """
        Collect count of advancing control-related bills.

        Returns:
            Dict with bill count or mock data
        """
        try:
            bill_count = self._fetch_bills()

            if bill_count is not None:
                return {
                    'value': bill_count,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'bills',
                        'source': 'CONGRESS_GOV',
                        'description': f'{bill_count} control-related bills advancing',
                        'data_source': 'LIVE'
                    }
                }

            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect Congress data: {e}")
            return self._get_mock_data()

    def _fetch_bills(self) -> Optional[int]:
        """Fetch recent bills from Congress.gov API."""
        try:
            # Get bills from current Congress (118th)
            headers = {'Accept': 'application/json'}
            params = {
                'format': 'json',
                'limit': 50,
                'sort': 'updateDate desc'
            }

            if self.api_key:
                params['api_key'] = self.api_key

            # Fetch recent bills
            url = f"{self.base_url}/bill"
            response = requests.get(url, params=params, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                bills = data.get('bills', [])

                # Count bills with concerning keywords in title
                concerning_count = 0
                for bill in bills:
                    title = bill.get('title', '').lower()
                    if any(kw in title for kw in self.keywords):
                        concerning_count += 1
                        self.logger.info(f"Found bill: {bill.get('title', '')[:60]}...")

                self.logger.info(f"Congress: {concerning_count} control-related bills found")
                return concerning_count

            elif response.status_code == 429:
                self.logger.warning("Congress.gov rate limited, using mock")
                return None
            else:
                self.logger.warning(f"Congress.gov returned {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to fetch Congress bills: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data when API unavailable."""
        return {
            'value': 3,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'bills',
                'source': 'mock_data',
                'description': '3 control-related bills (mock)',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate Congress bills data."""
        if not data or 'value' not in data:
            return False
        return isinstance(data['value'], (int, float)) and data['value'] >= 0
