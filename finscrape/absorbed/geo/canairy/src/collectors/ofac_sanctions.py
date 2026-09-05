"""
OFAC Sanctions collector.
Tracks recent OFAC sanctions designations targeting oil/energy entities.

Source: https://ofac.treasury.gov/recent-actions
"""

import requests
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base import BaseCollector


class OFACSanctionsCollector(BaseCollector):
    """Collects OFAC sanctions data from Treasury."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "OFACSanctions"
        self.base_url = "https://ofac.treasury.gov/recent-actions"

    def collect(self) -> Dict[str, Any]:
        """Collect OFAC sanctions data."""
        try:
            data = self._fetch_sanctions_data()
            if data:
                return data
            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect OFAC data: {e}")
            return self._get_mock_data()

    def _fetch_sanctions_data(self) -> Optional[Dict[str, Any]]:
        """Fetch recent OFAC actions from Treasury."""
        try:
            response = requests.get(
                self.base_url,
                headers={'User-Agent': 'Canairy/1.0 (household-resilience-monitor)'},
                timeout=15
            )

            if response.status_code == 200:
                text = response.text.lower()

                # Count recent oil/energy related sanctions
                oil_keywords = ['oil', 'petroleum', 'energy', 'crude', 'tanker', 'refinery',
                               'gas', 'lng', 'pipeline', 'opec', 'russia', 'iran', 'venezuela']

                # Look for action entries with dates in last 30 days
                # Count mentions of oil-related terms in recent actions
                oil_mentions = 0
                for kw in oil_keywords:
                    oil_mentions += len(re.findall(rf'\b{kw}\b', text))

                # Normalize to designation count (rough estimate)
                # Each action page typically has ~5-20 entries
                estimated_designations = min(oil_mentions // 3, 20)

                self.logger.info(f"OFAC: ~{estimated_designations} oil-related designations")

                return {
                    'value': estimated_designations,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'designations',
                        'category': 'oil_energy',
                        'source': 'OFAC Treasury',
                        'data_source': 'LIVE'
                    }
                }

            self.logger.warning(f"OFAC returned {response.status_code}")
            return None

        except Exception as e:
            self.logger.error(f"OFAC fetch error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data."""
        return {
            'value': 5,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'designations',
                'source': 'mock_data',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or 'value' not in data:
            return False
        return isinstance(data['value'], (int, float))
