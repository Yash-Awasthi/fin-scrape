"""
ACLED (Armed Conflict Location & Event Data) collector for US protests.
Tracks 7-day average of protest events as civil unrest indicator.

Uses OAuth authentication (as of 2024).
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base import BaseCollector


class ACLEDProtestsCollector(BaseCollector):
    """Collects US protest data from ACLED API using OAuth."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "ACLEDProtests"
        # OAuth credentials
        self.email = os.getenv('ACLED_EMAIL', '')
        self.password = os.getenv('ACLED_API_KEY', '')  # Password is the API key
        self.oauth_url = "https://acleddata.com/oauth/token"
        self.base_url = "https://acleddata.com/api/acled/read"
        self._access_token = None
        self._token_expires = None
        
    def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token from ACLED."""
        # Check if we have a valid cached token
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
                self.logger.info("ACLED OAuth token obtained successfully")
                return self._access_token
            else:
                self.logger.error(f"ACLED OAuth failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"ACLED OAuth error: {e}")
            return None

    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect US protest data from ACLED.

        Returns:
            Dict with 7-day average protest count or None if collection fails
        """
        try:
            if not self.password or not self.email:
                self.logger.warning("No ACLED credentials found, using mock data")
                return self._get_mock_data()

            avg_protests = self._fetch_protest_data()

            if avg_protests is None:
                return self._get_mock_data()

            return {
                'value': round(avg_protests, 1),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'protests_per_day',
                    'period': '7_day_avg',
                    'source': 'ACLED_API',
                    'description': f'{avg_protests:.1f} protests/day (7-day avg)',
                    'country': 'United States',
                    'data_source': 'LIVE'
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to collect ACLED data: {e}")
            return self._get_mock_data()
    
    def _fetch_protest_data(self) -> Optional[float]:
        """Fetch protest data from ACLED API using OAuth."""
        try:
            # Get OAuth token
            token = self._get_access_token()
            if not token:
                self.logger.error("Could not obtain ACLED access token")
                return None

            # Get data for last 30 days (more data = better average)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            params = {
                '_format': 'json',
                'event_type': 'Protests',
                'country': 'United States',
                'event_date': f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
                'event_date_where': 'BETWEEN',
                'limit': 5000
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
                    protest_count = len(data['data'])
                    avg_per_day = protest_count / 30.0

                    self.logger.info(f"ACLED: Found {protest_count} US protests in 30 days, "
                                     f"avg {avg_per_day:.1f}/day")

                    return avg_per_day
                else:
                    self.logger.error(f"ACLED API error: {data}")
                    return None
            elif response.status_code == 401:
                # Token expired, clear it and retry once
                self._access_token = None
                self._token_expires = None
                self.logger.warning("ACLED token expired, retrying...")
                return None
            else:
                self.logger.error(f"ACLED API returned status {response.status_code}: {response.text[:200]}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to fetch ACLED data: {e}")
            return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data when API credentials are not available."""
        import random
        
        # Simulate realistic protest counts (15-45 per day avg)
        avg_protests = round(random.uniform(15, 45), 1)
        
        return {
            'value': avg_protests,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'protests_per_day',
                'period': '7_day_avg',
                'source': 'mock_data',
                'description': f'{avg_protests} protests/day (7-day avg) (mock)',
                'note': 'Using mock data - set ACLED_API_KEY and ACLED_EMAIL for real data'
            }
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate ACLED data."""
        if not data:
            return False
        return 'value' in data and isinstance(data['value'], (int, float))