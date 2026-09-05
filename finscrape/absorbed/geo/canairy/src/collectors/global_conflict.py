"""
Global conflict intensity collector using ACLED data.
Tracks battle/explosion/remote violence events worldwide.

Uses OAuth authentication (as of 2024).
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base import BaseCollector


class GlobalConflictCollector(BaseCollector):
    """Collects global conflict intensity data from ACLED using OAuth."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "GlobalConflict"
        # OAuth credentials from environment
        self.email = os.getenv('ACLED_EMAIL', '')
        self.password = os.getenv('ACLED_API_KEY', '')
        self.oauth_url = "https://acleddata.com/oauth/token"
        self.base_url = "https://acleddata.com/api/acled/read"
        self._access_token = None
        self._token_expires = None

        # Event types we track for conflict intensity
        self.conflict_events = [
            'Battles',
            'Explosions/Remote violence',
            'Violence against civilians'
        ]

    def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token from ACLED."""
        if self._access_token and self._token_expires:
            if datetime.utcnow() < self._token_expires:
                return self._access_token

        try:
            response = requests.post(
                self.oauth_url,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={
                    'username': self.email,
                    'password': self.password,
                    'grant_type': 'password',
                    'client_id': 'acled'
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get('access_token')
                expires_in = data.get('expires_in', 86400)
                self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 300)
                self.logger.info("ACLED OAuth token obtained for global conflict")
                return self._access_token
            else:
                self.logger.error(f"ACLED OAuth failed: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"ACLED OAuth error: {e}")
            return None

    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect global conflict intensity data.

        Returns:
            Dict with 30-day average conflict events or mock data
        """
        try:
            if not self.password or not self.email:
                self.logger.warning("No ACLED credentials found, using mock data")
                return self._get_mock_response()

            events_avg = self._fetch_conflict_data()

            if events_avg is None:
                return self._get_mock_response()

            return {
                'value': round(events_avg, 1),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'events_per_day',
                    'period': '30_day_avg',
                    'source': 'ACLED_API',
                    'description': f'{events_avg:.1f} conflict events/day (30d avg)',
                    'event_types': self.conflict_events,
                    'data_source': 'LIVE'
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to collect global conflict data: {e}")
            return self._get_mock_response()

    def _fetch_conflict_data(self) -> Optional[float]:
        """Fetch and calculate 30-day average conflict events."""
        try:
            token = self._get_access_token()
            if not token:
                return None

            # Get data for last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            params = {
                'event_date': f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
                'event_type': 'Battles',  # Start with just battles for simpler query
                'limit': 10000
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=30,
                headers={
                    'Authorization': f'Bearer {token}',
                    'User-Agent': 'Canairy/1.0'
                }
            )

            if response.status_code == 200:
                data = response.json()

                if 'data' in data:
                    total_events = len(data['data'])
                    avg_per_day = total_events / 30.0
                    self.logger.info(f"ACLED Global: {total_events} battle events in 30 days, avg {avg_per_day:.1f}/day")
                    return avg_per_day

                return None
            else:
                self.logger.error(f"ACLED API returned {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to fetch ACLED global data: {e}")
            return None

    def _get_mock_response(self) -> Dict[str, Any]:
        """Return mock data for global conflict intensity."""
        import random
        base = random.uniform(200, 280)
        if random.random() < 0.2:
            base *= random.uniform(1.2, 1.5)

        return {
            'value': round(base, 1),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'events_per_day',
                'period': '30_day_avg',
                'source': 'mock_data',
                'description': f'{base:.1f} conflict events/day (mock)',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate global conflict data."""
        if not data:
            return False
        value = data.get('value')
        if not isinstance(value, (int, float)):
            return False
        return 0 <= value <= 10000
